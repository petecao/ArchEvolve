# Hardware catalog v0.1 format reference

The canonical representation is YAML restricted to JSON-compatible values. `archevolve.hardware_catalog.validate_catalog` is the executable structural/reference validator. This page describes the fields that a consumer needs; it is not a schema for hardware synthesis. See [the guide](hardware-catalog-handoff.md) for the reasoning behind the distinctions.

## Top-level objects

| Key | Type / meaning |
|---|---|
| `format` | Exactly `hardware-catalog-v0.1` |
| `catalog_id`, `revision` | Stable collection ID and data revision |
| `status` | `research_reviewed_prototype`, not a hardware-validation badge |
| `sources` | ID → primary source title, edition, URL, locator basis, optional exact-file SHA-256 |
| `claims` | ID → scoped statement, source references, exact locator, evidence kind and limitations |
| `mechanism_families` | Records with `id` and `description`; no inherited operation capabilities |
| `decision_questions` | Records with `id`, `question`, `why_it_matters`, `claim_refs` |
| `designs` | Concrete design/version, configuration or mapping records |

IDs are nonempty strings using letters, digits, `_`, `-`, `.`, or `:`; they start with a letter or digit. Lists of referenced IDs contain no duplicates. YAML mapping keys must be strings and duplicate keys are rejected before validation. Unsafe YAML tags, non-JSON objects and nonfinite numeric values are rejected by the loader.

A claim's `evidence_kind` is `paper_specification`, `code_inspection`, or `research_inference`. The statement and locator identify its actual scope. A source hash binds bytes, not truth. Numerical experimental observations must retain their cohort and must not be relabelled as universal hardware specifications.

## Concrete design record

Required keys: `id`, `name`, `revision`, `record_kind`, `summary`, `mechanism_refs`, `source_refs`, `operations`, `requirements`, `parameters`, `interface`, `limitations`.

`record_kind` is `design_version`, `configuration`, or `mapping`. A mapping record describes a specific published use, not a general capability for every array. Pure policy-controller and generic resource-only records remain outside v0's admitted scope.

`interface` describes `software_supplies`, `invocation`, `outputs`, and `claim_refs`. It is a source-backed interface description, not a synthesized physical port list or a promised C function signature.

## Operation record

| Key | Meaning |
|---|---|
| `id` | Stable within its design record |
| `operation` | `read`, `write`, `read_modify_write`, or `reduce` |
| `subtype` | Specific named form, e.g. `gather`, `stream_load`, `add`, `cas` or `prefetch` |
| `execution_role` | `execute` or `assist`; assistance does not perform the required program operation |
| `address_patterns` | Examined patterns from `sequential`, `constant_stride`, `indirect`, `ranged_indirect`, `chained_indirect`, `pointer_chase`; empty means no established coverage |
| `support` | `paper_specified`, `code_observed`, `unsupported`, or `unknown`, scoped to this record |
| `claim_refs` | Located evidence; paper/code support requires a corresponding claim kind |
| `result` | `form`, `old_value`, `validity`, `claim_refs` |
| `ordering` | `scope`, `description`, `claim_refs` |
| `completion` | `event`, `visibility`, `claim_refs`; these may describe different guarantees |
| `datatype_notes`, `limitations` | Type/path/numerical qualifications that the query does not prove |

`result.old_value` is `returned`, `not_returned`, `unknown`, or `not_applicable`. An optional return requires its stated operands and validity conditions; `returned` is not a global atomicity guarantee. Assistance cannot claim to return the required operation's old value.

Optional `realization` contains `kind` (`native_primitive`, `documented_sequence`, or `mapping_role`), `description`, and `claim_refs`. It prevents an operation sequence from being mistaken for one instruction.

Optional `type_constraints` contains `payload_types`, `index_width_bits`, `claim_refs`, and `notes`. Payload types use `uint32`, `int32`, `float32`, `uint64`, `int64`, `float64`. Empty lists or absent type constraints are unknown; they are not unrestricted domains. Index representation width does not establish valid numeric values, intermediate arithmetic or address containment.

## Requirements and parameters

Each requirement has `id`, `description`, `scope`, `claim_refs`, and `verification` (`required` or `unknown`). Retrieval does not discharge these. They can express region ownership, aliasing, numeric bounds, validity, synchronization or other source-specific obligations. They are not an executable theorem prover or an automatically checked predicate language.

Each parameter has `id`, `unit`, `state`, `value`, `domain`, `claim_refs`, and `notes`. States are:

- `fixed_reference`: a source/reference value is recorded, with evidence. It is not a selected configuration for the new workload.
- `open`: no value is chosen; any documented domain retains evidence and qualifications.
- `unknown`: the necessary domain/value is not established.

`value` and `domain` are explicit and may be null. Open/unknown parameters cannot silently fix a value. A domain or reference value needs evidence. A necessary bound from an integer field is not a complete legal configuration interval. Coupled conditions stay in scoped requirements/notes.

## Query/output interpretation

`query_catalog` filters by requested operation, optional subtype, address pattern, role, old-value requirement and recorded type domains. It returns matching evidence and exclusions, preserving the operation contract and all design requirements. It does not compare performance or prove mapping legality.

`conditional_executor` means matching execution evidence with conditions still to establish. `assistance_only` means an assisting operation, not a replacement for the requested value/update. `mapping_reference` stays specific to the published mapping. `needs_evidence` records missing capability evidence. `not_covered` is absence from this record's examined domain, not a proof of universal hardware impossibility. Unsupported paths remain visible as exclusions.

The BFS adapter additionally retains workload-source ambiguities and CPU update effects. It cannot infer immutable memory from a read label. Reference parameters are separate from open choices in generated interface views. The full catalog snapshot, request and trace preserve evidence omitted from the compact human summary.

An author can still mislabel a real mechanism despite satisfying this structure. Semantic source review is part of catalog maintenance. The v0 validator checks representation consistency, not the truth of arbitrary supplied claims.
