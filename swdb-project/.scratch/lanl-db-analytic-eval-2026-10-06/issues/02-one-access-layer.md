# 02 — Prefactor: one access layer for record reads

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 01
**Spec:** `../spec.md`
**Time estimate:** 3–4 h

**What to build:** Every record read and query goes through one interface beside the record store; the query and site-finder modules stop opening the generated database directly. Behavior does not change. Afterwards, pointing SWDB at another database (the main database, ADR 0014) means writing one adapter.

## Acceptance

- [ ] Every query command gives identical output before and after (existing tests stay green).
- [ ] Only the access layer opens the generated database.
- [ ] The interface is documented in the database reference.
