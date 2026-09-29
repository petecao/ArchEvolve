# T15 freeze dependency audit

Navigation updated: 2026-09-28 (Eastern Time).

Created: 2026-09-27 ET. Read-only spec, fixed-plan, and implementation audit. No dispatch, trace replay, runtime change, or budget extension.

## Finding

The current T15 attempt cannot admit its second complete series under its original deadline. Partial pilot evidence does not satisfy the existing freeze or native acceptance gates. This is an admission arithmetic conclusion, not an extrapolated execution-time estimate.

The fixed lease-recovery plan retains the 2026-09-27 09:14:09.851819 ET hard end. Each new series requires 21,600 seconds plus 30 seconds of cleanup; its latest possible start was 03:13:39.851819 ET. At the preserved 03:15:59.669928 ET observation only the first uniform18 series had started, with no accepted sample yet. Remaining time was 21,490.181891 seconds, less than 21,630. The plan contains two graph-family series, each three sources and two repetitions: twelve primary/diagnostic pairs, not four series.

The driver enforces the entire next-series allowance in [bfs_simulator_batch.py:516](../../../scripts/bfs_simulator_batch.py#L516), and repeats that admission for every series at [line 893](../../../scripts/bfs_simulator_batch.py#L893). A currently admitted series may continue within its own existing allowance; this audit does not terminate it or claim its final outcome.

## Why partial evidence cannot publish the existing freeze

- [Spec D13:256](../spec.md#L256) requires both graph families, baseline/reference cost and coverage evidence, and actual accelerator execution. [Lines 260–264](../spec.md#L260) distinguish traversal-source coverage from replay, require freezing before candidate assessment, and prohibit using calibration to waive accepted coverage cells.
- [Ticket 15 acceptance:357–374](../issues/15-baseline-pilot-and-protocol-freeze.md#L357) preserves budget-expiry incompleteness, both families, actual coverage and replay evidence. Line 370 explicitly keeps the gate unresolved if the bounded pilot cannot establish settings. T16 is an independent protocol route, not a substitute for this gate.
- Native preparation requires two distinct native packages covering both families at [bfs_freeze_pilot.py:348](../../../scripts/bfs_freeze_pilot.py#L348).
- Its accelerator gate requires actual distinct unchanged author-reference simulator executions at [line 628](../../../scripts/bfs_freeze_pilot.py#L628), exact source/replay cells and verified positive simulated ROI at [line 635](../../../scripts/bfs_freeze_pilot.py#L635), and observed accelerator execution at [line 645](../../../scripts/bfs_freeze_pilot.py#L645).
- [Lines 665–686](../../../scripts/bfs_freeze_pilot.py#L665) require six actual executions per workload, two identical configured replays for each of three sources, repeatability within the fixed ceiling, and full-tile, tail-tile, and competing-parent coverage. Supporting diagnostics at line 651 can supplement coverage cases; they do not replace missing timing cells or graph families.
- Publication refuses unmet gates at [bfs_freeze_pilot.py:720](../../../scripts/bfs_freeze_pilot.py#L720).
- The [native qualification continuation:11–15](../../../docs/archive/bfs-native-qualification-continuation-20260926.md#L13) requires actual T15 simulator packages before the separately bounded source-specific native prepare/publish operations. Each still invokes the original pinned qualification reader; neither cached qualification nor a third standalone readback is authorized by that continuation.

Thus a partial uniform run, existing ROI seal, diagnostic fixture, old tiny witness, or T16 artifact workload cannot establish current T15 completion or T18/T19 native acceptance. Changing the source grid, admitting a series after its fixed gate, or extending the deadline needs a new empirical plan; it is not a parser implementation choice.

## Work that remains independent

Preserve T15 actual outputs and terminal ownership/accounting, including partial results and failures. T16 retains its separate frozen-protocol and deadline requirements. T17 and T20 may proceed only within their existing source-specific admission and resource bounds. Bounded source repairs, local semantic regression checks, independent Standards/Spec reviews, and evidence-backed ticket/map synchronization remain useful without claiming empirical acceptance.

The narrow trace-parser optimization is independent implementation work. Its review must preserve complete stream consumption, compressed and decoded hashes, line numbers, deadline checks, and correctness output, including malformed inputs. A speedup on a synthetic fixture is not actual-trace performance evidence, and an old seal is not replacement correctness evidence.

## Preserved observations

Local read-only receipts: `/private/tmp/bfs-t15-progress-analysis-20260927.json`, `/private/tmp/bfs-t15-primary-stage-analysis-20260927.json`, `/private/tmp/bfs-t15-trace-metadata-analysis-20260927.json`, and `/private/tmp/bfs-t15-budget-and-trace-analysis-summary-20260927.json`. These timestamps describe observations, not current live state. The primary simulator reported exit zero at 03:16:43.614740 ET; overall public collection had not completed at the observation. No actual gzip trace was reread for this audit.
