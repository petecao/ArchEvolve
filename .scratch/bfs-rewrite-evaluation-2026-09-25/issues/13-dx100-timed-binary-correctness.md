# 13 — DX100 timed-binary correctness

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** claimed
**Blocked by:** 12
**Spec:** `../spec.md`

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## What to build

Attach an explicit BFS correctness outcome to the exact binary and execution whose simulated ROI is retained. Preserve the sealed timing boundary while checking the produced BFS result, including a real accelerated path. Make verifier failure visible even when the guest or simulator exits successfully.

## Scope and spec references

Implements D08, D10, D14 and AC09–AC11. The inspected DX100 BFS path reaches a simulation exit before its enclosing verifier. Continuing that same simulation after sealing the ROI is one approach to evaluate, not a mandated design. The obligation is correctness evidence for the timed code/workload with verification excluded from the declared performance ROI.

## Acceptance criteria

- [ ] Every attached correctness result identifies the exact timed binary/source, graph representation and logical workload, actual BFS source vertex, target/configuration, execution, and verifier/check version. Evidence from a different functional build cannot silently certify that binary.
- [ ] The check enforces BFS structure: the source is its own parent, reachable vertices have valid predecessor edges at the preceding BFS depth, and unreachable vertices are represented correctly. Different valid parent trees pass.
- [ ] A real bounded accelerated BFS execution produces explicit structural-correctness evidence and evidence that acceleration actually executed. Presence of accelerator calls in source, successful compilation, or a scalar-fallback run alone is insufficient.
- [ ] The declared correctness cases exercise applicable full/tail tiles and competing parent updates, with graph/source identities and observed path coverage retained. A finite checked workload set is not presented as a proof for all graphs.
- [ ] The selected correctness mechanism preserves the intended ROI and seals the timing evidence before any excluded verification. Its runtime behavior is validated; source inspection alone does not establish that post-ROI continuation or another mechanism works.
- [ ] A printed verifier failure yields a failed correctness outcome even with a successful process exit. Missing, interrupted, or ambiguous verifier output remains incomplete/unverified and cannot promote a candidate to an implementation or support a successful gain claim.
- [ ] Public result retrieval exposes the explicit verdict, path coverage, raw verifier evidence, and sealed ROI association in a fresh process. Previously retained unverified execution evidence is not discarded when checking fails.
- [ ] Verification and retry attempts have predeclared limits and obey host/lane/resource procedures. Requested repetitions are reconciled with actual completed checks rather than inferred from a guest trial argument.

## Verification

Drive the public evaluation/result workflow with valid and invalid BFS-output cases, including a verifier failure paired with process exit zero and an absent verdict. Those cases establish outcome handling. Real acceptance additionally requires the pinned model executing the timed BFS binary with demonstrable acceleration and a structural check outside its sealed ROI. A mock simulator or separate functional API execution cannot satisfy that requirement. Full profiling and performance comparison are not needed to establish the correctness mechanism.

## Dependencies and boundaries

Ticket 12 supplies identified binaries, simulator execution, raw ROI artifacts, and durable unverified outcomes. This ticket does not depend on ticket 14's profile collector or ticket 11's full comparison protocols: it can retain direct path/check evidence for a bounded, explicitly identified execution. It does not move ROI boundaries, select a new strategy, run the full workload matrix, or prove profitability. Candidate-specific checks later reuse this mechanism for the workloads actually timed.

## Dependent preparation — 2026-09-25

Claimed for exact-binary continuation implementation while ticket 12 builds the pinned model. Acceptance remains blocked by the real bounded build and execution. The planned driver seals the guest-emitted ROI statistics before resuming the same simulator and guest binary for the enclosing structural verifier. Contract fixtures remain explicitly classified and cannot satisfy the real accelerated-path criteria.

## Implementation evidence — 2026-09-25

The continuation driver in `scripts/dx100_verify.py` seals the actual guest-dumped interval and resumes the same machine once. `swdb/dx100.py` binds explicit verifier results and observed MAA path evidence to exact execution identities while retaining incomplete/failing outcomes. `python3 -m pytest tests/test_dx100.py -q` passed 13 tests in 37.04 seconds, including direct driver execution with fake gem5 events for PASS, FAIL with exit zero, absent/ambiguous verdict, unexpected terminal cause, and post-seal timeout. These are contract fixtures; actual model continuation and applicable accelerated coverage remain unaccepted.

## Candidate and coverage preparation — 2026-09-25

The public candidate compiler now binds changed source artifacts to bounded
compilation receipts without rebuilding the model. Its trusted complete-call
wrapper preserves the actual returned parent array across the sealed exit and
validates its length and value range before the protected structural verifier.
An independent diagnostic-only wrapper preserves the unchanged author's
traversal ROI and forwards its internal reset/dump/exit events. The original
author primary binary is unchanged. Author function identity and accelerator
tile/core mismatches reject before simulation.

Actual MAA completion and tile sizes are parsed only inside the sealed ROI.
Competing-update evidence first binds the instruction's virtual parent base,
then detects distinct values for the same observed physical word; physical
trace addresses are never directly compared with a guest virtual pointer.
The combined adapter/driver/profile suite passed 42 tests in 166.32 seconds.
These source and contract tests do not satisfy the still-pending real
accelerated full/tail/competing-update acceptance.


## Actual continuation evidence — 2026-09-25

The real a6 model run sealed its ROI at tick 2,187,360,749, then the unchanged
same guest printed exactly one `Verification: PASS`, verification time, and
average time. It did not produce the required last-active-thread exit event;
continuation reached the declared 10^12-tick ceiling. The public record remains
unverified despite its PASS line and process exit zero, as required by the
contract. See [the audited finite receipt](../observations/dx100-smoke-a6.json).
The tiny graph's observed frontiers (1, 9, 37, 17) select the author's scalar
fallback and cannot establish accelerator execution/full-tile/tail/conflict
coverage. No acceptance criterion is resolved by this bring-up observation.
