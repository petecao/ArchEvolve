# 05 — Remaining 9 tables, slide coverage check, README

Created: 2026-10-09
**Type:** slice
**Status:** wontfix
**Blocked by:** 03, 04
**Spec:** `../spec.md`

**What to build:** v1 maps every remaining slide table per the spec's mapping table:
`hardware_profiles`, `run_configs`, `performance_runs` (measured profiles only; estimates
excluded), `performance_metrics` (note: no measured/estimated marker), `Validation_definition`,
`Validation_results`, `physics_assets`, `kernel_dependencies`, `code_chunks`, `embeddings`. A test
fails if any table in the spec appendix is missing from v1. The compatibility README gains a
plain-language v1 section: the two sources, `link`, `cardinality`, the new extension concepts, and
the validation command for each version.

- [ ] All 16 slide tables appear in v1 with the slide's exact identifiers
- [ ] The slide inconsistencies (`correctness_runs`, `fixture_id` without a `fixtures` table) are kept as notes
- [ ] A coverage test fails when a slide table is removed from v1
- [ ] The README explains v1 without needing the schema open, and is dated
- [ ] The full existing test suite passes

## Comments

Superseded 2026-10-09 ET by [the LANL-shaped database spec](../../lanl-shaped-db-2026-10-09/spec.md): Yan-Ru wants the research database migrated to LANL's shape, not a mapping document.
