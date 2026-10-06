# 05 — Indirect accesses and the BFS baseline on the CPU

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 04
**Spec:** `../spec.md`
**Time estimate:** 1.5–2 days

**What to build:** The pass classifies `single_valued_indirect` and `ranged_indirect` accesses (and `pointer_chase` or `data_dependent_merge` where it can, otherwise `unknown`); the counted run records executions and footprint per access; characterization regions are the existing profile-package and site-finder region IDs, including loops the compiler outlines for OpenMP (D33); the requests-in-flight (latency) and cache-fit mechanism models exist. The BFS and BC baselines get estimates on a small Kronecker graph, covering what their paired timing covers (D16).

## Acceptance

- [ ] Classifications are compared with the 13 hand-written access patterns of `gapbs-bfs-do` and the BC implementation records; every mismatch is listed with a reason.
- [ ] One fixture kernel per indirect address shape, with hand-computed answers.
- [ ] Loops that map to no region are listed, never dropped.
- [ ] Estimates for `gapbs-bfs-do` and the BC baseline, each with a per-region report.
