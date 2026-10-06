# 19 — Prefactor: one access layer for record reads

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 01
**Spec:** `../spec.md`
**Time estimate:** 3–4 h

**What to build:** Move the direct SQLite reads in `swdb/db.py` and `swdb/site_finder.py` behind one interface next to `swdb/store.py`, so a different database later means a new adapter, not edits across tools. No behavior change.

## Acceptance

- [ ] Every query command returns the same output before and after (tests).
- [ ] Only the access layer opens SQLite.
