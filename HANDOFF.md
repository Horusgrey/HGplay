# HeirBud handoff (read this first, any Claude)

Last updated: 2026-10-06. Owner: Zack (coding novice; explain in plain words, no jargon).

## What this is
HeirBud: a Wisconsin unclaimed-property recovery tool for ZGroup LLC. It finds owners of state-held money, mails them honest letters, and tracks the claim. Nothing sends itself; a human approves every message.

## Where the real work lives
- **This GitHub repo (Horusgrey/HGplay), branch `claude/heirfinder-unclaimed-property-yzdxf7`, PR #1 (draft).** This is the ONLY source of truth for HeirBud code.
- Not source of truth: Netlify copies (just hosting), the Gemini/Sheets/Make.com "v2" pipeline in Drive (auto-sends emails, used a wrong fee cap; do not run), archived frontends in `archive/`.
- Planning/strategy material (org chart, roadmap, status page) lives as claude.ai artifacts and Drive docs. They do not sync with the repo.

## State
- v1.0.0, engineering complete. 157 tests pass (`python -m pytest tests/ -q`).
- Wisconsin rules in code (`compliance.py`): fee cap 10%, 24-month custody wait. Verified against Wis. Stat. 177.1301 and the WI DOR FAQ.
- Two letter modes: GRATUITY (no fee quoted, default) and CONTRACT (10% max, only after verified custody).
- No real owner data in the repo. Keep it that way.

## Other threads' HeirBud files (reconciled 2026-10-07)
A separate claude.ai chat built `heirbud_dashboard.html`, `heirbud_v2.html` (same filename as the archived one, different file) and `heirbud_engine_v2.zip`. These are an OLDER prototype line, not the repo's v1.0.0:
- The zip's `outreach_generator.py` uses 12/15/20% fee tiers. That is above Wisconsin's 10% cap. Do not run it or mail anything from it.
- Its "157 tests pass" is the repo's number, not the zip's. Treat the zip as untested.
- Its demo data uses real claimant names and amounts. Never copy real names, addresses or dollar amounts into this repo.
- Anything useful from those files (e.g. one-click Gmail compose, CSV drag-drop) must be ported INTO this repo and pass `compliance.py`, not run alongside it.
Other projects mentioned there (Clippy, Odin DNS, VCS-2/ZEarth) are parked and out of scope for HeirBud.

## The one real blocker
A Wisconsin attorney has not reviewed the model. Brief to send: `docs/LEGAL_REVIEW_BRIEF.md`. Remaining steps: `docs/LAUNCH_RUNBOOK.md`.

## Rules for any Claude working here
1. Work only in this repo for HeirBud; don't build parallel copies elsewhere.
2. Never add auto-send. Never quote a fee above `compliance.py`'s cap.
3. Update this file at the end of every session.
4. Don't open or merge pull requests unless Zack asks.

## Session log
- 2026-10-05: v1.0.0 declared, PII scrubbed, docs rewritten, backups added.
- 2026-10-06: added this handoff file.
