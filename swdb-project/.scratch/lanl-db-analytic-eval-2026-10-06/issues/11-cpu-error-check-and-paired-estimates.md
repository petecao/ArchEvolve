# 11 — CPU error check and paired estimates in ArchEvolve mode

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 05, 06, 07
**Spec:** `../spec.md`
**Time estimate:** 4–6 h

**What to build:** The BFS and BC baselines and candidates that already have ArchEvolve-mode native timings get estimates, giving the CPU error band per kernel and workload class (D14, D28). From then on, every ArchEvolve-mode CPU evaluation records a paired estimate beside its timing; the timing still decides (D27).

## Acceptance

- [ ] Only ArchEvolve-mode timings are used, never Extensa's.
- [ ] The band is written where verdicts read it.
- [ ] Large errors get a per-region explanation.
- [ ] CPU evaluation output is unchanged apart from the added estimate.
