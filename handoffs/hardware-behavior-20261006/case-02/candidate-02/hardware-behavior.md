# How this accelerator works

**dx100-artifact-e4fc4af / e4fc4afdf894f295442cef3604667a469fab8e62**

[Machine-readable behavior](hardware-behavior.yaml) · [Intrinsic draft](intrinsic-draft.yaml)

## What software asks hardware to do

Memory-mapped instruction stream, bases, typed scalar/vector tiles, optional mask and old-value destination. Range continuation registers and lower/upper bound tiles for range composition.

Invocation: Pinned MAA_gem5.hpp calls encode instructions and issue fences; wait_ready is a held mapped status read followed by mfence in the inspected core-0 interface.

## What software must observe

### dxc-stream_load

Role: **execute**; support: **code_observed**.

Workload targets: queue.shared.

Result and validity: scratchpad_tile; Only active lanes below produced tile size have fresh payloads; masked finished slots retain prior storage.

Ordering/association: Page/line requests may overlap; response words are placed in iteration-indexed destination slots. Indirect duplicate-list behavior is not claimed for this read operation.

Completion: Stream Response/Finish path calls finishInstructionCompute after its own request and latency checks; ready read responds when counter clears.

Visibility: Scratchpad payload is written before tile ready; end-to-end CPU read visibility still requires integration proof.

### dxc-gather

Role: **execute**; support: **code_observed**.

Workload targets: VertexOffsets, parent.

Result and validity: scratchpad_tile; Only active lanes below produced tile size have fresh payloads; masked finished slots retain prior storage.

Ordering/association: Iteration slots retain result association. Local duplicate-list processing and pending-line forwarding are observed; full inter-instruction/alias/global order remains unproved.

Completion: Instruction finish after pending-count/accounting and modeled latency checks; destination tiles become ready.

Visibility: Scratchpad payload is written before tile ready; end-to-end CPU read visibility still requires integration proof.

### dxc-ranged-gather

Role: **execute**; support: **code_observed**.

Workload targets: g.out_neighbors_.

Result and validity: index_tiles_then_gathered_tile; Range output is densely emitted only for active outer ranges; consume produced size and preserve continuation.

Ordering/association: Range loop emits outer/inner index pairs; subsequent gather uses result-slot association.

Completion: Range Finish records continuation registers and both output sizes; the dependent gather completes separately; wait on the actual producer/consumer tile.

Visibility: unknown: CPU-visible completion needs integration proof.

## Internal mechanism

Located edition-specific descriptions; annotation list is not an executable state machine or complete timing policy.

- **dx100-model-admission / dependency_tracking**: Public e4fc4af ILD: IF rejects full instruction storage, destination-tile conflicts and specified same-range read/write conflicts within maa_id. Ready selection scans from a random offset and accepts Service/Finished source status; Fill still waits at unfinished condition/index elements in original iteration order. These checks do not establish all aliases or fairness.
  Evidence: dx-internal-c13, dx-internal-c1.
- **dx100-model-physical-grouping / buffering**: Public e4fc4af ILD: form base + word_size * uint32 index, check virtual bounds, translate aligned blocks and decode configured Ramulator2 physical geometry into slice/grow keys. Unsent row records contain aligned physical lines; same-row overflow can use another record. Finite capacity failure retains the failed iteration. Geometry and merged-bank organization are configuration-dependent.
  Evidence: dx-internal-c1, dx-internal-c3, dx-internal-c4, dx-internal-c5.
- **dx100-model-duplicate-consumers / coalescing**: Public e4fc4af ILD: a matching unsent line appends another (original iteration, word offset) in a forward next_itr list using first/last pointers without consuming another line slot. Duplicate words retain separate consumers. Compatible reads across units may also share a Port packet and waiter list; same-unit duplicate outstanding reads are rejected.
  Evidence: dx-internal-c4, dx-internal-c5, dx-internal-c10.
- **dx100-model-fixed-slice-cycle / issue_policy**: Public e4fc4af with reorder enabled: final Fill or insertion failure enters Build; a producer wait alone does not. Each pass emits at most one line per active slice, channel fastest then rank, bank group, bank. Within a slice, scan row/line slots and other records of the same grow before another grow. Selection neither sorts addresses nor consults DRAM open-row state.
  Evidence: dx-internal-c6.
- **dx100-model-downstream-backpressure / issue_policy**: Public e4fc4af: new packets snoop at creation unless forced to cache. Eligibility-tick queues are grouped by channel/cache bus; writes precede reads, and cache indirect classes precede stream classes. Failed sends retain queued work and block that channel/bus until retry or capacity release. Generator order does not guarantee downstream DRAM command order or fairness.
  Evidence: dx-internal-c9, dx-internal-c10.
- **dx100-model-result-placement / reordering**: Public e4fc4af ILD: decode response physical line to slice/grow, consume its associations and sort those by itr, then write each returned word[wid] to TD[itr], including duplicate-word fanout. Sorting is within one response, not outgoing address sorting or global response ordering.
  Evidence: dx-internal-c8.
- **dx100-model-state-reuse / completion**: Public e4fc4af ILD: consume and invalidate offset entries and line slots; only after all lines return is a row record reset/reusable. Sent records cannot accept additions. Request may fill released space, but batch transition waits for queued packets sent and received == expected; final Fill status is re-evaluated. Completion also checks producer readiness, modeled scratchpad/table latency and empty histories/tables before destination Finished/Ready and dependent-source publication. Host synchronization remains required.
  Evidence: dx-internal-c7, dx-internal-c11.
- **dx100-model-reference-choices / buffering**: Public e4fc4af defaults include 16384 tile elements, 64 row records per slice, 8 line slots per subslice-row, 32 initial slices and 1-cycle row-table latency. Reorder is enabled; optional base-address/observed-row-count reconfiguration is disabled by default and is separate from fixed request selection. These are model defaults, not selected workload parameters or hardware timing evidence.
  Evidence: dx-internal-c12.

## Why it may help

These are conditional hypotheses, not speedup estimates or timing specifications.

- Grouping eligible accesses may reduce redundant memory requests while preserving each logical consumer.
  Basis: derived_reasoning_from_located_mechanism_not_a_measured_result.
  Conditions: Multiple reads share a group within the source-described admission window; The original result association and duplicate consumers are retained.
  Limits: Address diversity and finite group/offset capacity; Translation, cache routing and downstream service behavior.
- Source-described issue scheduling may expose independent memory work and improve useful service overlap.
  Basis: derived_reasoning_from_located_mechanism_not_a_measured_result.
  Conditions: Enough independent, ready requests under a legal mapping; Memory resources can serve the selected requests concurrently.
  Limits: Producer dependencies, admission stalls and transport backpressure; Setup/wait overhead and downstream scheduling; fairness is not implied.

## Implementation and evaluation obligations

Keep acceptance, payload readiness, memory visibility, storage reuse and CPU final effects distinct. Resolve the source contracts and these obligations before executable mapping:

- **dxc-region-binding** (Addresses touched by selected operations; not all CPU memory): Bind actual bases, registered regions, aliases and permitted writers before mapping.
- **dxc-widths** (Each mapped input tile and range composition): Prove payload, uint32 index and range bounds, signed continuation/stride and sizes fit without truncation.
- **dxc-validity** (Output lanes of masked reads/stores/RMW): Propagate masks and produced sizes; never consume inactive old-value slots as fresh values.
- **dxc-observer** (CPU consumption, memory updates and storage reuse): Establish required observer visibility and safe tile/region reuse separately from instruction finish.
- **dxc-numerical** (RMW operator, datatype and returned old values): Check duplicates and numerical equivalence for the requested result contract.
- **dxc-reuse** (Tile reuse, especially masks and aliased/wide tile storage): Before host overwrites tiles, establish which live operands consume them and a completion barrier covering those consumers; condition-only ready state is insufficient evidence.
- **dxc-old-destination** (Scalar/vector stores and RMW operations requesting old values): When old values are required, allocate and supply the optional destination tile and preserve it until all active results are consumed.
- **dxc-byte-offset** (All selected indirect loads, scalar/vector stores and RMW, including generated indices in ranged/chained sequences): Prove byte-offset product and base-address addition representability for every active indirect index. On the examined 32-bit int/uint32 ABI require word_size * index &lt; 2^32 before adding the base; 32-bit index encoding alone is insufficient.
- **dxc-capacity** (Configured tile capacity, produced lengths, uint16 size bookkeeping and callers consuming those lengths): Bind effective simulator/API tile configuration and prove every produced tile size fits its bookkeeping, alongside index/offset arithmetic and storage allocation. Do not infer a broad legal capacity range from Unsigned knobs.

Reference settings are not selected workload parameters. Parent freshness/ownership and synchronization remain requirements; a read label does not establish immutable data.

Suggested future measurements (not collected here):

- Logical read count, eligible grouping count and distinct memory request count, with exact scope
- Producer readiness, admission stalls, occupancy and independent requests outstanding
- Request issue, transport retry, response arrival, result placement and storage release as separate events
- Cache/memory route, service latency/bandwidth and address distribution under the actual configuration
- Host submission, waits, consumption and required CPU effect completion costs

## Source edition and limits

Catalog revision 0.1.10; SHA-256 1b3b6f823e4dc7930d13c7fec53d93a9e0b250fde885e0baf6c93770372390b8.

Claims, locators, URLs and source hashes are retained in the YAML. Local code or a finite illustrative scaffold does not establish every published configuration, global fairness, coherence, timing or end-to-end correctness.
