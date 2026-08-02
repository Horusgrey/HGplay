# HeirBud — The Autonomous Money-Maker (done right)

The goal is a system that runs itself as much as legally possible and puts money
in your pocket. In Wisconsin heir-finding, the fastest path to *collectible*
revenue runs **through** compliance, not around it: a fee over 10% is
unenforceable, and an agreement signed before the property has been in state
custody 24 months is **void**. So "compliant" and "gets paid" are the same
objective.

The design principle (straight from your own scope audit):

> **Maximize trustworthy throughput per human decision.**
> Automate the clerical 90%. Gate the regulated 10% behind one human click.

---

## The two lanes

| 🟢 AUTONOMOUS (runs itself) | 🔴 HUMAN-GATED (one approval each) |
|---|---|
| Import + dedupe state records | Confirm eligibility (custody ≥ 24 mo) |
| Prioritize by value/age/contactability | Approve outreach send |
| Skip-trace / enrich contacts | Sign off on the agreement |
| Draft the outreach (call/email/SMS) | Verify identity match |
| Build the daily action queue | File the claim with the state |
| Schedule + send follow-ups | Anything a lawyer would want to see |
| Classify inbound replies | |
| Track pipeline, fees, metrics | |
| Assemble the agreement PDF (once eligible) | |

Everything in the red lane is a *single decision*, surfaced to you with the
evidence already gathered. Everything else is machine work.

---

## How the pieces map to the code (all in this repo)

```
compliance.py          ← SINGLE SOURCE OF TRUTH: 10% cap, 24-month gate,
                          free-claim disclosure. Nothing else hard-codes a rule.
seed_from_csv.py        ← import + deterministic dedupe IDs
process_wisconsin_data.py ← WI export cleaner + priority scoring
heirbud_crm.py          ← SQLite pipeline w/ custody/eligibility/consent/suppression
outreach_generator.py   ← honest, capped call/email/SMS scripts (suppression-aware)
contract_generator.py   ← agreement PDF — REFUSES to render unless eligible
followup_engine.py      ← daily prioritized action queue (excludes suppressed)
heirbud_server.py       ← FastAPI: optional X-API-Key, eligibility + suppress endpoints
docs/EMAIL_TEMPLATE_LIBRARY.md   ← the proof-first copy that converts
docs/LEGAL_TEMPLATES_COMPLIANCE.md ← per-state agreement templates
docs/governance/*        ← the PRJ-HB7K4 canon (Start Here, Scope Audit, Master Control)
```

The compliance gates are enforced in code, not documentation:

- **Fee cap** — `compliance.cap_fee_pct(20)` returns `10`. Every module calls it;
  you cannot emit a 15% or 20% fee even by passing one in.
- **Eligibility gate** — `contract_generator.generate_contract()` calls
  `compliance.assert_agreement_allowed()` and raises `EligibilityError` unless
  the record has a verified custody date ≥ 24 months old **and** a human review
  flag. The API returns HTTP 422.
- **Suppression** — once a record is `SUPPRESSED`, outreach generation raises,
  the action queue skips it, and auto-advance can't resurrect it.

---

## The daily loop (what "autonomous" actually feels like)

```
Every morning, unattended:
  1. followup_engine builds TODAY_ACTIONS.md — who to call, chase, file, enrich,
     sorted by urgency then value, with the fee-if-recovered (NOT booked revenue).
  2. New state records imported + deduped + prioritized overnight.
  3. Draft outreach pre-generated for every ENRICHED record.

You, for ~30 min:
  4. Work the queue top-down. For each: approve the send (or skip).
  5. For any responder: click "eligible" once you've eyeballed the state record
     + custody date. That single click unlocks agreement generation.
  6. Send the agreement. Owner signs. You file.

Autonomous again:
  7. Follow-ups fire on schedule (day 7 / 14 / 21, then stop).
  8. Replies get classified; only INTERESTED/QUESTION reach you.
  9. Metrics roll up: response rate, consent rate, cycle time, realized fees.
```

You are the eligibility-and-approval brain. The machine is everything else.

---

## Revenue model (honest math)

At a 10% capped fee, the arithmetic still works because the volume is automated
and the cost per touch is near zero:

| Lane | Monthly contacts | Response | → Claims | Avg recovery | Fee @10% | **Revenue** |
|---|--:|--:|--:|--:|--:|--:|
| Conservative | 200 | 2% | 2 | $2,500 | $250 | **~$500** |
| Realistic | 800 | 2.5% | 10 | $3,000 | $300 | **~$3,000** |
| Scaled | 2,000 | 3% | 30 | $3,500 | $350 | **~$10,500** |

The lever is not a higher fee (illegal) — it's **more eligible, verified,
well-targeted contacts per human hour**, which is exactly what the autonomous
lane produces. High-value estate/trust/business cases (see the estate + business
templates in `docs/LEGAL_TEMPLATES_COMPLIANCE.md`) are the premium tier.

---

## What still needs a human before you go live

These are open items from the Master Control tracker — do NOT skip them:

1. **Legal sign-off** on the WI agreement template and outreach copy (D-007).
2. **A verified custody-date source** so eligibility isn't guesswork (D-004).
3. **Real auth + audit logging** before any multi-user or hosted deployment
   (D-006 / R-003) — the API key here is a prototype gate, not production auth.
4. **PII encryption + retention policy** before storing real claimants (R-004).
5. **A 25-record supervised pilot** before any scaled sending (D-009).

Until then: run it locally, on synthetic data, to validate the workflow — which
is precisely what the audit recommends (freeze as v0.2, test, then decide).

---

## See it run: `python demo_pilot.py`

A one-command pilot drives the whole loop against 24 synthetic records
(`fixtures/synthetic_wi_records.csv`) and proves each gate fires — import +
dedupe, eligibility verification, enrichment, honest capped outreach, a
**blocked** agreement for an ineligible record, an **allowed** agreement for an
eligible one (fed 20%, clamped to 10%), suppression, and the daily action queue.
It uses a throwaway DB and leaves no real data behind — exactly the supervised
pilot the audit asks for, minus real records.

## Roadmap to fuller autonomy (safe order)

1. **Now:** compliance gates live (done). Run the daily loop on synthetic data.
2. **Now:** custody-date verification workflow (`verification_queue.py`) —
   prioritized worklist of records needing a verified custody date, each with
   the DOR lookup link and report-year hint; verifications are recorded with
   required evidence + reviewer so every eligibility decision is attributable.
   (WI has no machine API for this, so the lookup stays human — but fast,
   prioritized, and auditable. If/when a data feed exists, it drops in here.)
3. **Then:** connect email send (Gmail API / dedicated domain) behind an
   "approve" button — see `docs/EMAIL_TEMPLATE_LIBRARY.md` deliverability rules.
4. **Later:** reply-classification + next-best-action suggestions (AI recommends,
   you authorize).
5. **Scale:** add a state rule-pack per new state (fee cap, waiting period,
   registration, disclosures) — schema-driven, never copy-pasted.

> An LLM is never the legal brain here. It extracts rules, drafts, classifies,
> and assembles. A human — and, before launch, a lawyer — approves.
