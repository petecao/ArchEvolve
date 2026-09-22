# 09 — Simulated cache misses (cachegrind)

Created: 2026-09-22
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 07
**Spec:** `../spec.md`

**What to build:** Profiles on mbit10 include first-level and last-level cache misses
simulated by cachegrind, clearly marked as simulated.

- [ ] `swdb profile` runs the implementation single-threaded under cachegrind (`--cache-sim=yes`) with a timeout, and records D1 and LL misses with `basis: simulated` and the simulated cache configuration.
- [ ] A run that times out is recorded as incomplete, never silently dropped.
- [ ] These tests are skipped on the Mac (valgrind does not run on macOS/arm64) and pass on mbit10.

## Comments
