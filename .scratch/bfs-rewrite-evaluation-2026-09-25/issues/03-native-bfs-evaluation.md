# 03 — Evaluate a native BFS candidate and retrieve its durable result

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** claimed
**Blocked by:** 02
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

**Progress (2026-09-25):** Tickets 01/02 are resolved. The native evaluator,
protected driver, evaluation schema, and public request/result tests are prepared.
Seventeen current cases passed across the public outcome suite and focused
process-cleanup, budget, macro-integrity, and real C++ fixture-driver checks.
Fixture durations remain contract evidence. This ticket awaits the coordinated
real native DX100 scalar diagnostic before resolution. Its initial real budgets
are build 180 seconds, each execution 30 seconds, total evaluation 300 seconds,
inside a 900-second lane budget; no gain assessment is authorized by this smoke.

## What to build

Carry a submitted CPU-runnable BFS candidate through native building, independent structural correctness checking, declared-ROI observation, and durable result retrieval. Link each observation to the actual candidate, binary, workload, target, build, and timing boundary. Preserve failures even when no valid performance profile can be written. Early real runs are correctness and diagnostic integration checks; they must not assess candidate profitability or claim a gain before the later protocol freeze.

## Scope and spec references

This slice contributes AC07–AC10, AC12–AC14, and AC20 through D02–D03, D10–D12, and D14. Use the source and comparison relationships established by ticket 01. Automatic hotspot discovery and complete dynamic profile packages are later slices; unavailable region or memory observations must be explicit rather than invented.

Use DX100 scalar top-down BFS for the first real native integration case, preserving the agreed starting order. Upstream direction-optimizing BFS remains required in the same deliverable; this order does not create a later-milestone exemption.

## Acceptance criteria

- [ ] Public evaluation consumes the identified candidate and returns a durable result identifying its proposal, source, binary, build settings, graph and actual traversal sources, native target, thread count, and declared ROI.
- [ ] Real native BFS code builds and executes on small diagnostic correctness cases; the structural check accepts different valid BFS parent trees while rejecting invalid predecessor, depth, source, or reachability results.
- [ ] Correctness evidence covers the code and workloads actually executed. An explicit verifier failure, including one accompanied by process exit zero, cannot become a successful correctness result.
- [ ] The evaluator preserves protected correctness and ROI inputs and records native ROI duration separately from outside-ROI diagnostics. Work inside a declared complete-BFS-call ROI remains timed.
- [ ] Build failure, correctness failure, timeout, exhausted execution budget, and missing observations remain retrievable with completed evidence. Incorrect candidates are not promoted to verified implementations.
- [ ] Result retrieval distinguishes an incomplete evaluation from a complete one, identifies unavailable region/profile metrics, and never represents missing evidence as a speedup of one.
- [ ] The explicitly chosen comparison baseline is retained independently of ancestry; obviously incompatible workload, target, or ROI evidence cannot produce a valid comparison. Pre-freeze results are diagnostic, not gain claims.
- [ ] A fresh process retrieves stage outcomes and raw-artifact references after success or failure, including completed evidence if the evaluating caller is interrupted.

## Verification

Drive submission, evaluation, and subsequent retrieval through public commands/messages. Deterministic external benchmark fixtures cover exit-zero verifier failure, build failure, timeout, missing output, and persistence behavior without counting as measurement evidence. After execution is separately authorized, include a small real native BFS build/check/diagnostic run through the same interface under the host rules. Full graph-family performance coverage and profitability claims remain later acceptance work.

## Dependencies and boundaries

Ticket 02 provides candidates, protected source context, and durable proposal outcomes. This ticket does not require automatic profiling, the live package generator, a working simulator, or the final workload set. It must expose incomplete profiling honestly until those capabilities arrive. Later graph/protocol enforcement and the baseline/reference pilot provide the gate for candidate performance assessment; this slice does not bypass that gate.
