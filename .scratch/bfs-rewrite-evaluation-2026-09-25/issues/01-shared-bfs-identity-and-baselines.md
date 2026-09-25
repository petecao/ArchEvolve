# 01 — Query shared BFS identity with source-specific context and explicit baselines

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** None
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution hold:** Publishing this ticket does not authorize implementation, builds, installations, benchmark/simulator runs, or remote execution. Wait for explicit user authorization.

## What to build

Extend public BFS lookup and comparison behavior so upstream GAPBS direction-optimizing BFS and DX100 scalar top-down BFS share one semantic kernel while retaining their own application source, revision, source baseline, and build/evaluator context. Expose the source ancestor, source baseline, and explicitly selected comparison baseline as separate relationships. Make this a compatible foundation for later workflow slices, without requiring a destructive conversion of existing records.

## Scope and spec references

This slice owns source/context resolution and explicit comparator behavior visible through public queries. It contributes AC01 and AC14, following D01–D03, D06, and D12. Preserve the existing YAML authority and generated-query-index model. Record format and compatibility decisions before implementing the affected interface; exact field names are not prescribed here.

## Acceptance criteria

- [ ] One public BFS query returns both starting implementations under one kernel identity and distinguishes their exact application origins and revisions.
- [ ] Each returned implementation resolves its own code and build/evaluator context; the DX100 implementation does not inherit an upstream URI, commit, include context, or verifier invocation merely because it shares the kernel.
- [ ] Public output distinguishes source ancestor, baseline found in that source, and comparison baseline, without substituting one relationship for another.
- [ ] A comparison whose ancestor differs from its explicitly selected baseline uses the selected baseline and reports both identities. Fixture comparisons are identified as such and make no empirical gain claim.
- [ ] A missing, conflicting, or semantically incompatible comparison target produces an explicit non-success response rather than silently falling back to ancestry or the old canonical baseline.
- [ ] Existing supported records and public queries retain their meaning through a documented compatibility path; no destructive migration or replacement of historical source provenance is required to complete this slice.
- [ ] Rebuilding the generated query index from authoritative records preserves both source contexts and comparator relationships, and a fresh public query returns the same identities.
- [ ] Incorrect or unchecked code remains distinguishable from a verified implementation; representing an imported source does not invent correctness evidence for a new target or workload.

## Verification

Drive the public CLI/message interface in separate processes against isolated records. Exercise legacy records, the two BFS source contexts, explicit ancestor-versus-comparator divergence, invalid references, and query-index regeneration. Source/context and comparison fixtures establish contract behavior only; this ticket does not require a DX100 build or performance run and cannot establish a speedup.

## Dependencies and boundaries

There is no ticket prerequisite. The execution hold still applies. Later slices provide proposal execution, live evaluator bindings, protocol-freeze enforcement, and real comparisons. Do not make those later capabilities prerequisites for truthful source lookup or explicit comparison selection. This ticket does not select an optimization strategy or change the shared BFS correctness semantics.
