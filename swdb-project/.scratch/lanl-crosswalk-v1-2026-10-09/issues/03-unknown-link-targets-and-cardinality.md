# 03 — Unknown link targets and cardinality

Created: 2026-10-09
**Type:** slice
**Status:** wontfix
**Blocked by:** 02
**Spec:** `../spec.md`

**What to build:** the v1 format can say where a link column points, or that it is unknown, and
how many LANL rows one SWDB record maps to. The v1 document uses this for:
`Validation_results.kernel_variant_id` (candidates: a `kernels` row, an `executables` row, a table
not shown), `Validation_results.fixture_id` (candidates: a `Validation_definition` row, a table not
shown), and `kernels` (cardinality `unknown`, note naming the one-to-many possibility). No
candidate is chosen.

- [ ] `kernel_variant_id` lists its three candidates; `fixture_id` lists its two
- [ ] The `kernels` mapping states cardinality `unknown` with the one-to-many note
- [ ] An `unknown` link with fewer than two candidates is refused
- [ ] A cardinality value outside `one_to_one`, `one_to_many`, `many_to_one`, `unknown` is refused
- [ ] The v0 document still validates

## Comments

Superseded 2026-10-09 ET by [the LANL-shaped database spec](../../lanl-shaped-db-2026-10-09/spec.md): Yan-Ru wants the research database migrated to LANL's shape, not a mapping document.
