# 33 — Per-line callgrind collection inside TDStep

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

**What to build:** The region profiler can record per-statement cache behavior for TDStep, as ground truth for the profiling agent.

## Acceptance

- [ ] A second callgrind execution, limited to TDStep and built with debug information, runs beside the whole-ROI one.
- [ ] A per-line parser handles name compression and subposition lines.
- [ ] Per-line rows go in a separate field of the region profile with its own validator; whole-ROI rows are unchanged.
- [ ] Last-level misses are summed per statement line range with basis simulated.
- [ ] Tests use a fixture callgrind file; existing profiling tests are unchanged.

## Comments
