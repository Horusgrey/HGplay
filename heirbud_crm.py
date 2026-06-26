"""
HeirBud CRM — SQLite-backed pipeline tracker for ZGroup LLC.
Stages: IDENTIFIED → ENRICHED → CONTACTED → RESPONDED → AGREEMENT_SENT → SIGNED → FILED → PAID → CLOSED
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "heirbud.db"

STAGES = ["IDENTIFIED", "ENRICHED", "CONTACTED", "RESPONDED",
          "AGREEMENT_SENT", "SIGNED", "FILED", "PAID", "CLOSED"]


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

    # ── PROSPECTS ──
    def add_prospect(self, p: dict) -> bool:
        """Insert prospect; returns False if already exists."""
        now = datetime.now().isoformat()
        try:
            with self._conn() as c:
                c.execute("""INSERT INTO prospects
                    (property_id, name, last_known_address, amount, property_type,
                     holder, priority, stage, phone, email, notes, search_urls,
                     created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (str(p["property_id"]), p["name"], p.get("last_known_address", ""),
                     float(p.get("amount", 0)), p.get("property_type", ""),
                     p.get("holder", ""), p.get("priority", "MEDIUM"),
                     p.get("stage", "IDENTIFIED"), p.get("phone"), p.get("email"),
                     p.get("notes", ""), json.dumps(p.get("search_urls", {})),
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
                   "priority", "phone", "email", "notes", "search_urls"}
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
        d["contact_log"] = self.get_contact_log(d["property_id"])
        return d

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
        # Auto-advance stage on key outcomes
        auto = {"Answered": "CONTACTED", "Sent": "CONTACTED", "Replied": "RESPONDED",
                "Agreement Sent": "AGREEMENT_SENT", "Signed": "SIGNED", "Paid": "PAID"}
        if outcome in auto:
            current = self.get_prospect(property_id)["stage"]
            if STAGES.index(auto[outcome]) > STAGES.index(current):
                self.update_stage(property_id, auto[outcome], f"Auto: {outcome}")
        return True

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
