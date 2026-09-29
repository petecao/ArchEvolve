# Documentation archive

Updated: 2026-09-28 (Eastern Time).

These are dated plans, reviews, diagnoses, and historical specifications. Read the
[five-page guide](../README.md) for onboarding and [reference](../reference/README.md)
for detailed interfaces. Dates and outcomes below belong to the retained notes;
they do not describe live host state or authorize a new run. Some notes document
contracts still used by the implementation; archiving does not revoke them.

Content was retained during consolidation, with relative links repaired and a
separate navigation date. Original content dates and outcome statements remain.
The machine-referenced handoff contract, JSON examples, evidence receipts, and
record metadata retain their existing locations and bytes.

## Handoff history

[The full 2026-09-27 handoff](bfs-handoff-20260927.md) preserves the chronological
results, examples, pause, and report snapshots removed from the concise guide.
Use the [current report command](../bfs-handoff.md#final-report-regeneration--2026-09-27)
to assess the records in your checkout.

## Find a relocated document

All former top-level detailed documents are listed here. A filename under
`docs/` in historical prose or a recorded command refers to the corresponding
location below. Repository-root paths inside code blocks retain their original
meaning; Markdown links resolve from each document's new directory.

| Former `docs/` filename | Retained document |
|---|---|
| `adding-a-strategy.md` | [Adding an optimization strategy or an intrinsic](../reference/adding-a-strategy.md) |
| `adding-an-application.md` | [Adding an application and its kernels](../reference/adding-an-application.md) |
| `bfs-a2-interruption-prelaunch-revision-20260926.md` | [A2 interruption fixture prelaunch correction](bfs-a2-interruption-prelaunch-revision-20260926.md) |
| `bfs-a2-linux-fixture-20260926.md` | [A2 Linux fixture route](bfs-a2-linux-fixture-20260926.md) |
| `bfs-artifact-freeze-recipe-20260925.md` | [Author BFS reference and matched-control freeze recipe](bfs-artifact-freeze-recipe-20260925.md) |
| `bfs-branch-consolidation-20260927.md` | [BFS branch consolidation](bfs-branch-consolidation-20260927.md) |
| `bfs-candidate-simulator-next-steps-20260926.md` | [T17/T20 controlled-simulator next steps](bfs-candidate-simulator-next-steps-20260926.md) |
| `bfs-capabilities.md` | [BFS accelerator capability contract](../reference/bfs-capabilities.md) |
| `bfs-coverage.md` | [BFS acceptance coverage query](../reference/bfs-coverage.md) |
| `bfs-dx100-coverage-a2-plan-20260926.md` | [Corrective fixed DX100 coverage attempt a2](bfs-dx100-coverage-a2-plan-20260926.md) |
| `bfs-dx100-coverage-execution-20260926.md` | [One finite DX100 coverage execution](bfs-dx100-coverage-execution-20260926.md) |
| `bfs-dx100-coverage-plan-20260926.md` | [Finite DX100 full/tail/competing-update correctness case](bfs-dx100-coverage-plan-20260926.md) |
| `bfs-dx100-design.md` | [DX100 preflight and execution design](../reference/bfs-dx100-design.md) |
| `bfs-dx100-execution.md` | [DX100 build and smoke execution](../reference/bfs-dx100-execution.md) |
| `bfs-dx100-exit-probe-20260926.md` | [One post-ROI syscall diagnostic](bfs-dx100-exit-probe-20260926.md) |
| `bfs-dx100-gzip-trace-20260926.md` | [Lossless DX100 debug transport](bfs-dx100-gzip-trace-20260926.md) |
| `bfs-dx100-inputs.md` | [DX100 serialized loader inputs](../reference/bfs-dx100-inputs.md) |
| `bfs-dx100-profiling.md` | [DX100 execution-derived profile collection](../reference/bfs-dx100-profiling.md) |
| `bfs-dx100-trial-identity.md` | [Simulator trial identity](../reference/bfs-dx100-trial-identity.md) |
| `bfs-dx100-witness-continuation-20260926.md` | [Proposed fresh DX100 correctness continuation](bfs-dx100-witness-continuation-20260926.md) |
| `bfs-dx100-witness-correction-20260926.md` | [Bounded correction of the author completion parser](bfs-dx100-witness-correction-20260926.md) |
| `bfs-dx100-witness-probe-plan-20260926.md` | [Prospective author v2 completion observation](bfs-dx100-witness-probe-plan-20260926.md) |
| `bfs-dx100-witness-v2.md` | [DX100 v2 completion witness](../reference/bfs-dx100-witness-v2.md) |
| `bfs-handoff.md` | [BFS workflow handoff](bfs-handoff-20260927.md) |
| `bfs-interim-review-20260926.md` | [Interim BFS implementation review](bfs-interim-review-20260926.md) |
| `bfs-linux-fixture-audit-20260926.md` | [Independent Linux fixture proof closure](bfs-linux-fixture-audit-20260926.md) |
| `bfs-linux-supervision-admission-20260926.md` | [Prospective Linux supervision admission](bfs-linux-supervision-admission-20260926.md) |
| `bfs-native-calibration-review-20260925.md` | [BFS baseline variability and fixed-recipe review](bfs-native-calibration-review-20260925.md) |
| `bfs-native-evaluator-design.md` | [Native BFS evaluator design](../reference/bfs-native-evaluator-design.md) |
| `bfs-native-one-thread-pilot-20260926.md` | [Prospective requested-one-thread native A/A calibration](bfs-native-one-thread-pilot-20260926.md) |
| `bfs-native-paired-pilot-20260926.md` | [Prospective native paired A/A pilot](bfs-native-paired-pilot-20260926.md) |
| `bfs-native-paired.md` | [Native paired collection contract](../reference/bfs-native-paired.md) |
| `bfs-native-qualification-continuation-20260926.md` | [Native qualification through required publication steps](bfs-native-qualification-continuation-20260926.md) |
| `bfs-native-readback-correction-20260926.md` | [Corrected native evidence readback](bfs-native-readback-correction-20260926.md) |
| `bfs-native-readback-preflight-20260926.md` | [One bounded native readback: concrete preflight](bfs-native-readback-preflight-20260926.md) |
| `bfs-native-readback-preflight-a2-20260926.md` | [Corrected native readback a2: concrete preflight](bfs-native-readback-preflight-a2-20260926.md) |
| `bfs-native-reassessment-20260926.md` | [Explicit native candidate reassessment](bfs-native-reassessment-20260926.md) |
| `bfs-native-region-comparison.md` | [Native selected-region comparisons](../reference/bfs-native-region-comparison.md) |
| `bfs-native-runtime-20260926.md` | [Native requested runtime inputs](bfs-native-runtime-20260926.md) |
| `bfs-one-thread-freeze-20260926.md` | [Explicit publication from the requested-one-thread calibration](bfs-one-thread-freeze-20260926.md) |
| `bfs-original-graph-oracle-20260926.md` | [Independent original-graph verification](bfs-original-graph-oracle-20260926.md) |
| `bfs-owned-observer-20260926.md` | [Owned process observations for the a3 proof](bfs-owned-observer-20260926.md) |
| `bfs-owned-rss-20260926.md` | [RSS observation across process exit](bfs-owned-rss-20260926.md) |
| `bfs-persistence-cost.md` | [Catalog persistence cost](../reference/bfs-persistence-cost.md) |
| `bfs-pilot-freeze.md` | [Native pilot review and protocol publication](../reference/bfs-pilot-freeze.md) |
| `bfs-post-a2-batch-sequence-20260926.md` | [Post-A2 T15/T16 sequence](bfs-post-a2-batch-sequence-20260926.md) |
| `bfs-post-roi-termination-diagnosis.md` | [BFS post-ROI termination diagnosis](bfs-post-roi-termination-diagnosis.md) |
| `bfs-process-exit-and-lease-closure-repair-20260926.md` | [Process-exit and historical lease-closure repair](bfs-process-exit-and-lease-closure-repair-20260926.md) |
| `bfs-profile-packages.md` | [BFS profile packages and strategy lookup](../reference/bfs-profile-packages.md) |
| `bfs-profiling.md` | [Automatic BFS diagnostics](../reference/bfs-profiling.md) |
| `bfs-protocol.md` | [BFS workloads and frozen comparisons](../reference/bfs-protocol.md) |
| `bfs-readiness-review-20260926.md` | [BFS implementation readiness review](bfs-readiness-review-20260926.md) |
| `bfs-remaining-evidence-gaps-20260926.md` | [Remaining BFS evidence gaps](bfs-remaining-evidence-gaps-20260926.md) |
| `bfs-remaining-simulation-sequence-20260926.md` | [Remaining BFS simulator calibration and reference sequence](bfs-remaining-simulation-sequence-20260926.md) |
| `bfs-rewrite-worker.md` | [BFS rewrite worker contract](../reference/bfs-rewrite-worker.md) |
| `bfs-roi-seal-bound-20260927.md` | [DX100 ROI seal size consistency](bfs-roi-seal-bound-20260927.md) |
| `bfs-scalar-v2-builds-20260926.md` | [Four unchanged scalar v2 builds](bfs-scalar-v2-builds-20260926.md) |
| `bfs-simulator-batches-20260926.md` | [Bounded simulator series for T15 and T16](bfs-simulator-batches-20260926.md) |
| `bfs-simulator-calibration-next-20260926.md` | [Finite DX100 correctness and simulator calibration sequence](bfs-simulator-calibration-next-20260926.md) |
| `bfs-simulator-primary-reuse-20260926.md` | [Retained primary build in a frozen simulator series](bfs-simulator-primary-reuse-20260926.md) |
| `bfs-simulator-series.md` | [Bounded simulator sample grids](../reference/bfs-simulator-series.md) |
| `bfs-source-identity.md` | [Source contexts and comparisons](../reference/bfs-source-identity.md) |
| `bfs-storage-transient-entries-20260926.md` | [Transient retained-file accounting correction](bfs-storage-transient-entries-20260926.md) |
| `bfs-supervision-recovery-20260926.md` | [Fixed supervision recovery](bfs-supervision-recovery-20260926.md) |
| `bfs-t15-correction-proofgroup-20260926.md` | [T15 corrective Linux proof group — 2026-09-26 ET](bfs-t15-correction-proofgroup-20260926.md) |
| `bfs-t15-gzip-correction-20260926.md` | [T15 lossless-transport correction](bfs-t15-gzip-correction-20260926.md) |
| `bfs-t15-setup-recovery-20260926.md` | [T15 setup-failure recovery](bfs-t15-setup-recovery-20260926.md) |
| `bfs-t16-freeze-preflight-20260926.md` | [T16 public freeze and comparison preflight](bfs-t16-freeze-preflight-20260926.md) |
| `bfs-t16-instrumentation-preparation-20260927.md` | [T16 instrumentation preparation diagnosis](bfs-t16-instrumentation-preparation-20260927.md) |
| `bfs-t17-controlled-simulator-readiness-20260926.md` | [T17 controlled-simulator freeze and execution readiness](bfs-t17-controlled-simulator-readiness-20260926.md) |
| `bfs-t17-diagnostic-build-20260926.md` | [One retained-candidate diagnostic build](bfs-t17-diagnostic-build-20260926.md) |
| `bfs-witness-launch-20260926.md` | [Fixed a3 driver and observer launcher](bfs-witness-launch-20260926.md) |
| `database.md` | [The SQLite database](../reference/database.md) |
| `format-proposal-v0.1.md` | [SW Database: Record Format Proposal](format-proposal-v0.1.md) |
| `format-v0.2.md` | [SW Database record format, version 0.2](format-v0.2.md) |
| `format-v0.3.md` | [SW Database record format, version 0.3](../reference/format-v0.3.md) |
| `format-v0.4.md` | [Workflow record format 0.4](../reference/format-v0.4.md) |
| `mbit10-profiling.md` | [Profiling on mbit10](../reference/mbit10-profiling.md) |
