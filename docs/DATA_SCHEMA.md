# Canonical Data Schema

Closes `docs/governance/HB-00_MASTER_CONTROL.md` D-004 ("full schema doc
pending"). This is the complete, current shape of `heirbud.db`
(`heirbud_crm.py`) and the outbox (`outbox.py`). If this file and the code
ever disagree, the code — specifically the `CREATE TABLE` statements — is
right.

---

## `prospects` — one row per unclaimed-property record

| Column | Type | Meaning |
|---|---|---|
| `property_id` | TEXT, PK | Deterministic ID (`seed_from_csv.deterministic_id`) or the state's own ID — never Python's randomized `hash()`, which broke dedupe before PRJ-HB7K4. |
| `name` | TEXT | Claimant/owner name as reported. |
| `last_known_address` | TEXT | Free-text `street, city, state, zip`. |
| `amount` | REAL | Dollar value as reported by the state — the *published* figure, never treated as booked revenue (see `analytics.py`'s value ladder). |
| `property_type` | TEXT | e.g. "Uncashed Checks", "Dormant Savings". |
| `holder` | TEXT | Who originally held the funds (bank, insurer, employer, etc.). |
| `priority` | TEXT | `HIGH` / `MEDIUM` / `LOW` — a coarse import-time bucket; superseded for actual work ordering by `scoring.prioritize()`. |
| `stage` | TEXT | One of the pipeline stages below. |
| `phone`, `email` | TEXT, nullable | Contact info — blank on import, filled by `skiptrace.enrich()` or manual entry. |
| `notes` | TEXT | Free-text operator notes. |
| `search_urls` | TEXT (JSON) | Pre-built people-search links (`seed_from_csv.build_search_urls`). |

### Compliance fields (PRJ-HB7K4 — the reason none of this is optional)

| Column | Type | Meaning |
|---|---|---|
| `custody_date` | TEXT, nullable | The **verified** date the property entered DOR custody. Not the report date — see `eligibility_state()` in `compliance.py` for why those are kept distinct. |
| `eligibility_reviewed` | INTEGER (bool) | 1 only once a human has confirmed the state record. `contract_generator.py` refuses to run without this. |
| `eligibility_reason` | TEXT | Last verdict text from `compliance.check_eligibility()`. |
| `consent_status` | TEXT | `NONE` / `GIVEN` / `WITHDRAWN`. Set by the owner portal (`record_consent`) or an opt-out. |
| `suppression_status` | TEXT | `ACTIVE` / `SUPPRESSED`. **Terminal** — `outreach_generator.py` and `outbox.py` both refuse suppressed records, re-checked at every stage. |
| `source_verified_date` | TEXT, nullable | Timestamp of the last human eligibility review. |
| `custody_evidence` | TEXT | How the custody date was confirmed (URL, screenshot location, note) — a reviewed decision without this is rejected by `crm.set_eligibility()`. |
| `report_year` | TEXT, nullable | Hint only, from the import file. Never a substitute for `custody_date`. |
| `fee_model` | TEXT | `CONTRACT` / `GRATUITY` — per-prospect, defaults to `CONTRACT`; most volume should run `GRATUITY` (see `docs/EMAIL_TEMPLATE_LIBRARY.md`). |

### Money-loop fields (payment_module.py)

| Column | Type | Meaning |
|---|---|---|
| `funds_received_date` | TEXT, nullable | Owner confirmed the state paid them. Nothing downstream (invoice, fee) can happen before this. |
| `fee_invoiced` | INTEGER (bool) | An invoice/thank-you PDF has been generated. |
| `fee_invoice_date` | TEXT, nullable | When. |
| `fee_paid` | INTEGER (bool) | The claimant paid the fee (CONTRACT mode only — GRATUITY has no owed fee). |
| `fee_paid_date` | TEXT, nullable | When. |
| `fee_reminders_sent` | INTEGER | Count — capped by `payment_module`'s finite-reminder rule. |
| `fee_last_reminder` | TEXT, nullable | Timestamp of the last reminder. |

### Housekeeping

`created_at`, `updated_at` — ISO timestamps, set on insert/update.

---

## Pipeline stages (`STAGES` in `heirbud_crm.py`)

```
IDENTIFIED → ENRICHED → CONTACTED → RESPONDED → AGREEMENT_SENT → SIGNED → FILED → PAID → CLOSED
                                                                                            ↘
                                                                               SUPPRESSED (terminal, any point)
```

Advances happen automatically on logged outcomes (e.g. adding contact info
moves `IDENTIFIED → ENRICHED`); nothing auto-advances *past* `SUPPRESSED`,
and nothing can leave `SUPPRESSED` once set.

---

## `contact_log` — append-only history of every touch

`id, property_id, method, outcome, notes, logged_at` — one row per call,
email, letter, or system event (eligibility reviews and consent grants are
logged here too, via `log_contact_attempt`). This plus `stage_history` is
the audit trail required by Definition of Done #4/#5: every contact and
eligibility decision has a who/what/when, even in this single-operator
build where "who" is usually just the operator's own name passed as
`reviewer`/`approver`.

## `stage_history` — append-only record of every stage transition

`id, property_id, from_stage, to_stage, notes, changed_at`.

---

## `outbox` — the approve-to-send queue (`outbox.py`)

| Column | Meaning |
|---|---|
| `id` | PK. |
| `property_id` | Which prospect. |
| `channel` | `email` / `sms` / etc. |
| `to_addr`, `subject`, `body` | The drafted message — generated by `outreach_generator.generate_scripts()`, which already carries the free-claim disclosure. |
| `status` | `DRAFT → APPROVED → SENT`, or `HELD` if a suppression is found at approve/send time. |
| `created_at`, `approved_at`, `approved_by`, `sent_at`, `send_result` | Full lifecycle timestamps + who approved it. |

A row can never reach `SENT` without a human `approved_by` on it, and
suppression is re-checked both at approval and at send — not just at draft
time — so a record suppressed *after* drafting still can't go out.

---

## Backups

`backup_restore.py` takes a consistent snapshot via SQLite's own backup API
(safe even while the server has the DB open) into `backups/` (gitignored —
it holds real PII once the system is used live). `tests/test_backup_restore.py`
proves the restore path actually recovers data, including that a restore
moves the old file aside (`.pre-restore`) rather than deleting it.
