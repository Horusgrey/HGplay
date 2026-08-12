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

# Close-probability priors by situation. Deliberately conservative; tune later.
P_SIMPLE = 0.60      # a clean individual owner claim
P_COMPLEX = 0.38     # estate/trust/business: bigger, slower, lower close rate
P_UNVERIFIED = 0.50  # multiplier while eligibility is unconfirmed
P_INELIGIBLE = 0.08  # can't contract yet; nearly parked

# Blend weights for the 0–100 priority score.
W_VALUE, W_ELIG, W_CONTACT, W_FIT = 0.42, 0.30, 0.18, 0.10

COMPLEX_SEGMENTS = {"ESTATE", "TRUST", "BUSINESS"}


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


def _value_score(amount: float) -> float:
    """Log-scaled 0..1. ~$100 → ~0, ~$300k → ~1. A whale leads but doesn't erase the pack."""
    if amount <= 0:
        return 0.0
    return max(0.0, min(1.0, (math.log10(amount) - 2) / (math.log10(300000) - 2)))


def _eligibility_score(p: dict) -> float:
    if p.get("suppression_status") == "SUPPRESSED":
        return 0.0
    if p.get("eligibility_reviewed"):
        return 1.0
    if p.get("custody_date"):
        # a custody date on file but not review-eligible → likely too recent
        return 0.35
    return 0.55                      # unverified but unknown — worth verifying


def _contact_score(p: dict) -> float:
    has_phone, has_email = bool(p.get("phone")), bool(p.get("email"))
    if has_phone and has_email:
        return 1.0
    if has_phone or has_email:
        return 0.7
    return 0.2


def _close_probability(p: dict, seg: str) -> float:
    base = P_COMPLEX if seg in COMPLEX_SEGMENTS else P_SIMPLE
    if p.get("suppression_status") == "SUPPRESSED":
        return 0.0
    if p.get("eligibility_reviewed"):
        return base
    if p.get("custody_date"):        # has a date but not eligible yet
        return base * P_INELIGIBLE
    return base * P_UNVERIFIED


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
    factors: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"property_id": self.property_id, "name": self.name, "amount": self.amount,
                "segment": self.segment, "score": self.score,
                "expected_fee": self.expected_fee, "track": self.track,
                "mode": self.mode, "factors": self.factors}


def score_prospect(p: dict) -> Lead:
    seg = segment(p)
    v, e, c = _value_score(float(p.get("amount", 0))), _eligibility_score(p), _contact_score(p)
    # fit = how closeable, given complexity
    prob = _close_probability(p, seg)
    fit = prob / P_SIMPLE                      # 0..~1, relative to the easy case
    score = 100 * (W_VALUE * v + W_ELIG * e + W_CONTACT * c + W_FIT * fit)
    if p.get("suppression_status") == "SUPPRESSED":
        score = 0.0
    expected_fee = round(float(p.get("amount", 0)) * compliance.WI_FEE_CAP * prob, 2)
    # An explicit per-prospect fee_model wins; otherwise recommend by situation.
    mode = (p.get("fee_model") or recommended_mode(p)).upper()
    return Lead(
        property_id=p.get("property_id", ""), name=p.get("name", ""),
        amount=float(p.get("amount", 0)), segment=seg, score=round(score, 1),
        expected_fee=expected_fee, track=recommended_track(p, seg, score), mode=mode,
        factors={"value": round(v, 2), "eligibility": round(e, 2),
                 "contact": round(c, 2), "fit": round(fit, 2),
                 "close_probability": round(prob, 2)})


def prioritize(prospects: list[dict], limit: int | None = None) -> list[dict]:
    """Score and rank prospects by expected, collectible fee — highest first."""
    leads = [score_prospect(p).as_dict() for p in prospects]
    # Primary sort by expected fee (dollars you can actually bank), then raw score.
    leads.sort(key=lambda l: (l["expected_fee"], l["score"]), reverse=True)
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
