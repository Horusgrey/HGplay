# LEGAL TEMPLATES & COMPLIANCE
## Agreements for HeirBud / ZGroup LLC

Complete legal framework for an unclaimed-property locator business, aligned
to `compliance.py` — the single source of truth for every number here. If
this document and the code ever disagree, the code is right and this file is
stale.

---

## IMPORTANT DISCLAIMER

These are template documents only. Before using any of them live:

- Confirm with a licensed Wisconsin attorney (see `docs/LEGAL_REVIEW_BRIEF.md`
  — this file is one of the attachments for that review)
- Verify current compliance with any other state before operating there
- Update annually, or whenever `compliance.WI_GUIDANCE_DATE` is re-verified
- Keep signed records for at least 7 years

This document is not legal advice.

---

## WISCONSIN — VERIFIED (source for the numbers `compliance.py` enforces)

| Rule | Value | Source |
|---|---|---|
| Fee cap | **10%** of the actual amount/value recovered | Wis. Stat. § 177.1301; WI DOR "Heir Finders or Locator Services" FAQ |
| Custody wait | Agreement **void** if signed before property has been in DOR custody **24 months** | Wis. Stat. § 177.1301 |
| Written agreement | Required **only if a fee is charged** (ch. 177 Subch. XIII disclosure requirements apply); no agreement at all is needed for the no-fee GRATUITY path | Wis. Stat. ch. 177 Subch. XIII |
| Registration/bonding | None found as of this review — confirm with counsel | — |
| Complexity exception | **None.** The 10% cap applies to every claimant type — individual, estate, trust, or dissolved business. There is no "20–25% for complex cases" carve-out under Wisconsin law. | Wis. Stat. § 177.1301 |

Everything below outside the Wisconsin section is **unverified by this
project** — carried over from earlier multi-state drafting, not confirmed
against current statute text. Do not operate in another state on the
strength of this document; re-verify first the same way Wisconsin was
verified above.

---

## DOCUMENT 0: GRATUITY-PATH DISCLOSURE (no agreement — default path)

Most outreach should use this path and `letter_generator.py`'s GRATUITY mode:
help is offered for free, no fee is quoted anywhere, and if the owner chooses
to send a thank-you after being paid, that's their call, not a term of a
contract. **No signature, no agreement, nothing to enforce** — which is also
why this path doesn't trip the fee-cap / 24-month statute at all: there's no
"agreement to pay compensation for locator services" for the statute to
reach.

```
I'm glad to help you find and file your claim with the State of
Wisconsin, at no cost and with no obligation. You can also do this
yourself, for free, at revenue.wi.gov/Pages/UnclaimedProperty.

If this helps you and you'd like to say thanks afterward, in any way
and any amount you choose, that's always welcome — but it is never
expected, never required, and we're not agreeing to anything here.
```

---

## DOCUMENT 1: WISCONSIN CONTINGENCY AGREEMENT (CONTRACT mode only)

**Use only after `compliance.assert_agreement_allowed()` passes** — i.e. a
human has verified the custody date on the state record and it is ≥24
months old. Never hand-fill the fee line; it must equal
`compliance.compliant_fee_pct()` (currently 10%) and never a higher figure.

```
UNCLAIMED PROPERTY FINDER SERVICE AGREEMENT

This Agreement is made on [DATE] between:

FINDER: [YOUR NAME], ZGroup LLC
Address: [YOUR ADDRESS]
Email: [YOUR EMAIL]   Phone: [YOUR PHONE]

and

CLAIMANT: [CLAIMANT NAME]
Address: [CLAIMANT ADDRESS]
Email: [CLAIMANT EMAIL]   Phone: [CLAIMANT PHONE]

PROPERTY DETAILS:
State: Wisconsin
Property ID: [PROPERTY ID]
Amount before fee: $[AMOUNT]
Amount after fee:  $[AMOUNT MINUS FEE]
Property Type: [TYPE]
Holder: [HOLDER NAME AND ADDRESS]
Property in DOR custody since: [VERIFIED CUSTODY DATE] (verified [MONTHS] months ago)

TERMS:

1. SERVICES. The Finder will assist the Claimant in locating and
   claiming unclaimed property held by the State of Wisconsin,
   including providing property details, guidance on completing
   claim forms, and support during the process.

2. CLAIMANT'S RIGHT TO CLAIM DIRECTLY. The Claimant acknowledges
   they may claim this property directly from the state at NO COST:
   revenue.wi.gov/Pages/UnclaimedProperty | (608) 267-7977

3. FINDER'S FEE. If the Claimant successfully receives payment from
   the state, the Claimant agrees to pay the Finder 10% of the
   amount received — the maximum permitted under Wisconsin law. This
   fee is contingent; no fee is owed unless and until the Claimant is
   paid. This Agreement is void if signed less than 24 months after
   the property entered state custody.

4. PAYMENT. Fee due within 30 days of the Claimant receiving payment
   from the state. Methods: [Venmo / PayPal / Zelle / Check].

5. NO UPFRONT COST. The Claimant pays nothing in advance.

6. NO GUARANTEE. The Finder does not guarantee release, amount, or timeline.

7. CANCELLATION. Either party may cancel at any time without penalty.

CLAIMANT ACKNOWLEDGMENT:
I understand I can claim this property for FREE directly from the
state. I am choosing to work with the Finder for assistance and
convenience, and I agree to the 10% contingent fee only if I am paid.

CLAIMANT SIGNATURE: ____________________  DATE: ________
CLAIMANT NAME (PRINTED): _______________________________
FINDER SIGNATURE: ______________________  DATE: ________
```

### Estates, trusts, and dissolved businesses

Same agreement, same 10% cap — Wisconsin draws no distinction for complexity.
What changes is **who has authority to sign**, not the fee:

**Estate of a deceased owner** — attach copies of:
- [ ] Death certificate
- [ ] Letters testamentary / letters of administration, **or** an affidavit
  of heirship if no formal probate
- [ ] Court order appointing the representative (if applicable)

**Dissolved or inactive business** — attach copies of:
- [ ] Articles of dissolution
- [ ] Corporate resolution authorizing the claim
- [ ] Proof of the signer's former officer/director status
- [ ] EIN documentation

Where the proper authority to act is unclear (contested estates, multiple
heirs, unclear corporate succession), that's the unauthorized-practice-of-law
line raised in `docs/LEGAL_REVIEW_BRIEF.md` §B — pause and get the signer's
documentation reviewed before proceeding, not just before collecting a fee.

---

## OTHER STATES — DRAFTS ONLY, NOT RE-VERIFIED (lower priority per Master Control)

Per `docs/governance/HB-00_MASTER_CONTROL.md`, multi-state expansion is
explicitly schema-driven, lower priority, and not active. The table below is
carried over from early drafting and **must be independently re-verified**,
the same way the Wisconsin numbers above were checked against statute text
and the DOR FAQ, before any of it is relied on:

| State | Registration | Written Agreement | Fee Cap (unverified) | Cancellation | Notes |
|-------|--------------|-------------------|---------|--------------|------------|
| California | Reported to require registration (~$250) before soliciting | Required | ~10% under 24 months; unconfirmed for older property | — | Register with State Controller first: ucpi.sco.ca.gov |
| Texas | Unverified | Unverified | Unverified | — | — |
| New York | Unverified | Reported to require a written agreement | Unverified | — | — |
| Florida | Unverified | Reported to require a written agreement | Unverified | 5-day reported | Property-age restrictions reported |
| Illinois | Unverified | Unverified | Unverified | — | — |
| Pennsylvania | Unverified | Unverified | Unverified | — | — |

Do not fill in a specific percentage for any of these states the way Wisconsin's
is filled in above until it's been checked against that state's actual statute,
the same way Wisconsin's 10%/24-month figures were checked against Wis. Stat.
§ 177.1301 and the WI DOR FAQ rather than assumed.

---

## RECORD KEEPING (Keep 7 Years)

- Every signed agreement
- Copies of all claim forms submitted
- Communication logs (emails, texts, call notes)
- Payment receipts
- All state correspondence

---

## PAYMENT TRACKING FIELDS

Client name | Agreement date (or "gratuity — no agreement") | State/type | Property amount | Fee % (10% max, or none) | Fee amount | Payment received date | Method | Notes

---

## RED FLAGS — DO NOT PROCEED

Do not work with anyone who:
- Refuses to sign an agreement (CONTRACT mode only — not applicable to GRATUITY)
- Wants to hide the claim from the state
- Asks you to misrepresent anything on forms
- Is trying to claim property that isn't theirs
- Pressures you for upfront payment, or
- Pressures you to skip the free-claim disclosure

If something feels wrong, walk away.
