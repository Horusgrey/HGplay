# Legal Review Brief — HeirBud (Wisconsin unclaimed-property locator)

**Purpose:** give a Wisconsin attorney everything needed to review this operation
in a single short engagement. This brief is written to make that meeting fast and
cheap — the specific questions are listed so counsel can price and answer them
directly. *This document is not legal advice; it is a request for it.*

---

## What the business does

We identify owners of unclaimed property held by the Wisconsin Department of
Revenue (public data), notify them transparently, and — for those who opt in —
assist with preparing and filing the state claim, for a contingency fee paid only
if they are actually paid.

**We always disclose, up front and prominently, that the owner can claim directly
from the state for free, and that we are a private locator, not the government.**

---

## What we have already built to be compliant

These controls are enforced in code, not just policy:

- **Fee ceiling.** Every fee is capped at **10%** of the amount recovered. The
  code cannot emit a higher figure. *(source: WI DOR locator guidance)*
- **24-month custody gate.** No locator agreement can be generated unless the
  property has been in DOR custody ≥ 24 months **and** a human has verified it
  with recorded evidence. Agreements for younger property are blocked outright.
- **Required agreement content.** The generated agreement states the service, the
  fee, the property value before and after the fee, the holder, the property
  description, a signature block, and a prominent free-claim disclosure.
- **Outreach controls.** No impersonation of the state, no manufactured urgency,
  no request for SSN/bank details at outreach. Opt-outs are honored automatically
  and permanently.
- **Audit trail.** Every stage change, contact, and eligibility decision is logged
  with who/what/when.

---

## The specific questions we need answered

**A. Fee & agreement**
1. Is a 10% contingency cap correct and current for Wisconsin locator services,
   and does it apply to the gross recovered amount or net of state deductions?
2. Does our agreement template contain everything Wisconsin requires, and is any
   required language missing or misstated? *(template attached: DOCUMENT 1 in
   `docs/LEGAL_TEMPLATES_COMPLIANCE.md`)*
3. Is the 24-month custody rule stated correctly, and is "custody date" the right
   trigger (vs. report date / date reported to DOR)?

**B. Unauthorized practice of law (the one we're most concerned about)**
4. Where is the line between permitted "assistance" (forms, guidance, document
   assembly) and the unauthorized practice of law, especially for **estate,
   trust, and dissolved-business** claims involving affidavits of heirship,
   letters testamentary, or corporate authority?
5. What must change in our service description so we stay clearly on the
   assistance side of that line?

**C. Registration & solicitation**
6. Does Wisconsin require any registration, bonding, or licensing to operate as a
   locator or to solicit owners?
7. Are there restrictions on *how* we may contact owners (waiting periods after a
   property is reported, permitted channels, written-agreement-before-fee rules)?

**D. Communications law**
8. Do our email and SMS templates comply with CAN-SPAM and TCPA (consent,
   opt-out, identification), given we contact people who haven't opted in?
9. Any Wisconsin-specific consumer-protection/UDAP concerns with the outreach copy
   as written? *(copy attached: `docs/EMAIL_TEMPLATE_LIBRARY.md`)*

**E. Data & records**
10. What are our obligations for handling owner PII and retaining signed
    agreements and claim records (retention period, security)?

**F. Multi-state (future, lower priority)**
11. For expansion, what's the right framework for a per-state "rule pack," and are
    there states we should avoid without registration (e.g., California)?

---

## What to attach when you send this

- `docs/LEGAL_TEMPLATES_COMPLIANCE.md` — the agreement templates (all states)
- `docs/EMAIL_TEMPLATE_LIBRARY.md` — the outreach copy and sequences
- `docs/governance/HB-00_SCOPE_AUDIT.md` — the internal compliance assessment
- A sample generated agreement PDF (run `contract_generator.py` on a synthetic,
  eligible record)
- This brief

---

## The ask, in one sentence

*"Please confirm our fee, agreement, timing, and outreach comply with current
Wisconsin law, tell us exactly where our 'assistance' risks crossing into the
unauthorized practice of law (especially for estates), and flag anything we must
change before we contact a single real owner."*

A fixed-fee review answering A–E is enough to start Wisconsin operations. F can
wait for expansion.
