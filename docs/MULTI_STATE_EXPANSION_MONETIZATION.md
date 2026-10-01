# MULTI-STATE EXPANSION & MONETIZATION
## How growth should work, once Wisconsin is proven

This doc previously described a Google Sheets + Apps Script + Make.com stack
with per-tier fees up to 25% and volume targets of hundreds of emails/day.
None of that exists in this codebase, several of its fee figures exceeded
what Wisconsin law allows (see `docs/LEGAL_TEMPLATES_COMPLIANCE.md`), and its
automation model had no human-approval step — the opposite of how
`outbox.py` is built. This version replaces it with what actually fits the
engine that exists: `compliance.py`, `scoring.py`, `household.py`,
`letter_generator.py`, `payment_module.py`, `analytics.py`.

Per `docs/governance/HB-00_MASTER_CONTROL.md`, multi-state is **WS-03,
P1, PLANNED** — not active. This is the plan for when it becomes active,
not a thing to start this week.

---

## PART 1: MONETIZATION — ALREADY BUILT, WISCONSIN-ONLY

The real model is two paths, chosen per prospect
(`scoring.recommended_mode`) or set globally, both already in
`letter_generator.py`:

- **GRATUITY (default).** No quoted fee anywhere. Free help; an optional,
  unprompted thank-you after the owner is paid. No agreement, so nothing for
  the 10%/24-month statute to even apply to.
- **CONTRACT.** Only for records that have passed
  `compliance.assert_agreement_allowed()` — a human-verified custody date
  ≥24 months. Fee is always `compliance.compliant_fee_pct()`, currently 10%,
  pulled from code, never typed by hand, never tiered by dollar amount.

There is no "ultra/high/medium/low fee tier" in this system, and there
shouldn't be one for Wisconsin — the statute caps every claimant type at the
same 10%, so a tiered fee schedule above that is not a monetization lever,
it's a compliance violation. The real leverage levers are the ones
`household.py` and `scoring.py` already implement:

- **Household consolidation** — one combined letter covering a person's
  several claims, instead of five separate mailings. More money per
  conversation, not a higher rate.
- **Heir bridges** — a living relative at the same address as a deceased
  owner's estate record, surfaced as a research lead to the *operator*, never
  disclosed between the two parties.
- **Achievable-first scoring** — `scoring.prioritize()` ranks by expected
  *collectible* fee and contactability, not raw dollar amount, so effort goes
  where it actually converts.

None of this requires a second state to be worth building out further.

---

## PART 2: WHEN A SECOND STATE IS ACTUALLY ON THE table

The right unit of work is a **per-state rule pack**, mirroring
`compliance.py`'s shape — not a copy of the Wisconsin letter with a new
state name swapped in. For each candidate state, before writing a single
line of code or outreach copy:

1. **Verify, don't assume, three numbers**: the fee cap (if any), the
   custody/waiting-period requirement (if any), and whether registration or
   bonding is required to solicit. Pull these from the state's own statute
   text or treasurer/comptroller FAQ page — the same way Wisconsin's 10%
   cap and 24-month wait were confirmed against Wis. Stat. § 177.1301 and
   the WI DOR FAQ, not copied from a generic multi-state guide.
2. **Write it into a `rules/<state>.py` module** shaped like `compliance.py`
   — its own `<STATE>_FEE_CAP`, its own custody/waiting constant, its own
   `FREE_CLAIM_DISCLOSURE` with that state's actual portal and phone number.
3. **Only then** let `letter_generator.py` and `scoring.py` take a state
   parameter and dispatch to the right rule pack.

`docs/LEGAL_TEMPLATES_COMPLIANCE.md` has draft (explicitly **unverified**)
templates for California, Texas, New York, Florida, Illinois, and
Pennsylvania as a starting point for step 1 above — not something to operate
from as-is.

---

## PART 3: WHAT "SCALE" SHOULD MEAN HERE

Not volume-of-sends — `outbox.py` is an approve-to-send queue by design, and
`followup_engine.py` caps every record at one follow-up. Scale means:

- More **verified, eligible** records in the pipeline (via
  `verification_queue.py`), not more unverified contacts.
- More **households found** per batch of records (via `household.py`), since
  that's free leverage on data already in hand.
- A **second state's rule pack** built correctly once Wisconsin's pilot
  economics (`analytics.py`'s funnel + value ladder) justify the engineering
  time — not before.

If hiring help ever makes sense, the roles are **verification** (confirming
custody dates against the state record) and **owner communication**
(answering replies a human should see) — not volume-sending, which stays
capped and approved regardless of headcount.
