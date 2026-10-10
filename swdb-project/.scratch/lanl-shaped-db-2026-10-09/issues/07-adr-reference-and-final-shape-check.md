# 07 — ADR 0015, database reference, final shape check

Created: 2026-10-09
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 03, 04, 05, 06
**Spec:** `../spec.md`

**What to build:** ADR 0015 (status proposed) records that the research database takes the main
database's shape and amends ADR 0014's "crosswalk instead of a shared schema", keeping its other
rules. The database reference document is rewritten for the new layout: LANL core, `swdb_`
extension, guessed columns, the measured-only rule, and how to drop the extension. One test checks
that all 16 slide tables plus `kernel_variants` exist with their expected columns. The build stays
about as fast as today.

About 1.5 h.

- [ ] ADR 0015 exists, is dated, and ADR 0014 points to it
- [ ] The reference document describes every LANL and `swdb_` table and is dated
- [ ] A test fails if any slide table is missing or has a wrong column
- [ ] A build of the repository records still takes about a second
- [ ] The full test suite passes
