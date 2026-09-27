# Hardware-request YAML → Mermaid

The converter in `tools/render_mermaid.py` is implemented. It requires Python 3.10+ and PyYAML. It makes no LLM calls and does not select or validate hardware capabilities.

## SPARTA demo

The [request](../examples/sparta-sort.hardware-request.yaml) uses Peter's real SPARTA workload description as context and elaborates the two previously proposed hardware families into **manually authored illustrative boundary sketches**:

1. Indirect prefetching: a conceptual access observer sends predicted addresses to a request issuer; the CPU retains the increments.
2. Declared fetching: a conceptual descriptor front end, fetch engine, and return storage; index stability, RMW data freshness, and the software interface remain unresolved.

These partitions and port names do not come from verified accelerator implementations. Component references remain unknown, sizes remain open, and the output makes no speedup claim. This demo tests diagram generation while BFS features and the catalog are pending; the modified BFS source is now available and BFS remains the project demonstration target.

See [the generated review report](../diagrams/sparta/README.md) or [the report with rendered SVGs](../diagrams/sparta/preview.md).

## Run

From the Desktop project directory:

```sh
cd /Users/jvgrewal/Desktop/ArchEvolve
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/render_mermaid.py examples/sparta-sort.hardware-request.yaml --output-dir diagrams/sparta --overwrite
```

The converter emits one `.mmd` file per candidate, a Markdown review report, a full request snapshot, and a manifest mapping candidate IDs to files. The report carries input/catalog references, the source file's SHA-256, workload context, assumptions, and complete candidate details.

Select one candidate with `--candidate sparta-sort-prefetch-1`. Empty candidate lists generate a report without inventing a diagram. Unfilled templates are refused by default; `--allow-template` generates a visibly labeled template preview.

Generated filenames use numeric indices, never untrusted candidate IDs. Existing files are preserved unless `--overwrite` is supplied. That flag replaces matching generated files; it does not remove older images or diagrams that are no longer in the new manifest. Use the manifest/report for the current set, or generate into a fresh directory when changing candidate sets.

## Optional SVG/PNG rendering

Mermaid source works in a compatible Markdown viewer. Local image export uses the optional, pinned Mermaid CLI dependency in `package.json`/`package-lock.json`.

On this Mac, Chrome is already installed, so the supplied Puppeteer configuration uses a separate profile under the project's `.cache` directory:

```sh
PUPPETEER_SKIP_DOWNLOAD=true npm ci --cache .cache/npm
npm run mermaid -- -i diagrams/sparta/README.md -o diagrams/sparta/preview.md -p tools/puppeteer.example.json -b white
npm run mermaid -- -i diagrams/sparta/candidate-02.mmd -o diagrams/sparta/candidate-02.png -p tools/puppeteer.example.json -b white -w 2200
```

Adjust `executablePath` for another platform/browser installation. The Python converter itself does not require Node, Chrome, or network access after PyYAML is installed. The generated diagrams request ELK layout, supported by the installed Mermaid CLI; other viewers need that layout registered or a supported fallback.

## What gets drawn

- One subgraph per supplied hardware block.
- Separate input/output port nodes with payload, type, element width, and boundary role.
- Blue host-facing ports, green memory-facing ports, gray internal ports, and amber unknown-role ports.
- Dashed explanatory annotations for functions/components and parameter values. These are not additional hardware.
- Exactly the connections present in `hardware.connections`; no inferred internal signal wiring.
- Open values as `OPEN`, and missing widths/types as `unknown`.

Behavior, ordering, completion, constraints, evidence, and unresolved questions remain in the report's candidate YAML. Diagram shape and color do not prove semantic compatibility. An unconnected boundary port remains visible without inventing an external component.

## Checks

The converter rejects malformed graph records, duplicate YAML keys/IDs, nonexistent connection endpoints, edges that do not go from outputs to inputs, invalid known widths, and inconsistent open/fixed parameter values. It escapes labels and uses generated Mermaid IDs so source text cannot create diagram commands or output paths.

These are narrow graph-integrity checks for the provisional format. No new full pipeline schema or capability checker has been added.

Run the tests with:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

The SPARTA diagrams have also been parsed/rendered with Mermaid CLI and visually inspected. Parser success does not establish hardware correctness.

References: [Mermaid flowchart syntax](https://mermaid.js.org/syntax/flowchart.html), [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli), and [PyYAML safe loading](https://pyyaml.org/wiki/PyYAMLDocumentation).
