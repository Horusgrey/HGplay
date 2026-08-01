# HeirBud / HeirFinder — ZGroup Unclaimed Property Engine

Wisconsin unclaimed-property finder and CRM pipeline for ZGroup LLC.

> **Compliance-first (PRJ-HB7K4).** Fees are capped at the Wisconsin 10% ceiling
> and agreements are gated behind a verified 24-month custody check — enforced in
> code via `compliance.py`, not just documented. Read **`AUTONOMOUS_SYSTEM.md`**
> for how the safe-automation architecture works, and **`docs/governance/`** for
> the project canon (Start Here, Scope Audit, Master Control).
>
> Status: **prototype — run locally on synthetic data.** Legal sign-off, real
> auth, and a supervised pilot are required before live paid outreach. See the
> Master Control deliverable tracker.

## Frontends

| File | What it is |
|------|-----------|
| `heirfinder_v1.html` | Standalone single-file tool — AI enrichment, outreach emails, localStorage. No server. |
| `heirbud_v2.html` | Full dashboard — connects to the FastAPI backend, CSV import, batch outreach, pipeline. |
| `heirbud_command_deck.html` | Command-deck interface (compliance-aware build). |

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
| `heirbud_server.py` | FastAPI server (optional `X-API-Key`, CORS allowlist) powering v2 |

## Docs

| File | What it is |
|------|-----------|
| `AUTONOMOUS_SYSTEM.md` | The autonomous money-maker design: automate the clerical 90%, gate the regulated 10% |
| `CATALOG.md` | Index of every file across all projects in this repo |
| `docs/EMAIL_TEMPLATE_LIBRARY.md` | Proof-first outreach copy + deliverability rules |
| `docs/LEGAL_TEMPLATES_COMPLIANCE.md` | Per-state agreement templates + compliance reference |
| `docs/governance/` | PRJ-HB7K4 canon: Start Here, Scope Audit, Master Control |

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
- `POST /crm/eligibility` — record a verified custody date + human review
- `POST /crm/suppress` — opt a record out of all future outreach
- `POST /contract/generate` — PDF agreement (422 if not eligible)
- `GET /pipeline/summary` — stage counts and total pipeline value

## Cron (daily autonomy layer)

```bash
# Mac/Linux — crontab -e
0 8 * * 1-5 cd /path/to/hgplay && python followup_engine.py
```
