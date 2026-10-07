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

2026-10-07 ET: Implementation remains claimed pending actual model/development/held-out
and verdict-reader receipts. All nine independent native calibrations and four
outcome-free BF/BC characterizations are retained. The prospective freeze uses
separate BFS and BC development/held-out bands with unchanged rounding-aware rules.
The protected CPU evaluator now has an exact canonical graph/source-slot count
adapter and pre-timing persisted-estimate admission. A public hypothetical-cost
fixture carries positive semantic kernel seconds; steady_clock boundary confidence
and original-driver band transfer remain unknown. Archived annotation pins,
source-slot mismatch, ambiguous selection and withheld-cost public guards are
being finalized before immutable source handoff. Parent owns all remote dispatch.

2026-10-07 01:00 ET final source handoff: protected positive/mismatch/unknown/archived
public gate passed (1 case, 491.36 s); strict legacy and prior paired behavior
passed (6 cases, 370.51 s); runtime unknown-envelope controls passed (3 cases).
Final catalogue validates all 665 records; all 905 parent protected blobs remain
byte-identical. A final-source public freeze/estimate/module pairing replay
carries fixture semantic kernel_seconds=7.92e-05 with elapsed seconds and band
null. This is transport evidence only. Evidence:
`evidence/11-final-source-validation-proof-20261007.json` and linked public proofs.
Status remains claimed until actual model, development, held-out and report phases.

2026-10-07 05:23 ET actual development admission: the accepted native g16 T1
export preserves five LLVM/libomp original-driver trials and separate correctness
per kernel. The unchanged selected-record reader passed once; source C/F6 remains
frozen. BFS median 0.00153 s versus forecast 0.08459283293734217 s gives frozen
rounding-aware log width 4.015855135911417; BC median 0.01923 s versus forecast
0.64771215194357 s gives width 3.5172348723064677. These broad development
envelopes are not validated accuracy; each kernel has one workload pair, and
its five advancing calls are not independent error observations. Both widths are
frozen before any g17 outcome. Exact admission and reader custody are in
`evidence/11-development-admission-20261007-a3/`. Ticket remains claimed pending
actual held-out validation and fresh verdict-reading report; parent owns dispatch.

2026-10-07 06:57 ET actual held-out admission: the unchanged selected-record
reader passed once against the accepted g17 native export. BFS prediction
0.14771765534735024 s versus native median 0.00274 s is inside its broad
55.4707101-fold development envelope. BC prediction 1.154672610067664 s versus
median 0.0294 s is outside its frozen 33.6911392-fold envelope; BC remains failed
and unvalidated with width 3.5172348723064677 unchanged. Both development widths
were frozen before either held-out native timing. Exact admission, reproducible
forecast-only per-region diagnostics and unsealed cleanup custody are in
`evidence/11-holdout-admission-20261007-a3/`; g16 history is retained. No rates,
recipes or costs are retuned. Fixed inferred serial memory terms dominate more
than 99.98% of each forecast; this is not measured regional error attribution.
Each kernel has one development pair and one held-out pair, not five independent
error observations. Ticket remains claimed pending the public report reader,
which must preserve failed BC confidence and unchanged forecast costs.
