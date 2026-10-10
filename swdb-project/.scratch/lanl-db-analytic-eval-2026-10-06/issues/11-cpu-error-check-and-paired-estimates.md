# 11 — CPU error check and paired estimates in ArchEvolve mode

Created: 2026-10-06
**Type:** slice
**Status:** resolved
**Blocked by:** 05, 06, 07
**Spec:** `../spec.md`
**Time estimate:** 4–6 h

**What to build:** The BFS and BC baselines and candidates that already have ArchEvolve-mode native timings get estimates, giving the CPU error band per kernel and workload class (D14, D28). From then on, every ArchEvolve-mode CPU evaluation records a paired estimate beside its timing; the timing still decides (D27).

## Acceptance

- [x] Only ArchEvolve-mode timings are used, never Extensa's.
- [x] The band is written where verdicts read it.
- [x] Large errors get a per-region explanation.
- [x] CPU evaluation output is unchanged apart from the added estimate.


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

2026-10-07 07:14 ET report administrative startup custody: original a3 generation 508
failed before Store or report publication because the standalone runner lacked
hashlib. The reviewed import-only repair and fresh raw attempt a4, portable
RED→GREEN checks, actual failure/staging custody and original unsealed dispatch
stream are preserved in `evidence/11-report-startup-recovery-controls-20261007-a4/`.
Logical canonical study IDs remain a3; source C/F6, forecasts, regional costs and
BFS/BC widths are unchanged. Retry acceptance and the public verdict reader are
pending. BC remains failed and unvalidated. Status remains claimed.

## Answer

Resolved: 2026-10-07 09:56 ET. The CPU service and error-band path, protected CPU paired-estimate adapter and actual native validation/report study are complete. The scientific result is a broad BFS pass and an observed BC failure; resolution does not claim accurate prediction or general CPU agreement.

| Kernel / g17 T1 | Frozen forecast s | Native median s | Forecast/native | Frozen log width | Held-out/report validation |
|---|---:|---:|---:|---:|---|
| BFS | 0.14771765534735024 | 0.00274 | 53.91155304647819× | 4.015855135911417 | validated within a 55.4707101× envelope |
| BC | 1.154672610067664 | 0.0294 | 39.274578573730075× | 3.5172348723064677 | failed, validated=false; 33.6911392× envelope unchanged |

Only native ArchEvolve-mode validation evidence is admitted. Separate LLVM22/libomp original-driver g16 development and g17 held-out pairs use the exact deterministic source policy, graph/input arguments, T1 scope, five advancing calls and independent correctness process. Model/calibration identities and both per-kernel development widths were frozen before either held-out native outcome. No Extensa timing enters this CPU band. Historical [8 native profiles and 51 evaluations/candidates](../evidence/11-historical-native-scope-audit.md) retain explicit runtime/source/process/ROI exclusions and null numeric comparisons rather than being relabeled as matched pairs.

The fresh verdict-reading protocols pin each held-out band and its immutable dependencies. The actual reports preserve seconds and the complete per-region cost values, along with the original widths and BC's exact `empirical_holdout_outside_frozen_width` reason. Both public verdict tokens are `within_error`; BFS's `validated=true` and BC's `validated=false` remain separately visible. One pair per development/held-out phase and five shared-process calls per pair do not establish a confidence interval, point accuracy or transfer to other implementations, kernels, threads, targets or evaluator ROIs.

Large errors have reproducible [g16](../evidence/11-development-admission-20261007-a3/README.md) and [g17](../evidence/11-holdout-admission-20261007-a3/README.md) forecast-only per-region explanations. The inferred serial memory scenario dominates more than 99.98% of both g17 forecasts; BFS BUStep/bu-vertex and InitParent/init-parent, and BC pbfs-edge/back-edge, account for the leading terms. Exclusive region maxima plus additive overheads reconcile each selected whole-median forecast trial. This does not assign observed error to regions, establish physical residency or count optimized hardware memory issues. No rates, costs, recipes or widths were tuned after application outcomes.

The prospective protected CPU adapter binds the canonical graph, source slot, fresh-process policy, compiler/runtime and protected semantic whole-kernel ROI before timing. A correctly matched persisted estimate is carried beside the native timing; native timing still decides. The positive public fixture transports `kernel_seconds=7.92e-05`; unsupported costs, scope mismatches and ambiguous selection remain explicit. Timer-boundary uncertainty leaves elapsed prediction/confidence null, and the original-driver band is not transferred. The output remains unchanged apart from the paired estimate. Public RED→GREEN and adjacent gates, including immutable archive validation and non-Linux unknown runtime handling, are retained in the [final source proof](../evidence/11-final-source-validation-proof-20261007.json); no native accuracy is inferred from fixtures.

Implementation/reference: [CPU native errors and pairing](../../../docs/reference/cpu-native-error.md), [independent service calibration](../../../docs/reference/cpu-service-calibration.md), [model/band runbook](../evidence/11-native-model-band-runbook.md). Frozen source C `f893fed400347ed23d92e917d8bde21b75e5375d`, estimator F6 `f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3` and all prior source/count/calibration records remain intact.

Actual evidence: [model receipt](../evidence/11-cpu-model-mbit10-20261006-a3.json), [development receipt](../evidence/11-cpu-development-mbit10-20261006-a3.json), [held-out receipt](../evidence/11-cpu-holdout-mbit10-20261006-a3.json), [report receipt](../evidence/11-cpu-band-report-mbit10-20261006-a3.json) and [accepted report admission/custody](../evidence/11-report-admission-closeout-20261007-a4/README.md). The actual report retry/raw is a4 while immutable logical IDs remain a3. Original startup failures, processing-cap custody, controls and unexecuted preparation labels stay unchanged. The actual report public validation passed 684 records; delivered integration has 686 including separate PR records. Parent independently accepted local admission `ab5c80d246fe8c7419a48b82eafb395c37e850c11c10fbd509de545fa62ae578`; report export `8969d567599cb9f0d071f77936ab283fcb97c137`. Cleanup removed only its consumed export checkout and retained raw/source/Git. No Store/full validation, tests, native/provider runs or SSH were repeated for this closeout.

## Code review 2026-10-09

2026-10-09 23:10 ET. The resolution and the recorded results (BFS validated at about
55×, BC failed) stand. The four band records and all evidence are unchanged. The
review corrected the code and the wording below.

- **Wording correction: "every ArchEvolve-mode CPU evaluation records a paired
  estimate".** This holds only when a matched estimate was saved beforehand for every
  source slot (`characterize --adapter registered-cpu --evaluation-request`, then
  `estimate`, both before `evaluate`). Neither `evaluate` nor a campaign produces the
  estimate. Without one, the evaluation records `paired_estimate.state: unavailable`
  with null seconds, and native timing decides as before. Wiring characterize and
  estimate into the evaluator was not done: it would add an instrumented run per slot
  to every evaluation's budget.
- **Which description the bands measure.** All four bands pin
  `mbit10.cpu.lanl20261006.t1.services.v1`. Its `memory_service_scenario` replaced
  ticket 07's measured stream, latency and cache mechanisms, and its basis is
  `inferred`. That scenario charges every logical read the cost of a serial dependent
  load over 8 MiB, which makes up more than 99.98% of each forecast. The BFS envelope
  therefore does not validate the measured ticket 07 values.
- **Held-out inputs must be unseen (fixed).** The collector and
  `validate-cpu-error-band` now refuse an input already timed for the same
  implementation and thread count (missing reason `unobserved_heldout_input`).
  Before this, BC g17 could have been reused as "held-out" for a retuned model, or a
  held-out input timed again until it passed. Only `cpu_native_validation` records are
  checked.
- **D25 is now tested (fixed).** The gain/no-gain branches could not run on any fixture.
  The rule is now `three_state`; reported held-out fixture bands show
  `error_band.fixture_verdict` on both sides of the band, and the public verdict stays
  `within_error`.
- **Large errors (fixed for new bands).** Format v2 bands add `large_errors`, which
  ranks the predicted regions for each error above `log 1.25`. It is forecast-only and
  `validate` recomputes it. The existing v1 bands keep their README explanations.
- **Smaller fixes.** Extensa-mode evaluations no longer add the `analytic_pairing` stage
  or evaluator scope. Archived `unavailable`/`excluded` paired estimates must carry no
  prediction. The unused `known` state was removed from the evaluation schema. There
  are now tests for the ArchEvolve-only refusals.

Open question for Yan-Ru: should a held-out input also count as "seen" when an older
native profile or evaluation of the same implementation and graph exists? Examples
are the historical GCC/libgomp profiles. The guard ignores them today; counting them
would require re-checking the existing bands.

Details: [cpu-native-error.md, code-review section](../../../docs/reference/cpu-native-error.md).
