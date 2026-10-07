# HeirBud canonical release

**v1.0.0 — compliance-hardened, pilot-ready pending legal sign-off**
Declared 2026-10-05. Project ID: PRJ-HB7K4.

This is the one canonical HeirBud package (per
`docs/governance/HB-00_START_HERE.md` Definition of Done #6). Earlier builds
live in `archive/` and must not be reused or extended.

## What "v1.0.0" means here

Every P0 and P1 engineering item in
`docs/governance/HB-00_MASTER_CONTROL.md` that doesn't require a real-world
action by the operator (ZGroup LLC / Zack) is done:

- Fee cap, 24-month custody gate, free-claim disclosure — enforced in code
  (`compliance.py`), not just documented.
- No real owner data anywhere in the repo, source, demos, or tests.
- One canonical frontend pair (`heirbud_command_center.html` standalone;
  `heirbud_console.html` + `owner_portal.html` server-backed). Everything
  else archived.
- Full data schema documented (`docs/DATA_SCHEMA.md`).
- Backups with a tested restore path (`backup_restore.py` +
  `tests/test_backup_restore.py`).
- 160+ passing tests locking every compliance gate, the household graph,
  and now backup/restore.

## What "v1.0.0" does NOT mean

It does not mean cleared for live outreach to real owners. Three things
remain outside engineering's control — see `docs/LAUNCH_RUNBOOK.md` for the
exact, ordered list:

1. **Legal sign-off** (`docs/LEGAL_REVIEW_BRIEF.md`) — a Wisconsin attorney
   has not yet reviewed the fee/agreement/outreach model. This is a human
   decision, not a code gate.
2. **Registration/bonding**, if Wisconsin turns out to require any —
   unconfirmed either way; the attorney review above should settle it.
3. **The operator's own identity and infrastructure** — real name/address in
   `letter_generator.SENDER`, a real `HEIRBUD_BASE_URL` domain, a real
   `HEIRBUD_API_KEY`, and the decision of which paid skip-trace provider (if
   any) to wire into `skiptrace.py`.

Bump this file (and re-run the full test suite) on any change to
`compliance.py`'s constants, the CRM schema, or the canonical frontend set.
