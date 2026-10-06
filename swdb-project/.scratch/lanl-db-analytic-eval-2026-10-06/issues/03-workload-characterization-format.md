# 03 — Workload characterization format v1 and `swdb characterize` from existing records

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 02
**Spec:** `../spec.md`
**Time estimate:** 3–4 h

**What to build:** Define `swdb.workload-characterization.v1` (D11) and a command that builds it from an implementation's access patterns, loops and formulas, evaluated on one input, with empty slots for static and dynamic counts.

## Acceptance

- [ ] JSON schema checked in; one characterization per (implementation, input).
- [ ] Per region: access patterns (address shape, element bytes, element-count formula and value), operation counts, dynamic counts, accelerator calls; unknown stays null.
- [ ] Regions are the function and loop regions SWDB already uses in profile packages and the site finder, with the same IDs (D33).
- [ ] Built for `gapbs-bfs-do` and `dx100-bfs-scalar` on the class graphs.
- [ ] Field names match Peter's feature reports where they overlap, and a reader imports his reports (`examples/received/*.features.v1.2.yaml` at the ArchEvolve root) as one input source (D20).
- [ ] The format is documented for outside readers (adoptable prototype, D7).
