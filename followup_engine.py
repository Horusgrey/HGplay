"""
followup_engine.py — The autonomy layer. Run daily (cron/Task Scheduler).

Produces TODAY_ACTIONS.md: a prioritized action queue so every working day
starts with an exact list of who to call, who to follow up with, and which
agreements are stale. No thinking required — just execute.

Usage:
    python followup_engine.py            # generate today's action queue
    python followup_engine.py --json     # machine-readable output
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

from heirbud_crm import HeirBudCRM
from outreach_generator import generate_scripts
import compliance

RULES = [
    # (stage, days_stale, action, urgency)
    ("RESPONDED",      1, "CLOSE: They responded — send the agreement TODAY", 1),
    ("AGREEMENT_SENT", 3, "CHASE: Agreement out {days}d with no signature — follow up", 2),
    ("CONTACTED",      3, "FOLLOW-UP: No response in {days}d — second touch (different channel)", 3),
    ("ENRICHED",       0, "CALL: Contact info ready — make the first call", 4),
    ("SIGNED",         2, "FILE: Signed {days}d ago — file with the state NOW", 1),
    ("IDENTIFIED",     7, "ENRICH: Sitting unenriched {days}d — find contact info or archive", 5),
]


def days_since(iso_ts: str) -> int:
    try:
        return (datetime.now() - datetime.fromisoformat(iso_ts)).days
    except (ValueError, TypeError):
        return 999


def build_action_queue(crm: HeirBudCRM) -> list[dict]:
    actions = []
    for stage, min_days, template, urgency in RULES:
        for p in crm.get_prospects_by_stage(stage):
            if p.get("suppression_status") == "SUPPRESSED":
                continue  # opted-out records never surface in the action queue
            log = p.get("contact_log") or []
            ref_ts = max((l["date"] for l in log), default=p.get("updated_at", ""))
            stale = days_since(ref_ts)
            if stale >= min_days:
                actions.append({
                    "urgency": urgency,
                    "stale_days": stale,
                    "property_id": p["property_id"],
                    "name": p["name"],
                    "amount": p["amount"],
                    "stage": stage,
                    "phone": p.get("phone"),
                    "email": p.get("email"),
                    "action": template.format(days=stale),
                    # Published property value × capped fee. NOT booked revenue —
                    # only realized once the owner is actually paid by the state.
                    "estimated_fee_if_recovered": compliance.fee_amount(p["amount"]),
                })
    # urgency first, then amount
    actions.sort(key=lambda a: (a["urgency"], -a["amount"]))
    return actions


def render_markdown(actions: list[dict], summary: dict) -> str:
    today = datetime.now().strftime("%A, %B %d, %Y")
    lines = [f"# HeirBud Daily Actions — {today}", ""]
    lines.append(f"**Pipeline:** {summary['total_prospects']} prospects · "
                 f"${summary['total_pipeline_value']:,.0f} total value")
    lines.append("")
    if not actions:
        lines.append("✅ Nothing stale. Pipeline is current. Go import more prospects.")
        return "\n".join(lines)

    total_fee = sum(a["estimated_fee_if_recovered"] for a in actions)
    lines.append(f"**{len(actions)} actions today** · ${total_fee:,.0f} estimated fees "
                 f"IF every case is recovered (not booked revenue)")
    lines.append("")

    for i, a in enumerate(actions, 1):
        contact = a["phone"] or a["email"] or "⚠ NO CONTACT INFO"
        lines.append(f"## {i}. {a['name']} — ${a['amount']:,.0f}")
        lines.append(f"**{a['action']}**")
        lines.append(f"- Stage: {a['stage']} ({a['stale_days']}d) · Contact: {contact} "
                     f"· Est. fee if recovered: ${a['estimated_fee_if_recovered']:,.0f}")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="Output JSON instead of markdown")
    ap.add_argument("--out", default="TODAY_ACTIONS.md", help="Output file path")
    args = ap.parse_args()

    crm = HeirBudCRM()
    actions = build_action_queue(crm)
    summary = crm.get_pipeline_summary()

    if args.json:
        print(json.dumps({"generated": datetime.now().isoformat(),
                          "actions": actions, "summary": summary}, indent=2))
        return

    md = render_markdown(actions, summary)
    Path(args.out).write_text(md, encoding="utf-8")
    print(md)
    print(f"\n→ Saved to {args.out}")


if __name__ == "__main__":
    main()
