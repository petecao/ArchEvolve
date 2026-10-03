# 46 — Library JSON schema and SQLite index

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 42
**Spec:** `../spec.md`

**What to build:** Once BC reuses entries, library entries get a JSON schema and SQLite tables, as ADR 0007 defers.

## Acceptance

- [ ] Library entries have a JSON schema.
- [ ] SQLite tables cover library entries and a new statements index.
- [ ] The database's staleness check covers the library folder.
- [ ] Tests cover indexing and staleness.

## Comments
