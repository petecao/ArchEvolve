# How this accelerator works

**maple-isca2022 / ISCA2022-paper+public-742a22d-inspection**

[Machine-readable behavior](hardware-behavior.yaml) · [Intrinsic draft](intrinsic-draft.yaml)

## What software asks hardware to do

Queue identities and lifecycle/binding, virtual pointers for individual fetches, or configured A/B bases plus begin/end bounds for LIMA. Software establishes producer/consumer schedule, stable arrays and memory route.

Invocation: User-mode MMIO stores issue produces/configuration and MMIO loads consume queue values, using ordinary core load/store instructions. INIT, OPEN/CLOSE, PRODUCE_PTR/CONSUME and LIMA_PRODUCE/LIMA are paper API names, not generated C declarations.

## What software must observe

### maple-lima-produce

Role: **execute**; support: **paper_specified**.

Workload targets: VertexOffsets, parent.

Result and validity: queue_value_stream; Caller must bind the iteration interval, result packing/count and consume sequence; full low-level ABI is unknown.

Ordering/association: Queue values retain reserved-slot/program association despite out-of-order replies; no global inter-queue or update order is established.

Completion: Consume returns the queued value; pointer-produce acknowledgement precedes fetch completion. LIMA-wide drain/completion details need mapping evidence.

Visibility: Queue values obey the stable-array and selected memory-route contract; they are not kept coherent after fetch.

### maple-pointer-fetch

Role: **execute**; support: **paper_specified**.

Workload targets: VertexOffsets, parent.

Result and validity: queue_value_stream; Consume corresponding queued data under exclusive binding, slot availability and stable-target conditions.

Ordering/association: Queue values retain reserved-slot/program association despite out-of-order replies; no global inter-queue or update order is established.

Completion: Consume returns the queued value; pointer-produce acknowledgement precedes fetch completion. LIMA-wide drain/completion details need mapping evidence.

Visibility: Queue values obey the stable-array and selected memory-route contract; they are not kept coherent after fetch.

### maple-lima-range

Role: **execute**; support: **paper_specified**.

Workload targets: g.out_neighbors_.

Result and validity: queue_value_stream; Bind the supplied begin/end range and word packing; this is not proof of autonomous nested row traversal.

Ordering/association: Queue values retain reserved-slot/program association despite out-of-order replies; no global inter-queue or update order is established.

Completion: Consume returns the queued value; pointer-produce acknowledgement precedes fetch completion. LIMA-wide drain/completion details need mapping evidence.

Visibility: Queue values obey the stable-array and selected memory-route contract; they are not kept coherent after fetch.

### maple-lima-stream

Role: **execute**; support: **paper_specified**.

Workload targets: queue.shared.

Result and validity: queue_value_stream; Bind the supplied begin/end range and word packing; this is not proof of autonomous nested row traversal.

Ordering/association: Queue values retain reserved-slot/program association despite out-of-order replies; no global inter-queue or update order is established.

Completion: Consume returns the queued value; pointer-produce acknowledgement precedes fetch completion. LIMA-wide drain/completion details need mapping evidence.

Visibility: Queue values obey the stable-array and selected memory-route contract; they are not kept coherent after fetch.

## Internal mechanism

Located edition-specific descriptions; annotation list is not an executable state machine or complete timing policy.

- **maple-queues / buffering**: Circular FIFOs share scratchpad. Full-queue produces and empty-queue consumes wait in buffered pipelines; configuration remains available.
  Evidence: maple-backpressure, maple-reference-config.
- **maple-index-chunks / buffering**: LIMA fetches adjacent B-index data in 64-byte chunks and iterates through those words to generate A addresses.
  Evidence: maple-lima.
- **maple-response-association / reordering**: Reserved queue slot indices are used as transaction IDs. Replies may arrive out of order but are placed into their associated FIFO slots for ordered consumption; this is response association, not a demonstrated DRAM-locality sort.
  Evidence: maple-queue-order.
- **maple-pipelined-issue / issue_policy**: Separate produce/consume/configuration pipelines permit concurrent operations. LIMA feeds generated requests into the produce path; a blocked queue need not stall other queues. No locality-aware A-address sorting policy is specified.
  Evidence: maple-backpressure, maple-lima.
- **maple-host-dependencies / dependency_tracking**: Software produces pointers or configures one-level LIMA intervals; queued replies retain slot identity. Dependencies needed to compute pointers/bounds stay in software unless the described LIMA operation covers them.
  Evidence: maple-api, maple-lima, maple-queue-order.
- **maple-two-stage-completion / completion**: The issue store acknowledgement occurs before the fetched memory data arrives; a consumer receives its data only on the queue-consume load response.
  Evidence: maple-acknowledgement.
- **maple-pinned-head-readiness / buffering**: In public RTL 742a22d's ordinary non-invalidation consume path, reservation/occupancy and valid payload are separate. The head and any additional piece required by the consume length must be valid before dequeue; ready later values do not bypass an unready head. Paper-evaluation configuration binding remains unknown.
  Evidence: maple-code-head-readiness.
- **maple-pinned-credit-transfer / completion**: In public RTL 742a22d's ordinary consume path, successful dequeue returns queue storage capacity with payload capture in the consume pipeline, before possible later NoC response delivery and CPU arithmetic. Admission, payload readiness, pipeline custody and CPU final use have distinct resource lifetimes.
  Evidence: maple-code-dequeue-custody.
- **maple-target-coalescing / coalescing**: unknown in this source-scoped handoff
  Evidence: none; do not infer support.
- **integration-maple-comparison_domain / other**: unknown in this source-scoped handoff
  Evidence: none; do not infer support.
- **integration-maple-completion / completion**: completion: {"CLOSE": "endpoint_disconnect_not_universal_drain", "command_ACK": "not_value_ready", "internal_LIMA_pointer_ACK": "individual_CPU_ACK_suppressed"}; basis=source_with_limit; source-scoped, no operation-support widening
  Evidence: integration-maple-P1, integration-maple-P5, integration-maple-A3, integration-maple-A6.
- **integration-maple-credit / buffering**: credit: {"CPU_final_effect": "separate_obligation", "release": "consume_capture_dequeue", "reserve": "owns_not_ready"}; basis=source_plus_consumer_obligation; source-scoped, no operation-support widening
  Evidence: integration-maple-P1, integration-maple-A2, integration-maple-A3.
- **integration-maple-grouping / buffering**: grouping: {"final_A_address_sort": "not_established", "final_A_duplicate_merge": "unknown", "index": "B_spatial_chunks"}; basis=source_plus_explicit_unknown; source-scoped, no operation-support widening
  Evidence: integration-maple-P3, integration-maple-A5.
- **integration-maple-interface / other**: interface: {"consumer": "MMIO_CONSUME", "delivery": "queue_operand", "producer": "bounded_range_submission"}; basis=source; source-scoped, no operation-support widening
  Evidence: integration-maple-P1, integration-maple-P2, integration-maple-A1b.
- **integration-maple-memory_routes / other**: memory_routes: {"choices": ["coherent_LLC", "direct_DRAM"], "later_queue_value_coherence": "not_guaranteed"}; basis=source_with_limit; source-scoped, no operation-support widening
  Evidence: integration-maple-P1, integration-maple-P5.
- **integration-maple-operation / other**: operation: {"consumer_arithmetic": "CPU", "expression": "A[B[i]]", "kind": "required_LIMA_PRODUCE"}; basis=source; source-scoped, no operation-support widening
  Evidence: integration-maple-P2, integration-maple-A1, integration-maple-A1b.
- **integration-maple-response / reordering**: response: {"arrival": "may_be_out_of_order", "association": "reserved_slot_transaction_id", "delivery": "per_queue_valid_head_FIFO", "global_queue_order": "not_claimed"}; basis=source; source-scoped, no operation-support widening
  Evidence: integration-maple-P1, integration-maple-A2, integration-maple-A4.
- **integration-maple-scheduling / issue_policy**: scheduling: {"arbitration": "eligible_queue_round_robin_in_inspected_paths", "global_fairness": "not_proven"}; basis=supplemental_source_with_limit; source-scoped, no operation-support widening
  Evidence: integration-maple-A3, integration-maple-A5.
- **integration-maple-state / buffering**: state: {"capacity": "configuration_specific_finite", "range_admission": "unlimited_unestablished", "storage": "partitioned_circular_reserved_valid_FIFO"}; basis=source; source-scoped, no operation-support widening
  Evidence: integration-maple-P3, integration-maple-A2, integration-maple-A5, integration-maple-A6.
- **integration-maple-translations / other**: translations: {"fault_shootdown_integration": "deployment_required", "local_TLB_PTW": "described"}; basis=source_with_limit; source-scoped, no operation-support widening
  Evidence: integration-maple-P4.
- **integration-maple-unknowns / other**: unknown in this source-scoped handoff
  Evidence: none; do not infer support.
- **integration-maple-width / other**: width: {"executable_illustration_bytes": 4, "inspected_payload_bytes": [4, 8]}; basis=supplemental_source; source-scoped, no operation-support widening
  Evidence: integration-maple-A3, integration-maple-A5.

## Why it may help

These are conditional hypotheses, not speedup estimates or timing specifications.

- Queue-backed asynchronous fetches may hide long memory latency when useful runahead and concurrent requests exceed producer/consumer communication costs.
  Basis: catalog_conditional_hypothesis.
  Conditions: Stable source arrays and a legal producer/consumer split; Enough independent requests and queue space for runahead; Useful lookahead and compatible pointer/index/queue formats.
  Limits: NoC/MMIO consume round-trip overhead; Queue-full/empty stalls, dependent address computation and translation misses; BFS mutable parent data fails the stable-array requirement without an additional mapping proof.

## Implementation and evaluation obligations

Keep acceptance, payload readiness, memory visibility, storage reuse and CPU final effects distinct. Resolve the source contracts and these obligations before executable mapping:

- **maple-stable-target** (All queue-fetched target arrays and any index data used for address generation): Establish stable data and ownership from fetch through consumption; a coherent request cannot refresh an already queued value after a CPU write.
- **maple-queue-lifecycle** (Per queue and participating software threads): Bind/init/open/close queues exclusively as required and establish producer/consumer counts, ordering, storage reuse and a nondeadlocking runahead schedule.
- **maple-typed-abi** (Pointers, A/B element formats, bounds, packed queue values and API operands): Resolve concrete payload/index/pointer types, element scaling, valid ranges, result packing and counts; paper-level operation names are not complete C signatures.
- **maple-source-binding** (Per BFS statement and ROI): Choose pointer-produce or LIMA mode and demonstrate source operand/interval correspondence; supplied bounds do not offload the full queue-to-CSR dependency chain.
- **maple-completion** (Fetch acceptance, queue value readiness, drain and memory observers): Distinguish pointer-produce acknowledgement from available fetched data, consuming a value, draining a loop and any required observer barrier.
- **maple-platform** (MMIO resource allocation, virtual address translation and memory path): Provide compatible NoC/MMIO integration, driver/MMU/shootdown support and chosen coherent LLC or noncoherent memory route.
- **maple-cpu-updates** (Current BFS parent CAS, parent store and queue append): Retain CPU updates and success-controlled side effects unless separate evidence establishes a supported atomic engine and equivalent mapping.

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
