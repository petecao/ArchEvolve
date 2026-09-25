# 04 — Apply natural-language and structured instructions with bounded repair

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** resolved
**Blocked by:** 03
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## What to build

Extend the public proposal workflow to interpret natural-language and structured rewrite instructions against the identified source, create real candidate edits, and use the existing independent native evaluator. Add a shared bounded build/correctness repair behavior that can also serve the supplied-code route. The ensemble supplies the strategy; the worker may repair an application of that intent but must not start a different strategy search.

## Scope and spec references

This slice contributes AC06–AC09 and AC20 through D06–D08 and D14–D15. Structured instructions are an intent/constraint contract, not a promised general-purpose deterministic rewrite language. Fixture profile packages may drive early tests without waiting for ticket 09. Record provider/producer identities and distinguish representative test clients from unavailable live Peter/Josh integrations.

## Acceptance criteria

- [x] Both a natural-language proposal and a structured-instruction proposal are accepted through the public interface and interpreted relative to their exact source, target regions, strategy, parameters, and constraints.
- [x] Each successful interpretation produces actual source changes and a candidate that proceeds through the independent native evaluation path; storing the instruction or merely returning a predetermined success status is insufficient.
- [x] The result retains the original instructions, interpretation, relevant source context, generated edits, provider/producer provenance, and available correctness/diagnostic observations.
- [x] Ambiguous or conflicting requirements that cannot be resolved within the supplied evidence produce an explicit unresolved outcome rather than an invented strategy, source mapping, or hardware capability.
- [x] Attempt and time/resource limits are explicit before execution. Every build/correctness repair records its triggering failure and changes while preserving the supplied strategy and allowed edit scope.
- [x] The shared repair behavior applies to a supplied-code candidate as well as an instruction-generated candidate; evaluator-owned verifier and ROI inputs remain protected throughout repairs.
- [x] Exhausted repair budgets and persistent failures return retained evidence. A regressing result, when a valid comparison is available, returns to the ensemble without autonomous performance tuning or strategy substitution.
- [x] New-process retrieval recovers the proposal, all retained attempts and candidate identities, final outcome, and reasons. Early diagnostic executions make no pre-freeze gain claim.

## Verification

Use public instruction submission, candidate/evaluation execution, and fresh-process result queries. Deterministic external rewrite-provider fixtures may check contract handling, repair bounds, and failure retention, but must not be cited as proof of general natural-language understanding or performance. Include small real BFS source-changing examples for both instruction forms through the configured rewrite path and native correctness evaluator after separate execution authorization; later campaign tickets establish full coverage and gains.

## Dependencies and boundaries

Ticket 03 supplies native evaluation and durable outcomes, including explicit verifier failure. Complete profile generation, DX100 builds, and full performance workloads are not prerequisites. This ticket does not choose strategies, synthesize a new hardware operation, promise success for arbitrary prose, or require live collaborator agents. Annotated-source interpretation is the next slice and reuses this worker behavior.

## Implementation progress

2026-09-25: Provider and repair design is recorded in `docs/bfs-rewrite-worker.md`. Worker preparation proceeds against the stable candidate interface while native evaluation acceptance completes; this ticket cannot resolve before Ticket 03. Root owns the bounded provider/repair integration and instruction/annotation route tests.

## Answer

2026-09-25: Resolved through the public `submit`, `repair`, `evaluate`, and fresh-process `get --chain` interfaces. The bounded Claude provider retains exact request/source/package context, interpretation, actual diff, provider identity, attempt limits, and failures. Repairs accept only build/correctness failures for the latest candidate, preserve original scope/intent, consume fixed budgets, and cannot tune a valid regression. Unresolved requirements remain explicitly unresolved.

The real natural-language candidate `bfs-instruction-smoke-20260925-a1.natural-language.proposal` passed 3/3 native structural checks. The real structured candidate from `bfs-instruction-smoke-20260925-a1.structured-instructions.proposal` passed 3/3 in `bfs-instruction-smoke-20260925-a2.evaluator-fixed`. Its original trusted-driver include failure and refused out-of-scope repair remain retained; the evaluator correction is a separate revision/evaluation.

Validation: `python3 -m pytest tests/test_bfs_rewrite.py -q` completed with **10 passed** (363.73 s). Contract fixtures cover all payload forms, unresolved intent, annotation protection, provider timeout, supplied-patch repair, immutable repair bounds, rejection of performance tuning, explicit baseline creation, and durable unresolved repair. Real execution metadata arrived through Git commits `29c35f` and `60c78420f3d6e69d9649e3edd6a1f3012eb20588`; raw artifacts stay on mbit10. See `docs/bfs-rewrite-worker.md` and `docs/bfs-handoff.md`. These diagnostic examples use labeled test clients and fixture profile packages; they establish no frozen-workload coverage or gain.
