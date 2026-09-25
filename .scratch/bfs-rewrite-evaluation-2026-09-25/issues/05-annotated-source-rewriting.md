# 05 — Interpret annotated source as an executable rewrite proposal

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** claimed
**Blocked by:** 04
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## What to build

Accept annotated BFS source as a supplied-code proposal, interpret the stated changes in their source context, and use the shared worker and evaluator to produce and check a changed candidate. Preserve both the annotations and the interpretation that led to the edits. Merely retaining comments, copying an annotated file unchanged, or relabeling an existing patch does not demonstrate this route.

## Scope and spec references

This slice contributes AC06–AC09 and AC20 through D06–D08 and D14–D15. It completes the annotated-source form alongside the patch and instruction forms. The same source identity, edit protections, bounded repairs, and durable outcomes apply regardless of whether a representative SW or HW producer submitted the source.

## Acceptance criteria

- [ ] Public submission accepts an annotated-source payload with exact source and profile-package references, producer provenance, selected intent, and evaluation constraints.
- [ ] A representative annotation that requires code modification is interpreted and produces a real changed candidate; unchanged comments or an unmodified source copy cannot satisfy successful rewriting.
- [ ] The result preserves the submitted annotated artifact, affected source locations, the worker's interpretation, supporting edits, and the final diff.
- [ ] Stale source, conflicting annotations, or requirements that remain uninterpretable produce explicit retained non-success outcomes instead of a guessed mapping.
- [ ] Annotation requests to change protected verifier or ROI inputs, or to assume unresolved hardware support, cannot bypass the protections used by the other proposal routes.
- [ ] The candidate uses the shared bounded build/correctness repair behavior and independent native evaluator; repairs remain attributable to the supplied intent.
- [ ] Successful and failed annotation-driven attempts are retrievable in a new process with their candidate and evidence when present, without representing fixture clients as live collaborator integration.

## Verification

Drive annotated-source submission through the public workflow and retrieve the result separately. Include an actual small BFS rewrite whose annotations describe a change not already present in the submitted code, then execute its native correctness path after authorization. Use deterministic provider fixtures for malformed/conflicting annotations and repair-limit tests, with their evidence limits explicit. Full accelerator and graph-family coverage is assigned to later acceptance runs.

## Dependencies and boundaries

Ticket 04 supplies instruction interpretation and shared repair; the patch, candidate, and native evaluation paths are inherited through it. Labeled fixture profile packages remain sufficient to exercise this route before ticket 09. Do not introduce a separate strategy-selection worker, require live Peter/Josh agents, or treat this slice as authorization for the later campaign.

## Implementation progress

2026-09-25: Root is preparing the annotated-source interface and tests against the shared bounded worker while Ticket 04 acceptance runs. This is dependent preparation; resolution requires Tickets 03 and 04 and real source-changing evaluation.
