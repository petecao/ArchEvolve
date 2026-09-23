# 14 — gapbs tc

Created: 2026-09-22
**Type:** slice
**Status:** resolved
**Blocked by:** 11
**Spec:** `../spec.md`

**What to build:** The database covers gapbs triangle counting, exercising the
data-dependent-merge address shape.

- [x] A kernel record with a verifier-based correctness check, and a baseline implementation record describing the sorted neighbor-list intersection as a data-dependent merge, with semantics with basis.
- [x] Profiles on mbit10 for the four pilot inputs validate, with a timeout per run. A run that times out at scale 22 is recorded as incomplete, not dropped. A view is generated for each completed pair.

## Comments

- 2026-09-23 (spec review fix): `RelabelByDegree` (a `BuilderBase` member) was missed by the kernel-symbol match. Recomputed from the raw output: kron-g16 kernel LL misses 105 -> 27,167; kron-g22 870,998,124 -> 898,933,973; inferred bottlenecks unchanged.

## Answer

Resolved 2026-09-22.

- Kernel `gapbs-tc` (TCVerifier, exact count) and baseline `gapbs-tc-ordered` (Hybrid →
  OrderedCount, with the degree relabeling inside the timed kernel recorded as a
  `condition`). The sorted neighbor-list intersection is
  `stream > ranged_indirect > single_valued_indirect > data_dependent_merge : read`.
- Profiles on mbit10 for the four pilot inputs, all valid, views generated for each:
  kron-g16-k16, urand-u16-k16, urand-u22-k16 complete; kron-g22-k16 recorded
  `complete: false` because gapbs's serial TCVerifier did not finish (30 min in the first
  attempt, which then wrote nothing; the profiler gained `--allow-unverified` to record a timed-out check,
  and the re-run recorded the correctness part `timed_out` after 900 s; the database's
  `profiles.correctness` column and the view mark it unverified). Its timing (3 trials per
  thread count, 1800 s timeout each) and cachegrind completed: 85.8 s at 1 thread, 5.87 s at
  16 threads (efficiency 0.91); inferred memory_bound (latency).
- Records: e6fbf25 (mbit10).
