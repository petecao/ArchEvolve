# Peter's measurement-method explanation: interpretation update

The supplied explanation is saved unchanged in [the received text](../examples/received/peter-measurement-methodology.txt). Its structured interpretation is [the methodology record](../examples/received/peter-measurement-methods.yaml), bound to the exact hashes of the two received v1.1 feature reports. This is an explanation of reported instrumentation, not a reproduced run.

## What is resolved

- Footprints were computed from array element counts and declared type sizes. These are logical array-capacity bytes, not measured resident memory or a tile/phase-scoped active working set.
- The `same line/page` labels count whether adjacent index values differ by at most a threshold. They are adjacent-pair proximity statistics, not cache-hit rates or exact block-membership counts.
- Queue pairs are taken within the current frontier. Neighbor pairs are taken within one vertex's adjacency row; the shown loop omits row transitions. The snippets do not trace the global multithreaded memory-access order.
- Peter explicitly reports 4-byte NodeID and 8-byte SGOffset for his source. Our pinned DX100 reference uses 4-byte SGOffset; the exact profiled fork/revision is still needed to bind his report to code.

## Why the locality labels need to change

With an aligned array of 8-byte elements and a 64-byte cache line, indices 7 and 8 refer to byte offsets 56 and 64. Their index distance is 1, which satisfies `diff <= 8`, yet the addresses belong to different cache lines.

The actual address-block test is:

```text
address1 = base_address + index1 * element_bytes
address2 = base_address + index2 * element_bytes
same_block = floor(address1 / block_bytes) == floor(address2 / block_bytes)
```

Use 64 for the stated line size or 4096 for the stated page size. This establishes address-block membership, not a cache hit: hit behavior also depends on history and execution. The existing instrumentation remains useful if labeled `fraction of adjacent pairs within 64 bytes` or `within 4096 bytes`.

The prototype now adds `adjacent_pair_proximity` and explicit pair-scope fields to normalized data. It preserves original labels in the received input, does not invent exact block counts, and still excludes these percentages from its candidate-priority rules. Mean distances retain their reported pair scope.

## Unit inconsistency

The explanation says all KB/MB values use binary divisors, but several sparse-graph values match decimal divisors. Canonical bytes avoid this ambiguity:

| Case | Parent bytes | Parent MiB | Parent MB | Neighbor MiB | Neighbor MB |
|---|---:|---:|---:|---:|---:|
| Fully connected K25000 | 100,000 | 0.095367 | 0.100000 | 2384.090424 | 2499.900000 |
| Sparse g18 | 1,048,572 | 0.999996 | 1.048572 | 29.033272 | 30.443592 |
| Sparse g21 | 8,388,600 | 7.999992 | 8.388600 | 242.375114 | 254.148728 |
| Sparse g24 | 67,108,848 | 63.999985 | 67.108848 | 1986.516647 | 2083.013680 |

For example, the reported g18 parent footprint of 1.05 MB is the rounded decimal value. The same 1,048,572 bytes are approximately 1.00 MiB. The dense report's 97.66 KB parent value is instead approximately 97.66 KiB. These mixed conventions should not be treated as one binary-unit table.

The adapter derives exact capacity bytes and explicit kB/MB/KiB/MiB values using the supplied counts and type widths. It separately compares the original rounded values to the two conversion conventions. It never overwrites the original report, treats derived capacity as measured residency, or chooses a hardware storage size from these calculations.

The optional methodology record is applied only when it names the exact input hash. Its hash is also part of run identity, and it is snapshotted with the output. A different report requires an explicit methodology binding.

## Still open

The profiled source commit/hash, build/run commands, raw logs, and aggregation across BFS levels/threads remain to be supplied. The source-method interpretation is now clear; there is no need to repeat the earlier request for a general explanation of these metrics.

This change does not affect the current offline exploration order or create an evaluated accelerator result.
