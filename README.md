# HeirBud / HeirFinder — ZGroup Unclaimed Property Engine

Wisconsin unclaimed property finder and CRM pipeline for ZGroup LLC.

## Two Versions

| File | What it is |
|------|-----------|
| `heirfinder_v1.html` | Standalone single-file tool — AI enrichment, outreach emails, localStorage persistence. No server needed. |
| `heirbud_v2.html` | Full dashboard — connects to the FastAPI backend, CSV import, batch outreach, stage pipeline, Gmail compose. |

## Backend Stack

| File | What it does |
|------|-------------|
| `heirbud_crm.py` | SQLite CRM — prospects, stage history, contact log, auto-stage advancement |
| `seed_from_csv.py` | Import WI bulk CSV → CRM with search URLs auto-generated |
| `outreach_generator.py` | Personalized call/email/SMS scripts by asset holder type |
| `contract_generator.py` | One-page contingency agreement PDFs (reportlab) |
| `followup_engine.py` | Daily prioritized action queue — run every morning |
| `heirbud_server.py` | FastAPI server that powers the v2 dashboard |

## Quick Start

```bash
pip install -r requirements.txt

# Seed from real WI data
python seed_from_csv.py --file WI_HeirFinder_Priority_Targets.csv --min-amount 50000

# Start the server
uvicorn heirbud_server:app --reload --port 8001

# Open heirbud_v2.html in browser
# (or open heirfinder_v1.html for the standalone tool)

# Every morning
python followup_engine.py
```

## Pipeline Stages

`IDENTIFIED → ENRICHED → CONTACTED → RESPONDED → AGREEMENT_SENT → SIGNED → FILED → PAID → CLOSED`

Stage advances automatically when contact outcomes are logged (Answered → CONTACTED, Replied → RESPONDED, Signed → SIGNED, etc.)

## Key API Endpoints

- `GET /actions/today` — prioritized daily action queue
- `POST /seed/csv` — upload CSV directly to server
- `POST /outreach/generate` — scripts for one prospect
- `POST /contract/generate` + `GET /contract/download/{id}` — PDF agreement
- `GET /pipeline/summary` — stage counts and total pipeline value

## Cron (full autonomy)

```bash
# Mac/Linux — crontab -e
0 8 * * 1-5 cd /path/to/hgplay && python followup_engine.py
```
