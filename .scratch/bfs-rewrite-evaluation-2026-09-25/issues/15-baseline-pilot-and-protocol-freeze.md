# 15 — Baseline pilot and protocol freeze

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** claimed
**Blocked by:** 11, 13, 14
**Spec:** `../spec.md`

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## What to build

Conduct a bounded baseline/reference pilot through the public workflow and publish the frozen protocols for the candidate coverage matrix. Select feasible workloads and defensible measurement rules using observed resource cost, correctness, attribution, and accelerator coverage. Do not use the gains of candidates awaiting assessment to choose their workloads or acceptance policy.

## Scope and spec references

Implements D10–D13 and the pilot gates supporting AC10–AC13, AC16–AC18. Use both unaccelerated starting implementations and the authors' fixed accelerated BFS as appropriate to calibration. Kronecker and uniform-random coverage, both application sources, and the separately required artifact reference cannot be removed because a smaller pilot is cheaper. Ticket 16 owns the artifact/reference comparison execution under its independently frozen protocol.

## Acceptance criteria

- [ ] Before execution, publish a bounded pilot plan with permitted baseline/reference artifacts, run/attempt and wall-time limits, resource/storage budgets, explicit stop conditions, and required host/lane checks. A budget expiry preserves evidence and an incomplete outcome rather than triggering an unbounded search for a gain.
- [ ] Real baseline/reference executions calibrate correctness-case and performance-workload sizes for both graph families. Selection reasons cite cost, coverage, and observed accelerator execution, without using performance gains from candidates being assessed.
- [ ] Workload records retain generator parameters/revision, normalization, realized graph properties, canonical identities, actual ordered traversal source IDs, and representation hashes. Equivalent loaded adjacency is checked across upstream and DX100 applications rather than inferred from a shared extension.
- [ ] Real pilot evidence establishes relevant accelerator full/tail and parent-update coverage, exact timed-binary correctness, BFS ROI and selected-region timing, and actual dynamic memory observations. Scalar fallback alone cannot justify accelerated coverage.
- [ ] Native timing variability and repeated identical simulation replays inform the recorded repetition/aggregation and profitability policies. Report actual completed executions, distinguish repeated graph/source pairs from different traversal sources, and do not assume deterministic timings or successful repetitions from a guest trial count.
- [ ] Freeze candidate-workload identities, vertices, native/simulated threads and targets, concrete configurations, semantic ROI definitions, correctness coverage, region/collector attribution, instrumentation treatment, repetitions/aggregation, and profitability criteria before candidate performance assessment. Initialization within a chosen complete-BFS-call ROI remains timed.
- [ ] A public query returns the frozen protocol identities, supporting pilot evidence, rejected/incomplete calibration cases, and the rule for protocol changes and required fresh comparisons. Native, simulated, diagnostic, and simulator-host quantities remain distinguishable.
- [ ] The frozen matrix preserves all eight starting-source/route/graph obligations and the minimum of one accelerator-using candidate from each starting implementation on both families. This ticket does not manufacture candidate coverage, a gain, or completion of the separately retained artifact-reference case.

## Verification

Use public requests to conduct the real bounded pilot, register its observations, freeze its protocols, and retrieve them in a fresh process. Reuse the native evaluation/profiling capabilities already available through the dependencies and the real DX100 correctness/profiling paths. Deterministic fixtures may check enforcement of missing settings or a changed protocol, but cannot select empirical sizes, establish timing variability, or replace the pilot's accelerator and memory observations. If the bounded pilot cannot establish the required settings, report the unresolved gate with retained evidence; do not mark the freeze complete.

## Dependencies and boundaries

Ticket 11 supplies workload/protocol identity and enforcement. Ticket 13 supplies exact timed-binary correctness; ticket 14 supplies simulated region/memory profiling and, through ticket 09's ancestry, the native profiling/evaluation foundation. No dependency on ticket 16 is introduced: the candidate matrix and artifact/reference work own separately frozen protocols. This slice does not generate rewrite proposals, assess candidate profitability, execute all coverage cells, or reproduce the full artifact campaign.

## Implementation progress

2026-09-25: Root owns dependent pilot preparation. The pre-execution limits and baseline-only selection rules are in `../pilot-plan.md`. Actual calibration awaits Tickets 11, 13, and 14; this ticket is not accepted or frozen by the plan.
