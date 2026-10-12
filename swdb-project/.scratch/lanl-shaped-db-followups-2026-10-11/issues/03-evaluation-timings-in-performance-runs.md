# 03 — Measured evaluation timings feed performance_runs

Created: 2026-10-11
**Type:** slice
**Status:** claimed
**Blocked by:** None — can start immediately
**Spec:** `../../lanl-shaped-db-2026-10-09/spec.md` (D4, "What fills each LANL table"); ticket
04 answer there

**What to build:** today only profile `timing[]` entries become `performance_runs`. Evaluations
also record measured native timings (for example ROI timings of a baseline run on a real
machine). Add them to `performance_runs` (and their run configs) when the timing is measured on a
real machine and the thing evaluated is an implementation (same rule as `Validation_results`).
Simulated (gem5) and estimated timings never enter; ADR 0013 (no gem5 results in ArchEvolve mode).

- [ ] A measured native evaluation timing of an implementation appears once in `performance_runs`
- [ ] gem5/simulated, estimated and rewrite-candidate timings never appear
- [ ] Origins, foreign-key, separability and record-field checks stay clean
- [ ] database.md updated
