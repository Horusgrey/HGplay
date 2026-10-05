# Launch Runbook — the steps only you can take

Everything engineering could close without a real-world decision or a real
attorney is done as of `VERSION.md` v1.0.0. What's left is a short, ordered
list of things that are genuinely yours to do — no amount of further coding
substitutes for any of them. This is the whole remaining path to a live,
compliant first pilot.

## 1. Get the legal review (blocks everything else)

Send a Wisconsin attorney `docs/LEGAL_REVIEW_BRIEF.md` plus its two
attachments (`docs/LEGAL_TEMPLATES_COMPLIANCE.md`,
`docs/EMAIL_TEMPLATE_LIBRARY.md`). It's written to be a single short, fixed-fee
engagement — the ten questions are specific on purpose. Do not skip to step 2
until you have answers to section A–E.

## 2. Decide your default fee model

`letter_generator.py` supports both, per prospect:
- **GRATUITY** (recommended default) — free help, no quoted fee, owner
  chooses whether to say thanks after being paid. No agreement, so nothing
  for the 10%/24-month statute to even reach.
- **CONTRACT** — a signed 10%-capped agreement, only for records that pass
  the 24-month verified-custody gate.

You can run both simultaneously (`fee_model` is per-prospect) — e.g.
GRATUITY for most records, CONTRACT for ones big enough that a claimant
might actually want you to handle the paperwork end-to-end.

## 3. Fill in your real identity

- `letter_generator.py`'s `SENDER` dict — your real name, return address,
  phone, email. Every letter currently prints `[Your Name]` /
  `[Your return address]` placeholders.
- Decide a real domain for `HEIRBUD_BASE_URL` (the QR code on every letter
  points here) — can stay `localhost` for a paper-only pilot with no QR
  follow-up, but needs a real domain before you rely on the QR.
- Copy `.env.example` to `.env`, set `HEIRBUD_API_KEY` to something real if
  the server will ever be reachable beyond your own machine.

## 4. Get your first verified batch

- Export real Wisconsin records (keep them **out of git** — `.gitignore`
  already blocks `WI_HeirFinder*.csv` and similar).
- `python seed_from_csv.py --file your_export.csv --min-amount 50000` (or
  the equivalent `/seed/csv` endpoint) to import.
- For each record you intend to act on, verify its custody date against
  the actual DOR record yourself, then record it:
  `POST /crm/eligibility` with `reviewed=true` and `evidence` describing how
  you checked. `GET /verification/worklist` shows what still needs this.
  HB-00_SCOPE_AUDIT's own recommendation is to start with **25 verified
  records**, not your whole list.

## 5. Run the pilot exactly like the synthetic one, but real

`python demo_pilot.py` already proves the mechanics end-to-end on fake data
— run it once more as a smoke test after any change. For the real pilot:

- USPS-first (`letter_generator.generate_letter`) — mail physical letters,
  per `HB-00_SCOPE_AUDIT`'s own recommendation for a pilot.
- Log every contact (`POST /crm/log_contact` or the console UI) — don't let
  anything happen outside the CRM's audit trail.
- Nothing auto-sends. `outbox.py` is approve-to-send by design — if you ever
  wire a real sender in (`GmailSenderStub` → something real), that stays
  true; the approval step is not something to "optimize away" later.
- Classify replies through `reply_classifier.py` / `POST /replies/process`
  so opt-outs are suppressed automatically and everything else is flagged
  for you, not auto-answered.

## 6. Close the loop and look at the numbers

`GET /analytics/summary` (or the console's Analytics tab) gives the funnel,
the value ladder (published → eligible → expected → realized — never
blurred into one number), and cycle times. Decide from real pilot numbers,
not projections, whether to scale the batch size, add a second state (see
`docs/MULTI_STATE_EXPANSION_MONETIZATION.md` Part 2 — verify that state's
actual statute the same way Wisconsin's was verified, don't reuse these
numbers), or bring in help for verification/customer-reply volume.

## Ongoing hygiene (not launch-blocking, but don't skip for long)

- `python backup_restore.py backup` — no cron for this yet; worth adding to
  your existing `followup_engine.py` crontab entry once you're live.
- Keep re-checking `compliance.WI_GUIDANCE_DATE` against current DOR
  guidance periodically — laws change, and this file is the single place
  that controls every fee and gate in the system.
