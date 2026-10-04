# Integrating Eric's operation evidence

Eric's PR #2 is merged. `catalog/hardware-v0.1.yaml` is the CLI default. Data revision `0.1.5` retains the selectable MAPLE addition from `0.1.3` and its `0.1.4` pinned-RTL supplement, and adds source-scoped internal mechanism details for DX100, Terminus, Prodigy and SpZip. See [the mechanism handoff](hardware-internals-v015.md). The earlier `catalog/seed.yaml` remains supported explicitly for historical comparisons. No LLM/API or evaluator calls are made.

## Run the new path

```sh
.venv/bin/python -m archevolve \
  --input examples/received/bfs-sparse.features.v1.2.yaml \
  --input examples/received/bfs-fully-connected.features.v1.2.yaml \
  --methods examples/received/peter-measurement-methods.v1.2.yaml \
  --catalog catalog/hardware-v0.1.yaml \
  --max-candidates 4 \
  --output-dir runs/bfs-hardware-v0.1 --overwrite
```

The CLI default budget includes the CPU comparison plus three exploration options. The library helper accepts an explicit budget; callers of the historical seed path can retain a budget of three.

## Mapping the input to queries

The adapter is intentionally scoped to the supplied TDStep representation:

| Workload expression/role | Capability query |
|---|---|
| Frontier queue stream | `read / stream_load / sequential` |
| Offsets indexed by the loaded frontier vertex | `read / gather / indirect` |
| Neighbor traversal bounded by VertexOffsets | `read / gather / ranged_indirect` |
| Parent read through a loaded neighbor ID | `read / gather / indirect`, with mutable-target warning |
| Conditional parent compare-and-swap | `read_modify_write / cas / indirect` |

Reported payload types and resolvable index widths qualify queries. Missing/conflicting workload types stay unknown and prevent a candidate from appearing fully specified. Numeric value domains, sign constraints and byte-offset arithmetic remain separate requirements. Small measured distances do not change a syntactically indirect access into a proven sequential instruction mapping.

CAS is queried by exact subtype, with success handling required by the source behavior. It is not replaced by an add/update or an operation that merely returns an old value. Unknown update kinds create a question instead of a wildcard RMW lookup.

## Retrieval and exploration ordering

`archevolve.evidence_select` calls Eric's `query_catalog` and records the complete matches and exclusions for every request. Operation support marked unknown remains in the trace but is not promoted to a usable interface option. Explicit unsupported paths remain excluded.

Matches are grouped by design/version and role: read execution, update execution, read assistance, mapping reference, or update assistance. A comparison baseline is retained. The budget then visits these groups in that order, choosing within each group by evidence completeness, code-observed support, and stable IDs. This is a transparent exploration order, not a cost/performance ranking.

Multiple matched operations in one candidate are **interface options**, not a proven combined architecture. A design/version may appear in several roles; support is never inherited from its family or a different configuration. Alternatives outside the budget remain in the trace.

Sparse and fully connected reports currently retrieve the same design groups because their required operation classes overlap. Their dynamic data and scopes remain separate. The reported profile changes the displayed order of read options, not source capabilities or the semantics of loaded-index expressions.

## What the output preserves

Each candidate carries:

- Exact design/operation revisions, support status, execution role, and realization kind.
- Matching requests and any missing workload/capability type evidence.
- Result form, old-value behavior, validity, ordering, completion and visibility.
- All design requirements and limitations, without declaring them discharged.
- Located claims and primary sources referenced by the operations, interfaces, requirements and parameters.
- Unchanged reference/open/unknown parameter contracts, and an empty selected configuration.

The default sample retrieves DX100 artifact read operations, a Terminus CAS option needing type/mapping evidence, and Prodigy assistance. DX100 artifact CAS is explicitly excluded; paper CAS with unknown support is not diagrammed as an executor.

## Diagram semantics

The generic renderer is reused, but these views represent operation contracts. Box IDs are actual catalog operation IDs. Input text is a shortened design-wide interface excerpt, with the full text retained in YAML; it is not a C operand signature. Result boxes reflect the catalog result form, and assistance results are explicitly labeled as not replacing the program's result.

`hardware.connections` stays empty: the catalog does not establish physical port wiring or legal component composition. Requested software types are displayed separately from unknown physical/ABI widths. Documented sequences are labeled as sequences. Reference parameters are annotations, not chosen values.

A future architecture-composition step needs mechanism/compatibility evidence and mapping checks. This integration does not fabricate those missing relations or automatically grow a trusted catalog from a trial.

## Artifacts and checks

The run includes received/normalized inputs, hardware requests, full query/selection traces, catalog/method snapshots, a derived non-exclusive navigation tree, decision questions, and source/code/input hashes. The source reports and Eric's catalog remain unchanged.

Tests exercise exact CAS exclusion, assistance versus execution, returned-old distinctions, mutable targets, type uncertainty, reference parameters, sequence realization, source claims, deterministic offline behavior, and the legacy seed path. These are software/representation checks, not hardware execution validation.
