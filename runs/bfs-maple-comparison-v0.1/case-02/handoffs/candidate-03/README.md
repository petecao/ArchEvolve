# Draft intrinsic descriptions

Candidate: **maple-isca2022:read_assist** (needs_evidence).

Generated from located catalog contracts. Peter owns the concrete software spec; Eric resolves hardware constraints. ABI and implementation are pending review.

[Candidate and evidence](candidate.yaml) · [Structured draft](intrinsic-draft.yaml) · [Interface diagram](interface.mmd) · [Workload context](context.mmd) · [Mechanism checklist](mechanisms.mmd)

## maple-lima-prefetch

Configure prefetch assistance for accesses to queue.shared, VertexOffsets, g.out_neighbors_, parent; the program still obtains its required values/updates through its original execution path.

Role: **assist**. Source support: **paper_specified**. Realization: **native_primitive**.

### Inputs and placement

The following are workload intents. The exact operand list and signature require Peter/Eric's specification.

| Request | Array | Pattern | Requested payload / index bits | Statements |
|---|---|---|---|---|
| access-01-read | queue.shared | sequential | int32 / n/a (no loaded-index request) | bfs-td-frontier |
| access-02-read | VertexOffsets | indirect | int32 / 32 | bfs-td-row-bounds |
| access-03-read | g.out_neighbors_ | ranged_indirect | int32 / 32 | bfs-td-neighbor |
| access-04-read | parent | indirect | int32 / 32 | bfs-td-parent-read |

Design-wide software contract: Queue identities and lifecycle/binding, virtual pointers for individual fetches, or configured A/B bases plus begin/end bounds for LIMA. Software establishes producer/consumer schedule, stable arrays and memory route.

Invocation: User-mode MMIO stores issue produces/configuration and MMIO loads consume queue values, using ordinary core load/store instructions. INIT, OPEN/CLOSE, PRODUCE_PTR/CONSUME and LIMA_PRODUCE/LIMA are paper API names, not generated C declarations.

### Result and behavior

Result: nonbinding_LLC_fill_hint

Validity: CPU demand loads obtain the program result; a prefetched line may be replaced before use.

Old-value behavior: not_applicable

Ordering: LLC hints do not replace demand-load order or CPU update synchronization.

Completion: Prefetch command/fill has no authoritative program-result completion; demand accesses remain on the core.

Visibility: Shared-cache assistance only; CPU demand accesses determine program values.

Type evidence: Paper discusses 32-bit evaluation words and a RISCV64 system, but the complete payload/sign, index/bounds and pointer-width API domains are not established.

Missing capability evidence: index_width_bits, payload_types

Missing workload evidence: none in the typed query; runtime placement/legality still require review

**Mutable target:** establish load freshness and synchronization before buffering or hoisting the access.

**Assistance:** this interface does not supply the required program load result or replace its atomic update.

Limitations:

- Concrete API types, queue packing, numeric bounds and memory-route semantics need confirmation.

## maple-pointer-prefetch

Configure prefetch assistance for accesses to VertexOffsets, parent; the program still obtains its required values/updates through its original execution path.

Role: **assist**. Source support: **paper_specified**. Realization: **native_primitive**.

### Inputs and placement

The following are workload intents. The exact operand list and signature require Peter/Eric's specification.

| Request | Array | Pattern | Requested payload / index bits | Statements |
|---|---|---|---|---|
| access-02-read | VertexOffsets | indirect | int32 / 32 | bfs-td-row-bounds |
| access-04-read | parent | indirect | int32 / 32 | bfs-td-parent-read |

Design-wide software contract: Queue identities and lifecycle/binding, virtual pointers for individual fetches, or configured A/B bases plus begin/end bounds for LIMA. Software establishes producer/consumer schedule, stable arrays and memory route.

Invocation: User-mode MMIO stores issue produces/configuration and MMIO loads consume queue values, using ordinary core load/store instructions. INIT, OPEN/CLOSE, PRODUCE_PTR/CONSUME and LIMA_PRODUCE/LIMA are paper API names, not generated C declarations.

### Result and behavior

Result: nonbinding_LLC_fill_hint

Validity: No returned gather result, atomic result or fetched-data readiness promise.

Old-value behavior: not_applicable

Ordering: LLC hints do not replace demand-load order or CPU update synchronization.

Completion: Prefetch command/fill has no authoritative program-result completion; demand accesses remain on the core.

Visibility: Shared-cache assistance only; CPU demand accesses determine program values.

Type evidence: Paper discusses 32-bit evaluation words and a RISCV64 system, but the complete payload/sign, index/bounds and pointer-width API domains are not established.

Missing capability evidence: index_width_bits, payload_types

Missing workload evidence: none in the typed query; runtime placement/legality still require review

**Mutable target:** establish load freshness and synchronization before buffering or hoisting the access.

**Assistance:** this interface does not supply the required program load result or replace its atomic update.

Limitations:

- Concrete API types, queue packing, numeric bounds and memory-route semantics need confirmation.

## Preconditions and legality

The following catalog requirements remain undischarged:

- **maple-stable-target** (All queue-fetched target arrays and any index data used for address generation): Establish stable data and ownership from fetch through consumption; a coherent request cannot refresh an already queued value after a CPU write.
- **maple-queue-lifecycle** (Per queue and participating software threads): Bind/init/open/close queues exclusively as required and establish producer/consumer counts, ordering, storage reuse and a nondeadlocking runahead schedule.
- **maple-typed-abi** (Pointers, A/B element formats, bounds, packed queue values and API operands): Resolve concrete payload/index/pointer types, element scaling, valid ranges, result packing and counts; paper-level operation names are not complete C signatures.
- **maple-source-binding** (Per BFS statement and ROI): Choose pointer-produce or LIMA mode and demonstrate source operand/interval correspondence; supplied bounds do not offload the full queue-to-CSR dependency chain.
- **maple-completion** (Fetch acceptance, queue value readiness, drain and memory observers): Distinguish pointer-produce acknowledgement from available fetched data, consuming a value, draining a loop and any required observer barrier.
- **maple-platform** (MMIO resource allocation, virtual address translation and memory path): Provide compatible NoC/MMIO integration, driver/MMU/shootdown support and chosen coherent LLC or noncoherent memory route.
- **maple-cpu-updates** (Current BFS parent CAS, parent store and queue append): Retain CPU updates and success-controlled side effects unless separate evidence establishes a supported atomic engine and equivalent mapping.

## Related accesses and side effects

A shared request group carries source context; it does not establish hardware fusion.

Reported workload update to preserve: CAS(addr=&parent[v], expected=curr_val, new_val=u). This is source/workload intent, not the proposed intrinsic signature.

- **bfs-td-traversal-and-discovery**: Source dependency chain from frontier load through row bounds and neighbor traversal to parent read and conditional CAS. The successful CAS also controls an explicit parent store and queue append. This context group is a manual proposal, not a proved single-accelerator mapping.
  Covered: access-01-read, access-02-read, access-03-read, access-04-read. Uncovered: access-04-update.

## Internal mechanism information

- **buffering**: Circular FIFOs share scratchpad. Full-queue produces and empty-queue consumes wait in buffered pipelines; configuration remains available.
- **buffering**: LIMA fetches adjacent B-index data in 64-byte chunks and iterates through those words to generate A addresses.
- **reordering**: Reserved queue slot indices are used as transaction IDs. Replies may arrive out of order but are placed into their associated FIFO slots for ordered consumption; this is response association, not a demonstrated DRAM-locality sort.
- **issue_policy**: Separate produce/consume/configuration pipelines permit concurrent operations. LIMA feeds generated requests into the produce path; a blocked queue need not stall other queues. No locality-aware A-address sorting policy is specified.
- **dependency_tracking**: Software produces pointers or configures one-level LIMA intervals; queued replies retain slot identity. Dependencies needed to compute pointers/bounds stay in software unless the described LIMA operation covers them.
- **completion**: The issue store acknowledgement occurs before the fetched memory data arrives; a consumer receives its data only on the queue-consume load response.
- **coalescing**: unknown; annotation needed from Eric

Missing descriptions do not imply that the hardware lacks the mechanism. No speedup is inferred from operation matching.

## Next review

- **Peter**: Confirm the matching source statements, region, phase and allowable replacement scope. Manual bindings are proposals; profiling placement is not confirmed.
- **Peter/Eric**: Specify exact operands, index arithmetic, masks/produced lengths, concrete types, invocation and completion API for each chosen operation or sequence.
- **Peter/Eric**: Discharge ownership, numeric domains, mutable-load freshness, ordering, repeated-target/concurrency and result validity requirements. Preserve CAS success and queue side effects.
- **Eric**: Add located internal buffering/coalescing/reordering/issue/dependency/completion details and conditions limiting performance.
- **Josh/Eric**: Establish whether related requests can share one legal mapping; the workload group and interface view do not prove combined execution.
- **Yan-Ru**: After Peter's spec is agreed, choose or synthesize an implementation and verify the rewritten kernel against the frozen correctness oracle.

[Source-backed logical block paths](structure.mmd) describe the paper's architecture, not a port netlist or a proved mapping of all BFS operations.
