"""
compliance.py — Single source of truth for unclaimed-property locator rules.

Per the HEIRBUD Scope Audit (PRJ-HB7K4, 2026-07-30), every fee, agreement,
outreach, and dashboard projection must derive from ONE place. This is that
place. No other module should hard-code a fee percentage or an eligibility
rule — they import from here.

Rules encoded here reflect Wisconsin DOR "Heir Finders or Locator Services"
guidance (dated 2025-11-04) as summarized in the project compliance pack:

  1. A locator's fee may not exceed 10% of the value actually recovered.
  2. A locator agreement is VOID if the property has been in DOR custody for
     less than 24 months. No agreement may be generated before then.
  3. Approved outreach must make the free state-claim option unmistakable and
     must not misrepresent the locator as the state or use false urgency.

LEGAL NOTE: This module is an operational control, not legal advice. Values
must be validated against current official guidance and qualified counsel
before any live agreement or paid locator activity. Update WI_GUIDANCE_DATE
whenever the rules are re-verified.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

# ── Wisconsin rule pack ──────────────────────────────────────────────────────
STATE = "WI"
WI_GUIDANCE_DATE = "2025-11-04"          # last date the rules below were verified
WI_FEE_CAP = 0.10                        # 10% max of recovered value
CUSTODY_MONTHS_REQUIRED = 24             # agreement void if custody < 24 months
FEE_PAYMENT_WINDOW_DAYS = 30             # fee due within N days of owner payment

# The single disclosure string. Do not paraphrase it in other modules.
FREE_CLAIM_DISCLOSURE = (
    "You have the right to claim this property yourself, directly from the "
    "State of Wisconsin, at no cost. Visit revenue.wi.gov/Pages/UnclaimedProperty "
    "or call (608) 267-7977. ZGroup LLC is a private locator service, is not the "
    "State of Wisconsin or any government agency, and its assistance is optional."
)

STATE_PORTAL = "revenue.wi.gov/Pages/UnclaimedProperty"
STATE_PHONE = "(608) 267-7977"


# ── Fee ──────────────────────────────────────────────────────────────────────
def cap_fee_pct(requested_pct: float) -> float:
    """Clamp any requested fee percentage to the state ceiling.

    Accepts either a fraction (0.10) or a whole percent (10) and always
    returns a whole percent, never above the cap.
    """
    pct = requested_pct * 100 if requested_pct <= 1 else float(requested_pct)
    return min(pct, WI_FEE_CAP * 100)


def compliant_fee_pct() -> float:
    """The default, always-safe fee percentage (whole percent)."""
    return WI_FEE_CAP * 100


def fee_amount(recovered_value: float, fee_pct: Optional[float] = None) -> float:
    """Fee owed on a recovered amount, using a capped percentage."""
    pct = cap_fee_pct(fee_pct) if fee_pct is not None else compliant_fee_pct()
    return round(float(recovered_value) * pct / 100, 2)


# ── Custody / eligibility ────────────────────────────────────────────────────
def _months_between(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


def _coerce_date(value) -> Optional[date]:
    """Parse a custody date from an ISO string, a year, or a date/datetime."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    # Bare year (e.g. "2021") → treat as Jan 1 of that year, conservatively.
    if s.isdigit() and len(s) == 4:
        return date(int(s), 1, 1)
    try:
        return datetime.fromisoformat(s).date()
    except ValueError:
        return None


@dataclass
class Eligibility:
    eligible: bool
    reason: str
    custody_months: Optional[int] = None
    custody_date: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "eligible": self.eligible,
            "reason": self.reason,
            "custody_months": self.custody_months,
            "custody_date": self.custody_date,
        }


def check_eligibility(custody_date, as_of: Optional[date] = None) -> Eligibility:
    """Is this record eligible for a *paid* locator agreement?

    Requires a verified custody date (when the property entered DOR custody)
    at least CUSTODY_MONTHS_REQUIRED months in the past. Without a verified
    custody date the record is INELIGIBLE by default — the audit is explicit
    that report-year is not a substitute for a verified custody date.
    """
    as_of = as_of or date.today()
    d = _coerce_date(custody_date)
    if d is None:
        return Eligibility(
            eligible=False,
            reason="No verified custody date on record. Verify the DOR custody "
                   "date before any agreement can be generated.",
            custody_date=None,
        )
    months = _months_between(d, as_of)
    if months < CUSTODY_MONTHS_REQUIRED:
        return Eligibility(
            eligible=False,
            reason=f"Property in custody {months} months (< {CUSTODY_MONTHS_REQUIRED} "
                   f"required). A locator agreement would be void.",
            custody_months=months,
            custody_date=d.isoformat(),
        )
    return Eligibility(
        eligible=True,
        reason=f"Eligible: in custody {months} months (>= {CUSTODY_MONTHS_REQUIRED}).",
        custody_months=months,
        custody_date=d.isoformat(),
    )


class EligibilityError(Exception):
    """Raised when an agreement is requested for an ineligible record."""


def assert_agreement_allowed(prospect: dict, as_of: Optional[date] = None) -> Eligibility:
    """Gate agreement generation. Raises EligibilityError if not allowed.

    A prospect may carry an explicit ``eligibility_reviewed`` flag set by a
    human reviewer; even so, the custody window is re-checked here so the code
    can never emit a void agreement.
    """
    elig = check_eligibility(prospect.get("custody_date"), as_of=as_of)
    if not elig.eligible:
        raise EligibilityError(elig.reason)
    if not prospect.get("eligibility_reviewed"):
        raise EligibilityError(
            "Custody window satisfied, but eligibility has not been reviewed by a "
            "human. Set eligibility_reviewed after confirming the state record."
        )
    return elig


if __name__ == "__main__":
    # Smoke test the rule pack.
    print(f"Fee cap: {compliant_fee_pct():.0f}%  ·  guidance {WI_GUIDANCE_DATE}")
    print("20% requested ->", cap_fee_pct(20), "%")
    print("fee on $283,265.10 ->", fee_amount(283265.10))
    print("custody 2021-01-01 ->", check_eligibility("2021-01-01").as_dict())
    print("custody 2025-06-01 ->", check_eligibility("2025-06-01").as_dict())
    print("no custody date    ->", check_eligibility(None).as_dict())
