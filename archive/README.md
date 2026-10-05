# Archive

Superseded builds, kept for history — not run, not linked from the live app,
and not something a new session should extend. This satisfies the
Definition-of-Done rule in `docs/governance/HB-00_START_HERE.md`: *"One
canonical release exists. Old builds are archived, not quietly reused."*

## frontends/

Three earlier HeirBud UIs, all superseded by the current canonical pair:
`heirbud_command_center.html` (standalone, no server) and
`heirbud_console.html` + `owner_portal.html` (server-backed, served by
`heirbud_server.py`).

| File | Why it's archived |
|---|---|
| `heirfinder_v1.html` | Earliest standalone tool. No compliance gates, no eligibility states — predates `compliance.py`. |
| `heirbud_v2.html` | Early FastAPI-connected dashboard. No eligibility/custody gate, no fee cap, no suppression handling. |
| `heirbud_command_deck.html` | Static demo dashboard with hardcoded sample data and no connection to the real CRM or `compliance.py` — not a working surface, a mockup. |

None of these are imported by any Python module and none are served by
`heirbud_server.py`. If a future session wants a feature that only exists
here, port the *logic* into the canonical frontend — don't resurrect the
file itself.
