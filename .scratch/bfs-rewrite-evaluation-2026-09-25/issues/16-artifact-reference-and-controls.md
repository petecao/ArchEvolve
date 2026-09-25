# 16 — Artifact reference and controls

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 11, 13, 14
**Spec:** `../spec.md`

**Execution hold:** Publishing this ticket does not authorize implementation, builds, installations, benchmark/simulator runs, or remote execution. Wait for explicit user authorization.

## What to build

Execute and retain the BFS-only authors' scalar/accelerated artifact comparison and additional controlled reference comparisons with matched CPU/cache/memory settings. Freeze this slice's protocols independently before its measured comparisons. Provide real reference evidence and explicit limits on attribution without waiting for candidate-workload calibration or requiring new rewrite proposals.

## Scope and spec references

Implements D10–D14 and AC10, AC13–AC16, AC18. The artifact pair preserves the authors' specified BFS input and configurations, including their different LLC settings. Controlled comparisons use the fixed scalar and author-accelerated BFS code with declared matched settings and enumerated software/accelerator differences. Candidate-specific controlled comparisons remain obligations of later candidate evaluation; these reference runs do not satisfy them automatically.

## Acceptance criteria

- [ ] Before execution, record a bounded BFS-only run plan, attempt/time/resource/storage limits, and host/lane checks. Instantiate and freeze this slice's graph/source identities, build settings, ROI, exact configurations, correctness scope, instrumentation treatment, repetitions/aggregation, and profitability/claim rules independently of ticket 15. These rules assess any reported gain; a positive gain is not required to complete the reference comparison.
- [ ] Resolve the artifact's prescribed graph family/scale and actual input identity from the pinned source, retaining generated/serialized identities and realized graph properties. A convenient smaller graph or matching filename is not silently accepted as the artifact case.
- [ ] Complete real scalar and author-accelerated BFS executions under the authors' BASE/accelerated configuration pair. Retain their actual configuration difference, including the LLC difference, instead of normalizing it away and calling the result a reproduction.
- [ ] Complete the additional controlled reference comparisons with matched CPU, cache, memory, workload, traversal sources, threads, and semantic ROI as declared. Enumerate remaining software and accelerator changes; do not claim an isolated software-rewrite gain from a joint hardware/software comparison.
- [ ] Each reported comparison has explicit baseline/result identities, exact timed-binary structural correctness, accelerator-use evidence for the accelerated case, BFS ROI duration, selected-region timing, and actual dynamic memory observations with truthful scope and basis.
- [ ] Preserve raw statistics, verifier output, model/build/binary/checkpoint identities, clock/timing conversion, and host cost separately. Missing, invalid, incomplete, or failed evidence cannot produce a successful speedup claim or a neutral value of one.
- [ ] Public retrieval exposes the independently frozen protocols, the real reference/control results, all failures or regressions, and their attribution limits. Existing evidence is reused only when all relevant identities and requirements actually match.
- [ ] Results do not claim generated-candidate acceptance, completion of the two-source accelerator minimum, or a gain over the authors' accelerated BFS. A reference or control outcome may be neutral or regressing without being hidden; execution remains bounded rather than continuing until a favorable ratio appears.

## Verification

Drive protocol registration, real model executions, correctness checking, profiling, comparisons, and fresh-process result retrieval through the public workflow. Fixture checks can establish configuration-mismatch rejection and preservation of failed outcomes, but cannot establish artifact reproduction, matched-control performance, or accelerator behavior. Inspect the retained actual configurations and evidence when accepting each real pair; a declared configuration label alone is insufficient.

## Dependencies and boundaries

Ticket 11 supplies explicit protocol/comparison enforcement; tickets 13 and 14 supply exact timed-binary correctness and actual simulated profiling. Ticket 15 is deliberately not a dependency. This slice owns its separate protocol freeze and may proceed alongside the candidate-matrix pilot. It does not select candidate workloads, rewrite code to beat the author result, run DMP/DAE or parameter sweeps unless separately scoped, or reproduce benchmarks beyond the required BFS path.
