# HEIRBUD — MASTER CONTROL

| | | |
|:--|:--|:--|
| **Project** | PRJ-HB7K4 | Updated 2026-10-05 |
| Current Phase | Engineering complete — legal review pending | |
| Overall Status | ENGINEERING COMPLETE | |
| Compliance Status | CODE-ENFORCED — attorney sign-off pending (`docs/LEGAL_REVIEW_BRIEF.md`) | |
| Production Status | BLOCKED — pending legal sign-off, not pending code | |
| Canonical Source | **v1.0.0** — see `VERSION.md` | |

**NEXT EXECUTIVE GATE:** No live paid outreach until a Wisconsin attorney
has reviewed `docs/LEGAL_REVIEW_BRIEF.md`. Every code-level gate (fee
ceiling, 24-month eligibility, approved agreement, data controls) is now
implemented and tested — see `docs/LAUNCH_RUNBOOK.md` for exactly what's
left and whose job each item is.

> Mirrored from the Drive spreadsheet. A `Repo` column has been added to show
> what this codebase now enforces as of 2026-08-01.

## Workstreams

| ID | Workstream | Status | Priority | Canonical Folder |
|:--|:--|:--|:--|:--|
| WS-01 | Command | ACTIVE | P0 | 00_COMMAND |
| WS-02 | Legal & Compliance | BLOCKED | P0 | 01_LEGAL_COMPLIANCE |
| WS-03 | Product Strategy | ACTIVE | P1 | 02_PRODUCT_STRATEGY |
| WS-04 | Data Ledger | ACTIVE | P0 | 03_DATA_LEDGER |
| WS-05 | CRM Pipeline | ACTIVE | P0 | 04_CRM_PIPELINE |
| WS-06 | Outreach | BLOCKED | P0 | 05_OUTREACH |
| WS-07 | Engineering | ACTIVE | P0 | 06_ENGINEERING |
| WS-08 | Automation & Agents | PLANNED | P1 | 07_AUTOMATION_AGENTS |
| WS-09 | Operations | PLANNED | P1 | 08_OPERATIONS |
| WS-10 | Analytics & Finance | PLANNED | P1 | 09_ANALYTICS_FINANCE |
| WS-11 | Testing & QA | PLANNED | P0 | 10_TESTING_QA |
| WS-12 | Deployment | BLOCKED | P1 | 11_DEPLOYMENT_RELEASES |
| WS-13 | Brand & Sales | PLANNED | P2 | 12_BRAND_SALES |

## Deliverables

| ID | P | Deliverable | Drive Status | Acceptance Criteria | **Repo (2026-10-05)** |
|:--|:--|:--|:--|:--|:--|
| D-001 | P0 | Correct WI fee ceiling across code and templates | NOT STARTED | No calc or agreement exceeds 10% | ✅ `compliance.WI_FEE_CAP`; all modules import it |
| D-002 | P0 | Implement 24-month custody eligibility gate | NOT STARTED | Agreement blocked until eligibility evidenced | ✅ `assert_agreement_allowed`; contract gen raises `EligibilityError` |
| D-003 | P0 | Declare canonical v0.2 prototype package | DONE | One frozen package with manifest + version | ✅ `VERSION.md` declares v1.0.0; superseded frontends moved to `archive/` |
| D-004 | P0 | Publish canonical schema + deterministic IDs | DONE | Lineage, dedupe, eligibility fields defined | ✅ deterministic IDs (`deterministic_id`); full schema in `docs/DATA_SCHEMA.md` |
| D-005 | P0 | Replace real demo records with synthetic data | DONE | No real owner data in demos/tests/docs | ✅ demos synthetic; `.gitignore` blocks real CSVs (2026-10-01 pass also scrubbed real names found in `heirbud_command_deck.html`/`heirbud_v2.html`/test fixtures — those three files are now archived) |
| D-006 | P0 | Auth, roles, secure secrets, audit logs | DONE for single-operator scope | Unauthorized API + PII access blocked/logged | ✅ `X-API-Key` + CORS allowlist; `.env.example` documents every secret (none hardcoded); `contact_log`/`stage_history` are the audit trail. Multi-user RBAC deliberately not built for a headcount of one — revisit if a second person is actually hired. |
| D-007 | P0 | Approve proof-first USPS pilot packet | BLOCKED on operator | Free path, identity, privacy, optional service clear | ◑ honest templates in `docs/EMAIL_TEMPLATE_LIBRARY.md`; **legal sign-off is the one remaining blocker — `docs/LAUNCH_RUNBOOK.md` step 1** |
| D-008 | P1 | Approve expanded pipeline + suppression model | DONE | Eligibility, consent, suppression, claim, payment states explicit | ✅ full state model documented in `docs/DATA_SCHEMA.md` |
| D-009 | P1 | Run controlled 25-record pilot | BLOCKED on operator | All verified; every touch logged; no auto-send | ⬚ ready to run — waiting on `docs/LAUNCH_RUNBOOK.md` steps 1–4 (legal sign-off + a real verified batch), not on code |
| D-010 | P1 | Baseline compliance + funnel dashboard | DONE | Metrics distinguish published/eligible/expected/realized | ✅ `analytics.py` + `GET /analytics/summary` + console Analytics tab |
| D-011 | P1 | Backups with tested recovery | DONE | A backup can actually be restored, proven by a test | ✅ `backup_restore.py` + `tests/test_backup_restore.py` |

Legend: ✅ done · ◑ partial · ⬚ not started

## Critical Risks

| ID | Severity | Risk | **Repo mitigation** |
|:--|:--|:--|:--|
| R-001 | CRITICAL | Fee calculations exceed WI 10% ceiling | ✅ central cap, clamps any input |
| R-002 | CRITICAL | Agreements generated before 24-month eligibility | ✅ hard eligibility gate |
| R-003 | CRITICAL | API exposes personal records without authentication | ◑ optional API key + CORS allowlist (full multi-user RBAC deliberately out of scope — see D-006) |
| R-004 | HIGH | PII in unencrypted SQLite and demos | ◑ synthetic demos + gitignore + tested backup/restore (field-level encryption-at-rest still pending — note for whenever the DB leaves a single operator's own machine) |
| R-005 | HIGH | Fallback IDs unstable; duplicates split | ✅ deterministic SHA-1 IDs |
| R-006 | HIGH | Unsupported urgency / generalized claims in outreach | ✅ rewritten honest templates |
| R-007 | HIGH | Multiple overlapping builds, no canonical release | ✅ v1.0.0 declared (`VERSION.md`); superseded builds in `archive/` |

## Decisions

| ID | Date | Status | Decision |
|:--|:--|:--|:--|
| DEC-001 | 2026-07-30 | APPROVED | One canonical HEIRBUD Live Operating System root |
| DEC-002 | 2026-07-30 | PROPOSED | Compliance-first product definition |
| DEC-003 | 2026-07-30 | APPROVED | Synthetic data for demos and testing |
