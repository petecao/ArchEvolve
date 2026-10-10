# 02 — First LANL slice: kernels and kernel_variants

Created: 2026-10-09
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 01
**Spec:** `../spec.md`

**What to build:** the build adds LANL's `kernels` table (slide columns: `id`, `slug`, `name`,
`category`) and the guessed `kernel_variants` table (`id`, `kernel_id`, `slug`). `kernels.slug` is
the SWDB kernel ID; `category` is the application domain when stated, else NULL. Each
implementation is one `kernel_variants` row. Integer IDs are assigned in a deterministic order.
The build also adds `swdb_row_origins` (table, row id, record id, record field) for every LANL row
and `swdb_guessed_columns` (table, column, reason), which lists `kernel_variants`. Foreign keys are
declared and checked at the end of each build.

This slice sets the test pattern later tickets extend: a shape test against the spec's appendix,
a separability test, an integrity test and an origin test.

About 3 h.

- [ ] `kernels` has exactly the slide's columns; `kernels.slug` equals the kernel ID
- [ ] `kernel_variants` has one row per implementation, linked to its kernel
- [ ] Every LANL row has a `swdb_row_origins` entry naming an existing record
- [ ] `PRAGMA foreign_key_check` is clean after a build, and still clean after deleting every `swdb_` table
- [ ] `swdb_guessed_columns` lists `kernel_variants` and its columns
- [ ] Unknown values (for example `category` with no stated domain) are NULL
