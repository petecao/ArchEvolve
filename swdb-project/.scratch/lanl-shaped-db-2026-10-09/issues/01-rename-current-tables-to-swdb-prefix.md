# 01 — Rename every current table to swdb_ (no behavior change)

Created: 2026-10-09
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

**What to build:** `swdb build` produces the same tables as today, each renamed with a `swdb_`
prefix (`swdb_meta`, `swdb_records`, `swdb_kernels`, `swdb_implementations`, `swdb_profiles`,
`swdb_metrics`, `swdb_library_entries`, …). Columns and contents do not change. Every query
command (`find`, `implementations`, `strategies`, `compare`, the site finder, record lookups) gives
identical output. Raw SQL inside `swdb-project/` (code, scripts, tools, tests, docs) uses the new
names. This prefactor frees the LANL table names (`kernels` above all) for ticket 02.

About 2 h.

- [ ] A fresh build contains only `swdb_`-prefixed tables, with today's columns
- [ ] Every query command's output is unchanged on the repository records
- [ ] No raw SQL in `swdb-project/` refers to an old table name
- [ ] An older database file is rebuilt automatically on first use (builder version changes)
- [ ] The full test suite passes; tests change only table names inside raw SQL, never expected results
