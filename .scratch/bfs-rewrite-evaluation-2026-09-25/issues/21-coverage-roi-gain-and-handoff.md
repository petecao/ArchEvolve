# 21 — Coverage, ROI gain, and collaborator handoff

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 16, 17, 18, 19, 20
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution hold:** Publishing this ticket does not authorize implementation, builds, installations, benchmark/simulator runs, or remote execution. Wait for explicit user authorization.

## What to build

Provide public retrieval of the complete BFS acceptance report and a collaborator handoff containing the versioned profile-package, rewrite-proposal, and evaluation-result contracts with realistic linked examples.

The report accounts for every required source/route/graph cell, native and simulated evidence, author-reference and controlled comparisons, both source-specific accelerator minima, and the overall requirement for at least one correct ROI gain. It preserves partial, failed, and regressing outcomes.

## Scope and specification coverage

Integrates AC01–AC20, with primary ownership of AC17, AC18, and AC20. Applies D01–D15. This is an evidence-backed completion query and handoff, not a new optimization campaign or permission to alter the accepted requirements.

## Acceptance criteria

- [ ] A public query produces all eight starting-implementation × proposal-route × graph-family cells with their actual proposal, candidate, evaluation, protocol, comparator, and raw-evidence identities. Unmet cells are visible rather than omitted.
- [ ] The report separately accounts for real native cases, the DX100-source and upstream-source accelerated candidates on both graph families, the artifact reference pair, and controlled comparisons. Reuse evidence only when its identities and obligations match.
- [ ] Correctness, accelerator execution, BFS ROI duration, selected-region duration, and dynamic memory profiling have separately assessable evidence. Reject fixture-only, functional-only, missing, incompatible, or incorrectly attributed evidence as satisfaction of the corresponding real acceptance obligation.
- [ ] Demonstrate at least one correct candidate gain against its explicit appropriate unaccelerated baseline under the frozen profitability policy. The qualifying result identifies the software/hardware changes and does not imply an isolated software gain when hardware also changed.
- [ ] Retain every attempted case's failures, incomplete measurements, and regressions, including cases from an earlier protocol that no longer satisfy the current comparison. Missing values are not neutral speedups; native and simulated times are not divided.
- [ ] A fresh process can reconstruct the report from persisted master metadata and regenerated query data, with external artifact availability or missing references stated explicitly. No worker process must remain alive to explain the result.
- [ ] Deliver versioned handoff contracts and linked examples covering natural language, structured instructions, annotated source, and patches, with both SW/HW test-client roles. State that live Peter/Josh integration has not occurred; document the model/interface/backend extension points for later co-design.
- [ ] Record the final acceptance status against AC01–AC20. If the required gain or any other obligation is absent, report incomplete acceptance and leave this ticket unresolved; return evidence to the proposal owner instead of launching an unbounded strategy search or inventing a successful result.

## Verification and demonstration

Exercise the public coverage/result query in a fresh process against the actual evidence from tickets 16–20. Use fixture-based negative checks to prove that incomplete or incompatible evidence cannot be counted, alongside inspection of the real linked artifacts.

## Dependencies and boundaries

Ticket 16 supplies actual artifact/control comparisons. Tickets 17–20 supply the four source/route batches, each on both graph families, with all four payload forms. Their dependency chains supply the shared workflow and profiling capabilities.

This ticket reports and checks existing evidence. If another bounded proposal or rerun is needed, identify that need for the owner; it is not automatic authority for the reporter to choose a different strategy. Neither all-cell gains nor a win over the authors' accelerated implementation is required.
