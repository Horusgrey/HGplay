"""
verification_queue.py — The custody-date verification workflow.

The 24-month eligibility gate needs a VERIFIED custody date (when the property
entered DOR custody). The audit is explicit that report-year is only a hint, not
a substitute. Wisconsin does not publish a machine API for this, so verification
is a human lookup against the official record — but the machine can make that
lookup fast, prioritized, and auditable.

This tool:
  • builds a worklist of records that cannot yet get an agreement because
    custody is unverified, highest value first (that's where verifying unlocks
    the most fee);
  • gives you, per record, the DOR portal link, the property ID, and the
    report-year hint so the lookup is one click;
  • records the verified custody date WITH evidence and a reviewer, so every
    eligibility decision is attributable.

Usage:
    python verification_queue.py                       # print + write the worklist
    python verification_queue.py --json                # machine-readable
    python verification_queue.py --apply WI-100000=2021-03-01 \
        --evidence "WI DOR portal lookup 2026-08-02; screenshot in Drive" \
        --reviewer zack                                # record one verification
"""
import argparse
import json
from pathlib import Path

from heirbud_crm import HeirBudCRM
import compliance


def build_worklist(crm: HeirBudCRM) -> list[dict]:
    items = []
    for p in crm.needs_custody_verification():
        items.append({
            "property_id": p["property_id"],
            "name": p["name"],
            "amount": p["amount"],
            "holder": p.get("holder", ""),
            "report_year_hint": p.get("report_year") or "—",
            "current_custody_date": p.get("custody_date") or "—",
            "status": p.get("eligibility_reason") or "not yet checked",
            "portal": compliance.STATE_PORTAL,
            "phone": compliance.STATE_PHONE,
            # potential fee IF this verifies eligible and later recovers — not booked.
            "fee_if_eligible_and_recovered": compliance.fee_amount(p["amount"]),
        })
    return items


def render_markdown(items: list[dict]) -> str:
    lines = ["# HeirBud — Custody Verification Worklist", ""]
    if not items:
        lines.append("✅ Every active record has a verified, eligible custody date.")
        return "\n".join(lines)
    unlockable = sum(i["fee_if_eligible_and_recovered"] for i in items)
    lines += [
        f"**{len(items)} records** need a verified custody date before any agreement.",
        f"Verifying them could unlock up to **${unlockable:,.0f}** in fees "
        f"(only if eligible AND recovered — not booked revenue).",
        "",
        f"For each: look up the property at **{items[0]['portal']}** "
        f"(or call {items[0]['phone']}), confirm the date it entered DOR custody, "
        f"then record it:",
        "",
        "```",
        "python verification_queue.py --apply <PID>=<YYYY-MM-DD> \\",
        '    --evidence "<how you confirmed it>" --reviewer <you>',
        "```",
        "",
        "| # | Property ID | Name | Amount | Report-yr hint | Status |",
        "|--:|:--|:--|--:|:--:|:--|",
    ]
    for i, it in enumerate(items, 1):
        lines.append(f"| {i} | {it['property_id']} | {it['name']} | "
                     f"${it['amount']:,.0f} | {it['report_year_hint']} | {it['status']} |")
    lines += ["", "> Report-year is a HINT ONLY. Confirm the actual custody date "
                  "against the official record — do not assume from report year."]
    return "\n".join(lines)


def apply_verification(crm: HeirBudCRM, spec: str, evidence: str, reviewer: str) -> dict:
    if "=" not in spec:
        raise SystemExit("--apply must look like PID=YYYY-MM-DD")
    pid, date = spec.split("=", 1)
    if not evidence.strip():
        raise SystemExit("--evidence is required to record a verification "
                         "(state how you confirmed the custody date).")
    verdict = crm.set_eligibility(pid.strip(), date.strip(), reviewed=True,
                                  reviewer=reviewer or "cli", evidence=evidence.strip())
    if verdict is None:
        raise SystemExit(f"No prospect with property_id {pid!r}")
    return verdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="Output JSON instead of markdown")
    ap.add_argument("--out", default="CUSTODY_VERIFY.md", help="Worklist output path")
    ap.add_argument("--apply", help="Record a verification: PID=YYYY-MM-DD")
    ap.add_argument("--evidence", default="", help="How the custody date was confirmed")
    ap.add_argument("--reviewer", default="", help="Who verified it")
    args = ap.parse_args()

    crm = HeirBudCRM()

    if args.apply:
        verdict = apply_verification(crm, args.apply, args.evidence, args.reviewer)
        state = "ELIGIBLE ✓" if verdict["eligible"] else "still INELIGIBLE"
        print(f"Recorded: {args.apply}  →  {state}\n  {verdict['reason']}")
        return

    items = build_worklist(crm)
    if args.json:
        print(json.dumps({"worklist": items}, indent=2))
        return
    md = render_markdown(items)
    Path(args.out).write_text(md, encoding="utf-8")
    print(md)
    print(f"\n→ Saved to {args.out}")


if __name__ == "__main__":
    main()
