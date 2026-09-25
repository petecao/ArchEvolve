# 17 — DX100 BFS: instruction-route acceptance

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** claimed
**Blocked by:** 04, 10, 15
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## What to build

Demonstrate the full public workflow for a representative SW Ensemble submission in natural language: query the DX100 scalar top-down BFS profile package, apply the specified optimization, and retrieve independently checked results for an accelerator-using candidate on both Kronecker and uniform-random graphs.

This is one starting implementation × proposal route, covering two graph-family cells and the DX100-source accelerator minimum. Use actual source changes, compilation, DX100 execution, and profiling. The producer is a labeled test client, not Peter's live agent.

## Scope and specification coverage

Covers AC06–AC11, AC13–AC14, AC16, AC18–AC20 and contributes evidence toward AC17. Applies D06–D14. A gain is not required in this individual ticket; correct accelerator execution on both graph families is required.

## Acceptance criteria

- [ ] Obtain the exact baseline source/context, ranked regions, and dynamic memory evidence through the public profile-package query. Record the package identity used by the test client.
- [ ] Submit natural-language instructions in the versioned proposal envelope, identifying the strategy, target regions, preserved semantics, ROI, and supported DX100 operation/interface requirements. Preserve test-client and SW-producer provenance.
- [ ] Produce real changed source from that proposal, including any necessary wrappers or supporting edits over existing operations. Record the source snapshot, resulting binary, diff, and bounded repairs; evaluator-owned correctness and ROI surfaces remain protected.
- [ ] Evaluate a qualifying candidate on both graph families under ticket 15's frozen protocol. Replay its actual graph/source workloads and retain the explicit unaccelerated DX100-source comparison baseline and declared target configuration.
- [ ] For both graph families, retain BFS structural correctness evidence covering the timed binary and affirmative evidence that the accelerator path actually executes. Cover relevant full/tail tiles and competing parent updates; scalar fallback alone does not qualify.
- [ ] Retrieve the BFS-level ROI duration, selected-region durations, and refreshed dynamic memory observations with scope, units, source correspondence, and attribution limits. Keep simulated target time and simulator host cost distinct.
- [ ] A fresh public query reconstructs the profile package, proposal, candidate, correctness, hardware/interface identities, protocol, comparator, timing/profiling evidence, and raw-artifact references.
- [ ] Retain every failed attempt and regression. Enforce the declared repair/run budgets and host resource rules. If no candidate meets correctness and actual acceleration on both families, leave this acceptance case incomplete and return evidence to the proposal owner rather than changing strategies autonomously.

## Verification and demonstration

Run the real query → proposal → rewrite → check → DX100 measurement/profile → retrieval sequence. Fast fixtures may check message or failure behavior, but cannot establish acceleration, correctness of the timed BFS binary, dynamic behavior, or performance.

## Dependencies and boundaries

Ticket 04 supplies instruction rewriting and bounded repair; 10 supplies operation contracts and capability checks; 15 supplies the frozen candidate protocol and verified evaluator/profiling prerequisites. Complete profile packages and the simulation backend are inherited through those dependencies.

Do not require every BFS phase to accelerate. Do not require a gain in this case or a win over the authors' accelerated version. No new hardware operation, live collaborator integration, or entire-paper campaign is included.

## Implementation progress

2026-09-25: Root owns dependent preparation of the representative proposal and public campaign driver. No candidate performance assessment begins before Ticket 15 freezes compatible protocols. Actual acceptance remains pending; preparation does not satisfy the listed blockers.
