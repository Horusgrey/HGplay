# HeirBud / HeirFinder — ZGroup Unclaimed Property Engine

Wisconsin unclaimed-property finder and CRM pipeline for ZGroup LLC.

> **Compliance-first (PRJ-HB7K4).** Fees are capped at the Wisconsin 10% ceiling
> and agreements are gated behind a verified 24-month custody check — enforced in
> code via `compliance.py`, not just documented. Read **`STRATEGY.md`** for the
> business thinking, **`AUTONOMOUS_SYSTEM.md`** for the safe-automation
> architecture, **`docs/LEGAL_REVIEW_BRIEF.md`** for the lawyer hand-off, and
> **`docs/governance/`** for the project canon (Start Here, Scope Audit, Master Control).
>
> Status: **prototype — run locally on synthetic data.** Legal sign-off, real
> auth, and a supervised pilot are required before live paid outreach. See the
> Master Control deliverable tracker.

## Frontends

| File | What it is |
|------|-----------|
| `heirbud_command_center.html` | **⭐ The one you actually run.** The whole engine as a single browser file — no Python, no server, no install. Open it, import your CSV, and everything (ranking, households, custody gate, letters, invoices, collections) runs on your own machine. Data stays in the browser and never leaves the device. |
| `heirbud_console.html` | **Operator console** — served same-origin by the server at `/`. Pipeline, today's actions, verification worklist, approve-to-send outbox, prioritized prospect table, funnel analytics. Theme-aware. |
| `owner_portal.html` | **Owner-facing trust page** — served at `/verify?id=…`. Owners verify their own record, see the free state path front-and-center, opt in or opt out. |
| `heirfinder_v1.html` | Standalone single-file tool — AI enrichment, outreach emails, localStorage. No server. |
| `heirbud_v2.html` | Earlier dashboard — connects to the FastAPI backend, CSV import, batch outreach, pipeline. |
| `heirbud_command_deck.html` | Command-deck interface (compliance-aware build). |

### Operator console

```bash
uvicorn heirbud_server:app --port 8001
# then open http://localhost:8001/  ← the console, served same-origin (no CORS setup)
```

One glance shows the whole operation: eligible value vs published value (kept
distinct — published is never treated as booked revenue), the custody
verification worklist, the outbox awaiting your approval, and today's actions.
Every money/legal action (verify, suppress, approve-to-send) is one click and,
where the server has `HEIRBUD_API_KEY` set, gated by the key field in the header.

## Backend Stack

| File | What it does |
|------|-------------|
| `compliance.py` | **Single source of truth** — 10% fee cap, 24-month eligibility gate, free-claim disclosure |
| `heirbud_crm.py` | SQLite CRM — prospects, stage history, contact log, custody/eligibility/consent/suppression |
| `seed_from_csv.py` | Import WI bulk CSV → CRM with deterministic dedupe IDs + search URLs |
| `process_wisconsin_data.py` | WI export cleaner + priority scoring |
| `outreach_generator.py` | Honest, capped call/email/SMS scripts by holder type (suppression-aware) |
| `contract_generator.py` | One-page agreement PDFs — refuses to render unless eligible (reportlab) |
| `followup_engine.py` | Daily prioritized action queue — run every morning |
| `verification_queue.py` | Custody-date verification worklist — record eligibility with evidence |
| `analytics.py` | Funnel + value ladder + cycle times + plain-English narrative |
| `scoring.py` | Achievable-first prioritization — sweet-spot value, barrier model, findability, segment + track + mode |
| `contact_finder.py` | Intelligent skip-tracing — name variants, findability score, ranked lookups, deceased→heir pivot |
| `household.py` | **Household graph** — folds duplicate people into one conversation, finds an estate's heirs inside your own list, boosts ranking by leverage |
| `autopilot.py` | One command advances the whole operation and writes the operator brief |
| `payment_module.py` | Closes the money loop — mode-aware invoice/thank-you, friendly finite reminders, reconciliation |
| `reply_classifier.py` | Rule-based inbound-reply sorting — auto-suppress opt-outs, flag real leads |
| `outbox.py` | Approve-to-send queue — nothing sends without human approval (dry-run sender) |
| `heirbud_server.py` | FastAPI server (optional `X-API-Key`, CORS allowlist) powering v2 |

## Docs

| File | What it is |
|------|-----------|
| `AUTONOMOUS_SYSTEM.md` | The autonomous money-maker design: automate the clerical 90%, gate the regulated 10% |
| `CATALOG.md` | Index of every file across all projects in this repo |
| `docs/EMAIL_TEMPLATE_LIBRARY.md` | Proof-first outreach copy + deliverability rules |
| `docs/LEGAL_TEMPLATES_COMPLIANCE.md` | Per-state agreement templates + compliance reference |
| `docs/governance/` | PRJ-HB7K4 canon: Start Here, Scope Audit, Master Control |

## Try it in one command (synthetic data)

```bash
pip install -r requirements.txt
python demo_pilot.py          # watch the whole loop on synthetic data
python autopilot.py --file yourfile.csv   # advance everything, get today's operator brief
```

`demo_pilot.py` runs the entire loop against `fixtures/synthetic_wi_records.csv` (24 fake
records) and proves every compliance gate fires: fee clamps to 10%, agreements
are refused for ineligible/unverified records, and suppressed records vanish
from outreach and the action queue. Uses a throwaway DB — no real data touched.

## Quick Start

```bash
pip install -r requirements.txt

# Import records (uses deterministic dedupe IDs)
python seed_from_csv.py --file your_wi_export.csv --min-amount 50000

# Start the server (set a key to require auth on mutating endpoints)
export HEIRBUD_API_KEY=changeme            # optional but recommended
uvicorn heirbud_server:app --reload --port 8001

# Open heirbud_v2.html (or heirfinder_v1.html for the standalone tool)

# Every morning — the autonomy layer
python followup_engine.py
```

## Compliance gates (enforced in code)

```python
import compliance
compliance.cap_fee_pct(20)          # -> 10.0   (never above the WI ceiling)
compliance.check_eligibility("2025-06-01")   # -> ineligible: custody < 24 months
# contract_generator.generate_contract(record)  raises EligibilityError
#   unless record has a verified custody_date >= 24mo AND eligibility_reviewed
```

Real owner data must never enter the repo — demos use synthetic records and
`.gitignore` blocks WI CSV exports, the SQLite DB, and generated contracts.

## Pipeline Stages

`IDENTIFIED → ENRICHED → CONTACTED → RESPONDED → AGREEMENT_SENT → SIGNED → FILED → PAID → CLOSED`
plus terminal **`SUPPRESSED`** (opted-out; never contacted again).

Stages advance automatically when contact outcomes are logged. Suppressed
records can never be resurrected by auto-advance.

## Key API Endpoints

- `GET /actions/today` — prioritized daily action queue
- `POST /seed/csv` — upload CSV directly to server
- `POST /outreach/generate` — scripts for one prospect (409 if suppressed)
- `GET /verification/worklist` — records needing a verified custody date
- `POST /crm/eligibility` — record a verified custody date + evidence + human review
- `POST /crm/suppress` — opt a record out of all future outreach
- `POST /contract/generate` — PDF agreement (422 if not eligible)
- `POST /replies/process` — classify an inbound reply + take the safe auto-action
- `POST /outbox/draft` → `POST /outbox/approve` → `POST /outbox/send` — approve-to-send flow
- `GET /analytics/summary` — funnel, value ladder, cycle times, narrative
- `GET /leads/prioritized` — prospects ranked by holistic priority (achievable first)
- `GET /prospects/{id}/find` — intelligent skip-trace plan for one prospect
- `GET /autopilot/brief` — run the autonomous pass, return the operator brief
- `GET /payments/dashboard` · `POST /payments/funds-received` · `/invoice` · `/fee-paid` — the money loop
- `GET /owner/{token}` · `POST /owner/{token}/request-help` · `/not-me` — owner portal
- `GET /pipeline/summary` — stage counts and total pipeline value

## Tests

```bash
python -m pytest tests/ -q     # 48 tests locking every compliance gate
```

The suite fails loudly if any gate regresses — fee cap, eligibility, evidence
requirement, suppression, dedupe, outreach copy, reply auto-actions, and the
outbox's no-send-without-approval rule.

## Cron (daily autonomy layer)

```bash
# Mac/Linux — crontab -e
0 8 * * 1-5 cd /path/to/hgplay && python followup_engine.py
```
