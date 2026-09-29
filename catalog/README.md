# Provisional hardware catalog seed

`seed.yaml` is a small local catalog constructed from Eric's taxonomy documents. **It is not Eric's delivered machine-readable catalog and has not been reviewed as an implementation specification.**

The text snapshots in `sources/` preserve the document wording used for this seed; hashes and source links are in the catalog. Draft 3's embedded diagrams are not present in its text export. The seed uses family groupings from the project review and Draft 2's axes, rather than claiming to import every graph node automatically.

Five entries are included:

- Existing CPU execution as an unmeasured comparison baseline.
- Indirect prefetch family.
- Declared gather/read family.
- Stride prefetch family.
- Declared bulk-read family.

Each record has an ID/revision, taxonomy references, applicability signals, a provisional hardware boundary sketch, conditions to establish, and open parameters. The block partitions and ports were authored for this prototype. They are not verified IMP, DMP, DMA, or DX100 implementations.

All seed mechanisms retain the original CPU update behavior. Declared-read candidates exclude the mutable `parent` stream from their targets. This restriction does not itself prove correctness: source bindings, aliasing, coherence, and actual interfaces still need review.

## Offline selection policy

The selector walks the records and logs every decision. It retains eligible entries, places the CPU baseline first, then gives priority to matching reported features. The default budget includes the baseline plus two exploratory alternatives.

- A reported mean index jump of at least 16 elements marks a large-jump signal for this prototype.
- If all supplied indexed-stream means are at most 1.1 elements, a near-unit signal is set.
- Missing statistics remain unknown.

These are adjustable ordering heuristics, not measured speedup estimates or calibrated bottleneck rules. Candidates outside the budget remain in the trace as eligible alternatives. Hardware-implication prose and alleged cache-hit percentages are excluded from these rules.

## Extending the catalog

Add a versioned record with a unique ID, supported selection signals, explicit evidence status, I/O graph, and unresolved requirements. `validate_catalog` and the diagram validator check the supported structure and graph references. A new record can then participate without changing the selection loop.

The supported signals and target policies form a small, intentional interface; new kinds of workload evidence need a corresponding normalizer/selector change. Merely adding a field does not create a new capability.

Experiments should remain separate records with input/catalog/code hashes. A tested parameter value does not automatically become a new taxonomy branch. Proposing and reviewing genuinely new capabilities is future work; this offline prototype does not mutate the trusted catalog or promote claims automatically.
