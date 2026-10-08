# Draft intrinsic descriptions

Candidate: **dx100-artifact-e4fc4af:read_execute** (conditional).

Generated from located catalog contracts. Peter owns the concrete software spec; Eric resolves hardware constraints. ABI and implementation are pending review.

[Candidate and evidence](candidate.yaml) · [Structured draft](intrinsic-draft.yaml) · [Interface diagram](interface.mmd) · [Workload context](context.mmd) · [Mechanism checklist](mechanisms.mmd)

## dxc-gather

Propose gather for the matched accesses to VertexOffsets, parent, subject to the catalog's mapping requirements.

Role: **execute**. Source support: **code_observed**. Realization: **native_primitive**.

### Inputs and placement

The following are workload intents. The exact operand list and signature require Peter/Eric's specification.

| Request | Array | Pattern | Requested payload / index bits | Statements |
|---|---|---|---|---|
| access-02-read | VertexOffsets | indirect | int32 / 32 | bfs-td-row-bounds |
| access-04-read | parent | indirect | int32 / 32 | bfs-td-parent-read |

Design-wide software contract: Memory-mapped instruction stream, bases, typed scalar/vector tiles, optional mask and old-value destination. Range continuation registers and lower/upper bound tiles for range composition.

Invocation: Pinned MAA_gem5.hpp calls encode instructions and issue fences; wait_ready is a held mapped status read followed by mfence in the inspected core-0 interface.

### Result and behavior

Result: scratchpad_tile

Validity: Only active lanes below produced tile size have fresh payloads; masked finished slots retain prior storage.

Old-value behavior: not_applicable

Ordering: Iteration slots retain result association. Local duplicate-list processing and pending-line forwarding are observed; full inter-instruction/alias/global order remains unproved.

Completion: Instruction finish after pending-count/accounting and modeled latency checks; destination tiles become ready.

Visibility: Scratchpad payload is written before tile ready; end-to-end CPU read visibility still requires integration proof.

Type evidence: 32/64-bit payload paths; indirect indices are uint32; stream min/max/stride use int.

Missing capability evidence: none in the query; mapping requirements still apply

Missing workload evidence: none in the typed query; runtime placement/legality still require review

**Mutable target:** establish load freshness and synchronization before buffering or hoisting the access.

Limitations:

- Byte-offset product representability is required (dxc-byte-offset-domain); index_width_bits does not promise the entire unsigned index domain.

## dxc-ranged-gather

Propose gather for the matched accesses to g.out_neighbors_, subject to the catalog's mapping requirements.

Role: **execute**. Source support: **code_observed**. Realization: **documented_sequence**.

### Inputs and placement

The following are workload intents. The exact operand list and signature require Peter/Eric's specification.

| Request | Array | Pattern | Requested payload / index bits | Statements |
|---|---|---|---|---|
| access-03-read | g.out_neighbors_ | ranged_indirect | int32 / 32 | bfs-td-neighbor |

Design-wide software contract: Memory-mapped instruction stream, bases, typed scalar/vector tiles, optional mask and old-value destination. Range continuation registers and lower/upper bound tiles for range composition.

Invocation: Pinned MAA_gem5.hpp calls encode instructions and issue fences; wait_ready is a held mapped status read followed by mfence in the inspected core-0 interface.

### Result and behavior

Result: index_tiles_then_gathered_tile

Validity: Range output is densely emitted only for active outer ranges; consume produced size and preserve continuation.

Old-value behavior: not_applicable

Ordering: Range loop emits outer/inner index pairs; subsequent gather uses result-slot association.

Completion: Range Finish records continuation registers and both output sizes; the dependent gather completes separately; wait on the actual producer/consumer tile.

Visibility: unknown: CPU-visible completion needs integration proof.

Type evidence: Range bounds uint32, continuation and stride int; payload datatype does not widen this path.

Missing capability evidence: none in the query; mapping requirements still apply

Missing workload evidence: none in the typed query; runtime placement/legality still require review

Limitations:

- Composed operation, not a native gather-range opcode.
- Negative or overflowing range/stride values not established as legal.
- Byte-offset product representability is required (dxc-byte-offset-domain); index_width_bits does not promise the entire unsigned index domain.

## dxc-stream_load

Propose stream_load for the matched accesses to queue.shared, subject to the catalog's mapping requirements.

Role: **execute**. Source support: **code_observed**. Realization: **native_primitive**.

### Inputs and placement

The following are workload intents. The exact operand list and signature require Peter/Eric's specification.

| Request | Array | Pattern | Requested payload / index bits | Statements |
|---|---|---|---|---|
| access-01-read | queue.shared | sequential | int32 / n/a (no loaded-index request) | bfs-td-frontier |

Design-wide software contract: Memory-mapped instruction stream, bases, typed scalar/vector tiles, optional mask and old-value destination. Range continuation registers and lower/upper bound tiles for range composition.

Invocation: Pinned MAA_gem5.hpp calls encode instructions and issue fences; wait_ready is a held mapped status read followed by mfence in the inspected core-0 interface.

### Result and behavior

Result: scratchpad_tile

Validity: Only active lanes below produced tile size have fresh payloads; masked finished slots retain prior storage.

Old-value behavior: not_applicable

Ordering: Page/line requests may overlap; response words are placed in iteration-indexed destination slots. Indirect duplicate-list behavior is not claimed for this read operation.

Completion: Stream Response/Finish path calls finishInstructionCompute after its own request and latency checks; ready read responds when counter clears.

Visibility: Scratchpad payload is written before tile ready; end-to-end CPU read visibility still requires integration proof.

Type evidence: 32/64-bit payload paths; indirect indices are uint32; stream min/max/stride use int.

Missing capability evidence: none in the query; mapping requirements still apply

Missing workload evidence: none in the typed query; runtime placement/legality still require review

Limitations:

No additional operation-specific limitations recorded; design requirements still apply.

## Preconditions and legality

The following catalog requirements remain undischarged:

- **dxc-region-binding** (Addresses touched by selected operations; not all CPU memory): Bind actual bases, registered regions, aliases and permitted writers before mapping.
- **dxc-widths** (Each mapped input tile and range composition): Prove payload, uint32 index and range bounds, signed continuation/stride and sizes fit without truncation.
- **dxc-validity** (Output lanes of masked reads/stores/RMW): Propagate masks and produced sizes; never consume inactive old-value slots as fresh values.
- **dxc-observer** (CPU consumption, memory updates and storage reuse): Establish required observer visibility and safe tile/region reuse separately from instruction finish.
- **dxc-numerical** (RMW operator, datatype and returned old values): Check duplicates and numerical equivalence for the requested result contract.
- **dxc-reuse** (Tile reuse, especially masks and aliased/wide tile storage): Before host overwrites tiles, establish which live operands consume them and a completion barrier covering those consumers; condition-only ready state is insufficient evidence.
- **dxc-old-destination** (Scalar/vector stores and RMW operations requesting old values): When old values are required, allocate and supply the optional destination tile and preserve it until all active results are consumed.
- **dxc-byte-offset** (All selected indirect loads, scalar/vector stores and RMW, including generated indices in ranged/chained sequences): Prove byte-offset product and base-address addition representability for every active indirect index. On the examined 32-bit int/uint32 ABI require word_size * index &lt; 2^32 before adding the base; 32-bit index encoding alone is insufficient.
- **dxc-capacity** (Configured tile capacity, produced lengths, uint16 size bookkeeping and callers consuming those lengths): Bind effective simulator/API tile configuration and prove every produced tile size fits its bookkeeping, alongside index/offset arithmetic and storage allocation. Do not infer a broad legal capacity range from Unsigned knobs.

## Related accesses and side effects

A shared request group carries source context; it does not establish hardware fusion.

Reported workload update to preserve: CAS(addr=&parent[v], expected=curr_val, new_val=u). This is source/workload intent, not the proposed intrinsic signature.

- **bfs-td-traversal-and-discovery**: Source dependency chain from frontier load through row bounds and neighbor traversal to parent read and conditional CAS. The successful CAS also controls an explicit parent store and queue append. This context group is a manual proposal, not a proved single-accelerator mapping.
  Covered: access-01-read, access-02-read, access-03-read, access-04-read. Uncovered: access-04-update.

## Internal mechanism information

- **dependency_tracking**: Public e4fc4af ILD: IF rejects full instruction storage, destination-tile conflicts and specified same-range read/write conflicts within maa_id. Ready selection scans from a random offset and accepts Service/Finished source status; Fill still waits at unfinished condition/index elements in original iteration order. These checks do not establish all aliases or fairness.
- **buffering**: Public e4fc4af ILD: form base + word_size * uint32 index, check virtual bounds, translate aligned blocks and decode configured Ramulator2 physical geometry into slice/grow keys. Unsent row records contain aligned physical lines; same-row overflow can use another record. Finite capacity failure retains the failed iteration. Geometry and merged-bank organization are configuration-dependent.
- **coalescing**: Public e4fc4af ILD: a matching unsent line appends another (original iteration, word offset) in a forward next_itr list using first/last pointers without consuming another line slot. Duplicate words retain separate consumers. Compatible reads across units may also share a Port packet and waiter list; same-unit duplicate outstanding reads are rejected.
- **issue_policy**: Public e4fc4af with reorder enabled: final Fill or insertion failure enters Build; a producer wait alone does not. Each pass emits at most one line per active slice, channel fastest then rank, bank group, bank. Within a slice, scan row/line slots and other records of the same grow before another grow. Selection neither sorts addresses nor consults DRAM open-row state.
- **issue_policy**: Public e4fc4af: new packets snoop at creation unless forced to cache. Eligibility-tick queues are grouped by channel/cache bus; writes precede reads, and cache indirect classes precede stream classes. Failed sends retain queued work and block that channel/bus until retry or capacity release. Generator order does not guarantee downstream DRAM command order or fairness.
- **reordering**: Public e4fc4af ILD: decode response physical line to slice/grow, consume its associations and sort those by itr, then write each returned word[wid] to TD[itr], including duplicate-word fanout. Sorting is within one response, not outgoing address sorting or global response ordering.
- **completion**: Public e4fc4af ILD: consume and invalidate offset entries and line slots; only after all lines return is a row record reset/reusable. Sent records cannot accept additions. Request may fill released space, but batch transition waits for queued packets sent and received == expected; final Fill status is re-evaluated. Completion also checks producer readiness, modeled scratchpad/table latency and empty histories/tables before destination Finished/Ready and dependent-source publication. Host synchronization remains required.
- **buffering**: Public e4fc4af defaults include 16384 tile elements, 64 row records per slice, 8 line slots per subslice-row, 32 initial slices and 1-cycle row-table latency. Reorder is enabled; optional base-address/observed-row-count reconfiguration is disabled by default and is separate from fixed request selection. These are model defaults, not selected workload parameters or hardware timing evidence.

Missing descriptions do not imply that the hardware lacks the mechanism. No speedup is inferred from operation matching.

## Next review

- **Peter**: Confirm the matching source statements, region, phase and allowable replacement scope. Manual bindings are proposals; profiling placement is not confirmed.
- **Peter/Eric**: Specify exact operands, index arithmetic, masks/produced lengths, concrete types, invocation and completion API for each chosen operation or sequence.
- **Peter/Eric**: Discharge ownership, numeric domains, mutable-load freshness, ordering, repeated-target/concurrency and result validity requirements. Preserve CAS success and queue side effects.
- **Eric**: Add located internal buffering/coalescing/reordering/issue/dependency/completion details and conditions limiting performance.
- **Josh/Eric**: Establish whether related requests can share one legal mapping; the workload group and interface view do not prove combined execution.
- **Yan-Ru**: After Peter's spec is agreed, choose or synthesize an implementation and verify the rewritten kernel against the frozen correctness oracle.
