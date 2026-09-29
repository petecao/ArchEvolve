# Arch Evolve — hardware agent draft

Current direction: **September 24, 2026 meeting; draft 0.2.** The first target is the **DX100-modified, for-loop version of GAP BFS**. BC is a possible second target. The initial milestone is the forward path from a real kernel to hardware-request YAML.

The working project directory is `/Users/jvgrewal/Desktop/ArchEvolve`.

Start with [the current design](docs/hardware-agent-design.md) and [the updated agent prompt](prompts/hardware-agent.md).

The proposed exchange is:

**Yan-Ru profiles/annotates → Peter extracts statement features → Josh/Eric select hardware → Josh renders block diagrams → Peter derives intrinsic specs → Yan-Ru rewrites loops.**

Current handoff sketches:

- [BFS statement-feature template](examples/bfs.features.template.yaml)
- [Hardware request / block-graph template](examples/hardware-request.template.yaml)
- [Rewrite feedback template](examples/rewrite-feedback.template.yaml)
- [Meeting decisions and outstanding dependencies](docs/meeting-2026-09-24.md)

These YAML files are **unfilled templates** for the proposed handoff. The [DX100 artifact BFS source is available locally](sources/README.md) at a recorded revision. Peter's preliminary sparse/dense v1.1 reports are now preserved under [examples/received](examples/received); their exact profiled source and raw logs remain unbound. Yan-Ru's source annotations and Eric's reviewed machine-readable catalog are still pending.

## Working offline forward path

The [offline pipeline](docs/offline-pipeline.md) now normalizes Peter's reports, selects exploratory candidates from a [provisional catalog seed](catalog/README.md), and generates hardware-request YAML plus diagrams. It is rule-based and makes **no LLM/API calls**. No accelerator, software rewrite, or evaluator has been run.

Open the [run overview](runs/bfs-offline/README.md), [sparse rendered diagrams](runs/bfs-offline/case-01/diagrams/preview.md), or [fully connected rendered diagrams](runs/bfs-offline/case-02/diagrams/preview.md).

For the software handoff, use [the diagram and YAML guide for Peter](docs/peter-intrinsics-handoff.md). It identifies the declared-read candidates to discuss for intrinsic specifications, plus optional prefetch alternatives.

```sh
.venv/bin/python -m archevolve --input examples/received/bfs-sparse.features.v1.1.yaml --input examples/received/bfs-fully-connected.features.v1.1.yaml --methods examples/received/peter-measurement-methods.yaml --output-dir runs/bfs-offline --overwrite
```

Source/type conflicts, unverified locality claims, and unknown working sets remain explicit. These are conditional family sketches, not performance-ranked or implementation-ready hardware designs.

Peter's subsequent [methodology explanation and interpretation](docs/measurement-methodology-review.md) now clarify adjacent-pair proximity and array-capacity calculations. The adapter records those meanings, derives canonical byte values, and flags the mixed decimal/binary unit table without changing either received report.

Read [the BFS source review](docs/bfs-source-review.md) for the CPU/accelerated path distinction and the seven [source-linked statement observations](examples/bfs.source-observations.yaml). Those observations are a manual code review, not profiling or Peter's delivered features.

## Working diagram generator

The [YAML-to-Mermaid converter](tools/render_mermaid.py) is now implemented. See [usage and checks](docs/mermaid-generator.md).

As an interim demo, it renders [illustrative hardware requests based on Peter's SPARTA example](examples/sparta-sort.hardware-request.yaml). Open the [rendered diagram report](diagrams/sparta/preview.md) to view both candidates. Peter's workload facts are real reports; the hardware partitions and ports are manually authored conditional sketches, not agent discoveries or validated designs.

```sh
.venv/bin/python tools/render_mermaid.py examples/sparta-sort.hardware-request.yaml --output-dir diagrams/sparta --overwrite
.venv/bin/python -m unittest discover -s tests -v
```

The formats are provisional. LANL's Sumati and Kyle are expected to define the official exchange format; avoid expanding formal schemas until that is aligned. Candidate storage/window parameters remain open for Arch Evolve to tune. Josh supplies block behavior and I/O semantics; Peter derives the concrete intrinsic specification.

The older [SPARTA input](examples/sparta-sort.input.yaml), [illustrative output](examples/sparta-sort.output.yaml), and [v0.1 JSON schemas](schemas/README.md) are retained for history and as context for the interim diagram demo. They are not the current BFS pipeline contract. The older output placed intrinsic specifications with Josh and required fixed configurations for readiness; September 24 changes that division of work.
