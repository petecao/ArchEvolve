# 07 — Profiling: timing and footprints

Created: 2026-09-22
**Type:** slice
**Status:** resolved
**Blocked by:** 03, 04, 06
**Spec:** `../spec.md`

**What to build:** `swdb profile <implementation> <input> <machine>` builds and runs an
implementation, measures time across thread counts, computes array footprints, keeps the
raw output outside git, and writes a profile record. The workload view then shows those
numbers.

- [x] Profile schema: build (compiler, flags, source commit), run (command, threads, binding, date), counts with scope and note, metrics with units, a bottleneck fact, and raw-file pointers.
- [x] The timing sweep runs 1, 2, 4, 8, and 16 threads with several trials each, parses the benchmark's own timer lines, and records median and spread per thread count.
- [x] Footprints per array are computed from element size times element count on the input.
- [x] While counters are unavailable, the bottleneck is recorded with `basis: inferred` and names the metrics it rests on.
- [x] Raw output goes to a runs folder outside git, and the profile records the folder used. On mbit10, that folder is on `/data1`, or on `/data` when `/data1` has under 20 GB free.
- [x] On mbit10, runs go through the host's socket-lane procedure, which is documented in the repo.
- [x] The Mac tests use a stub benchmark that prints gapbs-style timer lines.
- [x] `swdb view` fills counts, metrics, and bottleneck from the profile.

## Comments

- 2026-09-22 (spec review fix): On mbit10 `swdb profile` itself refuses to run unless a `socket_lane.sh` process is an ancestor and its affinity is exactly one NUMA node (verified positive and negative on mbit10); the lab-host test runs only inside a lane.

## Answer

Resolved 2026-09-22.

- Profile schema (build, environment, parts with outcomes, timing, counts with scope,
  metrics with units, inferred bottleneck with `rests_on`, `runs_folder`).
- `swdb profile` (`swdb/profile.py`): build, correctness check (stops on failure), timing
  sweep at 1/2/4/8/16 threads × `--trials` (default 5), each parsed from gapbs's own
  `Trial Time` lines → median, min, max, spread, speedup, parallel efficiency;
  footprints = element bytes × element count on the input (undirected aliases once;
  lower bound when a size is data-dependent); bottleneck `basis: inferred` from footprint
  vs one socket's LLC, 16-thread efficiency, and simulated LL miss rate.
- Raw output outside git; refuses a runs folder inside the repo; mbit10 runs go through
  `scripts/mbit10/profile_in_lane.sh` (MemAcc `socket_lane.sh`, lease check incl. legacy,
  disk rule), documented in `docs/mbit10-profiling.md`.
- Mac tests use a stub benchmark printing gapbs timer lines (`tests/test_profile.py`);
  `swdb view` fills counts, metrics, and bottleneck from the profile.
- First real profile: `gapbs-pr-gs.kron-g16-k16.mbit10.20260922t212238z` (14 s run).
