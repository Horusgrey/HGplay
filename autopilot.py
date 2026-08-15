"""
autopilot.py — One command that runs the whole operation up to the human gates.

    python autopilot.py                 # advance the current CRM, write the brief
    python autopilot.py --file wi.csv   # seed from a CSV first, then advance
    python autopilot.py --json          # machine-readable

Everything the machine can safely do on its own, it does: import, score and rank
by achievable value, build a contact-find plan for anyone unenriched, assemble
the verification worklist, and flag who's ready to mail. Then it hands you ONE
operator brief — a short, ranked list of exactly the decisions only a human
should make. Nothing is contacted, sent, or marked eligible automatically.
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

from heirbud_crm import HeirBudCRM
import scoring
import contact_finder
from verification_queue import build_worklist
from analytics import summary as analytics_summary

FIND_WORTH_IT = 45          # findability at/above which chasing contact is worth the minutes


def run(crm: HeirBudCRM) -> dict:
    prospects = crm.get_all_prospects()
    active = [p for p in prospects if p.get("suppression_status") != "SUPPRESSED"]
    ranked = scoring.prioritize(active)

    # 1) FIND — eligible-or-verifiable leads we can't yet reach, worth locating.
    to_find = []
    for lead in ranked:
        p = crm.get_prospect(lead["property_id"])
        if p.get("phone") or p.get("email"):
            continue
        plan = contact_finder.build_plan(p)
        if plan.findability >= FIND_WORTH_IT or lead["score"] >= 55:
            top = plan.strategies[0] if plan.strategies else None
            to_find.append({
                "property_id": lead["property_id"], "name": lead["name"],
                "amount": lead["amount"], "score": lead["score"],
                "findability": plan.findability, "findability_label": plan.findability_label,
                "deceased": plan.deceased_likely, "first_move": top.label if top else "—",
                "first_url": top.url if top else "", "reason": lead["reason"]})

    # 2) VERIFY — records blocked from an agreement until custody is confirmed.
    to_verify = build_worklist(crm)

    # 3) MAIL — eligible, reachable, not yet contacted: ready for an approved letter.
    ready_to_mail = []
    for lead in ranked:
        p = crm.get_prospect(lead["property_id"])
        if (p.get("eligibility_reviewed") and (p.get("phone") or p.get("email"))
                and p["stage"] in ("IDENTIFIED", "ENRICHED")):
            ready_to_mail.append({"property_id": lead["property_id"], "name": lead["name"],
                                  "amount": lead["amount"], "mode": lead["mode"],
                                  "expected_fee": lead["expected_fee"]})

    # 4) REPLIES — anyone who responded and awaits a human.
    waiting = [{"property_id": p["property_id"], "name": p["name"], "amount": p["amount"]}
               for p in crm.get_prospects_by_stage("RESPONDED")]

    # 5) COLLECT — the money loop: invoice those who got paid, nudge the overdue.
    from payment_module import dashboard as pay_dashboard
    pay = pay_dashboard(crm)

    return {
        "generated": datetime.now().isoformat(),
        "counts": {"active": len(active), "to_find": len(to_find),
                   "to_verify": len(to_verify), "ready_to_mail": len(ready_to_mail),
                   "replies_waiting": len(waiting),
                   "to_invoice": len(pay["to_invoice"]), "reminders_due": len(pay["reminders_due"]),
                   "collected_fees": pay["collected_fees"]},
        "find": to_find, "verify": to_verify, "mail": ready_to_mail, "replies": waiting,
        "collect": pay,
        "narrative": analytics_summary(crm)["narrative"],
        "top_leads": ranked[:10],
    }


def render_brief(r: dict) -> str:
    c = r["counts"]
    L = [f"# HeirBud — Operator Brief", f"_{datetime.now().strftime('%A, %B %d, %Y')}_", "",
         "The machine advanced everything it safely can. Here's what needs *you*.", "",
         f"**{c['to_find']}** to find · **{c['to_verify']}** to verify · "
         f"**{c['ready_to_mail']}** ready to mail · **{c['replies_waiting']}** replies waiting", ""]

    L.append("## The story")
    for line in r["narrative"]:
        L.append(f"- {line}")
    L.append("")

    if r["replies"]:
        L.append("## 🔔 Replies waiting — handle these first")
        for x in r["replies"]:
            L.append(f"- **{x['name']}** (${x['amount']:,.0f}) — someone answered. Respond.")
        L.append("")

    col = r.get("collect", {})
    if col.get("to_invoice"):
        L.append("## 💰 Invoice these — they got their money")
        for x in col["to_invoice"]:
            what = "thank-you note" if x["mode"] == "GRATUITY" else f"invoice (${x['fee']:,.0f})"
            L.append(f"- **{x['name']}** — send {what}")
        L.append("")
    if col.get("reminders_due"):
        L.append("## 💵 Gentle fee reminders due")
        for x in col["reminders_due"]:
            L.append(f"- **{x['name']}** — reminder #{x['reminder_number']} · ${x['fee']:,.0f} · "
                     f"{x['days_since_funds']}d since funds")
        L.append("")

    if r["mail"]:
        L.append("## 📮 Ready to mail — approve & send")
        for x in r["mail"]:
            L.append(f"- **{x['name']}** — ${x['amount']:,.0f} · {x['mode'].title()} · "
                     f"est. fee ${x['expected_fee']:,.0f}")
        L.append("")

    if r["find"]:
        L.append("## 🔍 Find these — reachable, worth the minutes")
        for x in r["find"]:
            tag = " · DECEASED→heir" if x["deceased"] else ""
            L.append(f"- **{x['name']}** (${x['amount']:,.0f}) · findable: "
                     f"{x['findability']:.0f} ({x['findability_label']}){tag}")
            L.append(f"  - Start: [{x['first_move']}]({x['first_url']})")
        L.append("")

    if r["verify"]:
        L.append("## 🗂 Verify custody — unlocks agreements")
        for x in r["verify"][:12]:
            L.append(f"- **{x['name']}** (${x['amount']:,.0f}) — {x['status']}")
        if len(r["verify"]) > 12:
            L.append(f"- …and {len(r['verify']) - 12} more")
        L.append("")

    if not any([r["replies"], r["mail"], r["find"], r["verify"]]):
        L.append("✅ Nothing needs a decision right now. Import more leads to keep the engine fed.")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="Seed from this CSV before advancing")
    ap.add_argument("--min-amount", type=float, default=0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default="OPERATOR_BRIEF.md")
    args = ap.parse_args()

    crm = HeirBudCRM()
    if args.file:
        from seed_from_csv import seed
        res = seed(args.file, args.min_amount, 100000, False)
        print(f"Seeded: +{res['added']} added, {res['skipped_duplicates']} dupes\n")

    r = run(crm)
    if args.json:
        print(json.dumps(r, indent=2))
        return
    brief = render_brief(r)
    Path(args.out).write_text(brief, encoding="utf-8")
    print(brief)
    print(f"\n→ Saved to {args.out}")


if __name__ == "__main__":
    main()
