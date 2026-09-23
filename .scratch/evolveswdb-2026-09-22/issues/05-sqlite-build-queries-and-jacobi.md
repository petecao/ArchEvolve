# 05 — SQLite build and queries, plus the Jacobi implementation

Created: 2026-09-22
**Type:** slice
**Status:** resolved
**Blocked by:** 02
**Spec:** `../spec.md` (ADR 0002)

**What to build:** The owner and agents query the database. `swdb build` generates
SQLite from the YAML files, and `find` and `implementations` answer questions from it.
The Jacobi implementation of PageRank shows the "SW specs" query working.

- [x] `swdb build` regenerates the SQLite file from scratch on every run, finishes in about a second for the pilot, and the file is ignored by git.
- [x] The Jacobi implementation record (`PageRankPull` from upstream `pr_spmv.cc`) stores its code file next to the record, with origin, build command, correctness check, and semantics showing no loop-carried dependency.
- [x] `swdb find` filters access patterns by address shape, update kind, and semantic value, and prints YAML or JSON.
- [x] `swdb implementations <pagerank kernel> --require loop_carried_dependencies=false` returns Jacobi and not the baseline; without the requirement it returns both.
- [x] The database tables are documented so the owner can write their own SQL.

## Comments

- 2026-09-22 (spec review fix): The SQLite file records its records folder and a fingerprint of the files; queries rebuild unless both match, and sibling folders get their own default file (the reviewer's a/b reproduction is a test).

## Answer

Resolved 2026-09-22.

- `swdb build` regenerates `build/swdb.sqlite` from scratch (temp file + rename) in
  0.05 s for the pilot records; `build/` and `*.sqlite` are gitignored
  (`tests/test_db.py::test_database_file_is_ignored_by_git`).
- Jacobi: `records/implementations/gapbs-pr-jacobi.yaml` with its code file
  `records/implementations/gapbs-pr-jacobi/pr_spmv.cc` (upstream copy, sha256 checked),
  origin `upstream_alternative`, build `-I {app}/src`, semantics with
  `loop_carried_dependencies: false` on every pattern.
- `swdb find --shape/--update/--semantic/--kernel` and `swdb implementations <kernel>
  --require f=v` (YAML or JSON). `swdb implementations gapbs-pr --require
  loop_carried_dependencies=false` → `gapbs-pr-jacobi` only; without it → both. Unknown
  never satisfies a requirement.
- Tables documented in `docs/database.md`; a test fails if any table or column is missing
  there. `swdb sql` runs your own SQL.
