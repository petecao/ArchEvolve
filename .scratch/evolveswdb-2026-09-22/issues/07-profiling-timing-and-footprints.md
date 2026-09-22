# 07 — Profiling: timing and footprints

Created: 2026-09-22
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 03, 04, 06
**Spec:** `../spec.md`

**What to build:** `swdb profile <implementation> <input> <machine>` builds and runs an
implementation, measures time across thread counts, computes array footprints, keeps the
raw output outside git, and writes a profile record. The workload view then shows those
numbers.

- [ ] Profile schema: build (compiler, flags, source commit), run (command, threads, binding, date), counts with scope and note, metrics with units, a bottleneck fact, and raw-file pointers.
- [ ] The timing sweep runs 1, 2, 4, 8, and 16 threads with several trials each, parses the benchmark's own timer lines, and records median and spread per thread count.
- [ ] Footprints per array are computed from element size times element count on the input.
- [ ] While counters are unavailable, the bottleneck is recorded with `basis: inferred` and names the metrics it rests on.
- [ ] Raw output goes to a runs folder outside git, and the profile records the folder used. On mbit10, that folder is on `/data1`, or on `/data` when `/data1` has under 20 GB free.
- [ ] On mbit10, runs go through the host's socket-lane procedure, which is documented in the repo.
- [ ] The Mac tests use a stub benchmark that prints gapbs-style timer lines.
- [ ] `swdb view` fills counts, metrics, and bottleneck from the profile.

## Comments
