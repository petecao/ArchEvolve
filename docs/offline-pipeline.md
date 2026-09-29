# Offline forward-path prototype

The first executable pipeline accepts the two received v1.1 TDStep reports, normalizes them, inspects a provisional catalog, emits candidate hardware-request YAML, and generates Mermaid diagrams. It uses **explicit rules with zero LLM/API calls**. It does not compile a kernel, run perf, rewrite code, evaluate hardware, or prove a speedup.

## Run

From the project root, with the existing Python environment:

```sh
.venv/bin/python -m archevolve \
  --input examples/received/bfs-sparse.features.v1.1.yaml \
  --input examples/received/bfs-fully-connected.features.v1.1.yaml \
  --methods examples/received/peter-measurement-methods.yaml \
  --output-dir runs/bfs-offline
```

Use `--overwrite` to replace matching output files for a repeat run, `--max-candidates` to change the per-case budget, or `--catalog` for another compatible catalog. `--methods` applies Peter's explicit methodology only to reports whose hashes it names; omit it for a report without such a clarification. Use a fresh directory when changing the case/candidate set to avoid mistaking stale images for current output; the current manifest is authoritative.

Run checks with:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Optional local image previews use the already installed Mermaid CLI:

```sh
npm run mermaid -- -i runs/bfs-offline/case-01/diagrams/README.md -o runs/bfs-offline/case-01/diagrams/preview.md -p tools/puppeteer.example.json -b white
npm run mermaid -- -i runs/bfs-offline/case-02/diagrams/README.md -o runs/bfs-offline/case-02/diagrams/preview.md -p tools/puppeteer.example.json -b white
```

## Artifacts

The [run overview](../runs/bfs-offline/README.md) links to each case. Each case has:

- `input.received.yaml`: the original report, unchanged.
- `normalized.yaml`: reported accesses, preserved CAS semantics, source-binding status, method-scoped proximity statistics, byte-derived capacities, and unresolved questions.
- `hardware-request.yaml`: selected family sketches, rationale, target-access IDs, open parameters, and hardware graphs.
- `selection-trace.yaml`: every catalog entry's matching signals, selected/deferred status, and targeted accesses.
- `diagrams/`: Mermaid files, report, request snapshot, and manifest.

The run records hashes of inputs, catalog, methodology when supplied, generated request, and pipeline code. Repeated execution with unchanged inputs/configuration produces the same run ID and artifacts. Each workload is processed independently; there is no pooling of sparse/dense measurements.

## Current results

| Report | Comparison and exploratory candidates |
|---|---|
| Sparse | CPU baseline; indirect prefetch family; declared gather/read family |
| Fully connected | CPU baseline; stride prefetch family; declared bulk-read family |

This is an exploration shortlist. The CPU has not been measured here, and no selected accelerator has been established as better. The catalog is seeded from Eric's documents and needs his review for actual capabilities, composition, and interfaces.

## Differences that remain unresolved

1. **Source identity and widths.** Both reports point to a `DataLayoutAPI` source without a commit/hash and report 8-byte `VertexOffsets`. Our pinned DX100 reference defines 4-byte `SGOffset`. The adapter retains both values and marks the effective interface width unresolved. It does not silently rewrite the report or bind it to our checkout.
2. **Profile provenance.** Raw logs, exact build flags, dataset/source vertex, repetition/phase boundaries, and the exact profiled revision are not bound to these YAMLs. The sparse file also includes several graph scales. Values remain reported, not independently reproduced.
3. **Metric labels and conversions.** Peter has now supplied the instrumentation/formulas. The percentages measure adjacent-index proximity within frontiers/neighbor rows, and footprints are calculated array capacities. Their interpretation is resolved; exact cache-block membership and hit rates were not measured by these snippets. Several sparse-table values match decimal MB despite the stated binary convention. The prototype preserves the originals, derives canonical bytes with explicit units, and records that unit inconsistency. See [the methodology review](measurement-methodology-review.md).
4. **Statement mapping.** The reports describe arrays/expressions but do not identify exact statements in the profiled source. The adapter emits stable access IDs within each case and leaves statement IDs empty. Our earlier source observations remain reference material, not a substitute for this binding.

The dense report correctly distinguishes discovery-phase CAS from later reads. The adapter retains the kernel's conditional CAS even where a stream is described as `cached_streaming_read`. Declared-read mechanisms do not target the mutable parent update. No early-exit transformation is proposed from observing zero discoveries so far. Resolved methodology interpretations remain visible in outputs but are no longer emitted as unanswered clarification requests.

## A concise message for Yan-Ru

> Peter's sparse/dense YAML is enough for me to start. For your annotation/profiling, please include the exact TDStep source revision, build/graph commands, and raw logs when ready. One thing to reconcile: Peter's reports use 64-bit offsets, while the DX100 artifact uses 32-bit. Comments marking queue → offsets → neighbors → parent read/CAS → queue append are enough; no rewrite needed yet.

## What remains to implement later

- Bind the reports to the actual profiled source and confirmed metrics.
- Replace/review seed family sketches with Eric's real component records and constraints.
- Add a live model backend when requested; the existing system prompt is not executed by this offline backend.
- Connect Peter's intrinsic-spec generation, Yan-Ru's rewriting, and the evaluator.
- Add persistent evaluation feedback and reviewed catalog-extension proposals. Current manifests retain offline trial identity only.
