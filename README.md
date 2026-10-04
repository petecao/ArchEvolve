# ArchEvolve — hardware exploration prototype

The active target is the **DX100-modified GAP BFS**, using Peter's v1.2 sparse and fully connected reports. Eric's [hardware evidence catalog](docs/hardware-catalog-handoff.md) is the default hardware knowledge input: seven source/version/configuration records, 39 operations and 46 located claims. Data revision 0.1.3 adds MAPLE from Eric's selected ISCA 2022 paper.

Local work for this task lives in `/Users/jvgrewal/Desktop/ArchEvolve`. Run commands from the repository root.

## Software database (`swdb-project/`)

Added 2026-09-29 ET. Yan-Ru's EvolveSWDB repository now lives in [`swdb-project/`](swdb-project/README.md), imported with `git subtree` so its full history is kept. It holds the kernel records, schemas, vocabularies, profiling scripts, and the `swdb` tool. Its own rules ([AGENTS.md](swdb-project/AGENTS.md), [CONTEXT.md](swdb-project/CONTEXT.md), [ADRs](swdb-project/docs/adr/)) apply inside that folder only.

```sh
cd swdb-project && python3 -m pytest -q
```

## Current offline forward path

**Feature reports → normalized evidence → typed operation queries → conditional candidates → intrinsic-description packages, YAML and Mermaid.**

The pipeline makes no LLM/API or evaluator calls. It preserves scope, source uncertainty, result validity, ordering/completion obligations and parameter states. It does not generate an executable rewrite or prove performance/composition.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m archevolve --input examples/received/bfs-sparse.features.v1.2.yaml --input examples/received/bfs-fully-connected.features.v1.2.yaml --methods examples/received/peter-measurement-methods.v1.2.yaml --source-context examples/bfs.source-observations.yaml --focus-design dx100-artifact-e4fc4af --focus-design maple-isca2022 --compare-design dx100-artifact-e4fc4af --compare-design maple-isca2022 --max-candidates 4 --output-dir runs/bfs-maple-comparison-v0.1
.venv/bin/python -m unittest discover -s tests -v
```

The default catalog is `catalog/hardware-v0.1.yaml` (format v0.1, data revision 0.1.3); `--catalog` may be omitted. The received feature files still use schema 1.1 despite being report revision v1.2.

## Results and handoff

- **[Peter's intrinsic handoff](docs/peter-intrinsics-handoff.md)**: current images, operation contracts, and source requirements.
- **[MAPLE/DX100 handoff](docs/maple-dx100-handoff.md)**: the selected second fetcher, known internal mechanisms, diagrams and typed/mapping gaps.
- [Latest focused BFS comparison](runs/bfs-maple-comparison-v0.1/README.md).
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
