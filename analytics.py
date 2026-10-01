"""
analytics.py — The funnel's story, in numbers and in plain English.

Turns the CRM into the metrics the PRJ-HB7K4 audit asks for (deliverable D-010),
keeping its hard distinction between four different dollar figures that lesser
dashboards blur into one:

    Published value  — what the state lists. NOT revenue.
    Eligible value   — records with a verified, human-reviewed custody date.
    Expected fee     — 10% of eligible value, IF every eligible case recovers.
    Realized fee     — 10% of what has actually been PAID. The only real money.

It also narrates the funnel: where prospects fall out, where the money is, and
what to fix next. Pure computation — no I/O beyond the CRM, fully testable.
"""
from __future__ import annotations

import statistics
from datetime import datetime

import compliance
from heirbud_crm import HeirBudCRM, STAGES

LINEAR = [s for s in STAGES if s != "SUPPRESSED"]   # the forward funnel
PAID_STAGES = {"PAID"}                               # realized money lives here


def _furthest_reached(crm: HeirBudCRM) -> dict[str, int]:
    """Highest linear stage index each prospect has ever touched.

    A prospect at SIGNED has passed through CONTACTED etc., and a suppressed
    record still counts for the stages it reached before opting out — so we take
    the max over its current stage plus every from/to stage in its history.
    """
    hist: dict[str, set[str]] = {}
    for h in crm.get_stage_history():
        hist.setdefault(h["property_id"], set()).update(
            s for s in (h["from_stage"], h["to_stage"]) if s in LINEAR)
    out = {}
    for p in crm.get_all_prospects():
        stages = set(hist.get(p["property_id"], set()))
        if p["stage"] in LINEAR:
            stages.add(p["stage"])
        out[p["property_id"]] = max((LINEAR.index(s) for s in stages), default=0)
    return out


def funnel(crm: HeirBudCRM) -> list[dict]:
    """Count of prospects that reached at least each stage, with step conversion."""
    reached = _furthest_reached(crm)
    counts = [sum(1 for idx in reached.values() if idx >= i) for i in range(len(LINEAR))]
    rows = []
    for i, stage in enumerate(LINEAR):
        prev = counts[i - 1] if i else counts[0]
        step = (counts[i] / prev * 100) if i and prev else (100.0 if i == 0 else 0.0)
        rows.append({"stage": stage, "reached": counts[i],
                     "step_conversion_pct": round(step, 1)})
    return rows


def value_ladder(crm: HeirBudCRM) -> dict:
    """The four-rung money story — kept deliberately distinct."""
    ps = crm.get_all_prospects()
    published = sum(p["amount"] for p in ps)
    eligible = sum(p["amount"] for p in ps if p.get("eligibility_reviewed"))
    # Realized = fees you've actually COLLECTED (claimant paid the fee), not merely
    # claims the state paid. This is the only real money.
    realized = sum(compliance.fee_amount(p["amount"]) for p in ps if p.get("fee_paid"))
    return {
        "published_value": round(published, 2),
        "eligible_value": round(eligible, 2),
        "expected_fee": compliance.fee_amount(eligible),   # 10% of eligible
        "realized_fee": round(realized, 2),                # fees actually collected
        "eligible_pct_of_published": round(eligible / published * 100, 1) if published else 0.0,
    }


def compliance_metrics(crm: HeirBudCRM) -> dict:
    ps = crm.get_all_prospects()
    n = len(ps) or 1
    active = [p for p in ps if p.get("suppression_status") != "SUPPRESSED"]
    verified = [p for p in ps if p.get("eligibility_reviewed")]
    suppressed = [p for p in ps if p.get("suppression_status") == "SUPPRESSED"]
    return {
        "total": len(ps),
        "active": len(active),
        "eligibility_verified": len(verified),
        "eligibility_verified_pct": round(len(verified) / n * 100, 1),
        "suppressed": len(suppressed),
        "suppression_rate_pct": round(len(suppressed) / n * 100, 1),
    }


def _median_days(crm: HeirBudCRM, frm: str, to: str) -> float | None:
    """Median days between two stage transitions, across prospects that made both."""
    by_pid: dict[str, dict[str, str]] = {}
    for h in crm.get_stage_history():
        by_pid.setdefault(h["property_id"], {})
        # first time each stage was entered
        by_pid[h["property_id"]].setdefault(h["to_stage"], h["changed_at"])
    spans = []
    for stages in by_pid.values():
        if frm in stages and to in stages:
            try:
                a = datetime.fromisoformat(stages[frm])
                b = datetime.fromisoformat(stages[to])
                if b >= a:
                    spans.append((b - a).total_seconds() / 86400)
            except (ValueError, TypeError):
                continue
    return round(statistics.median(spans), 1) if spans else None


def cycle_times(crm: HeirBudCRM) -> dict:
    return {
        "contacted_to_responded": _median_days(crm, "CONTACTED", "RESPONDED"),
        "agreement_to_signed": _median_days(crm, "AGREEMENT_SENT", "SIGNED"),
        "signed_to_paid": _median_days(crm, "SIGNED", "PAID"),
    }


def narrate(fn: list[dict], vl: dict, cm: dict) -> list[str]:
    """The Fable layer: turn the numbers into the story a human should hear."""
    lines = []
    ident = fn[0]["reached"] if fn else 0
    lines.append(
        f"{cm['eligibility_verified']} of {ident or cm['total']} records are verified "
        f"eligible for a paid agreement ({cm['eligibility_verified_pct']}%). Everything "
        f"else is blocked from an agreement until its custody date is confirmed.")

    lines.append(
        f"${vl['published_value']:,.0f} of published property narrows to "
        f"${vl['eligible_value']:,.0f} eligible ({vl['eligible_pct_of_published']}%). "
        f"At the 10% cap that's ${vl['expected_fee']:,.0f} in reachable fees — "
        + (f"${vl['realized_fee']:,.0f} realized so far."
           if vl['realized_fee'] else "none realized yet (pilot stage)."))

    # Biggest leak = where the MOST prospects fall out, measured up through PAID.
    # CLOSED is post-money bookkeeping, not an acquisition step, so it's excluded —
    # otherwise a 1→0 CLOSED blip would masquerade as the worst leak.
    leaks = []
    for r in fn[1:]:
        if r["stage"] == "CLOSED":
            continue
        prev = fn[LINEAR.index(r["stage"]) - 1]
        lost = prev["reached"] - r["reached"]
        if lost > 0 and prev["reached"] > 0:
            leaks.append((lost, r, prev["stage"]))
    if leaks:
        lost, worst, prev = max(leaks, key=lambda t: (t[0], -t[1]["step_conversion_pct"]))
        lines.append(
            f"Most prospects stop at {prev} → {worst['stage']}: {lost} fall out there "
            f"({worst['step_conversion_pct']}% carry through). That's where to focus next.")
    else:
        lines.append("No drop-off to report yet — move records deeper into the funnel "
                     "to see where they leak.")

    if cm["suppression_rate_pct"]:
        lines.append(f"{cm['suppression_rate_pct']}% have opted out and are suppressed — "
                     f"honored automatically, never contacted again.")
    return lines


def summary(crm: HeirBudCRM) -> dict:
    fn = funnel(crm)
    vl = value_ladder(crm)
    cm = compliance_metrics(crm)
    return {
        "funnel": fn,
        "value_ladder": vl,
        "compliance": cm,
        "cycle_times": cycle_times(crm),
        "narrative": narrate(fn, vl, cm),
        "fee_cap_pct": compliance.compliant_fee_pct(),
        "generated": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(summary(HeirBudCRM()), indent=2))
