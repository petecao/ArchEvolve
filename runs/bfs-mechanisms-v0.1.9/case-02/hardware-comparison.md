# Hardware interface comparison

Same typed requests, source contracts and mechanism gaps. No performance ranking or legal combined mapping.

Eric's selected second fetcher is maple-isca2022. Status: cataloged_paper_evidence_mapping_and_types_pending. Assistance is a different role from returned-load execution. Internal annotations explain available mechanisms; missing mechanism/model data remains explicit.

| Design | Conditional read matches | Assistance matches | Reads needing evidence | Internal details missing |
|---|---|---|---|---|
| dx100-artifact-e4fc4af | access-01-read, access-02-read, access-03-read, access-04-read | none | none | none in checklist; model still needed |
| maple-isca2022 | none | access-01-read, access-02-read, access-03-read, access-04-read | access-01-read, access-02-read, access-03-read, access-04-read | coalescing |

## dx100-artifact-e4fc4af

Pinned gem5/API implementation with observed reads, masks, range continuation and optional pre-update result tiles.

Inputs: Memory-mapped instruction stream, bases, typed scalar/vector tiles, optional mask and old-value destination. Range continuation registers and lower/upper bound tiles for range composition.

Invocation: Pinned MAA_gem5.hpp calls encode instructions and issue fences; wait_ready is a held mapped status read followed by mfence in the inspected core-0 interface.

Outputs: Input-associated fetched/old values in scratchpad tiles; range indices; memory writes.

### Internal mechanism evidence

- **dependency_tracking**: Public e4fc4af ILD: IF rejects full instruction storage, destination-tile conflicts and specified same-range read/write conflicts within maa_id. Ready selection scans from a random offset and accepts Service/Finished source status; Fill still waits at unfinished condition/index elements in original iteration order. These checks do not establish all aliases or fairness.
- **buffering**: Public e4fc4af ILD: form base + word_size * uint32 index, check virtual bounds, translate aligned blocks and decode configured Ramulator2 physical geometry into slice/grow keys. Unsent row records contain aligned physical lines; same-row overflow can use another record. Finite capacity failure retains the failed iteration. Geometry and merged-bank organization are configuration-dependent.
- **coalescing**: Public e4fc4af ILD: a matching unsent line appends another (original iteration, word offset) in a forward next_itr list using first/last pointers without consuming another line slot. Duplicate words retain separate consumers. Compatible reads across units may also share a Port packet and waiter list; same-unit duplicate outstanding reads are rejected.
- **issue_policy**: Public e4fc4af with reorder enabled: final Fill or insertion failure enters Build; a producer wait alone does not. Each pass emits at most one line per active slice, channel fastest then rank, bank group, bank. Within a slice, scan row/line slots and other records of the same grow before another grow. Selection neither sorts addresses nor consults DRAM open-row state.
- **issue_policy**: Public e4fc4af: new packets snoop at creation unless forced to cache. Eligibility-tick queues are grouped by channel/cache bus; writes precede reads, and cache indirect classes precede stream classes. Failed sends retain queued work and block that channel/bus until retry or capacity release. Generator order does not guarantee downstream DRAM command order or fairness.
- **reordering**: Public e4fc4af ILD: decode response physical line to slice/grow, consume its associations and sort those by itr, then write each returned word[wid] to TD[itr], including duplicate-word fanout. Sorting is within one response, not outgoing address sorting or global response ordering.
- **completion**: Public e4fc4af ILD: consume and invalidate offset entries and line slots; only after all lines return is a row record reset/reusable. Sent records cannot accept additions. Request may fill released space, but batch transition waits for queued packets sent and received == expected; final Fill status is re-evaluated. Completion also checks producer readiness, modeled scratchpad/table latency and empty histories/tables before destination Finished/Ready and dependent-source publication. Host synchronization remains required.
- **buffering**: Public e4fc4af defaults include 16384 tile elements, 64 row records per slice, 8 line slots per subslice-row, 32 initial slices and 1-cycle row-table latency. Reorder is enabled; optional base-address/observed-row-count reconfiguration is disabled by default and is separate from fixed request selection. These are model defaults, not selected workload parameters or hardware timing evidence.

### Exact request matches

| Request | Matching operation / status / role / support | Exclusions |
|---|---|---|
| access-01-read | dxc-stream_load / conditional_executor / execute / code_observed | none |
| access-02-read | dxc-gather / conditional_executor / execute / code_observed | dxc-chained-gather: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim.; dxc-ranged-gather: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim. |
| access-03-read | dxc-ranged-gather / conditional_executor / execute / code_observed | dxc-chained-gather: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim.; dxc-gather: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim. |
| access-04-read | dxc-gather / conditional_executor / execute / code_observed | dxc-chained-gather: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim.; dxc-ranged-gather: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim. |
| access-04-update | no match | dxc-cas: Explicitly unsupported in this examined configuration/path. |

## maple-isca2022

NoC-connected MMIO engine provides asynchronous pointer/loop fetches into ordered queues, or speculative LLC hints. Pipelining and runahead hide latency; CPU performs computation and updates.

Inputs: Queue identities and lifecycle/binding, virtual pointers for individual fetches, or configured A/B bases plus begin/end bounds for LIMA. Software establishes producer/consumer schedule, stable arrays and memory route.

Invocation: User-mode MMIO stores issue produces/configuration and MMIO loads consume queue values, using ordinary core load/store instructions. INIT, OPEN/CLOSE, PRODUCE_PTR/CONSUME and LIMA_PRODUCE/LIMA are paper API names, not generated C declarations.

Outputs: FIFO-delivered fetched values for queue mode, or nonbinding shared-LLC fills for speculative prefetch mode. CPU remains responsible for computation and updates.

### Internal mechanism evidence

- **buffering**: Circular FIFOs share scratchpad. Full-queue produces and empty-queue consumes wait in buffered pipelines; configuration remains available.
- **buffering**: LIMA fetches adjacent B-index data in 64-byte chunks and iterates through those words to generate A addresses.
- **reordering**: Reserved queue slot indices are used as transaction IDs. Replies may arrive out of order but are placed into their associated FIFO slots for ordered consumption; this is response association, not a demonstrated DRAM-locality sort.
- **issue_policy**: Separate produce/consume/configuration pipelines permit concurrent operations. LIMA feeds generated requests into the produce path; a blocked queue need not stall other queues. No locality-aware A-address sorting policy is specified.
- **dependency_tracking**: Software produces pointers or configures one-level LIMA intervals; queued replies retain slot identity. Dependencies needed to compute pointers/bounds stay in software unless the described LIMA operation covers them.
- **completion**: The issue store acknowledgement occurs before the fetched memory data arrives; a consumer receives its data only on the queue-consume load response.
- **buffering**: In public RTL 742a22d's ordinary non-invalidation consume path, reservation/occupancy and valid payload are separate. The head and any additional piece required by the consume length must be valid before dequeue; ready later values do not bypass an unready head. Paper-evaluation configuration binding remains unknown.
- **completion**: In public RTL 742a22d's ordinary consume path, successful dequeue returns queue storage capacity with payload capture in the consume pipeline, before possible later NoC response delivery and CPU arithmetic. Admission, payload readiness, pipeline custody and CPU final use have distinct resource lifetimes.
- **coalescing**: unknown; not recorded
- **other**: unknown; not recorded
- **completion**: completion: {"CLOSE": "endpoint_disconnect_not_universal_drain", "command_ACK": "not_value_ready", "internal_LIMA_pointer_ACK": "individual_CPU_ACK_suppressed"}; basis=source_with_limit; source-scoped, no operation-support widening
- **buffering**: credit: {"CPU_final_effect": "separate_obligation", "release": "consume_capture_dequeue", "reserve": "owns_not_ready"}; basis=source_plus_consumer_obligation; source-scoped, no operation-support widening
- **buffering**: grouping: {"final_A_address_sort": "not_established", "final_A_duplicate_merge": "unknown", "index": "B_spatial_chunks"}; basis=source_plus_explicit_unknown; source-scoped, no operation-support widening
- **other**: interface: {"consumer": "MMIO_CONSUME", "delivery": "queue_operand", "producer": "bounded_range_submission"}; basis=source; source-scoped, no operation-support widening
- **other**: memory_routes: {"choices": ["coherent_LLC", "direct_DRAM"], "later_queue_value_coherence": "not_guaranteed"}; basis=source_with_limit; source-scoped, no operation-support widening
- **other**: operation: {"consumer_arithmetic": "CPU", "expression": "A[B[i]]", "kind": "required_LIMA_PRODUCE"}; basis=source; source-scoped, no operation-support widening
- **reordering**: response: {"arrival": "may_be_out_of_order", "association": "reserved_slot_transaction_id", "delivery": "per_queue_valid_head_FIFO", "global_queue_order": "not_claimed"}; basis=source; source-scoped, no operation-support widening
- **issue_policy**: scheduling: {"arbitration": "eligible_queue_round_robin_in_inspected_paths", "global_fairness": "not_proven"}; basis=supplemental_source_with_limit; source-scoped, no operation-support widening
- **buffering**: state: {"capacity": "configuration_specific_finite", "range_admission": "unlimited_unestablished", "storage": "partitioned_circular_reserved_valid_FIFO"}; basis=source; source-scoped, no operation-support widening
- **other**: translations: {"fault_shootdown_integration": "deployment_required", "local_TLB_PTW": "described"}; basis=source_with_limit; source-scoped, no operation-support widening
- **other**: unknown; not recorded
- **other**: width: {"executable_illustration_bytes": 4, "inspected_payload_bytes": [4, 8]}; basis=supplemental_source; source-scoped, no operation-support widening

### Conditional performance hypotheses

- Queue-backed asynchronous fetches may hide long memory latency when useful runahead and concurrent requests exceed producer/consumer communication costs.
  Conditions: Stable source arrays and a legal producer/consumer split; Enough independent requests and queue space for runahead; Useful lookahead and compatible pointer/index/queue formats.
  Limits: NoC/MMIO consume round-trip overhead; Queue-full/empty stalls, dependent address computation and translation misses; BFS mutable parent data fails the stable-array requirement without an additional mapping proof.

### Exact request matches

| Request | Matching operation / status / role / support | Exclusions |
|---|---|---|
| access-01-read | maple-lima-prefetch / needs_evidence / assist / paper_specified; maple-lima-stream / needs_evidence / execute / paper_specified | maple-pointer-prefetch: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim. |
| access-02-read | maple-lima-prefetch / needs_evidence / assist / paper_specified; maple-lima-produce / needs_evidence / execute / paper_specified; maple-pointer-fetch / needs_evidence / execute / paper_specified; maple-pointer-prefetch / needs_evidence / assist / paper_specified | maple-lima-range: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim. |
| access-03-read | maple-lima-prefetch / needs_evidence / assist / paper_specified; maple-lima-range / needs_evidence / execute / paper_specified | maple-lima-produce: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim.; maple-pointer-fetch: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim.; maple-pointer-prefetch: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim. |
| access-04-read | maple-lima-prefetch / needs_evidence / assist / paper_specified; maple-lima-produce / needs_evidence / execute / paper_specified; maple-pointer-fetch / needs_evidence / execute / paper_specified; maple-pointer-prefetch / needs_evidence / assist / paper_specified | maple-lima-range: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim. |
| access-04-update | maple-cas / needs_evidence / execute / unknown | none |

[Full comparison YAML](hardware-comparison.yaml) retains operation/type constraints, located evidence, parameters and mapping requirements.

To compare a newly curated design, supply repeated `--compare-design` IDs with the DX100 reference. Comparison retrieval is independent of the diagram candidate budget.
