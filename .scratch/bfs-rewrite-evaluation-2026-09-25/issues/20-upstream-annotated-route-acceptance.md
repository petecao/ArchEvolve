# 20 — Upstream BFS: annotated-source route acceptance

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 05, 10, 15
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution hold:** Publishing this ticket does not authorize implementation, builds, installations, benchmark/simulator runs, or remote execution. Wait for explicit user authorization.

## What to build

Demonstrate a representative HW Ensemble submission containing annotated upstream GAPBS direction-optimizing BFS source. Interpret the annotations into an accelerator-using rewrite, then independently check and evaluate the timed candidate on DX100 for both Kronecker and uniform-random graphs.

This is the upstream starting implementation × supplied-code route, covering two graph-family cells, the annotated-source example, and the upstream-source accelerator minimum. The producer is a labeled test client, not Josh's live agent.

## Scope and specification coverage

Covers AC01, AC06–AC11, AC13–AC14, AC16, AC18–AC20 and contributes evidence toward AC17. Applies D01 and D06–D15.

## Acceptance criteria

- [ ] Retrieve the upstream implementation's source/context and workload-specific profile package. Retain its source identity throughout the proposal and result; shared BFS identity must not replace its provenance with the DX100 source.
- [ ] Submit annotated source in a versioned HW-producer proposal, with explicit annotation interpretation, optimization intent, target regions, supported operation/interface requirements, and correctness/ROI constraints.
- [ ] Produce actual executable changes reflecting the annotations, not merely copied comments. Use existing DX100 operations and any recorded generated wrappers/call sequences; preserve the diff, supporting edits, exact candidate/binary identities, and bounded repairs.
- [ ] Evaluate a qualifying accelerator-using candidate on both graph families under ticket 15's frozen protocol. Compare against the explicit appropriate upstream unaccelerated baseline using compatible semantic ROI and declared controlled configurations.
- [ ] On both graph families, retain structural BFS correctness evidence covering the timed code and affirmative accelerator-execution evidence. Include relevant tile/tail and parent-update cases. Calls present in source or scalar fallback alone do not establish acceleration.
- [ ] Retrieve simulated BFS ROI duration, selected-region timing, changed-region/source associations, and refreshed dynamic memory observations with units, model/configuration identity, scope, and attribution limits.
- [ ] A fresh public query reconstructs the input package, annotated submission and interpretation, candidate, hardware/interface/backend pair, protocol, comparison, correctness, and raw timing/profiling evidence.
- [ ] Retain failures, incomplete measurements, and regressions within explicit budgets. If no candidate is correct and actually accelerates on both graph families, leave this acceptance case incomplete and return evidence to the proposal owner.

## Verification and demonstration

Run the actual annotated-source → rewrite → compile → independent correctness → DX100 timing/profile → retrieval workflow on both graph families. Contract fixtures cannot satisfy the timed-binary correctness or accelerator-use requirements.

## Dependencies and boundaries

Ticket 05 provides annotation interpretation through the shared worker; 10 provides operation contracts and capability checks; 15 provides the frozen protocol and verified backend/profile prerequisites.

Only selected BFS phases need use DX100. No new hardware operation, automatic strategy replacement, all-phase acceleration, or individual speedup requirement is introduced.
