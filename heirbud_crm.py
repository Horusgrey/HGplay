"""
HeirBud CRM — SQLite-backed pipeline tracker for ZGroup LLC.
Stages: IDENTIFIED → ENRICHED → CONTACTED → RESPONDED → AGREEMENT_SENT → SIGNED → FILED → PAID → CLOSED

Compliance fields (per PRJ-HB7K4 audit) track custody date, eligibility
review, consent, and suppression so no agreement can be generated for an
ineligible or opted-out record. SUPPRESSED is a terminal stage: a record
there must never be contacted again.
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "heirbud.db"

STAGES = ["IDENTIFIED", "ENRICHED", "CONTACTED", "RESPONDED",
          "AGREEMENT_SENT", "SIGNED", "FILED", "PAID", "CLOSED", "SUPPRESSED"]

# Columns added after v1. Migrated in on open so existing DBs keep working.
COMPLIANCE_COLUMNS = {
    "custody_date": "TEXT",             # verified DOR custody date (ISO or year)
    "eligibility_reviewed": "INTEGER DEFAULT 0",  # 1 once a human confirms
    "eligibility_reason": "TEXT DEFAULT ''",       # last eligibility verdict
    "consent_status": "TEXT DEFAULT 'NONE'",       # NONE | GIVEN | WITHDRAWN
    "suppression_status": "TEXT DEFAULT 'ACTIVE'", # ACTIVE | SUPPRESSED
    "source_verified_date": "TEXT",     # when the state record was re-verified
    "custody_evidence": "TEXT DEFAULT ''",  # how custody date was confirmed (source/url/note)
    "report_year": "TEXT",              # HINT ONLY — not a substitute for custody_date
}


class HeirBudCRM:
    def __init__(self, db_path=DB_PATH):
        self.db_path = str(db_path)
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS prospects (
                property_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                last_known_address TEXT,
                amount REAL DEFAULT 0,
                property_type TEXT,
                holder TEXT,
                priority TEXT DEFAULT 'MEDIUM',
                stage TEXT DEFAULT 'IDENTIFIED',
                phone TEXT,
                email TEXT,
                notes TEXT DEFAULT '',
                search_urls TEXT DEFAULT '{}',
                custody_date TEXT,
                eligibility_reviewed INTEGER DEFAULT 0,
                eligibility_reason TEXT DEFAULT '',
                consent_status TEXT DEFAULT 'NONE',
                suppression_status TEXT DEFAULT 'ACTIVE',
                source_verified_date TEXT,
                custody_evidence TEXT DEFAULT '',
                report_year TEXT,
                created_at TEXT,
                updated_at TEXT
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS contact_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id TEXT NOT NULL,
                method TEXT,
                outcome TEXT,
                notes TEXT,
                logged_at TEXT,
                FOREIGN KEY (property_id) REFERENCES prospects(property_id)
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS stage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id TEXT NOT NULL,
                from_stage TEXT,
                to_stage TEXT,
                notes TEXT,
                changed_at TEXT
            )""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_stage ON prospects(stage)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_amount ON prospects(amount)")
            # Migrate compliance columns onto pre-existing databases.
            existing = {r[1] for r in c.execute("PRAGMA table_info(prospects)")}
            for col, decl in COMPLIANCE_COLUMNS.items():
                if col not in existing:
                    c.execute(f"ALTER TABLE prospects ADD COLUMN {col} {decl}")

    # ── PROSPECTS ──
    def add_prospect(self, p: dict) -> bool:
        """Insert prospect; returns False if already exists."""
        now = datetime.now().isoformat()
        try:
            with self._conn() as c:
                c.execute("""INSERT INTO prospects
                    (property_id, name, last_known_address, amount, property_type,
                     holder, priority, stage, phone, email, notes, search_urls,
                     custody_date, eligibility_reviewed, eligibility_reason,
                     consent_status, suppression_status, source_verified_date,
                     custody_evidence, report_year,
                     created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (str(p["property_id"]), p["name"], p.get("last_known_address", ""),
                     float(p.get("amount", 0)), p.get("property_type", ""),
                     p.get("holder", ""), p.get("priority", "MEDIUM"),
                     p.get("stage", "IDENTIFIED"), p.get("phone"), p.get("email"),
                     p.get("notes", ""), json.dumps(p.get("search_urls", {})),
                     p.get("custody_date"), int(bool(p.get("eligibility_reviewed", 0))),
                     p.get("eligibility_reason", ""), p.get("consent_status", "NONE"),
                     p.get("suppression_status", "ACTIVE"), p.get("source_verified_date"),
                     p.get("custody_evidence", ""), p.get("report_year"),
                     now, now))
            return True
        except sqlite3.IntegrityError:
            return False

    def get_prospect(self, property_id: str) -> dict | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM prospects WHERE property_id=?",
                            (str(property_id),)).fetchone()
        return self._hydrate(row) if row else None

    def get_all_prospects(self, stage=None, min_amount=None) -> list[dict]:
        q = "SELECT * FROM prospects WHERE 1=1"
        args = []
        if stage:
            q += " AND stage=?"
            args.append(stage)
        if min_amount:
            q += " AND amount>=?"
            args.append(min_amount)
        q += " ORDER BY amount DESC"
        with self._conn() as c:
            rows = c.execute(q, args).fetchall()
        return [self._hydrate(r) for r in rows]

    def update_prospect(self, property_id: str, **fields) -> bool:
        allowed = {"name", "last_known_address", "amount", "property_type", "holder",
                   "priority", "phone", "email", "notes", "search_urls",
                   "custody_date", "eligibility_reviewed", "eligibility_reason",
                   "consent_status", "suppression_status", "source_verified_date",
                   "custody_evidence", "report_year"}
        sets, args = [], []
        for k, v in fields.items():
            if k in allowed:
                if k == "search_urls" and isinstance(v, dict):
                    v = json.dumps(v)
                sets.append(f"{k}=?")
                args.append(v)
        if not sets:
            return False
        sets.append("updated_at=?")
        args.append(datetime.now().isoformat())
        args.append(str(property_id))
        with self._conn() as c:
            cur = c.execute(f"UPDATE prospects SET {','.join(sets)} WHERE property_id=?", args)
        return cur.rowcount > 0

    def _hydrate(self, row) -> dict:
        d = dict(row)
        try:
            d["search_urls"] = json.loads(d.get("search_urls") or "{}")
        except (json.JSONDecodeError, TypeError):
            d["search_urls"] = {}
        d["eligibility_reviewed"] = bool(d.get("eligibility_reviewed"))
        d["contact_log"] = self.get_contact_log(d["property_id"])
        return d

    # ── ELIGIBILITY / CONSENT ──
    def set_eligibility(self, property_id: str, custody_date: str,
                        reviewed: bool = False, reviewer: str = "",
                        evidence: str = "") -> dict | None:
        """Record a verified custody date (with evidence) and re-run the check.

        Returns the compliance verdict dict, or None if the prospect is absent.
        Marking ``reviewed=True`` asserts a human confirmed the state record;
        only then can an agreement be generated (see compliance.assert_agreement_allowed).
        ``evidence`` should say HOW custody was confirmed (e.g. "WI DOR portal
        lookup 2026-08-02, property WI-100000, screenshot in Drive/…"). Marking
        reviewed=True without evidence is refused — a review must be attributable.
        """
        from compliance import check_eligibility  # local import avoids cycle at import time
        if not self.get_prospect(property_id):
            return None
        if reviewed and not (evidence or "").strip():
            raise ValueError("A reviewed eligibility decision requires evidence "
                             "(how the custody date was confirmed).")
        verdict = check_eligibility(custody_date)
        self.update_prospect(
            property_id,
            custody_date=custody_date,
            eligibility_reviewed=int(bool(reviewed and verdict.eligible)),
            eligibility_reason=verdict.reason,
            custody_evidence=evidence,
            source_verified_date=datetime.now().isoformat() if reviewed else None,
        )
        if reviewer or evidence:
            self.log_contact_attempt(property_id, "System", "Eligibility Reviewed",
                                     f"{reviewer or 'reviewer'}: {verdict.reason} | {evidence}".strip())
        return verdict.as_dict()

    def needs_custody_verification(self) -> list[dict]:
        """Records that cannot yet get an agreement because custody is unverified.

        Returns active (non-suppressed) prospects that lack a human-reviewed,
        eligible custody date — i.e. the custody-verification worklist. Highest
        value first, since that is where a verified eligible date unlocks the
        most fee.
        """
        out = []
        for p in self.get_all_prospects():
            if p.get("suppression_status") == "SUPPRESSED":
                continue
            if p.get("eligibility_reviewed") and p.get("custody_date"):
                continue  # already verified + eligible (reviewed only set when eligible)
            out.append(p)
        out.sort(key=lambda r: r.get("amount", 0), reverse=True)
        return out

    def suppress(self, property_id: str, reason: str = "") -> bool:
        """Opt a record out of all future outreach. Terminal and irreversible in flow."""
        if not self.get_prospect(property_id):
            return False
        self.update_prospect(property_id, suppression_status="SUPPRESSED",
                             consent_status="WITHDRAWN")
        self.update_stage(property_id, "SUPPRESSED", reason or "Suppressed")
        return True

    def record_consent(self, property_id: str, source: str = "owner-portal") -> bool:
        """Owner opted IN to assistance. Records consent and moves to RESPONDED.

        Refused for suppressed records — an opt-out is never overridden.
        """
        p = self.get_prospect(property_id)
        if not p or p.get("suppression_status") == "SUPPRESSED":
            return False
        self.update_prospect(property_id, consent_status="GIVEN")
        # Neutral outcome so we control the transition (no accidental double-advance).
        self.log_contact_attempt(property_id, source, "Consent Given",
                                 "Owner requested assistance")
        if p["stage"] not in ("CLOSED",) and STAGES.index("RESPONDED") > STAGES.index(p["stage"]):
            self.update_stage(property_id, "RESPONDED", "Owner requested help via portal")
        return True

    # ── STAGE ──
    def update_stage(self, property_id: str, stage: str, notes: str = "") -> bool:
        if stage not in STAGES:
            raise ValueError(f"Invalid stage: {stage}. Must be one of {STAGES}")
        p = self.get_prospect(property_id)
        if not p:
            return False
        now = datetime.now().isoformat()
        with self._conn() as c:
            c.execute("UPDATE prospects SET stage=?, updated_at=? WHERE property_id=?",
                      (stage, now, str(property_id)))
            c.execute("""INSERT INTO stage_history (property_id, from_stage, to_stage, notes, changed_at)
                         VALUES (?,?,?,?,?)""",
                      (str(property_id), p["stage"], stage, notes, now))
        return True

    # ── CONTACT LOG ──
    def log_contact_attempt(self, property_id: str, method: str, outcome: str, notes: str = "") -> bool:
        if not self.get_prospect(property_id):
            return False
        with self._conn() as c:
            c.execute("""INSERT INTO contact_log (property_id, method, outcome, notes, logged_at)
                         VALUES (?,?,?,?,?)""",
                      (str(property_id), method, outcome, notes, datetime.now().isoformat()))
        # Auto-advance stage on key outcomes — but never resurrect a suppressed record.
        auto = {"Answered": "CONTACTED", "Sent": "CONTACTED", "Replied": "RESPONDED",
                "Agreement Sent": "AGREEMENT_SENT", "Signed": "SIGNED", "Paid": "PAID"}
        if outcome in auto:
            current = self.get_prospect(property_id)["stage"]
            if current != "SUPPRESSED" and STAGES.index(auto[outcome]) > STAGES.index(current):
                self.update_stage(property_id, auto[outcome], f"Auto: {outcome}")
        return True

    def get_stage_history(self, property_id: str | None = None) -> list[dict]:
        """Stage transitions, oldest first. All prospects, or one if given."""
        q = "SELECT property_id, from_stage, to_stage, notes, changed_at FROM stage_history"
        args = []
        if property_id:
            q += " WHERE property_id=?"
            args.append(str(property_id))
        q += " ORDER BY changed_at"
        with self._conn() as c:
            return [dict(r) for r in c.execute(q, args).fetchall()]

    def get_contact_log(self, property_id: str) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("""SELECT method, outcome, notes, logged_at as date
                                FROM contact_log WHERE property_id=?
                                ORDER BY logged_at""", (str(property_id),)).fetchall()
        return [dict(r) for r in rows]

    # ── REPORTING ──
    def get_pipeline_summary(self) -> dict:
        with self._conn() as c:
            rows = c.execute("""SELECT stage, COUNT(*) as n, COALESCE(SUM(amount),0) as total
                                FROM prospects GROUP BY stage""").fetchall()
        summary = {s: {"count": 0, "value": 0.0} for s in STAGES}
        for r in rows:
            if r["stage"] in summary:
                summary[r["stage"]] = {"count": r["n"], "value": round(r["total"], 2)}
        total = self._conn().execute(
            "SELECT COUNT(*) as n, COALESCE(SUM(amount),0) as v FROM prospects").fetchone()
        return {"stages": summary,
                "total_prospects": total["n"],
                "total_pipeline_value": round(total["v"], 2)}

    def get_prospects_by_stage(self, stage: str) -> list[dict]:
        return self.get_all_prospects(stage=stage)

    def needs_followup(self, days: int = 3) -> list[dict]:
        """Prospects contacted >N days ago with no response."""
        cutoff = datetime.now().timestamp() - days * 86400
        out = []
        for p in self.get_all_prospects(stage="CONTACTED"):
            log = p["contact_log"]
            if not log:
                continue
            last = max(log, key=lambda x: x["date"])
            try:
                last_ts = datetime.fromisoformat(last["date"]).timestamp()
                if last_ts < cutoff:
                    out.append(p)
            except (ValueError, TypeError):
                continue
        return out


if __name__ == "__main__":
    crm = HeirBudCRM()
    print(json.dumps(crm.get_pipeline_summary(), indent=2))
