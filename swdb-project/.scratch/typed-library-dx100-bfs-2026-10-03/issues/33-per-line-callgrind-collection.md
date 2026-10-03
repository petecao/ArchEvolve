# 33 — Per-line callgrind collection inside TDStep

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

**What to build:** The region profiler can record per-statement cache behavior for TDStep, as ground truth for the profiling agent.

## Acceptance

- [x] A second callgrind execution, limited to TDStep and built with debug information, runs beside the whole-ROI one.
- [x] A per-line parser handles name compression and subposition lines.
- [x] Per-line rows go in a separate field of the region profile with its own validator; whole-ROI rows are unchanged.
- [x] Last-level misses are summed per statement line range with basis simulated.
- [x] Tests use a fixture callgrind file; existing profiling tests are unchanged.

## Comments

## Answer

Implemented optional `per_line: true` collection in `swdb/bfs_profiling.py`, separate `per_line_memory`/`statement_memory` schema fields, and the independent `swdb.callgrind.lines.v1` parser/validator. The second debug binary bounds global instrumentation to scalar TDStep, preserving original debug lines and capturing all OpenMP workers. Compressed names, relative subpositions, repeated self costs, inclusive call-edge exclusion, counter bounds/hierarchy and raw summary checks are covered. Statement costs sum simulated `DLmr + DLmw` over the seven mapped ranges.

Validation: the original 26 BFS profiling tests passed unchanged alongside 18 initial new tests (44 passed); the final expanded annotation/parser/mapping/driver suite, format documentation and original profiler suite pass 54 tests. All 379 current records validate. Real collection is ticket 34, not this fixture-backed implementation result. Each TDStep invocation starts with fresh modeled caches, and optimized/coalesced/inlined-header work limits source-line attribution; these diagnostics establish no native or hardware gain. The 12-dump fixture verifies numeric invocation order past dump 9.
