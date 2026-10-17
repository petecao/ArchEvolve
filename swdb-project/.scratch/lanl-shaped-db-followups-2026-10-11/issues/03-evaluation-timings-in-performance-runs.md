# 03 — Measured evaluation timings feed performance_runs

Created: 2026-10-11
Updated: 2026-10-11 23:28 ET (resolved)
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../../lanl-shaped-db-2026-10-09/spec.md` (D4, "What fills each LANL table"); ticket
04 answer there

**What to build:** today only profile `timing[]` entries become `performance_runs`. Evaluations
also record measured native timings (for example ROI timings of a baseline run on a real
machine). Add them to `performance_runs` (and their run configs) when the timing is measured on a
real machine and the thing evaluated is an implementation (same rule as `Validation_results`).
Simulated (gem5) and estimated timings never enter; ADR 0013 (no gem5 results in ArchEvolve mode).

- [x] A measured native evaluation timing of an implementation appears once in `performance_runs`
- [x] gem5/simulated, estimated and rewrite-candidate timings never appear
- [x] Origins, foreign-key, separability and record-field checks stay clean
- [x] database.md updated

## Answer

A finished evaluation of an implementation, run on a machine record, now gives one
`performance_runs` row (plus a shared `run_configs` row). `elapsed_seconds` is the median of its
measured native trials (`timing[]` entries with basis `measured`, quantity
`native_roi_wall_seconds`, evidence kind `execution`). That equals `summary.median_roi_seconds`.
"What ran" uses one shared rule, `swdb/lanl.py` `evaluated_implementation`, which
`Validation_results` also uses. gem5, contract-fixture and rewrite-candidate timings never
count. Neither do aggregates or unfinished evaluations. On the current records this is 34
evaluations.

- **Code:** `swdb/lanl.py` (`evaluated_implementation`, `evaluation_workload`),
  `swdb/lanl_performance.py` (`_evaluation_runs`), `swdb/lanl_validation.py` (uses the helpers).
- **Tests:** `tests/test_lanl_performance.py` (closure adds a native baseline, a measured rewrite,
  a gem5 baseline, a contract fixture, and an unfinished native baseline).
- **Docs:** `docs/reference/database.md`, sections `run_configs` and `performance_runs`.
- **Rule hardening:** an aggregate has no `request.candidate`. The shared rule now reads its
  top-level `candidate` instead of treating it as the plain implementation. This changes no
  current `Validation_results` row, because aggregates name no workload.
