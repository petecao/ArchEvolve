# 02 — Kernel and baseline implementation for gapbs PageRank

Created: 2026-09-22
**Type:** slice
**Status:** resolved
**Blocked by:** 01
**Spec:** `../spec.md` (ADRs 0001, 0003)

**What to build:** The database describes gapbs PageRank: a kernel defined by its
correctness check, and its baseline implementation with code, loops, access-pattern
chains, and semantics. `swdb validate` enforces the rules that keep those facts honest.

- [x] gapbs is copied in from upstream GitHub at a pinned commit with a provenance note (URL, commit, date, license); MemAcc's local `pr_push.cc` is not included.
- [x] Kernel schema and a PageRank kernel record: what it computes, its correctness check (verifier command plus tolerance), and its baseline implementation ID.
- [x] Implementation schema and the baseline implementation record (`PageRankPullGS`): code copied with file and line range, loops with trip counts and parallelism, access patterns as chains of steps, semantics per access pattern with basis. It states the Gauss-Seidel loop-carried dependency.
- [x] A test confirms the recorded code equals the copied source at the recorded lines.
- [x] Vocabularies for address shapes (with their attributes), update kinds, basis, array roles, and count scopes, each value with a one-line meaning.
- [x] Validator rules, each with a passing and a failing fixture: every reference resolves; IDs are unique; `basis: unknown` requires `value: null`; vocabulary values exist; step attributes match their address shape.

## Comments

- 2026-09-22 (spec review fix): Added the missing failing fixtures: duplicate provenance and loop IDs, dangling loop parent, trip-count symbol outside the vocabulary, nonexistent `run.index_stream.pattern`, `deprecated_by` of another kind, excerpt without lines, code without a local copy.

## Answer

Resolved 2026-09-22.

- gapbs copied unchanged from upstream commit `2972aeb` into `apps/gapbs/` with
  `apps/gapbs/PROVENANCE.md` (URL, commit, date, license, how to check); every tracked file
  except `.github/` matched upstream by sha256; no `pr_push.cc`.
- Kernel schema + `records/kernels/gapbs-pr.yaml`: what it computes, correctness check
  (`{binary} {input_args} -n 1 -v`, PRVerifier `src/pr.cc` 76-94 copied, pass regex,
  tolerance 1e-4 L1), baseline `gapbs-pr-gs`.
- Implementation schema + `records/implementations/gapbs-pr-gs.yaml` (PageRankPullGS,
  `src/pr.cc` 34-61 copied; loops init/sweep/vertex/edge with trip counts and OpenMP
  schedule; five access patterns as chains; the gather is
  `stream > ranged_indirect > single_valued_indirect : read` with
  `loop_carried_dependencies: true, basis: code_reading` (Gauss-Seidel, lines 49/53)).
- Vocabularies with one-line meanings: `address_shapes`, `index_transforms`,
  `update_kinds`, `basis`, `array_roles`, `count_scopes` (+ others in `vocab/`).
- Validator rules, each with a passing and a failing fixture in
  `tests/test_validate_rules.py`: references resolve (and to the right kind), unique IDs,
  `basis: unknown` requires `value: null` (and a known basis needs a value), vocabulary
  values, step attributes per address shape, chain rules, formula symbols, excerpt equals
  the source lines (`tests/test_records.py::test_recorded_code_equals_the_copied_source`).
- Evidence: `python3 -m pytest` → 167 passed, 1 skipped (Mac, 2026-09-22); the same suite
  under jsonschema 4.10.3 / PyYAML 6.0.1 passed; on mbit10 (commit 677346d) 150 passed.

Decisions: evidence_refs point to provenance IDs of the same record; kind schemas share
`$defs` merged from the envelope (no cross-file `$ref`); the ID of the baseline is
`gapbs-pr-gs`.
