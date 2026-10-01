# Draft intrinsic descriptions

Candidate: **prodigy-hpca2021:read_assist** (needs_evidence).

Generated from located catalog contracts. Peter owns the concrete software spec; Eric resolves hardware constraints. ABI and implementation are pending review.

[Candidate and evidence](candidate.yaml) · [Structured draft](intrinsic-draft.yaml) · [Interface diagram](interface.mmd) · [Workload context](context.mmd) · [Mechanism checklist](mechanisms.mmd)

## prod-prefetch

Configure prefetch assistance for accesses to VertexOffsets, g.out_neighbors_, parent; the program still obtains its required values/updates through its original execution path.

Role: **assist**. Source support: **paper_specified**. Realization: **documented_sequence**.

### Inputs and placement

The following are workload intents. The exact operand list and signature require Peter/Eric's specification.

| Request | Array | Pattern | Requested payload / index bits | Statements |
|---|---|---|---|---|
| access-02-read | VertexOffsets | indirect | int32 / 32 | bfs-td-row-bounds |
| access-03-read | g.out_neighbors_ | ranged_indirect | int32 / 32 | bfs-td-neighbor |
| access-04-read | parent | indirect | int32 / 32 | bfs-td-parent-read |

Design-wide software contract: Data Indirection Graph with array layout, dependency edges and triggers; no accelerator instruction stream.

Invocation: Runtime stores configure memory-mapped tables; demand accesses and fills drive prefetching.

### Result and behavior

Result: cache_fill_hint

Validity: CPU demand access remains authoritative; sequences may be dropped.

Old-value behavior: not_applicable

Ordering: No program-operation ordering or required-value delivery supplied by prefetch sequence order.

Completion: Prefetch fill may trigger another traversal; no software operation-completion event.

Visibility: Cache residency only; no update completion or immutable-memory guarantee.

Type evidence: Node data_size and address interpretation configured in DIG; no universal width domain asserted.

Missing capability evidence: index_width_bits, payload_types

Missing workload evidence: none in the typed query; runtime placement/legality still require review

**Mutable target:** establish load freshness and synchronization before buffering or hoisting the access.

**Assistance:** this interface does not supply the required program load result or replace its atomic update.

Limitations:

- This cannot substitute for an architectural load executor or CPU CAS.

## Preconditions and legality

The following catalog requirements remain undischarged:

- **prod-description** (DIG and each participating array): Register valid nodes, bounds, sizes, traversal edges and trigger edges for the actual workload.
- **prod-context** (Private per-core prefetcher and context switches): Preserve the correct per-thread prefetcher context; establish trigger partitioning for parallel use.

## Related accesses and side effects

A shared request group carries source context; it does not establish hardware fusion.

Reported workload update to preserve: CAS(addr=&parent[v], expected=curr_val, new_val=u). This is source/workload intent, not the proposed intrinsic signature.

- **bfs-td-traversal-and-discovery**: Source dependency chain from frontier load through row bounds and neighbor traversal to parent read and conditional CAS. The successful CAS also controls an explicit parent store and queue append. This context group is a manual proposal, not a proved single-accelerator mapping.
  Covered: access-02-read, access-03-read, access-04-read. Uncovered: access-01-read, access-04-update.

## Internal mechanism information

- **buffering**: unknown; annotation needed from Eric
- **coalescing**: unknown; annotation needed from Eric
- **reordering**: unknown; annotation needed from Eric
- **issue_policy**: unknown; annotation needed from Eric
- **dependency_tracking**: unknown; annotation needed from Eric
- **completion**: unknown; annotation needed from Eric

Missing descriptions do not imply that the hardware lacks the mechanism. No speedup is inferred from operation matching.

## Next review

- **Peter**: Confirm the matching source statements, region, phase and allowable replacement scope. Manual bindings are proposals; profiling placement is not confirmed.
- **Peter/Eric**: Specify exact operands, index arithmetic, masks/produced lengths, concrete types, invocation and completion API for each chosen operation or sequence.
- **Peter/Eric**: Discharge ownership, numeric domains, mutable-load freshness, ordering, repeated-target/concurrency and result validity requirements. Preserve CAS success and queue side effects.
- **Eric**: Add located internal buffering/coalescing/reordering/issue/dependency/completion details and conditions limiting performance.
- **Josh/Eric**: Establish whether related requests can share one legal mapping; the workload group and interface view do not prove combined execution.
- **Yan-Ru**: After Peter's spec is agreed, choose or synthesize an implementation and verify the rewritten kernel against the frozen correctness oracle.
