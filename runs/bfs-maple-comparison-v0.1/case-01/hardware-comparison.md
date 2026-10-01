# Hardware interface comparison

Same typed requests, source contracts and mechanism gaps. No performance ranking or legal combined mapping.

Eric's selected second fetcher is maple-isca2022. Status: cataloged_paper_evidence_mapping_and_types_pending. Assistance is a different role from returned-load execution. Internal annotations explain available mechanisms; missing mechanism/model data remains explicit.

| Design | Conditional read matches | Assistance matches | Reads needing evidence | Internal details missing |
|---|---|---|---|---|
| dx100-artifact-e4fc4af | access-01-read, access-02-read, access-03-read, access-04-read | none | none | buffering, coalescing, reordering, issue_policy, dependency_tracking, completion |
| maple-isca2022 | none | access-01-read, access-02-read, access-03-read, access-04-read | access-01-read, access-02-read, access-03-read, access-04-read | coalescing |

## dx100-artifact-e4fc4af

Pinned gem5/API implementation with observed reads, masks, range continuation and optional pre-update result tiles.

Inputs: Memory-mapped instruction stream, bases, typed scalar/vector tiles, optional mask and old-value destination. Range continuation registers and lower/upper bound tiles for range composition.

Invocation: Pinned MAA_gem5.hpp calls encode instructions and issue fences; wait_ready is a held mapped status read followed by mfence in the inspected core-0 interface.

Outputs: Input-associated fetched/old values in scratchpad tiles; range indices; memory writes.

### Internal mechanism evidence

- **buffering**: unknown; not recorded
- **coalescing**: unknown; not recorded
- **reordering**: unknown; not recorded
- **issue_policy**: unknown; not recorded
- **dependency_tracking**: unknown; not recorded
- **completion**: unknown; not recorded

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
- **coalescing**: unknown; not recorded

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
