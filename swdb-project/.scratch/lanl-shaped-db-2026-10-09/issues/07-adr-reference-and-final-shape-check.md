# 07 — ADR 0015, database reference, final shape check

Created: 2026-10-09
**Type:** slice
**Status:** resolved
**Blocked by:** 03, 04, 05, 06
**Spec:** `../spec.md`

**What to build:** ADR 0015 (status proposed) records that the research database takes the main
database's shape and amends ADR 0014's "crosswalk instead of a shared schema", keeping its other
rules. The database reference document is rewritten for the new layout: LANL core, `swdb_`
extension, guessed columns, the measured-only rule, and how to drop the extension. One test checks
that all 15 slide tables ("16" was a miscount, corrected 2026-10-11) plus `kernel_variants` exist with their expected columns. The build stays
about as fast as today.

About 1.5 h.

- [ ] ADR 0015 exists, is dated, and ADR 0014 points to it
- [ ] The reference document describes every LANL and `swdb_` table and is dated
- [ ] A test fails if any slide table is missing or has a wrong column
- [ ] A build of the repository records still takes about a second
- [ ] The full test suite passes

## Comments

**2026-10-11 19:15 ET — Yan-Ru's decision (build speed).** The "about a second" premise was false
before this work: a build of the repository records takes ~170 s (plus ~530 s validation), peaks
at 4.9 GB RAM and writes a 952 MB file, mostly estimate JSON. Yan-Ru dropped the build-speed
criterion from this effort. The checkbox "A build of the repository records still takes about a
second" no longer applies. Spec user story 34 is void for the same reason.

## Answer

Resolved 2026-10-11 22:05 ET on `lanl-shaped-db` (ADR merge 1b4f57cd; reference/test merge
9d7f54bb, commits 64f53622, 43225380).
- ADR 0015 (proposed) records that the research database takes the main database's shape; ADR 0014
  points to it.
- `docs/reference/database.md` rewritten: LANL core (15 slide tables + guessed `kernel_variants`),
  `swdb_` extension, guessed columns, measured only, unknown is NULL, how to drop the extension
  (commands verified on a scratch build: 16 tables remain, FK check clean).
- `tests/test_lanl_shape.py` checks the exact core table set, every column and the guessed list in
  one build; verified to fail on a renamed column and on a missing table.
- GLOSSARY: LANL core, guessed column, SWDB extension; Crosswalk marked historical. Stale crosswalk
  prose fixed in 7 docs.
- Build-speed criterion dropped (2026-10-11 comment).
