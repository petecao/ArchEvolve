# 04 — Workload view

Created: 2026-09-22
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 02, 03
**Spec:** `../spec.md`

**What to build:** The HW Ensemble Agent gets `swdb view <implementation> <input>
<machine>`, which prints one workload in Josh's existing format with array sizes
evaluated for that input and every unknown left visibly unknown.

- [ ] Output field names and nesting match Josh's `sparta-sort.input.yaml` (a test compares against the copied draft).
- [ ] `workload_id` is `<implementation>@<input>@<machine>`.
- [ ] Element counts are evaluated to numbers from the input's properties; if a property is unknown, the count shows as unknown, never guessed.
- [ ] A formula that uses a symbol the input does not define makes the command exit non-zero, naming the symbol.
- [ ] Semantic values appear with their evidence, and the basis of each is visible.
- [ ] With no profile yet, counts, metrics, and bottleneck appear explicitly as unknown.

## Comments
