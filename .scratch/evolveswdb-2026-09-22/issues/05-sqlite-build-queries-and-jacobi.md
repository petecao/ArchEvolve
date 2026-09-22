# 05 — SQLite build and queries, plus the Jacobi implementation

Created: 2026-09-22
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 02
**Spec:** `../spec.md` (ADR 0002)

**What to build:** The owner and agents query the database. `swdb build` generates
SQLite from the YAML files, and `find` and `implementations` answer questions from it.
The Jacobi implementation of PageRank shows the "SW specs" query working.

- [ ] `swdb build` regenerates the SQLite file from scratch on every run, finishes in about a second for the pilot, and the file is ignored by git.
- [ ] The Jacobi implementation record (`PageRankPull` from upstream `pr_spmv.cc`) stores its code file next to the record, with origin, build command, correctness check, and semantics showing no loop-carried dependency.
- [ ] `swdb find` filters access patterns by address shape, update kind, and semantic value, and prints YAML or JSON.
- [ ] `swdb implementations <pagerank kernel> --require loop_carried_dependencies=false` returns Jacobi and not the baseline; without the requirement it returns both.
- [ ] The database tables are documented so the owner can write their own SQL.

## Comments
