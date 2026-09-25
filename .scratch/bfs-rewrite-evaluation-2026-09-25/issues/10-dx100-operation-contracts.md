# 10 — Query DX100 operation contracts and check proposal capabilities

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** resolved
**Blocked by:** 02
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## What to build

Implementation preparation claimed 2026-09-25 by `host_dx100`. Ticket 02's
public proposal interface is available for integration; final acceptance waits
for its verification. Root owns the shared CLI/store/vocabulary registration.

Expose versioned, source-backed contracts for existing DX100 operations through the public capability query and proposal-checking path. Describe the operations sufficiently for a rewrite worker to use supported calls or generate wrappers over them, while rejecting unresolved required capabilities. Keep CPU intrinsic facts distinct from accelerator resources and synchronization, and keep hardware model, interface, backend, and execution host identities separate for later co-design.

## Scope and spec references

This slice contributes AC08, AC19, and AC20 through D06–D09 and D15. The initial catalog is limited to operations supported by the pinned DX100 source/model. It does not implement new operations, make a generated declaration executable, or establish a working simulator. Source-supported capabilities and current executable readiness must remain distinguishable.

## Acceptance criteria

- [x] A public capability query returns existing DX100 operations with stable identities, interface/model versions, and evidence pointing to their actual declarations and implementing backend.
- [x] Contracts state signatures/types, memory effects, applicable masks and repeated-index behavior, ordering/completion, resources, and header/build dependencies; unsupported or unknown details remain explicit.
- [x] Accelerator requirements are represented independently of CPU ISA flags, while existing CPU intrinsic capability queries and their meaning remain supported.
- [x] A proposal's declared operation requirements are checked against the selected versioned target/interface rather than a matching function name alone; unsupported or conflicting requirements produce a durable explicit non-success outcome.
- [x] Required support that remains unknown is not treated as available. Public output distinguishes a capability supported by the named source/model from an executable backend that has actually been built or verified.
- [x] A wrapper or call sequence over supported operations retains the requirements of its underlying calls. A generated symbol, wrapper declaration, or claimed interface cannot satisfy an otherwise unsupported hardware operation.
- [x] Hardware model/configuration, software interface, evaluator backend, and host references remain distinct; a future model/interface can be described without being mislabeled as executable or measured before matching support exists.
- [x] A fresh query retrieves operation contracts, proposal requirement checks, and rejection evidence with their versions and provenance, without claiming a live collaborator integration or DX100 execution result.

## Verification

Exercise public capability queries and patch-proposal requirement checks against isolated records with source-backed DX100 contract examples. Include an unknown operation, wrong interface version, unresolved required semantic property, and a wrapper that attempts to claim unsupported support. Alternate-backend fixtures establish identity/contract behavior only. This ticket requires source verification, not a simulator build or performance run; later bring-up and acceptance slices establish actual executable behavior.

## Dependencies and boundaries

Ticket 02 supplies public proposals and durable rejection/candidate outcomes. The source-context foundation is inherited through it. Instruction rewriting, complete profile generation, and simulator bring-up are not hidden prerequisites. Wrapper generation itself uses the later/shared worker path; this slice supplies its capability contract and checks. Future customized co-design remains supported by explicit identities, but new hardware-operation implementation is outside the first deliverable.

## Implementation evidence — 2026-09-25

Implemented `swdb/capabilities.py`, the operation/hardware-target schemas, seven
source-backed BFS operation records, and the four-core pinned DX100 target.
Root integrated the public `capabilities` command, normal record vocabulary,
and store indexing. The proposal checker checks exact interface/model identity,
required semantic values, bounded wrapper expansion, and executable-readiness
requests; unknown support remains unresolved before candidate creation.

`tests/test_capabilities.py`: 13 public workflow cases passed in 268.20 seconds;
the subsequently added alternate-backend rejection case passed separately in
22.99 seconds (14 cases total). These tests create real source edits, retain
durable proposal/candidate metadata, and retrieve results in later processes;
they do not execute DX100 or establish performance. `swdb validate` passed all
69 records at this checkpoint. Source declaration hashes match the vendored
pinned headers. Schema-document coverage reports no missing capability fields.

Contract documentation: `docs/bfs-capabilities.md`. Pinned model evidence,
source fingerprints, resource interpretation, and future build plan:
`docs/bfs-dx100-design.md`. Backend readiness remains `source_supported` with
no build evidence. Ticket 02 passed its 10 public tests and was resolved before this ticket.

## Answer

Resolved 2026-09-25. The public capability query and proposal checks expose the
source-supported DX100 contracts and retain explicit unsupported/unknown outcomes.
Fourteen public tests passed, including fresh-process retrieval and actual source
patch creation. No model execution or performance evidence is claimed. Context:
`docs/bfs-capabilities.md` and `docs/bfs-dx100-design.md`.
