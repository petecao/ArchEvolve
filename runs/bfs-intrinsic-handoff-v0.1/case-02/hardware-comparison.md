# Hardware interface comparison

Same typed requests, source contracts and mechanism gaps. No performance ranking or legal combined mapping.

Eric's newly selected second fetcher is pending. Existing designs can be inspected here; assistance is a different role from returned-load execution. Missing mechanism data prevents a scheduling/performance comparison.

| Design | Conditional read matches | Assistance matches | Reads needing evidence | Internal details missing |
|---|---|---|---|---|
| dx100-artifact-e4fc4af | access-01-read, access-02-read, access-03-read, access-04-read | none | none | buffering, coalescing, reordering, issue_policy, dependency_tracking, completion |
| spzip-isca2021-push | none | access-02-read, access-04-read | access-02-read, access-03-read, access-04-read | buffering, coalescing, reordering, issue_policy, dependency_tracking, completion |
| prodigy-hpca2021 | none | access-02-read, access-03-read, access-04-read | access-02-read, access-03-read, access-04-read | buffering, coalescing, reordering, issue_policy, dependency_tracking, completion |

## dx100-artifact-e4fc4af

Pinned gem5/API implementation with observed reads, masks, range continuation and optional pre-update result tiles.

Inputs: Memory-mapped instruction stream, bases, typed scalar/vector tiles, optional mask and old-value destination. Range continuation registers and lower/upper bound tiles for range composition.

Invocation: Pinned MAA_gem5.hpp calls encode instructions and issue fences; wait_ready is a held mapped status read followed by mfence in the inspected core-0 interface.

Outputs: Input-associated fetched/old values in scratchpad tiles; range indices; memory writes.

| Request | Matching operation / status / role | Exclusions |
|---|---|---|
| access-01-read | dxc-stream_load / conditional_executor / execute | none |
| access-02-read | dxc-gather / conditional_executor / execute | dxc-chained-gather: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim.; dxc-ranged-gather: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim. |
| access-03-read | dxc-ranged-gather / conditional_executor / execute | dxc-chained-gather: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim.; dxc-gather: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim. |
| access-04-read | dxc-gather / conditional_executor / execute | dxc-chained-gather: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim.; dxc-ranged-gather: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim. |
| access-04-update | no match | dxc-cas: Explicitly unsupported in this examined configuration/path. |

## spzip-isca2021-push

DCL fetcher supplies compressed traversal streams but only prefetches shared destination data; CPU performs destination atomics.

Inputs: DCL queue/operator contexts describing data traversal and optional compression, plus stream inputs.

Invocation: Configure contexts through memory-mapped I/O; enqueue input ranges/values and dequeue output streams.

Outputs: Fetched/decompressed streams and markers; destination prefetches.

| Request | Matching operation / status / role | Exclusions |
|---|---|---|
| access-01-read | no match | spzip-destination-prefetch: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim. |
| access-02-read | spzip-destination-prefetch / needs_evidence / assist | spzip-neighbors: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim. |
| access-03-read | spzip-neighbors / needs_evidence / execute | spzip-destination-prefetch: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim. |
| access-04-read | spzip-destination-prefetch / needs_evidence / assist | spzip-neighbors: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim. |
| access-04-update | no match | none |

## prodigy-hpca2021

Per-core nonbinding prefetcher guided by software-described data structures and single-valued/ranged traversal edges.

Inputs: Data Indirection Graph with array layout, dependency edges and triggers; no accelerator instruction stream.

Invocation: Runtime stores configure memory-mapped tables; demand accesses and fills drive prefetching.

Outputs: Nonbinding cache fills; CPU still executes the program and its updates.

| Request | Matching operation / status / role | Exclusions |
|---|---|---|
| access-01-read | no match | prod-prefetch: Requested address pattern is not in this record; absence is not a universal hardware impossibility claim. |
| access-02-read | prod-prefetch / needs_evidence / assist | none |
| access-03-read | prod-prefetch / needs_evidence / assist | none |
| access-04-read | prod-prefetch / needs_evidence / assist | none |
| access-04-update | no match | none |

[Full comparison YAML](hardware-comparison.yaml) retains operation/type constraints, located evidence, parameters and mapping requirements.

To compare a newly curated design, supply repeated `--compare-design` IDs with the DX100 reference. Comparison retrieval is independent of the diagram candidate budget.
