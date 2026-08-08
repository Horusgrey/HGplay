# HGplay — Repository Catalog

Sandbox for Zack's projects. Index of every file, grouped by project.

---

## 🟢 HeirBud / HeirFinder — Wisconsin unclaimed-property engine (active)

Compliance-first (PRJ-HB7K4). Start with `AUTONOMOUS_SYSTEM.md`, then `README.md`.

### Core engine
| File | Purpose |
|------|---------|
| `compliance.py` | **Single source of truth** — 10% fee cap, 24-month eligibility gate, disclosure |
| `heirbud_crm.py` | SQLite CRM — pipeline + custody/eligibility/consent/suppression fields |
| `seed_from_csv.py` | WI CSV import with deterministic dedupe IDs |
| `process_wisconsin_data.py` | WI export cleaner + priority scoring |
| `outreach_generator.py` | Honest, capped call/email/SMS scripts (suppression-aware) |
| `contract_generator.py` | Agreement PDFs — refuses to render unless eligible |
| `followup_engine.py` | Daily prioritized action queue (autonomy layer) |
| `verification_queue.py` | Custody-date verification worklist — prioritized, evidence-tracked |
| `reply_classifier.py` | Rule-based inbound-reply sorting + safe auto-actions |
| `outbox.py` | Approve-to-send queue with pluggable sender (dry-run default) |
| `heirbud_server.py` | FastAPI backend — optional API key, eligibility + suppress endpoints |
| `demo_pilot.py` | **One-command end-to-end pilot** on synthetic data — proves every gate |
| `fixtures/synthetic_wi_records.csv` | 24 fake WI records (16 eligible / 5 ineligible / 3 unverified) |
| `tests/` | 48 pytest cases locking every compliance gate |
| `requirements.txt` | Python deps |

### Frontends
| File | Purpose |
|------|---------|
| `heirbud_console.html` | **Operator console** — served at `/`, one-glance pipeline/worklist/outbox/actions |
| `heirfinder_v1.html` | Standalone tool (localStorage, AI enrichment) |
| `heirbud_v2.html` | Earlier dashboard (connects to FastAPI) |
| `heirbud_command_deck.html` | Command-deck interface |

### Docs
| File | Purpose |
|------|---------|
| `AUTONOMOUS_SYSTEM.md` | The autonomous money-maker design + revenue model |
| `docs/EMAIL_TEMPLATE_LIBRARY.md` | Proof-first outreach copy + deliverability rules |
| `docs/LEGAL_TEMPLATES_COMPLIANCE.md` | Per-state agreement templates + compliance ref |
| `docs/governance/HB-00_START_HERE.md` | Project mission + operating rules |
| `docs/governance/HB-00_SCOPE_AUDIT.md` | Whole-project assessment + launch blockers |
| `docs/governance/HB-00_MASTER_CONTROL.md` | Deliverable / risk / decision tracker (+ repo status) |

---

## 🎓 Odin / EduQuest — credential platform

| File | Purpose |
|------|---------|
| `ODIN_CANON1.md` | Canon v1.0 architecture spec — single index.html, no build step |
| `ODIN_SESSION_NOTES_202606123.md` | Strategic pivot: "credential not platform" |
| `Odin_Platform_PassOff_Guide.md` | Backend integration guide (Express/Mongoose/MongoDB) |
| `odinplatformlive1.html` | XP stub → eduquest-xp-api.onrender.com |
| `odin_platform_updated.html` | Polished Tailwind UI with AI curriculum generator |

---

## 🎬 EDNA CORE — AI screenwriting

| File | Purpose |
|------|---------|
| `ednacore5.html` | Full tool — UCS v2.0, CineFlow grammar, Claude 5-section output |

---

## 🌍 GMAPz Scout — film location scouting

| File | Purpose |
|------|---------|
| `gmapz_scout4.html` | 3D globe (Cesium.js), sun calculator, exports VCS-15 .md + VCO .json |

---

## Not committed (runtime / private — see `.gitignore`)

- `heirbud.db` — the live CRM database (may contain real PII)
- `contracts/` — generated agreement PDFs
- `WI_HeirFinder*.csv` and other real state exports — keep owner data out of git
- `TODAY_ACTIONS.md` — regenerated daily by `followup_engine.py`
