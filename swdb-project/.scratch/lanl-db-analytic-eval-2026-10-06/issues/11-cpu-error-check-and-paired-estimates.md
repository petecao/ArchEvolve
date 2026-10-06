# 11 — CPU error check and paired estimates in ArchEvolve mode

Created: 2026-10-06
**Type:** slice
**Status:** claimed
**Blocked by:** 05, 06, 07
**Spec:** `../spec.md`
**Time estimate:** 4–6 h

**What to build:** The BFS and BC baselines and candidates that already have ArchEvolve-mode native timings get estimates, giving the CPU error band per kernel and workload class (D14, D28). From then on, every ArchEvolve-mode CPU evaluation records a paired estimate beside its timing; the timing still decides (D27).

## Acceptance

- [ ] Only ArchEvolve-mode timings are used, never Extensa's.
- [ ] The band is written where verdicts read it.
- [ ] Large errors get a per-region explanation.
- [ ] CPU evaluation output is unchanged apart from the added estimate.


## Comments

2026-10-06 ET: Claimed on `codex/lanl-ticket11`, based exactly on integration
`8e2156a4e1f1bd9da46f2510393901e4e4ca2a65`; tickets05/06/07 resolved. Approved
public seams are native-service calibration/import, `characterize`, `estimate`,
`freeze-protocol` and `validate`, plus the existing CPU evaluator output. One public
RED→GREEN slice at a time. Parent owns all mbit10 dispatch and source synchronization.

Scope choice before application error observations: complete supported T1 BFS/BC
first; fresh uninstrumented LLVM22/libomp g16 development timings, then fresh g17
held-out pairs after model/calibration/development-width freeze. Historical
ArchEvolve native baselines/candidate artifacts retain honest estimates/exclusion
reports; GCC/libgomp, source or ROI mismatches stay explicit. No Extensa timing is
admitted. Missing costs, shapes, lifetime facts and execution scope remain unknown.

09 owns shared observation/schema/composition changes.11 owns separate generic CPU
service/calibration/band modules, typed schemas and optional protocol-band binding.
Shared API agreement is `/private/tmp/lanl-09-11-shared-interface-20261006.md`;
plans are `/private/tmp/lanl-ticket11-readonly-plan-20261006.md` and
`/private/tmp/lanl-ticket11-t1-completeness-appendix-20261006.md`. Actual dependent
counter/calibration jobs wait for the integrated09 foundation and stable plugin.
