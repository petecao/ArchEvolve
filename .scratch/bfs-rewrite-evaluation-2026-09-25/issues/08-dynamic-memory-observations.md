# 08 — Return actual memory-behavior observations for BFS executions

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 06
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution hold:** Publishing this ticket does not authorize implementation, builds, installations, benchmark/simulator runs, or remote execution. Wait for explicit user authorization.

## What to build

Extend the public BFS profiling result with actual execution- or simulation-derived memory observations, such as access counts or cache behavior. Deliver at least one supported observation family and expose unsupported metrics honestly. Tie observations to the particular source/binary and workload, including any separately instrumented diagnostic artifact, so an ensemble can distinguish observed memory behavior from static access-pattern descriptions and inferred explanations.

## Scope and spec references

This slice contributes AC04, AC09, and AC13 through D03–D05, D11, and D14. It does not require unavailable native hardware counters, full address traces, or multiple new collection systems. Counter-free execution observations or a supported memory model are acceptable when their basis and limits are explicit. DX100-specific collection follows in the simulator profiling slice.

## Acceptance criteria

- [ ] A real BFS execution or supported diagnostic simulation produces at least one actual memory-behavior observation retrievable through the public profiling/query interface.
- [ ] Each observation states its definition, units, collector/model identity, source/binary and workload identity, collection scope, attribution granularity, and evidence basis.
- [ ] ROI-wide observations are not presented as measurements of individual loops or functions. Static formulas or source-derived access patterns are not relabeled as dynamic observations.
- [ ] Unsupported, missing, or failed metrics and uncertain bottleneck explanations are explicit; a result with every dynamic memory metric unavailable cannot claim complete memory profiling.
- [ ] Model-derived cache observations are labeled simulated and are not described as native hardware measurements. Actual counts are distinguished from inferred values.
- [ ] If profiling uses a different instrumented artifact or execution, the result records that difference and its relationship to the timed artifact; diagnostic runtime cannot replace primary ROI timing.
- [ ] Profiling a changed candidate collects fresh observations linked to that candidate. A fixed source-order graph traversal is not substituted for the actual BFS frontier order when claiming dynamic index behavior.
- [ ] Successful and partial observations survive fresh-process retrieval, with raw-artifact references and failure reasons; missing evidence is not converted into a neutral performance result.

## Verification

Drive public native execution/diagnostic profiling and retrieval after authorization, retaining actual collector output for a small BFS case. Use deterministic external collector fixtures only to check parsing, evidence labels, scope, and unavailable-output behavior. Those fixtures do not satisfy the real-observation criterion. No pre-freeze gain claim or DX100 installation is required by this slice.

## Dependencies and boundaries

Ticket 06 provides execution-bound function/source context. Loop discovery is not a prerequisite because correctly scoped ROI/function observations can be useful independently. Ticket 09 assembles complete profile packages; this slice must not claim that an incomplete package meets that later gate. Choose the supported collection method during implementation design without broadening the task into full tracing or causal proof.
