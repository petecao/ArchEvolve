# MAPLE: the second fetcher

Eric selected [Tiny but Mighty: Designing and Realizing Scalable Latency Tolerance for Manycore SoCs](https://jbalkind.github.io/docs/isca2022_maple.pdf), ISCA 2022, DOI `10.1145/3470496.3527400`. The author-hosted 14-page PDF is hashed in `catalog/hardware-v0.1.yaml` as `maple-paper`. The raw PDF and page renders are local ignored review material in `.cache/papers/`; no binary or full-paper text is committed.

This source-reviewed MAPLE addition is catalog data revision **0.1.3**. It was authored from the supplied paper; Eric/Peter still need to review its mapping and typed API. No MAPLE implementation was run. Earlier six design records and their claims are preserved unchanged.

## Start here

| Workload | MAPLE queue-fetch description | Queue-fetch diagrams | MAPLE LLC assistance | Comparison |
|---|---|---|---|---|
| Sparse BFS | [Draft](../runs/bfs-maple-comparison-v0.1/case-01/handoffs/candidate-04/README.md), [YAML](../runs/bfs-maple-comparison-v0.1/case-01/handoffs/candidate-04/intrinsic-draft.yaml) | [Preview](../runs/bfs-maple-comparison-v0.1/case-01/handoffs/candidate-04/previews.md), [paper paths](../runs/bfs-maple-comparison-v0.1/case-01/handoffs/candidate-04/structure.mmd) | [Draft](../runs/bfs-maple-comparison-v0.1/case-01/handoffs/candidate-03/README.md) | [DX100/MAPLE](../runs/bfs-maple-comparison-v0.1/case-01/hardware-comparison.md) |
| Fully connected BFS | [Draft](../runs/bfs-maple-comparison-v0.1/case-02/handoffs/candidate-04/README.md), [YAML](../runs/bfs-maple-comparison-v0.1/case-02/handoffs/candidate-04/intrinsic-draft.yaml) | [Preview](../runs/bfs-maple-comparison-v0.1/case-02/handoffs/candidate-04/previews.md), [paper paths](../runs/bfs-maple-comparison-v0.1/case-02/handoffs/candidate-04/structure.mmd) | [Draft](../runs/bfs-maple-comparison-v0.1/case-02/handoffs/candidate-03/README.md) | [DX100/MAPLE](../runs/bfs-maple-comparison-v0.1/case-02/hardware-comparison.md) |

Each case also has a DX100 read package at `candidate-02`. MAPLE's queue mode is a returned-value path; its speculative LLC mode is assistance. They remain separate options within one parameterized design entry.

## The useful contrast

| Boundary | DX100 artifact | MAPLE paper |
|---|---|---|
| Software submission | Instruction/tile/mask operands | Pointer produces or configured LIMA array bases and interval; MMIO queue lifecycle |
| Read results | Scratchpad tiles associated with iteration slots | Fetched values consumed from reserved FIFO slots |
| Described internal mechanism | Existing operation/result/configuration evidence; full internal scheduling annotations remain unrecorded | Independent pipelines, queue buffering/backpressure, parallel fetches and slot-ID response association |
| Loop-address generation | Documented range-generator plus gather sequence | One-level A[B[i]] interval; A=0 for B[i]; host supplies the interval |
| Completion | Per-instruction/tile completion and observer/reuse obligations | Produce acknowledgement precedes fetched-data readiness; CONSUME returns available queue data |
| Mutable target | Ownership/freshness mapping must be established | Queued data is not kept coherent after fetch; stable fetched arrays are required |
| BFS updates | Inspected artifact CAS unsupported | No current CAS contract; atomics are discussed as an extension |

The MAPLE mechanism is latency tolerance through asynchronous supply and producer runahead. Its transaction IDs associate out-of-order replies with reserved slots; this does not establish sorting target addresses by DRAM locality. LIMA reads its index stream in 64-byte chunks, which does not prove merging unrelated target addresses. `coalescing` remains explicitly unknown. The DX100 column is limited to its existing catalog evidence; missing annotations are not a claim that DX100 lacks internal scheduling.

### Software-facing options

- **Pointer fetch:** the host computes a target pointer, issues `PRODUCE_PTR`, and later obtains the value using `CONSUME`. This documented sequence does not offload host pointer arithmetic.
- **LIMA indexed queue fetch:** configure A/B and the interval, then use `LIMA_PRODUCE` and consume the resulting values for A[B[i]].
- **LIMA stream/range queue fetch:** A=0 supplies B[i]. For BFS neighbor rows, software must still obtain the CSR bounds and submit each required interval; a native nested frontier-to-CSR traversal is not established.
- **LLC assistance:** `LIMA` and pointer `PREFETCH` request nonbinding shared-cache fills. CPU demand loads and updates still determine program results.

These are paper API descriptions, not generated C prototypes. Exact payload/index/pointer types, word packing, operand scaling, lengths and drain behavior remain unknown. The reported four-byte evaluation words and RISCV64 core do not establish the complete API type domains, so typed BFS matches stay `needs_evidence`.

### BFS mapping limits

Start by considering stable graph arrays and phase-stable frontier ranges. The catalog can identify potential operations, but a compatible queue/LIMA implementation and legal source mapping remain to be proved.

The parent read is coupled to concurrent CAS in the current TDStep. MAPLE's stable-array rule prevents treating that queued read as automatically legal. A coherent LLC fetch does not refresh a value already stored in a queue. Preserve CAS, its explicit successful-branch store, and queue append on the CPU while resolving the chosen read/assistance mapping. Epoch-stable algorithms in the paper are not an equivalence proof for this TDStep.

Queue capacity, producer runahead, data dependencies, translation overhead and core-to-engine round-trip cost are inputs for future performance modeling. The reference 1-KB scratchpad/eight queues/32-entry sensitivity point are recorded separately from open runtime allocation and prefetch distance. No storage configuration or numerical speedup is selected for BFS.

## Reproduce

```sh
.venv/bin/python -m archevolve \
  --input examples/received/bfs-sparse.features.v1.2.yaml \
  --input examples/received/bfs-fully-connected.features.v1.2.yaml \
  --methods examples/received/peter-measurement-methods.v1.2.yaml \
  --source-context examples/bfs.source-observations.yaml \
  --focus-design dx100-artifact-e4fc4af \
  --focus-design maple-isca2022 \
  --compare-design dx100-artifact-e4fc4af \
  --compare-design maple-isca2022 \
  --max-candidates 4 \
  --output-dir runs/bfs-maple-comparison-v0.1
```

Use `--overwrite` for an exact repeat. `--focus-design` controls which candidates get packages, while the full catalog query trace is retained. It is a requested scope, not a performance preference. `--compare-design` remains independent of package budget.

The source-backed `structure.mmd` follows the paper's logical produce/consume paths and explicitly labels queue-mode storage edges. It does not infer port widths, a RTL netlist, or a complete BFS composition. `interface.mmd` remains the operation contract view; `context.mmd` shows the manually proposed BFS statement relations.

## Next review

Peter/Eric should confirm source-to-mode choice and concrete operand domains, queues/packing/counts, MMIO/driver requirements, memory route, stable-array conditions and completion/drain behavior before Yan-Ru implements a replacement. Full-model scheduling/coalescing and BFS performance remain open; the second-fetcher selection and paper mechanism evidence are now available.

Validation: 86 software tests pass. All candidate interface/context/mechanism/logical-path Mermaid sources were rendered, and representative views were visually inspected. PDF and generated-text hashes, local links, and preservation of the earlier catalog records/claims/sources were checked. These checks validate the software handoff and source tracing, not an executed MAPLE accelerator.
