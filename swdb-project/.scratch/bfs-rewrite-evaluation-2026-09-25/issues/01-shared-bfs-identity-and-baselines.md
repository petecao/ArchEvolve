# 01 — Query shared BFS identity with source-specific context and explicit baselines

Navigation updated: 2026-09-28 (Eastern Time).

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** resolved
**Blocked by:** None
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution authorization:** The user authorized implementation and execution on 2026-09-25.

Execution authorized by the user's 2026-09-25 request to implement all tickets autonomously. Claimed 2026-09-25 by the identity agent.

## What to build

Extend public BFS lookup and comparison behavior so upstream GAPBS direction-optimizing BFS and DX100 scalar top-down BFS share one semantic kernel while retaining their own application source, revision, source baseline, and build/evaluator context. Expose the source ancestor, source baseline, and explicitly selected comparison baseline as separate relationships. Make this a compatible foundation for later workflow slices, without requiring a destructive conversion of existing records.

## Scope and spec references

This slice owns source/context resolution and explicit comparator behavior visible through public queries. It contributes AC01 and AC14, following D01–D03, D06, and D12. Preserve the existing YAML authority and generated-query-index model. Record format and compatibility decisions before implementing the affected interface; exact field names are not prescribed here.

## Acceptance criteria

- [x] One public BFS query returns both starting implementations under one kernel identity and distinguishes their exact application origins and revisions.
- [x] Each returned implementation resolves its own code and build/evaluator context; the DX100 implementation does not inherit an upstream URI, commit, include context, or verifier invocation merely because it shares the kernel.
- [x] Public output distinguishes source ancestor, baseline found in that source, and comparison baseline, without substituting one relationship for another.
- [x] A comparison whose ancestor differs from its explicitly selected baseline uses the selected baseline and reports both identities. Fixture comparisons are identified as such and make no empirical gain claim.
- [x] A missing, conflicting, or semantically incompatible comparison target produces an explicit non-success response rather than silently falling back to ancestry or the old canonical baseline.
- [x] Existing supported records and public queries retain their meaning through a documented compatibility path; no destructive migration or replacement of historical source provenance is required to complete this slice.
- [x] Rebuilding the generated query index from authoritative records preserves both source contexts and comparator relationships, and a fresh public query returns the same identities.
- [x] Incorrect or unchecked code remains distinguishable from a verified implementation; representing an imported source does not invent correctness evidence for a new target or workload.

## Verification

Drive the public CLI/message interface in separate processes against isolated records. Exercise legacy records, the two BFS source contexts, explicit ancestor-versus-comparator divergence, invalid references, and query-index regeneration. Source/context and comparison fixtures establish contract behavior only; this ticket does not require a DX100 build or performance run and cannot establish a speedup.

## Dependencies and boundaries

There is no ticket prerequisite. Execution is authorized by the 2026-09-25 user request. Later slices provide proposal execution, live evaluator bindings, protocol-freeze enforcement, and real comparisons. Do not make those later capabilities prerequisites for truthful source lookup or explicit comparison selection. This ticket does not select an optimization strategy or change the shared BFS correctness semantics.

## Answer

Resolved: 2026-09-25 (Eastern Time).

Implemented additive format 0.4 ownership, evaluator, scoped verification, source
baseline, and explicit comparison baseline. Formats 0.2/0.3 preserve historical
kernel defaults and ancestry profile pairing. The versioning and compatibility
choices were documented before the interface changes in
[the source-context contract](../../../docs/reference/bfs-source-identity.md).

`swdb implementations gapbs-bfs` returns upstream direction-optimizing BFS and
DX100 scalar top-down BFS with independently resolved sources, revisions, headers,
build commands, executable check bindings, and three separate relationships.
`Store.source_context` is the shared resolver used by query and profiling. The
generated `implementation_contexts` table preserves these identities on rebuild.
The DX100 source subset under `apps/dx100` is byte-identical to pinned revision
`e4fc4afdf894f295442cef3604667a469fab8e62`, with a checksum manifest; its imported
record is explicitly unchecked. Existing upstream correctness references retain
their historical mbit10 workload scope only. No native run or gain is claimed here.

`swdb compare` selects an explicit implementation and exact profile pair; it
rejects absent/conflicting/cross-kernel targets, mismatched profile ownership or
source revisions, absent correctness, and incompatible workload/target/threads/ROI/
protocol/basis. It never substitutes source ancestry. Fixture comparisons report
only `fixture_ratio` with `gain_claim: false`; execution pairs remain diagnostics
until later workflow policy acceptance.

Validation: the new public subprocess source/comparator suite passed 22 tests;
an additional focused run passed 10 tests covering new malformed-context cases,
explicit-comparator divergence, and the repaired legacy database isolation fixture.
The broad source/db/profile/view/applies/format regression run passed 97 tests with
3 lab-only skips. Its three failures were the isolation fixture (fixed and retested)
and two format-document checks affected by concurrently introduced workflow schemas
(owned by the root agent). `git diff --check` passed and authoritative records
validate. Source-specific evaluator execution and fresh-process index regeneration
are tested; fixtures establish contract behavior, not performance evidence.

Context pointer: [source-context compatibility and command contract](../../../docs/reference/bfs-source-identity.md),
[public workflow tests](../../../tests/test_bfs_identity.py),
and [DX100 source provenance](../../../apps/dx100/PROVENANCE.md).
