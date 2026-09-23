# 09 — Simulated cache misses (cachegrind)

Created: 2026-09-22
**Type:** slice
**Status:** resolved
**Blocked by:** 07
**Spec:** `../spec.md`

**What to build:** Profiles on mbit10 include first-level and last-level cache misses
simulated by cachegrind, clearly marked as simulated.

- [x] `swdb profile` runs the implementation single-threaded under cachegrind (`--cache-sim=yes`) with a timeout, and records D1 and LL misses with `basis: simulated` and the simulated cache configuration.
- [x] A run that times out is recorded as incomplete, never silently dropped.
- [x] These tests are skipped on the Mac (valgrind does not run on macOS/arm64) and pass on mbit10.

## Comments

- 2026-09-22 (spec review fix): Cachegrind kernel matching now accepts qualified and templated demangled names and notes kernel symbols with no function; `swdb recompute-cachegrind` re-read all 32 profiles: only the Kronecker tc profiles changed (see 14).

## Answer

Resolved 2026-09-22.

- `swdb profile --cachegrind yes|auto` builds a `-g` copy and runs
  `valgrind --tool=cachegrind --cache-sim=yes` single-threaded, one trial, under
  `--cachegrind-timeout`; records D1 and LL misses, data refs, and rates with
  `basis: simulated`, kernel-only (functions in `run.kernel_symbols`, including OpenMP
  outlined bodies) and whole-run, with cachegrind's cache configuration in the note
  (LL = host L3, 25165824 B, 12-way).
- A timeout (or exit 0 without output) is a `timed_out`/`failed` part and the profile is
  `complete: false`; never dropped (tested with a fake valgrind on the Mac).
- Real runs: the lab-host test ran on mbit10 (`-g 10`, 150 passed); pilot scale-22 GS
  cachegrind took about 5 minutes.
