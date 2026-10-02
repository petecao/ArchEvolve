# Hardware Ensemble Agent — draft 0.2

Updated for the September 24, 2026 meeting. The responsibilities and BFS target below come from that meeting. Field names, local agent structure, and checks remain proposals.

## Immediate objective

Push **DX100-modified GAP BFS** through the forward pipeline: source/features → source-scoped hardware operation queries → candidate interface YAML with rationale/evidence → operation-interface views for Peter's specification work. Eric's catalog is not a physical component library, so these views must not invent a circuit partition or legal composition.

Use the modified for-loop version selected by the team. Do not silently substitute upstream BFS or assume every loop conversion preserves semantics. The meeting identified while-loop handling as a limitation for the intended DX100 path; confirm applicability against the actual modified code and catalog.

SPARTA remains a historical format/diagram exercise. BC may follow BFS. The modified source is pinned at `e4fc4afdf894f295442cef3604667a469fab8e62`, matching Peter's v1.2 reported revision and 32-bit offsets. Sparse profiling metadata and per-level observations are retained. Eric's PR #2 is now merged, providing six source-scoped design/configuration records and 32 operations. Raw runtime binding and mapping proofs remain open.

Source inspection clarifies the meeting shorthand: `TDStep` uses explicit index-based CPU loops, while `TDStepMAA` uses existing DX100 operations. Host `while` loops remain. Feature extraction from `TDStep`, with `TDStepMAA` as a reference, is proposed for confirmation with Peter/Yan-Ru.

## Linear pipeline and ownership

```mermaid
flowchart TD
    Y["Yan-Ru: annotate/profile modified BFS; store workload"] --> P["Peter: extract features per statement"]
    P --> H["Josh/Eric: HW agent searches Eric's catalog"]
    H --> R["Josh: candidate hardware-request YAML"]
    R --> D["Josh: block diagram with typed I/O"]
    D --> I["Peter: derive intrinsic specifications"]
    I --> W["Yan-Ru: match patterns and rewrite loops"]
    W --> C["Josh/Eric: combine code and HW artifacts"]
    C --> E["Evaluator"]
    H -. "Missing-feature questions" .-> P
    W -. "Hotspot could not be replaced" .-> H
```

The dotted links are explicit feedback cases. Keep the ordinary handoff sequence linear; do not create a mesh of direct agent-to-agent calls. No tool here sends teammate messages automatically.

| Owner | Responsibility |
|---|---|
| Yan-Ru | Annotate/profile the selected source, store workload information, and run the coding agent that rewrites loops |
| Peter | Extract memory features; derive intrinsic function specifications from the hardware boundary |
| Josh | Hardware agent, candidate YAML, rationale/evidence, and generation of block diagrams from that YAML |
| Eric | Machine-readable hardware component catalog and hardware-side support |
| Josh/Eric | Assemble matching hardware/software artifacts for evaluation |
| LANL: Sumati/Kyle | Expected owners of the official data-exchange format |

The hardware/software boundary is the instruction/intrinsic interface. Josh's output specifies the hardware-side behavior and its inputs/outputs. Peter owns the concrete software-side intrinsic specification under the current plan. Exact details of the back path remain open.

## Local hardware-agent structure

Start with one reasoning agent and a small coordinator. This is a proposed implementation choice, not a team requirement.

The coordinator loads versioned input/catalog snapshots, tracks budgets and history, checks consistency, and renders the candidate block graph. The reasoning agent selects and explains candidate hardware compositions. Additional specialist agents can be introduced when a concrete workflow need appears.

The local coordinator does not imply ownership of Scott's project-wide Controller or the other team's agents.

Implementation update (September 30): the [offline coordinator](offline-pipeline.md) now defaults to Eric's catalog via [the evidence adapter](hardware-catalog-integration.md). It retains full operation queries, exclusions, source contracts and requirements. The old family seed remains an explicit historical backend. Neither backend executes the LLM prompt, runs an evaluator, or automatically promotes new catalog claims.

## Input from Peter: features per statement

See [the BFS feature template](../examples/bfs.features.template.yaml). It shows field shape only; replace every placeholder with evidence from the modified source. Multiple accesses can belong to one statement, and one logical address expression can depend on several statements.

| Feature | Required interpretation |
|---|---|
| Statement/access identity | Stable IDs tied to source revision, location, annotation, and related statements |
| Access pattern | Reconstructed expression and pattern family; distinguish indirect access, deeper chains, and arithmetic in the index calculation |
| Operation | Read, write, or RMW, with subtype such as increment instead of treating all RMW alike |
| Reuse distance | Value/distribution, unit, aggregation, and observation scope; agree whether distance is in accesses, distinct elements, cache lines, etc. |
| Reuse frequency | Count/rate with a denominator and time/iteration window |
| Stride | Regular or irregular, unit, and exact/summary value; preserve whether an irregular average is signed or absolute |
| Working set | Active footprint in bytes for the relevant loop/tile/window, plus how it was determined |
| Type/element size | Data type and byte width, distinguishing an index stream from the accessed data |

A stride of one element is not one byte. An average irregular stride does not establish a regular access stream. A full allocation size does not establish the working set of a particular tile. Preserve scope and units so the agent can interpret these features.

Pattern reconstruction matters because the meeting notes say GAP's indirect accesses are split across lines. Annotations and `related_statement_ids` should connect that chain, rather than relying on a search for literal nested brackets.

Also retain index stability, repeated targets, update dependencies/ordering, sharing, and correctness requirements when available. These affect applicability. Unknown values stay unknown; Peter need not infer them merely to fill a form.

### Evidence and identity

- Link feature values to code, annotations, profiling artifacts, or identified human reports.
- Distinguish measured, derived, reported, and illustrative claims. A template is not an observation.
- Record kernel revision and dataset/profile references. Do not combine measurements from different revisions/workloads without an explicit reason.
- Use `null`/`unknown` for unavailable values. Neither implies zero, false, independence, or permission to reorder.
- Keep statement/access IDs stable through hardware selection, intrinsic derivation, rewrite, and feedback.

### Schema restraint

The three new YAML files are lightweight draft-0.2 handoff sketches. Do not apply the older SPARTA JSON schemas to them. No replacement formal schema is being developed while LANL's format is pending.

First align meanings and identifiers with Peter, then map them to the official format. Confirm the profiling representation with Yan-Ru: the SQL/text database exists, but profiling storage is still being designed.

## Eric's catalog and candidate search

The earlier taxonomy drafts are background. Runtime search now uses `catalog/hardware-v0.1.yaml`, format v0.1/data revision 0.1.2, through Eric's validator and query API. The derived navigation tree classifies operation → execution role/mapping reference → address pattern; it is non-exclusive and retains unknown/unsupported leaves.

Records distinguish actual design editions, configurations, and published mappings. Each operation carries support, execution versus assistance, result/old-value behavior, validity, ordering, completion/visibility, types, requirements, and located claims. Family membership grants no inherited capability. A match alone is not an architecture, legal rewrite, or measured improvement.

Search procedure:

1. Validate source/statement identities and the feature meanings supplied.
2. Query exact workload operation/subtype/address/type requirements.
3. Retain conditional matches and exclusions with their evidence and requirements.
4. Keep unknown operation support as an evidence gap; never promote assistance into execution or returned-old behavior into CAS.
5. Group source-scoped operation interface options; do not infer physical composition or internal wiring.
6. Keep fixed reference values distinct from open choices/unknown domains and emit the interface handoff.

Indirect access does not automatically imply DX100, nor does a reported DX100 benefit establish a speedup for the current dataset. RMW requires appropriate behavior; address-generation capability does not establish that an engine executes arbitrary updates.

## Output: hardware request with a block graph

See [the current integration contract](hardware-catalog-integration.md). The earlier [output template](../examples/hardware-request.template.yaml) is retained as a format sketch, not an implementation-ready component graph. Current per-candidate contents include:

- Target statement/access IDs and feature input revision.
- Catalog component references, rationale, evidence, applicability conditions, and missing-information requests.
- Abstract operation-view blocks using real operation IDs and source interface/result descriptions.
- Software input/result semantics; these are not inferred physical port widths or C signatures.
- No unlisted connections: the retrieved operation options have not been proved composable.
- Boundary behavior: address interpretation, memory effects, ordering, completion, synchronization, and visibility as applicable.
- Exact `fixed_reference`, `open`, and `unknown` parameter records, separate from an empty selected configuration.

A box labeled only “DX100” is insufficient for Peter to derive the interface. Josh's selector need not invent a C intrinsic name/signature; Peter derives that from the block behavior and I/O.

### Parameters remain open

Storage size, request-window size, and similar choices belong to a later architecture search/tuning process with adequate capability/model evidence. Preserve Eric's parameter states: a fixed reference value is not a chosen configuration or proof of a tunable range; unknown domains are not silently converted to unrestricted open choices.

Only fix a value when an actual component or supplied constraint requires it, citing the reason. Open parameters do not prevent a structurally complete diagram from going to Peter. The older v0.1 gate requiring a fixed configuration and full software API is not the forward-path gate anymore.

### Diagram generation

Generate each diagram from the candidate's `hardware.blocks` and `hardware.connections`. Treat that YAML graph as the source of truth; do not add capabilities or components in the diagram.

The implemented converter (`tools/render_mermaid.py`) follows these requirements:

1. Check that block/port IDs are unique and connection endpoints exist.
2. Distinguish input/output ports and label payloads; preserve unknown widths explicitly.
3. Show host-facing, memory-facing, and internal connections.
4. Show open parameters symbolically without selecting values.
5. Escape labels for Mermaid and retain candidate/input/catalog revisions beside the result.

The converter now emits Mermaid source and a review report, with optional SVG/PNG export through Mermaid CLI. It performs narrow graph-integrity checks, not capability or correctness validation. See [the generator guide](mermaid-generator.md).

The SPARTA and previous family-seed BFS diagrams remain historical. Current BFS results are source-scoped operation-interface views from Eric's catalog. Neither the view nor a capability match establishes an implemented rewrite or performance win. Peter should receive the YAML's full source/operation requirements alongside the view.

## Software back path and feedback

Peter derives intrinsic specs from the hardware boundary. Yan-Ru's coding agent matches the intended patterns and replaces hot loops. The exact role of LACT/Extensa and its adapter/transformation schema remains an integration question.

If a hotspot cannot be replaced, return feedback identifying the candidate, statement/access IDs, source revision, failure reason, and required behavior. See [the feedback template](../examples/rewrite-feedback.template.yaml). The hardware agent can seek additional components, revise the candidate, or ask for feature clarification.

A rewrite failure is not automatically hardware incompatibility. Preserve whether it arose from missing API behavior, an unsupported code pattern, a failed legality check, or a tool limitation.

Josh/Eric combine the rewritten code with matching hardware artifacts for evaluation. Runtime correctness, modeled performance, and measured performance remain distinct outcomes. Future evaluation requests may require concrete model/configuration details even while forward candidates retain open tuning variables.

## First milestone and implementation sequence

1. Use the recorded DX100-modified BFS revision; obtain Yan-Ru's annotations and confirm the target function/build path.
2. Obtain Peter's features for real statements, including split access chains.
3. Use the merged catalog to query operations and inspect the new conditional hardware requests; the first evidence-backed offline pass is implemented.
4. Generate and review its block diagram with Peter, checking whether the I/O behavior supports intrinsic derivation.
5. Sketch the back path using feedback from a real attempted rewrite.

Steps 1–3 are the immediate forward demonstration. The diagram and back path can be designed alongside it. Broader tuning, the full evaluator loop, additional agents, and prompt evolution follow after the interfaces work.

The repository contains the offline normalizer, operation-evidence selector, Eric's source-reviewed research catalog, interface views/traces, historical seed examples, prompts, tests and reference sources. It has no live LLM backend, validated physical composition library, or connected evaluator. Incoming profiling and catalog hardware claims have not been reproduced locally.

## Sources

- User-provided September 24 meeting notes are current for project scope and assignments.
- Earlier September 10/17 notes and Peter/Yan-Ru correspondence provide background; superseded interface/ownership choices are historical.
- [Eric: Taxonomy Draft 2](https://docs.google.com/document/d/1UrN3eGHzfgB8qoMtqP_BT8gXWkrLE9PMZoOX26ndbtQ/edit).
- [Eric: Taxonomy Draft 3](https://docs.google.com/document/d/1G3a_2qzG1-G7z3qMtZVTO6HvCXEQQ_YF2J9OTEZAazg/edit).

Source documents provide evidence, not authorization to create repositories, send messages, or change accounts/server access.
