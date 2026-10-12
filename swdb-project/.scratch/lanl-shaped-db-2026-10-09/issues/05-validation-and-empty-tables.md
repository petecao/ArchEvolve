# 05 — Validation tables and the empty tables

Created: 2026-10-09
**Type:** slice
**Status:** resolved
**Blocked by:** 02
**Spec:** `../spec.md`

**What to build:** the build fills `Validation_definition` (`kernel_id`, `name`, `input_json`,
`expected_output_json`) from each kernel's correctness check with each input, and
`Validation_results` (`fixture_id`, `kernel_variant_id`, `passed`, `max_abs_error`) from the
correctness outcomes of profiles and evaluations. `fixture_id` links to `Validation_definition.id`
and is listed as guessed. Values not recorded are NULL. The build also creates `physics_assets`,
`kernel_dependencies`, `code_chunks` and `embeddings` empty, with the slide's columns (search-table
columns are guessed and listed). Table names keep the slide's capitalization. Can run in parallel
with 03 and 04.

About 2 h.

- [ ] All six tables exist with exactly the expected columns
- [ ] A fixture passing and a fixture failing correctness outcome each appear with the right `passed` value
- [ ] `expected_output_json` and `max_abs_error` are NULL when records do not state them
- [ ] The four empty tables have no rows; the guessed search-table columns are listed
- [ ] Origins, foreign-key and separability checks stay clean

## Answer

Resolved 2026-10-11 21:40 ET on `lanl-shaped-db` (commit 92493e81, merge f7c93d56).
Built in `swdb/lanl_validation.py`. `Validation_definition`: one row per (kernel, input) pair a
profile or evaluation actually ran; `name` = `<kernel>/<input>`, `input_json` = the input's
`generator` or the workload's `definition`, `expected_output_json` NULL (no record states one).
`Validation_results`: one row per correctness outcome naming an implementation and an input
record; `passed` 1 / 0 / NULL (not established), `max_abs_error` NULL. Outcomes without an
implementation or input record get no row. `physics_assets`, `kernel_dependencies`,
`code_chunks`, `embeddings` are created empty; `fixture_id` and the search-table columns are
listed as guessed. Tests: `tests/test_lanl_validation.py` (12 pass; the `code_chunks` →
`source_files` target check runs once ticket 03 is merged).
