# 04 — Workload view

Created: 2026-09-22
**Type:** slice
**Status:** resolved
**Blocked by:** 02, 03
**Spec:** `../spec.md`

**What to build:** The HW Ensemble Agent gets `swdb view <implementation> <input>
<machine>`, which prints one workload in Josh's existing format with array sizes
evaluated for that input and every unknown left visibly unknown.

- [x] Output field names and nesting match Josh's `sparta-sort.input.yaml` (a test compares against the copied draft).
- [x] `workload_id` is `<implementation>@<input>@<machine>`.
- [x] Element counts are evaluated to numbers from the input's properties; if a property is unknown, the count shows as unknown, never guessed.
- [x] A formula that uses a symbol the input does not define makes the command exit non-zero, naming the symbol.
- [x] Semantic values appear with their evidence, and the basis of each is visible.
- [x] With no profile yet, counts, metrics, and bottleneck appear explicitly as unknown.

## Comments

## Answer

Resolved 2026-09-22.

- `swdb view <implementation> <input> <machine> [--format yaml|json] [--profile ID]`
  (`swdb/view.py`).
- `tests/test_view.py` compares the output with Josh's `sparta-sort.input.yaml`: every key
  and nesting level is present (extra keys are only additions: `address_chain`,
  `pattern_class`, `element_count_formula`, `semantics_evidence`, `condition`,
  `undirected_alias`).
- `workload_id` = `<implementation>@<input>@<machine>`; element counts evaluated from the
  input (null while a property is unknown, never guessed); a symbol the input does not
  define exits 1 naming it; semantic values with basis and evidence under
  `semantics_evidence`; with no profile, counts/metrics/bottleneck are explicitly unknown
  (`iterations: {value: null, scope: unknown}`, `bottleneck.classification: unknown`).
