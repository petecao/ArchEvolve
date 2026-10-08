# ArchEvolve — hardware exploration prototype

The active target is the **DX100-modified GAP BFS**, using Peter's v1.2 sparse and fully connected reports. Eric's [hardware evidence catalog](docs/hardware-catalog-handoff.md) is the default hardware knowledge input: **20 source/version/configuration/mapping records, 62 operations and 204 located claims** (data revision **0.1.17**). TMU, COBRA and AXI-Pack are scoped mapping records, not generic gather replacements.

The [current mechanism handoff](docs/mechanism-handoff-2026-10-06/README.md) explains scheduling, grouping, response association, credits, completion and unresolved implementation details. It includes a small executable association scaffold; no cycle model, RTL or target-performance validation is implied.

## Current offline forward path

**Feature reports → normalized evidence → typed operation queries → conditional candidates → intrinsic-description packages, YAML and Mermaid.**

The pipeline makes no LLM/API or evaluator calls. It preserves scope, source uncertainty, result validity, ordering/completion obligations and parameter states. It does not generate an executable rewrite or prove performance/composition.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m archevolve --input examples/received/bfs-sparse.features.v1.2.yaml --input examples/received/bfs-fully-connected.features.v1.2.yaml --methods examples/received/peter-measurement-methods.v1.2.yaml --source-context examples/bfs.source-observations.yaml --focus-design dx100-artifact-e4fc4af --focus-design maple-isca2022 --compare-design dx100-artifact-e4fc4af --compare-design maple-isca2022 --max-candidates 4 --output-dir runs/bfs-maple-comparison-v0.1
.venv/bin/python -m unittest discover -s tests -v
```

The default catalog is `catalog/hardware-v0.1.yaml` (format v0.1, data revision 0.1.17); `--catalog` may be omitted. The received feature files still use schema 1.1 despite being report revision v1.2.

## Results and handoff

- **[Peter's intrinsic handoff](docs/peter-intrinsics-handoff.md)**: current images, operation contracts, and source requirements.
- **[How all 20 hardware records accelerate work](docs/hardware-mechanism-overview.md)**: work delegated, operand/result movement, and software synchronization, with 71 linked catalog claims.
- **[Hardware behavior and acceleration mechanisms](docs/hardware-behavior-handoff.md)**: October 6 response to Peter, with separate source-scoped DX100/MAPLE sheets and automatic behavior output for future packages.
- [Pipette queue/RA mechanisms](docs/pipette-catalog-admission/README.md): committed register queues, rollback, finite shared storage and a portable lifecycle subset from the MICRO 2020 reference.
- [Flat-HTA key-map mechanisms](docs/hta-catalog-admission/README.md): cache-line lookup/branch operations with explicit tombstone and overflow ownership.
- [SMASH bitmap-index mechanisms](docs/smash-catalog-admission/README.md): hierarchical block indexing with separate CPU rank, operand loads and arithmetic.
- [Fifer temporal-stage mechanisms](docs/fifer-catalog-admission/README.md): output-reserved scheduling, drain/save/load reconfiguration and independent ordered DRM delivery.
- [ExTensor ordered-fiber mechanisms](docs/extensor-catalog-admission/README.md): sparse coordinate intersection, SkipTo synchronization and operand staging from the MICRO 2019 reference.
- [PHI bulk scatter mechanisms](docs/phi-catalog-admission/README.md): cache partial reductions, selective update bins and explicit flush/visibility phases from the MICRO 2019 reference.
- **[MAPLE/DX100 handoff](docs/maple-dx100-handoff.md)**: the selected second fetcher, known internal mechanisms, diagrams and typed/mapping gaps.
- [Validated v0.1.9 mechanism-rich BFS comparison](runs/bfs-mechanisms-v0.1.9/README.md).
- [Earlier focused BFS comparison](runs/bfs-maple-comparison-v0.1/README.md).
- **[October 1 candidate packages](runs/bfs-intrinsic-handoff-v0.1/README.md)**: high-level intrinsic descriptions, structured drafts, explicitly grouped source context and same-request comparisons.
- [Proposed shared handoff format](docs/intrinsic-handoff-format.md) and [implementation plan](docs/october-01-implementation-plan.md).
- [Run overview](runs/bfs-hardware-v0.1/README.md).
- [Sparse interface views](runs/bfs-hardware-v0.1/case-01/diagrams/preview.md).
- [Fully connected interface views](runs/bfs-hardware-v0.1/case-02/diagrams/preview.md).
- [Derived catalog navigation](runs/bfs-hardware-v0.1/catalog.navigation.yaml) and [decision questions](runs/bfs-hardware-v0.1/catalog.decision-questions.yaml).

The latest focused run includes the CPU comparison, DX100 reads, MAPLE queue fetching and MAPLE LLC assistance. Earlier snapshots retain Terminus CAS and Prodigy options. The unrestricted catalog query remains available; focus controls package scope rather than performance ranking.

**Important distinctions:** DX100 artifact CAS is explicitly excluded. Prefetch assistance does not return the requested gather result. A range-generation/load sequence is not one invented instruction. Fixed reference settings are not chosen tuning values. Unknown parameter domains remain unknown.

## Architecture and responsibilities

Yan-Ru profiles/annotates → Peter extracts features → Josh/Eric explore hardware → Josh provides interface views → Peter derives intrinsic specs → Yan-Ru rewrites loops. Josh/Eric then assemble matching artifacts for evaluation. Failed mappings can feed back to hardware exploration.

- [Current design](docs/hardware-agent-design.md)
- [Evidence-catalog integration](docs/hardware-catalog-integration.md)
- [Offline pipeline and input interpretation](docs/offline-pipeline.md)
- [Future agent prompt](prompts/hardware-agent.md) — not executed by the offline backend
- [Mermaid converter](docs/mermaid-generator.md)

The catalog describes existing operations/configurations, not a ready-to-compose physical block library. The diagrams are source-scoped **operation-interface views**; their abstract ports do not invent ABI widths or physical wiring. Peter/Eric must establish a concrete mapping before a code rewrite.

The October 1 generator accepts located internal-mechanism annotations and preserves missing scheduling details as unknown. MAPLE now supplies queue/pipeline/response-ordering annotations and a paper logical-path schematic. Concrete signatures, implementations and performance remain pending. `--source-context` uses matching manual source observations; it does not substitute for confirmed profiling placement. `--focus-design` restricts handoff packages to a requested comparison while retaining all query evidence.

## Inputs and history

The [source checkouts](sources/README.md), [source review](docs/bfs-source-review.md), [received reports](examples/received), and [measurement-method review](docs/measurement-methodology-review.md) remain available. The current reports reconcile 32-bit offsets with the recorded DX100 revision, but raw profiling and trial/ROI linkage are not independently verified.

Historical [SPARTA diagrams](diagrams/sparta/preview.md), [family-seed BFS runs](runs/bfs-offline-v1.2/README.md), and [v0.1 schemas](schemas/README.md) are retained. The old selector can still be exercised explicitly with `--catalog catalog/seed.yaml --max-candidates 3`; it is no longer the default. Historical family partitions must not be mistaken for verified hardware interfaces.

## Recent scoped catalog additions

Catalog revision 0.1.17 adds four records while retaining the earlier sixteen designs and project selection.

| Design | Examined operation |
| --- | --- |
| azul-micro2024 | mapped_sparse_row_partial_sum |
| telos-isca2025-public-model | stencil_neighbor_contribution_sum |
| svr-micro2024 | transient_indirect_chain_prefetch |
| triangel-isca2024 | temporal_address_prefetch |

Azul is limited to mapped sparse row partial sums, and Telos describes the public stencil source model. SVR and Triangel provide prefetch assistance. Each record retains its type, interface and implementation evidence requirements. The Telos private repair experiments remain separate from the examined public source.
