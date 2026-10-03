# Implementation code review

Created: 2026-10-03 ET

Review base: `9ef348fdaa5b26ff5e37a66d1781084b1b2eea40` on `yanrujhou_main`.
Initial Standards and Spec review covered `ed8c233`; final independent review covered
the corrections committed in `349cf1e`.
The final fixes and evidence are committed in the local correction batch. Both final independent reviews pass.

| Axis | Priority | Finding | Correction and evidence |
|---|---|---|---|
| Standards | P1 | Fixture certification could grant real certification, sharing and submission | State, promotion and review validation require `evidence_kind: execution`. Temporary execution-envelope test doubles are explicitly labeled and isolated. Independent gate replay refuses fixture-only admission. |
| Standards | P2 | An arbitrary reviewer could grant the shared tier | Promotion and current-review checks require Yan-Ru Jhou or the `yanrujhou` alias; persisted promotion uses the canonical name. Independent replay refuses unrelated reviewers. |
| Spec | P1 | Differential certification compiled the canonical driver/header instead of the selected lowering's declared inputs | Compile the pinned lowering, driver and intrinsic reference through explicit include seams; validate the supported input set; honor build definitions; reject matrix overrides; recheck input hashes after execution. 109 focused regressions pass, including broken repinned headers, changed macros, drivers and source stability. All ten durable lowerings pass recertification. Fresh candidate receipt `certification.1e4397e31d594245bc10bd80ff2107f5` passes ten matrix cells and rejects sixteen controls. |
| Spec | P2 | A completed missing witness became inconclusive and a positive run could hide it | Completed required-witness failure derives refuted and fails evaluator correctness/gain eligibility. Incomplete continuation/frontier output remains unverified. Six public evaluator regressions plus existing v2/read-only checks pass: 33 total. Library-state regressions pass: 31 total. |
| Standards | P1 | Repinning intrinsic semantics could promote an unchanged lowering using an old receipt | Certification captures the complete dependency closure before execution, persists every normative hash, and checks those hashes after execution. State, review and promotion require current bindings. Ten new producer/schema regressions pass, including actual compiled changed-reference failure and mid-run mutation abort. All twelve fresh durable receipts and 22 final public submission checks pass; all 3,679 current cases have verified coverage. |
| Standards | P2 | A stale target proposal could reinterpret its result using a changed contract witness | Target state requires the current contract hash and complete contract dependency closure before interpreting its checks. Both changed-witness and changed-dependency regressions pass. Independent replay confirms stale evidence derives draft, while a valid current proposal still grants evaluated_on_target. |

The Standards agent independently rechecked the two admission fixes with the actual
normative library and an isolated in-memory store. The Spec agent independently
reproduced rejection of a broken repinned lowering and altered reference, and found
no further actionable producer/witness issue. Human review, send, cleanup and
real target-run tasks remain separate; fixture checks do not resolve those tasks.

The earlier serial full-suite run was superseded after review fixes: 1,111 passed,
15 skipped, one previously fixed failure, then an intentional interrupt. It is not a
passing full-suite result. The fresh frozen suite contains 3,661 cases in 133 files,
split into three disjoint file partitions with separate temporary directories,
logs and JUnit receipts under `/private/tmp/swdb-typed-library-verification-20261003`.

Full-suite follow-up, 03:37 ET: simulator batch-admission/recovery/T16 setup
errors exposed a synthetic fixture missing `settings.workloads`. The fixture now
explicitly declares its timed workload. All 174 tests in the three affected files
pass in a fresh process; no product-code gate was weakened. Original test groups
continue and their final results will be combined with the complete affected-file
rerun, keeping the superseded setup errors visible in the verification ledger.

Fixture audit, 03:40 ET: the intrinsic SQL test also assumed only three legacy
rows. Its added-scatter assertions are preserved and inventory completeness now
uses the authoritative YAML IDs. The complete affected-file rerun passes 184 cases
in 48.77s. JUnit: `/private/tmp/swdb-typed-library-verification-20261003/affected-fixtures.xml`.
No further stale accelerator inventories or production inventory defect were found.

03:50 ET: partition3 finished with 1,180 passed,10 skipped and 30 setup errors.
JUnit identity matching confirms every error is covered by the fresh passing
affected-file receipt. Two other partitions remain active; no final full-suite
pass is asserted until complete unique-case coverage is checked.

Final Standards closeout, 04:08 ET: no new actionable documented-standard
violation or baseline smell. All 21 current hashes/states and packet receipt
references were independently checked. Human and real-target tasks remain open.

Final Spec closeout, 04:09 ET: no new actionable issue in the local
implementation. The BFS contract binds 18 dependency pins (nine intrinsic/lowering
pairs; ALU is unused). All 21 current entries validate and remain experimental.
Remote tickets 27/28/29/34/36 are unexecuted, ticket 31 is conditional and untriggered,
and the eight human tickets remain open.

Standards: four admission/custody findings corrected and independently confirmed.
Spec: two producer/witness findings corrected and independently confirmed.
No remaining actionable finding on either axis.

Full partition closeout, 04:12 ET: partition1 finished 1,212 passed, three
skipped and six failed; partition2 finished 1,197 passed and 23 skipped; partition3
finished 1,180 passed, ten skipped and30 setup errors. One failure is the already
corrected intrinsic inventory assertion. Five ISA-profile failures come from a
fixture that copies intrinsic records without their operation dependencies; it
now copies the operation folder too. Complete ISA-file rerun is active. Product
validation and ISA rejection semantics remain unchanged.

Final verification, 04:15 ET: all 3,679 current collected cases have exact
receipt coverage: 3,643 pass, 36 skip, zero unresolved failure/error. The frozen
3,661-case suite is combined with 391 unique fresh affected-file cases, including
18 added review regressions. All 36 original fixture failures/errors have fresh
passing case-matched receipts; original logs are preserved. The full ISA file
passes 25 cases; final submit file passes 22; library 35, producer/delivery 120,
gem5 driver 6. All 404 records validate and git diff --check passes. See
[verification.json](verification.json) for hashes, partitions and corrections.

Supplemental runtime review, 2026-10-03 08:37 ET: fixed baseline `8959b4dfd149273e89884be87bee9c0adb60e0fc`, working diff of the collector, region-profile schema, two complete affected test files, and format documentation. Independent Standards and Spec reviewers both report no actionable discrepancy. Collector uses one continuous complete-BFS interval and exactly one final client dump, with only TDStep/outlined-worker self costs retained and whole-call cache history disclosed. Strict summary/self-cost checks, counter hierarchy, raw reparse, source and binary pins remain unchanged. Historical `tdstep_position` and new aggregate `dump_position` require exactly one valid coordinate.

Fresh affected-file verification passed all58 cases twice; durable JUnit records58 passed in32.34s. Current collection reconciles3,687 cases to3,651 pass and36 skip with zero unresolved failure/error, preserving the two retired historical test names and all original failed receipts. Eight new cases cover the runtime correction. All425 current local records validate. Real a1 is partial/failed and preserved; fresh remote a2 is still required before tickets27/34 can close.

Actual evidence audit, 2026-10-03 08:57 ET: independent a2 sealed package, all source manifests, graph/binary/output/raw pins and compatible public context checks pass. Strict raw reparse verifies one client dump,2,138 parsed self-cost rows, exactly31 retained TDStep/worker rows, and exact seven mapped statement costs. Attribution remains bounded/partial and costs simulated; queue append has no attributable debug row. The provider workspace withholds per-line truth, prior claims and evaluator/accelerator material. Actual provider attempt2 guard/audit passes and login copy is deleted, but schema400 exposed unsupported uniqueItems; this runtime issue is being corrected at the Codex transport seam with full local validation retained.

Supplemental provider transport review, 2026-10-03 09:01 ET: fixed baseline `f6972ebbf9c842c1a7091716505577d06c637231`; exact adapter/test diff reviewed independently on Standards and Spec axes. Both pass with no actionable discrepancy. A copied wire schema removes `uniqueItems` only at schema nodes, preserving property/definition names and literal const/enum/default/example data. The normative schema, real local validator, model/effort pins, guard, audit and credential cleanup remain unchanged. Three new focused regressions pass; complete affected-file tests are running before publication and fresh actual annotation.

Provider transport verification, 2026-10-03 09:03 ET: all45 cases in the two affected files pass in344.07s. Complete stdout plus exact45-case list and their hashes are preserved without an artificial JUnit rerun. Current full-suite identity coverage is3,690 cases:3,654 pass,36 skip, zero unresolved. Both independent review axes pass; no actionable code issue remains. Actual provider success still requires a fresh post-sync request.

Actual annotation closeout, 2026-10-03 09:19 ET: independent audit reproduces all seven raw-derived simulated costs, midranks, Spearman0.4925690038994379, top-three2/3 and exactly two cost contradictions. Full source/input/prompt/provider/wire pins, append-only claims and unchanged facts/profile verify. Three actual commands only read declared inputs; no compiler/profiler/evaluator/benchmark run. Metadata6c65bdf is published/read back and all443 records validate.

Supplemental production P2 finding: the two actual completed `candidate_build` records in8506be7 erroneously refute19cited entries because `_target_state` conflated executed compilation with completed target execution. Historical reconstruction confirms all21 shared/certified at8959b4d and19 shared/refuted at8506be7/f642a94 with identical normative pins; annotation changes no state. The correction requires entered simulation/execution history before deriving target status. Actual compilation/discovery/collection/package records cannot affect it; genuine completed required-witness or normal-exit failure still refutes, and incomplete actual runs remain inconclusive. All47 affected cases pass in8.18s, including12newregressions from real public preparation shape. Standards review passes againstf642a94; Spec review and publication are pending.

Final target-state review, 2026-10-03 09:23 ET: both independent Standards and Spec axes pass against fixed f642a94. The extra Spec checkpoint finding is corrected: the trusted guest driver requests checkpoint before ROI/BFS, so checkpoint-only history derives inconclusive after identity checks and cannot grant target qualification or refute its timed witness. The simulation/execution verdict predicates remain strict. Final affected file passes all50 cases in7.95s, including15 new production-shape regressions; original47-case receipt remains byte-identical. Current collection reconciles3,705 identities to3,669 pass/36 skip with zero unresolved. Corrected local actual-record readback restores all21 shared/certified entries without modifying normative entries, dependency pins or reviews. No remaining actionable review finding.

Publication readback, 2026-10-03 09:26 ET: final correction5943c9a is synchronized on mbit10; all443 records validate and the live derived-state query returns all21 shared/certified. Normative entries, dependencies and actual promotion reviews remain unchanged. No target execution is inferred from preparation.

Memory-admission follow-up, 2026-10-03 ET: both independent Standards and Spec axes pass against fixed e74c85b. The selected-node estimate preserves the measured36 GiB budget and16GB/MMIO model. Review findings are corrected: disjoint counters reconcile; complete zone managed totals are required for cache credit; present contradictions refuse before missing-proof fallback; impossible managed/reserve totals refuse even when MemFree suffices. Final affected files pass39 cases in7.47s with22 new adversaries. Reconciled coverage is3,727 identities (3,691 pass/36 skip), zero unresolved. All earlier local receipts are retained. [Admission clarification](evaluation/memory-admission-clarification.md).

Bounded-completion review, 2026-10-03 11:08 ET: both independent Standards and Spec axes pass against fixed `e6dee10dd74dc475eaf783016d1f3ddbf102e7ee`. The actual primary companion exposed a P1 classification defect: strict v2 guest completion passed with a bound zero-status exit witness, while the library incorrectly required a normal simulator exit. Individual v2 executions now use `validate_record_witness`, preserving exact seals, checker/binding identities, protected correctness, present-file verification, retained custody and remote-unverified availability. Detected v2 validation failures cannot fall back to legacy flags. Aggregate wrappers execute no guest; their actual component records independently derive target state. Legacy normal-exit behavior, checkpoint/incomplete handling, required coverage and real correctness/L3 refutation precedence remain intact.

All 200 affected tests pass in 8.57s, including 25 new cases: coherent bounded/normal v2 completion, nineteen malformed or tampered adversaries, and four aggregate cases. The corrected public fixture retains its genuine bounded-completion semantics. Reconciled current coverage is 3,752 identities: 3,716 pass and 36 skip, zero unresolved. No normative entry, dependency pin, protected binary, frozen protocol or model changed. [JUnit receipt](evaluation/bounded-completion-a1-junit-20261003.xml).
