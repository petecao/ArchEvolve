# 04 — Apply natural-language and structured instructions with bounded repair

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** claimed
**Blocked by:** 03
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## What to build

Extend the public proposal workflow to interpret natural-language and structured rewrite instructions against the identified source, create real candidate edits, and use the existing independent native evaluator. Add a shared bounded build/correctness repair behavior that can also serve the supplied-code route. The ensemble supplies the strategy; the worker may repair an application of that intent but must not start a different strategy search.

## Scope and spec references

This slice contributes AC06–AC09 and AC20 through D06–D08 and D14–D15. Structured instructions are an intent/constraint contract, not a promised general-purpose deterministic rewrite language. Fixture profile packages may drive early tests without waiting for ticket 09. Record provider/producer identities and distinguish representative test clients from unavailable live Peter/Josh integrations.

## Acceptance criteria

- [ ] Both a natural-language proposal and a structured-instruction proposal are accepted through the public interface and interpreted relative to their exact source, target regions, strategy, parameters, and constraints.
- [ ] Each successful interpretation produces actual source changes and a candidate that proceeds through the independent native evaluation path; storing the instruction or merely returning a predetermined success status is insufficient.
- [ ] The result retains the original instructions, interpretation, relevant source context, generated edits, provider/producer provenance, and available correctness/diagnostic observations.
- [ ] Ambiguous or conflicting requirements that cannot be resolved within the supplied evidence produce an explicit unresolved outcome rather than an invented strategy, source mapping, or hardware capability.
- [ ] Attempt and time/resource limits are explicit before execution. Every build/correctness repair records its triggering failure and changes while preserving the supplied strategy and allowed edit scope.
- [ ] The shared repair behavior applies to a supplied-code candidate as well as an instruction-generated candidate; evaluator-owned verifier and ROI inputs remain protected throughout repairs.
- [ ] Exhausted repair budgets and persistent failures return retained evidence. A regressing result, when a valid comparison is available, returns to the ensemble without autonomous performance tuning or strategy substitution.
- [ ] New-process retrieval recovers the proposal, all retained attempts and candidate identities, final outcome, and reasons. Early diagnostic executions make no pre-freeze gain claim.

## Verification

Use public instruction submission, candidate/evaluation execution, and fresh-process result queries. Deterministic external rewrite-provider fixtures may check contract handling, repair bounds, and failure retention, but must not be cited as proof of general natural-language understanding or performance. Include small real BFS source-changing examples for both instruction forms through the configured rewrite path and native correctness evaluator after separate execution authorization; later campaign tickets establish full coverage and gains.

## Dependencies and boundaries

Ticket 03 supplies native evaluation and durable outcomes, including explicit verifier failure. Complete profile generation, DX100 builds, and full performance workloads are not prerequisites. This ticket does not choose strategies, synthesize a new hardware operation, promise success for arbitrary prose, or require live collaborator agents. Annotated-source interpretation is the next slice and reuses this worker behavior.

## Implementation progress

2026-09-25: Provider and repair design is recorded in `docs/bfs-rewrite-worker.md`. Worker preparation proceeds against the stable candidate interface while native evaluation acceptance completes; this ticket cannot resolve before Ticket 03. Root owns the bounded provider/repair integration and instruction/annotation route tests.
