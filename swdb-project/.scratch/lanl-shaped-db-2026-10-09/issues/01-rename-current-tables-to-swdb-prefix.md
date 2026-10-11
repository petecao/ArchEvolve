# 01 — Rename every current table to swdb_ (no behavior change)

Created: 2026-10-09
**Type:** slice
**Status:** claimed
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

## Comments

**2026-10-11 19:15 ET — Yan-Ru's decision (fixtures).** Tests that copy the whole repository
catalog (~1 GB, ~700 s per `swdb` command) already time out before this work. Yan-Ru approved
switching those fixtures to the record-closure helper (`Records.copy_closure`, LR-03). This is a
fixture change; expected results still do not change. Keep a full-catalog copy only where catalog
integration is what the test checks. This amends the last checkbox: "tests change only table
names inside raw SQL, and catalog-copying fixtures may move to the closure helper".
