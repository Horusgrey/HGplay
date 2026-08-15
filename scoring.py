"""
scoring.py — Principled lead prioritization. "High dollar ≠ high priority."

The audit is explicit: a $300k estate that needs probate, letters testamentary,
and three heirs is not automatically a better lead than a clean $8k owner claim
you can close in a week. So priority is a blend, not a sort-by-amount:

    value        — recoverable dollars, log-scaled so a whale doesn't erase the
                   pack but still leads
    eligibility  — verified-eligible earns full weight; unverified is discounted;
                   ineligible/suppressed collapse toward zero
    contactability — can we actually reach them?
    fit          — is this a case we can realistically close, given complexity?

Each lead also gets a SEGMENT (owner / estate / trust / business) and a
recommended TRACK — the strategically correct next move — so the operator spends
effort where expected, collectible fee per human hour is highest.

Heuristic weights live here and are meant to be tuned against real pilot data.
Nothing here sends, contacts, or decides eligibility — it only ranks.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

import compliance
import contact_finder

# Close-probability priors by situation. Deliberately conservative; tune later.
P_SIMPLE = 0.60      # a clean individual owner claim
P_COMPLEX = 0.38     # estate/trust/business: bigger, slower, lower close rate
P_UNVERIFIED = 0.50  # multiplier while eligibility is unconfirmed
P_INELIGIBLE = 0.08  # can't contract yet; nearly parked

# Blend weights for the 0–100 priority score.
W_VALUE, W_ELIG, W_CONTACT, W_FIT = 0.42, 0.30, 0.18, 0.10

COMPLEX_SEGMENTS = {"ESTATE", "TRUST", "BUSINESS"}

# The "sweet spot": big enough to be worth the effort, small enough to close
# cleanly. Below the floor it's barely worth a stamp; above the ceiling the
# money usually comes wrapped in probate, multiple heirs, and extra scrutiny —
# so raw size STOPS buying priority and starts costing it.
SWEET_FLOOR = 800.0
SWEET_CEILING = 60000.0
# Property types that signal friction (heavier documentation / more parties).
_HIGH_BARRIER_TYPES = re.compile(
    r"SECURIT|STOCK|DIVIDEND|MUTUAL|BROKERAGE|INSURANCE|ANNUIT|LIFE|SAFE\s*DEPOSIT|MINERAL|ROYALT")


def segment(prospect: dict) -> str:
    """Classify the CLAIMANT type from the owner NAME.

    Only the owner name is inspected — never the holder. The holder is always a
    company (the bank/insurer that reported the property), so including it would
    mislabel every individual whose funds came from a corporation as a business.
    """
    name = str(prospect.get("name", "")).upper()
    if re.search(r"\bESTATE\b|\bDECEASED\b|\bEST OF\b|ESTATE OF", name):
        return "ESTATE"
    if re.search(r"\bTRUST\b|\bTRUSTEE\b|\bLIVING TRUST\b", name):
        return "TRUST"
    if re.search(r"\bLLC\b|\bINC\b|\bCORP\b|\bCOMPANY\b|\bCO\.?\b|DISSOLVED|\bLP\b|\bLTD\b", name):
        return "BUSINESS"
    return "OWNER"


def barrier_score(p: dict, seg: str) -> float:
    """0..1 estimate of how much friction stands between this claim and a payout.

    Barriers = the reasons a huge claim is often NOT the best claim: probate,
    multiple heirs, corporate authority, and the heavier scrutiny that big
    insurance/securities balances attract.
    """
    b = 0.0
    if seg == "ESTATE":
        b += 0.55                     # probate, heirship, documentation
    elif seg == "TRUST":
        b += 0.45
    elif seg == "BUSINESS":
        b += 0.50                     # corporate authority, EIN, dissolution docs
    amount = float(p.get("amount", 0))
    if amount >= 100000:
        b += 0.25                     # large balances draw extra verification
    elif amount >= 50000:
        b += 0.12
    if _HIGH_BARRIER_TYPES.search(str(p.get("property_type", "")).upper()):
        b += 0.15
    return max(0.0, min(1.0, b))


def _value_priority(amount: float) -> float:
    """Sweet-spot value in 0..1 — rewards the achievable middle, tapers the whales.

    Rises with amount up to the sweet ceiling, then DECAYS: past ~$60k, more money
    means more barriers, so it should not keep buying priority.
    """
    if amount <= 0:
        return 0.0
    lo, hi = math.log10(max(amount, 1)), math.log10(SWEET_CEILING)
    base = (lo - math.log10(SWEET_FLOOR)) / (hi - math.log10(SWEET_FLOOR))
    base = max(0.0, min(1.0, base))
    if amount > SWEET_CEILING:                       # taper the megaclaims
        over = (math.log10(amount) - hi) / (math.log10(2_000_000) - hi)
        base = 1.0 - min(0.5, max(0.0, over) * 0.5)  # down to 0.5 at ~$2M
    return round(base, 3)


def _eligibility_score(p: dict) -> float:
    if p.get("suppression_status") == "SUPPRESSED":
        return 0.0
    if p.get("eligibility_reviewed"):
        return 1.0
    if p.get("custody_date"):
        # a custody date on file but not review-eligible → likely too recent
        return 0.35
    return 0.55                      # unverified but unknown — worth verifying


def _reachability(p: dict) -> tuple[float, float]:
    """(contact_score 0..1, findability 0..100). Reachability drives priority now.

    If we already hold a phone/email, reachability is high. If not, we fall back
    to how *findable* the person is (contact_finder) — a findable lead with no
    contact yet is worth more than an unfindable one.
    """
    has_phone, has_email = bool(p.get("phone")), bool(p.get("email"))
    find = contact_finder.build_plan(p).findability
    if has_phone and has_email:
        return 1.0, find
    if has_phone or has_email:
        return 0.75, find
    return round(0.10 + 0.75 * (find / 100), 3), find


def _close_probability(p: dict, seg: str) -> float:
    base = P_COMPLEX if seg in COMPLEX_SEGMENTS else P_SIMPLE
    if p.get("suppression_status") == "SUPPRESSED":
        return 0.0
    base *= (1 - 0.5 * barrier_score(p, seg))        # barriers erode close odds
    if p.get("eligibility_reviewed"):
        return round(base, 4)
    if p.get("custody_date"):        # has a date but not eligible yet
        return round(base * P_INELIGIBLE, 4)
    return round(base * P_UNVERIFIED, 4)


def recommended_track(p: dict, seg: str, score: float) -> str:
    """The strategically correct next move for this lead."""
    if p.get("suppression_status") == "SUPPRESSED":
        return "SUPPRESSED"
    if not p.get("eligibility_reviewed"):
        return "VERIFY FIRST"        # can't contract until custody is confirmed
    if seg in COMPLEX_SEGMENTS:
        return "PREMIUM — specialist handling"   # estate/trust/business, needs docs
    if float(p.get("amount", 0)) < 500:
        return "SELF-SERVE NUDGE"    # too small to justify high touch; point to state
    return "FAST TRACK"              # clean, eligible owner claim


# Below this recovery amount, a formal contract isn't worth the friction — a
# warm gratuity note builds goodwill and referrals and converts better.
GRATUITY_CEILING = 2000.0


def recommended_mode(prospect: dict) -> str:
    """CONTRACT vs GRATUITY, chosen by situation — the operator can always override.

    Small claims → GRATUITY: low friction, high trust, goodwill/referrals; the fee
    wouldn't be worth a signed agreement anyway. Larger or complex claims →
    CONTRACT: enough money on the line to warrant a written, enforceable fee.
    """
    seg = segment(prospect)
    if seg in COMPLEX_SEGMENTS:
        return "CONTRACT"                     # estates/trusts/business: always paper it
    return "GRATUITY" if float(prospect.get("amount", 0)) < GRATUITY_CEILING else "CONTRACT"


@dataclass
class Lead:
    property_id: str
    name: str
    amount: float
    segment: str
    score: float
    expected_fee: float
    track: str
    mode: str = "CONTRACT"
    findability: float = 0.0
    barrier: float = 0.0
    reason: str = ""
    factors: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"property_id": self.property_id, "name": self.name, "amount": self.amount,
                "segment": self.segment, "score": self.score,
                "expected_fee": self.expected_fee, "track": self.track,
                "mode": self.mode, "findability": self.findability,
                "barrier": self.barrier, "reason": self.reason, "factors": self.factors}


def _priority_reason(seg: str, amount: float, barrier: float, find: float, elig: bool) -> str:
    """One plain line on why this lead sits where it does."""
    if seg in COMPLEX_SEGMENTS:
        return f"{seg.title()} — real money but real barriers; specialist track, not a quick win."
    if amount > SWEET_CEILING:
        return "Large balance — worth it, but expect extra scrutiny; not automatically top priority."
    if SWEET_FLOOR <= amount <= SWEET_CEILING:
        base = "Right-sized and clean — the achievable sweet spot."
    else:
        base = "Small — low touch; point them to the free path, keep goodwill."
    if find >= 70:
        base += " Easy to reach."
    elif find < 40:
        base += " Hard to locate — invest in the find first."
    return base


def score_prospect(p: dict) -> Lead:
    seg = segment(p)
    amount = float(p.get("amount", 0))
    v = _value_priority(amount)
    e = _eligibility_score(p)
    c, find = _reachability(p)
    bar = barrier_score(p, seg)
    prob = _close_probability(p, seg)
    fit = prob / P_SIMPLE                      # 0..~1, relative to the easy case
    score = 100 * (W_VALUE * v + W_ELIG * e + W_CONTACT * c + W_FIT * fit)
    if p.get("suppression_status") == "SUPPRESSED":
        score = 0.0
    expected_fee = round(amount * compliance.WI_FEE_CAP * prob, 2)
    mode = (p.get("fee_model") or recommended_mode(p)).upper()
    return Lead(
        property_id=p.get("property_id", ""), name=p.get("name", ""),
        amount=amount, segment=seg, score=round(score, 1),
        expected_fee=expected_fee, track=recommended_track(p, seg, score), mode=mode,
        findability=find, barrier=round(bar, 2),
        reason=_priority_reason(seg, amount, bar, find, bool(p.get("eligibility_reviewed"))),
        factors={"value": round(v, 2), "eligibility": round(e, 2),
                 "contact": round(c, 2), "fit": round(fit, 2),
                 "close_probability": round(prob, 2)})


def prioritize(prospects: list[dict], limit: int | None = None) -> list[dict]:
    """Rank prospects by the holistic priority score — achievable wins first.

    Score (not raw dollars) leads, because it already folds in the sweet-spot
    value curve, barriers, eligibility, and findability — so a clean, reachable,
    right-sized claim outranks a huge-but-barriered one, exactly as it should for
    a solo operator working for cash flow. Expected fee breaks ties and is shown
    alongside so the size of each prize stays visible.
    """
    leads = [score_prospect(p).as_dict() for p in prospects]
    leads.sort(key=lambda l: (l["score"], l["expected_fee"]), reverse=True)
    return leads[:limit] if limit else leads


if __name__ == "__main__":
    demos = [
        {"property_id": "1", "name": "Jane Owner", "amount": 8000, "holder": "US BANK",
         "eligibility_reviewed": True, "phone": "x", "email": "y"},
        {"property_id": "2", "name": "ESTATE OF J. SMITH", "amount": 300000,
         "holder": "METLIFE", "eligibility_reviewed": True, "email": "y"},
        {"property_id": "3", "name": "Bob Unverified", "amount": 50000, "holder": "COINBASE"},
    ]
    for l in prioritize(demos):
        print(f"{l['score']:5.1f}  ${l['expected_fee']:>10,.0f}  {l['segment']:8} "
              f"{l['track']:28} {l['name']}")
