# 46 — Library JSON schema and SQLite index

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 42
**Spec:** `../spec.md`

**What to build:** Once BC reuses entries, library entries get a JSON schema and SQLite tables, as ADR 0007 defers.

## Acceptance

- [x] Library entries have a JSON schema.
- [x] SQLite tables cover library entries and a new statements index.
- [x] The database's staleness check covers the library folder.
- [x] Tests cover indexing and staleness.

## Comments

## Answer

Resolved 2026-10-03 23:50 ET (agent, BC track). Regression in this state: 204 passed (index, database, library, strategy queries); the 1 failure is the pre-existing ticket-39 list (sandbox `/private/tmp` denial).

**Built.**
- `schemas/library/library_entry.schema.json`: the shape of all four entry kinds (common and
  per-kind required fields, clause and pattern-key items). `swdb/library.py` validates
  entries against it (replacing the inline shape); pin, reference and clause checks follow.
- SQLite (`swdb/db.py`): `library_entries` (kind, path, content sha256, derived tier and
  status, cited contract), `library_dependencies`, `library_clauses`, and the statements index
  `statements` plus `statement_steps` (implementation statement annotations). Documented in
  `docs/reference/database.md`.
- Staleness: the fingerprint covers every file of the library folder beside `records/`
  (entries and pinned code); `meta` records `library_dir`. Queries rebuild after a library edit.

**Tests.** `tests/test_library_index.py`, 8 cases (schema over every repository entry; three
shape errors reported by field; entries, hashes, dependencies, clauses; statements and steps;
staleness after entry, pinned-code and new-file changes; records without a library). The
existing table/column documentation test covers the new tables.

**Assumptions.** Tier and status in SQLite are derived exactly as `swdb.library` derives them
at build time; an underivable state is NULL. A records folder other than the repository's uses
`library/` beside it, as `swdb submit` does.
