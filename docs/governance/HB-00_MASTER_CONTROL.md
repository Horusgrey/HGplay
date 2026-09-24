# HEIRBUD — MASTER CONTROL

| | | |
|:--|:--|:--|
| **Project** | PRJ-HB7K4 | Updated 2026-07-30 |
| Current Phase | Prototype consolidation and compliance correction | |
| Overall Status | ACTIVE BUILD | |
| Compliance Status | BLOCKED — fee and eligibility logic | |
| Production Status | BLOCKED — prototype only | |
| Canonical Source | NOT YET DECLARED | |

**NEXT EXECUTIVE GATE:** No live paid outreach until fee ceiling, 24-month
eligibility, approved agreement, and data controls are implemented.

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

| ID | P | Deliverable | Drive Status | Acceptance Criteria | **Repo (2026-08-01)** |
|:--|:--|:--|:--|:--|:--|
| D-001 | P0 | Correct WI fee ceiling across code and templates | NOT STARTED | No calc or agreement exceeds 10% | ✅ `compliance.WI_FEE_CAP`; all modules import it |
| D-002 | P0 | Implement 24-month custody eligibility gate | NOT STARTED | Agreement blocked until eligibility evidenced | ✅ `assert_agreement_allowed`; contract gen raises `EligibilityError` |
| D-003 | P0 | Declare canonical v0.2 prototype package | IN PROGRESS | One frozen package with manifest + version | ◑ code consolidated in repo; version tag pending |
| D-004 | P0 | Publish canonical schema + deterministic IDs | NOT STARTED | Lineage, dedupe, eligibility fields defined | ◑ deterministic IDs ✅ (`deterministic_id`); eligibility/consent/suppression fields ✅; full schema doc pending |
| D-005 | P0 | Replace real demo records with synthetic data | NOT STARTED | No real owner data in demos/tests/docs | ✅ demos synthetic; `.gitignore` blocks real CSVs |
| D-006 | P0 | Auth, roles, secure secrets, audit logs | NOT STARTED | Unauthorized API + PII access blocked/logged | ◑ optional `X-API-Key` + CORS allowlist; roles/audit pending |
| D-007 | P0 | Approve proof-first USPS pilot packet | BLOCKED | Free path, identity, privacy, optional service clear | ◑ honest templates in `docs/EMAIL_TEMPLATE_LIBRARY.md`; legal sign-off pending |
| D-008 | P1 | Approve expanded pipeline + suppression model | NOT STARTED | Eligibility, consent, suppression, claim, payment states explicit | ◑ SUPPRESSED stage + consent fields ✅; full state model pending |
| D-009 | P1 | Run controlled 25-record pilot | BLOCKED | All verified; every touch logged; no auto-send | ⬚ pending D-001/002/007 (now unblocked) |
| D-010 | P1 | Baseline compliance + funnel dashboard | NOT STARTED | Metrics distinguish published/eligible/expected/realized | ⬚ pending |

Legend: ✅ done · ◑ partial · ⬚ not started

## Critical Risks

| ID | Severity | Risk | **Repo mitigation** |
|:--|:--|:--|:--|
| R-001 | CRITICAL | Fee calculations exceed WI 10% ceiling | ✅ central cap, clamps any input |
| R-002 | CRITICAL | Agreements generated before 24-month eligibility | ✅ hard eligibility gate |
| R-003 | CRITICAL | API exposes personal records without authentication | ◑ optional API key + CORS allowlist (full RBAC pending) |
| R-004 | HIGH | PII in unencrypted SQLite and demos | ◑ synthetic demos + gitignore (encryption pending) |
| R-005 | HIGH | Fallback IDs unstable; duplicates split | ✅ deterministic SHA-1 IDs |
| R-006 | HIGH | Unsupported urgency / generalized claims in outreach | ✅ rewritten honest templates |
| R-007 | HIGH | Multiple overlapping builds, no canonical release | ◑ consolidated in repo (tag pending) |

## Decisions

| ID | Date | Status | Decision |
|:--|:--|:--|:--|
| DEC-001 | 2026-07-30 | APPROVED | One canonical HEIRBUD Live Operating System root |
| DEC-002 | 2026-07-30 | PROPOSED | Compliance-first product definition |
| DEC-003 | 2026-07-30 | APPROVED | Synthetic data for demos and testing |
