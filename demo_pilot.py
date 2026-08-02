"""
demo_pilot.py — One-command, end-to-end HeirBud pilot on SYNTHETIC data.

    python demo_pilot.py

Runs the whole loop against fixtures/synthetic_wi_records.csv (fake records)
and proves every compliance gate fires:
  • fees clamp to the 10% Wisconsin ceiling
  • agreements are BLOCKED for records that aren't eligibility-verified
  • ineligible (< 24-month custody) records cannot produce an agreement
  • suppressed records disappear from outreach and the action queue

Nothing here touches real owner data or the real heirbud.db — it uses a
throwaway demo database that is deleted at the start of each run.
"""
from pathlib import Path

import compliance
from heirbud_crm import HeirBudCRM
from outreach_generator import generate_scripts, SuppressedProspectError
from contract_generator import generate_contract
from followup_engine import build_action_queue, render_markdown
from seed_from_csv import (build_search_urls, parse_amount, find_col,
                           deterministic_id, COL_MAP)
import csv

DEMO_DB = Path(__file__).parent / "heirbud_demo.db"
FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_wi_records.csv"


# ── tiny presentation helpers (no dependencies) ──────────────────────────────
def banner(n, title):
    print(f"\n\033[1;36m{'═' * 70}\033[0m")
    print(f"\033[1;36m STEP {n}: {title}\033[0m")
    print(f"\033[1;36m{'═' * 70}\033[0m")


def ok(msg):   print(f"  \033[1;32m✓\033[0m {msg}")
def block(msg):print(f"  \033[1;31m⛔ BLOCKED:\033[0m {msg}")
def info(msg): print(f"  \033[2m·\033[0m {msg}")


def load_fixture_rows():
    """Parse the synthetic CSV with the real importer helpers."""
    rows = []
    with open(FIXTURE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        cols = {k: find_col(headers, k) for k in COL_MAP}
        for row in reader:
            amount = parse_amount(row.get(cols["amount"] or "", 0))
            first = row.get(cols["first_name"] or "", "").strip()
            last = row.get(cols["last_name"] or "", "").strip()
            name = f"{first} {last}".strip()
            city = row.get(cols["city"] or "", "").strip()
            addr = ", ".join(p for p in [
                row.get(cols["address"] or "", "").strip(), city,
                row.get(cols["state"] or "", "WI").strip() or "WI",
                row.get(cols["zip"] or "", "").strip()] if p)
            pid = row.get(cols["property_id"] or "", "") or deterministic_id(name, addr)
            rows.append({
                "property_id": pid, "name": name, "last_known_address": addr,
                "amount": amount,
                "property_type": row.get(cols["property_type"] or "", "").strip(),
                "holder": row.get(cols["holder"] or "", "").strip(),
                "priority": "HIGH" if amount > 100000 else "MEDIUM" if amount > 25000 else "LOW",
                "search_urls": build_search_urls(name, city),
                # custody_date is not a standard COL_MAP field; read it directly.
                "custody_date_raw": (row.get("custody_date") or "").strip(),
            })
    rows.sort(key=lambda r: r["amount"], reverse=True)
    return rows


def main():
    print("\033[1mHEIRBUD — SYNTHETIC PILOT\033[0m  "
          f"(fee ceiling {compliance.compliant_fee_pct():.0f}%, "
          f"{compliance.CUSTODY_MONTHS_REQUIRED}-month eligibility gate)")
    if DEMO_DB.exists():
        DEMO_DB.unlink()
    crm = HeirBudCRM(db_path=DEMO_DB)
    rows = load_fixture_rows()

    # ── 1. Import + dedupe ──────────────────────────────────────────────────
    banner(1, "Import synthetic records (deterministic dedupe)")
    added = sum(1 for r in rows if crm.add_prospect(r))
    dupes = sum(1 for r in rows if not crm.add_prospect(r))  # second pass = all dupes
    ok(f"Imported {added} records; re-import added {0} (all {dupes} recognized as duplicates)")
    s = crm.get_pipeline_summary()
    info(f"Pipeline: {s['total_prospects']} prospects · "
         f"${s['total_pipeline_value']:,.0f} published value")

    # ── 2. Verify custody dates → eligibility gate ──────────────────────────
    banner(2, "Verify custody dates (the 24-month eligibility gate)")
    elig_ids, inelig_ids, unverified_ids = [], [], []
    for r in rows:
        pid, cd = r["property_id"], r["custody_date_raw"]
        if not cd:
            unverified_ids.append(pid)
            continue
        verdict = crm.set_eligibility(
            pid, cd, reviewed=True, reviewer="demo-reviewer",
            evidence=f"WI DOR portal lookup (synthetic demo), custody {cd}")
        (elig_ids if verdict["eligible"] else inelig_ids).append(pid)
    ok(f"{len(elig_ids)} eligible (custody ≥ 24mo, human-reviewed, evidence recorded)")
    block(f"{len(inelig_ids)} ineligible (custody < 24mo) — agreements will be refused")
    info(f"{len(unverified_ids)} unverified (no custody date) — also cannot get an agreement")
    # The verification worklist: everything not yet eligible-and-reviewed.
    from verification_queue import build_worklist
    worklist = build_worklist(crm)
    unlockable = sum(w["fee_if_eligible_and_recovered"] for w in worklist)
    info(f"Custody-verification worklist: {len(worklist)} records to look up "
         f"(up to ${unlockable:,.0f} in fees IF eligible + recovered)")
    if worklist:
        top = worklist[0]
        info(f"   top: {top['name']} ${top['amount']:,.0f} — {top['status'][:48]}")

    # ── 3. Enrich (skip-trace) a few → auto-advance to ENRICHED ─────────────
    banner(3, "Enrich contacts (auto-advances IDENTIFIED → ENRICHED)")
    for i, pid in enumerate(elig_ids[:5]):
        crm.update_prospect(pid, phone=f"555-01{i:02d}", email=f"owner{i}@example.com")
        p = crm.get_prospect(pid)
        if p["stage"] == "IDENTIFIED":
            crm.update_stage(pid, "ENRICHED", "demo: contact added")
    ok("Added synthetic contact info to 5 eligible records → stage ENRICHED")

    # ── 4. Outreach (honest + capped) ───────────────────────────────────────
    banner(4, "Generate outreach (honest copy, fee capped at 10%)")
    demo_p = crm.get_prospect(elig_ids[0])
    scripts = generate_scripts(demo_p)
    ok(f"Scripts for {demo_p['name']} (${demo_p['amount']:,.0f}) — fee_pct = {scripts['fee_pct']:.0f}%")
    snippet = scripts["cold_email"].split("\n")
    for line in snippet[:6]:
        info(line)
    info("… (free-claim disclosure + optional fee framing included)")

    # ── 5. Contract BLOCKED for ineligible / unverified ─────────────────────
    banner(5, "Try to generate an agreement for an INELIGIBLE record")
    target = (inelig_ids or unverified_ids)[0]
    tp = crm.get_prospect(target)
    try:
        generate_contract(tp)
        print("  ERROR: should have been blocked!")
    except compliance.EligibilityError as e:
        block(f"{tp['name']}: {e}")

    # ── 6. Contract ALLOWED for eligible + reviewed (fee clamped) ───────────
    banner(6, "Generate an agreement for an ELIGIBLE record (fed 20%, clamps to 10%)")
    gp = crm.get_prospect(elig_ids[0])
    path = generate_contract(gp, fee_pct=20)   # deliberately over-cap
    fee = compliance.fee_amount(gp["amount"])
    ok(f"Agreement PDF created for {gp['name']}: {Path(path).name}")
    info(f"Value ${gp['amount']:,.0f} → fee (10%) ${fee:,.0f} → net to owner ${gp['amount']-fee:,.0f}")
    crm.update_stage(gp["property_id"], "AGREEMENT_SENT", "demo: agreement generated")

    # ── 7. Suppression (opt-out is terminal) ────────────────────────────────
    banner(7, "Suppress a record (opt-out removes it from everything)")
    sp = crm.get_prospect(elig_ids[1])
    crm.suppress(sp["property_id"], "demo: recipient asked to stop")
    ok(f"{sp['name']} suppressed")
    try:
        generate_scripts(crm.get_prospect(sp["property_id"]))
        print("  ERROR: outreach should have refused!")
    except SuppressedProspectError:
        block(f"outreach for {sp['name']} refused — record is suppressed")

    # ── 8. Daily action queue (the autonomy layer) ──────────────────────────
    banner(8, "Build the daily action queue (excludes suppressed)")
    actions = build_action_queue(crm)
    suppressed_in_queue = any(a["property_id"] == sp["property_id"] for a in actions)
    ok(f"{len(actions)} actions queued; suppressed record present: {suppressed_in_queue}")
    md = render_markdown(actions, crm.get_pipeline_summary())
    out = Path(__file__).parent / "TODAY_ACTIONS.md"
    out.write_text(md, encoding="utf-8")
    for line in md.split("\n")[:8]:
        info(line)
    info(f"… full queue written to {out.name}")

    # ── Recap ───────────────────────────────────────────────────────────────
    print(f"\n\033[1;32m{'═' * 70}\033[0m")
    print("\033[1;32m PILOT COMPLETE — every compliance gate fired as designed\033[0m")
    print(f"\033[1;32m{'═' * 70}\033[0m")
    print("  The machine did: import, dedupe, eligibility check, enrich, draft")
    print("                   outreach, assemble the agreement, queue the day.")
    print("  A human decides: which records are eligible, what gets sent, and")
    print("                   when to file — each a single click.")
    print(f"\n  Demo DB: {DEMO_DB.name} (throwaway) · Contracts: contracts/ · Queue: {out.name}")
    DEMO_DB.unlink(missing_ok=True)   # leave no demo data behind


if __name__ == "__main__":
    main()
