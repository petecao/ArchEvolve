# 19 — Upstream BFS: instruction-route acceptance

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-26 (Eastern Time)
**Type:** slice
**Status:** claimed
**Blocked by:** 04, 15
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## What to build

Demonstrate a representative structured-instruction proposal for upstream GAPBS direction-optimizing BFS through the native public workflow on both Kronecker and uniform-random graphs. The worker resolves the specified source regions, applies the supplied optimization intent, and returns independently checked and reprofiled code.

This is the upstream starting implementation × instruction route, covering two graph-family cells and the structured-instruction payload example.

## Scope and specification coverage

Covers AC01, AC06–AC10, AC12–AC14, AC16, AC18, AC20 and contributes evidence toward AC17. Applies D01, D06–D08, and D10–D14.

## Acceptance criteria

- [ ] Retrieve an actionable profile package for upstream direction-optimizing BFS and retain its actual source/build/evaluator context. Do not substitute DX100 top-down source merely because both implementations share one kernel.
- [ ] Submit structured instructions with explicit strategy parameters, target identities, profile-package reference, semantic constraints, and ROI requirements. Label the submission as a representative test client.
- [ ] Apply the instructions to produce real changed CPU-runnable code. Record how rules and preconditions were interpreted, the resulting source/binary identities, diff, supporting edits, and bounded repairs; the structured description is not treated as a proof of legality.
- [ ] Evaluate the candidate and its explicit upstream unaccelerated comparison baseline on both graph families under ticket 15's frozen native protocol, replaying the recorded traversal sources.
- [ ] Retain BFS structural correctness evidence covering the timed code and all timing-claim workloads. Keep protected checks and ROI boundaries intact, including initialization inside the selected BFS-call ROI.
- [ ] Retrieve actual BFS ROI and selected-region timing plus refreshed dynamic memory observations and changed-region associations. Expose unsupported metrics, diagnostic differences, and attribution limits accurately.
- [ ] A fresh public query reconstructs the structured proposal, candidate, native hardware configuration, protocol, comparison, correctness, timing/profiling, and raw evidence.
- [ ] Retain all failures and regressions within declared budgets. If the selected strategy cannot produce a valid complete case, return its evidence without independently selecting another strategy or claiming that fixtures establish native performance.

## Verification and demonstration

Run the complete real structured-instruction → rewrite → native evaluation → reprofiling → retrieval workflow on both graph families. Supplement it with public-behavior tests for wrong-source targeting and unsatisfied preconditions.

## Dependencies and boundaries

Ticket 04 provides structured-instruction rewriting and bounded repairs. Ticket 15 provides the native evaluator, profile packaging, and frozen experiment protocol through its dependency chain. The case does not require tickets 17 or 18 to complete; scheduling must still respect the agreed DX100-first starting order and lab resource limits.

Ticket 20 owns the upstream-source accelerator minimum. A native gain in this case is useful but is not an individual completion condition.

## Implementation progress

2026-09-25: Root owns dependent preparation of the representative proposal and public campaign driver. No candidate performance assessment begins before Ticket 15 freezes compatible protocols. Actual acceptance remains pending; preparation does not satisfy the listed blockers.


## Initial provider result — 2026-09-26 11:13 ET

The explicitly approved `upstream-instructions` source/profile payload was sent through
Claude Code in the bounded three-request socket-0 batch. This request created an unverified candidate.
The [initial batch summary](../observations/provider-initial-summary-20260926.json)
retains the actual outcome; no repair, retry, compile, performance evaluation or
final acceptance followed from this submission. The original annotations and
proposal context remain retained.

The six-file result packet was committed on mbit10 as `5f1b802`, but automatic
approval review rejected its new GitHub packet/branch. Exact approval is pending;
canonical proposal/candidate records have not been imported into this checkout.
See [the concrete inventory](../observations/provider-export-inventory-20260926.json).

## Native launch preparation — 2026-09-27 ET

[Data-only preparation](../operator-recipes/native-acceptance/README.md) now binds
the actual original request, candidate, source/package identities, retained patch
and provider-budget history. All four historical package contexts explicitly use
four threads; the prospective one-thread reassessment preserves that history.
Protocol, fresh-package and host-admission fields remain unset pending T15 and
source-specific qualification/publication. The existing public campaign CLI is
sufficient; no provider, build, measurement, new allowance or acceptance is claimed.
