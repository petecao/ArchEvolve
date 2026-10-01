# Draft intrinsic handoff format

This is a proposed shared YAML format for the October 1 workflow. It is generated offline for discussion with Peter/Eric/Yan-Ru, not yet a team-agreed ABI or LANL exchange standard. No formal DSL is required.

## One candidate per package

Each `case-NN/handoffs/candidate-NN/` package contains:

- `README.md`: readable high-level intrinsic descriptions, source placement proposals, behavior, legality requirements and review questions.
- `intrinsic-draft.yaml`: `format: intrinsic-handoff-v0.1`; structured software-facing descriptions.
- `candidate.yaml`: the full candidate, located claims, source references, parameter contracts and unresolved requirements.
- `interface.mmd`: catalog operation interfaces with inputs/outputs and optional mechanism annotations.
- `context.mmd`: explicitly recorded source-statement relations, distinguishing matched requests, uncovered requests and retained side effects. These edges are workload relations, not hardware wiring.
- `mechanisms.mmd`: described/unknown internal mechanisms as annotations, without invented wiring.
- `manifest.json`: candidate identity, originating hardware-request hash and generated-text hashes.

The draft is generated even when source placement or hardware types are incomplete. Unresolved fields remain explicit and the overall status stays `draft_requires_review`. PNG/SVG previews can be rendered locally; they are presentation assets outside the text manifest.

## Common terms and fields

| Field or term | Meaning |
|---|---|
| `candidate_id`, `catalog_design_id`, revision | Exact workload option and examined design/configuration; family names do not inherit capabilities. |
| `operations[].id` | Exact catalog operation, not a synthesized C function name. |
| `intent` | High-level description of the proposed operation or assistance. |
| `execution_role` | `execute` can conditionally supply the program result; `assist` provides help such as prefetching. |
| `realization` | Native primitive, documented multi-step sequence, mapping role, or unrecorded. A sequence is not one new instruction. |
| `logical_inputs` | Target arrays, requested data/index types, patterns and source statements; these are workload intents, not an ABI operand list. |
| `design_interface` | Full design-wide input/invocation/output contract from Eric's representation. |
| `supported_type_constraints` | Hardware type/index domains from evidence; kept separate from workload-requested types. |
| `preconditions`, `requirements` | Conditions that must be established before applying the mapping. Retrieval does not discharge them. |
| `postconditions.catalog_result` | Exact result form, validity and old-value semantics from the catalog. |
| `ordering`, `completion` | Result ordering, completion event and memory visibility. |
| `request_groups` | Explicit source-context bundles plus matched/unmatched capability requests and side effects. |
| `workload_semantics` | Reported update primitive, source binding and evidence status; the original CAS operands remain visible. |
| `mechanism_context` | Internal scheduling descriptions, evidence references and unknown checklist items. |
| `parameter_contract` | Reference settings, open values and unknown domains; no configuration is selected here. |
| `concrete_signature`, `implementation_ref` | Null until the downstream spec and implementation exist. |
| `readiness`, `review_questions` | What remains for Peter/Eric/Yan-Ru before implementation and evaluation. |

The current read options include mutable parent state: a read match does not permit stale buffering or reordering across updates. CAS must retain comparison/update semantics and success-controlled effects. Prodigy assistance does not return a gather result. Numerical and ownership/concurrency checks remain necessary even when type widths match.

## Source context and grouped requests

Pass `--source-context examples/bfs.source-observations.yaml` to use our explicitly recorded manual BFS review. Its file, function and revision must match the received report, with no conflicting profiling revision. Otherwise the context is retained as unbound and requests stay singleton groups with no supplied source locations.

`access_bindings` explicitly maps an array and read/update purpose to statement IDs. `request_groups` lists related statements; their existing `related_statement_ids` provide dependencies. No grouping is inferred merely because two arrays look alike. For BFS the context includes parent CAS, the successful-branch store and queue append, even when a read candidate covers only the fetch requests.

These are manual source proposals, not Peter/Yan-Ru's confirmed annotated profile. A workload bundle identifies what to consider together; joint hardware execution still requires mechanism and composition evidence. Uncovered operations and side effects remain visible.

## Optional catalog mechanism annotations

Eric can add `internal_mechanisms` to a design without changing its existing operations. This is a flexible annotation list, not a universal implementation scaffold. Entries have:

```yaml
internal_mechanisms:
  - id: request-grouping
    kind: coalescing
    status: unknown
    description: null
    claim_refs: []
```

Kinds: `buffering`, `coalescing`, `reordering`, `issue_policy`, `dependency_tracking`, `completion`, or `other`. A `described` entry requires a nonempty description and located paper/code claim references. An `unknown` entry has a null description and no claim references. Existing family classifications and buffer capacity parameters do not automatically fill these descriptions. Known operation completion remains in the operation contract even when internal completion scheduling is unrecorded.

Optional `performance_hypotheses` entries contain `id`, `description`, `workload_conditions`, `limiting_factors`, and `claim_refs`. They are preserved as conditional hypotheses; the pipeline produces no cycle estimate or numerical speedup. Workload counters alone do not establish that a scheduling mechanism will help.

New primary catalog designs should follow the meeting's recent major-conference policy. Eric must establish qualifying publication metadata; pinned implementation artifacts can remain supporting evidence. The current catalog is preserved rather than silently filtered using incomplete publication metadata.

## Same-workload comparison

Every evidence-catalog run includes `hardware-comparison.yaml` and a readable `.md`. By default it compares selected designs. Repeated `--compare-design` IDs compare any existing catalog entries against the same typed requests, independently of diagram selection budget:

```sh
--compare-design dx100-artifact-e4fc4af \
--compare-design spzip-isca2021-push \
--compare-design prodigy-hpca2021
```

The included example contrasts existing DX100 execution, SpZip's scoped Push mapping, and Prodigy assistance. SpZip has missing typed evidence; Prodigy remains assistance. This is preparation for Eric's selected second fetcher, not a claim that his new selection has arrived. Replace/add its catalog ID when the entry is available. Mechanism and model gaps remain explicit; no performance winner is chosen.

## Review responsibilities

Josh supplies the candidate package and high-level description. Peter confirms source placement and derives the concrete intrinsic specification, rewritten abstraction and legality/pre/postconditions. Eric resolves hardware mechanism and mapping requirements. Yan-Ru implements/reuses the intrinsic after that agreement and verifies the rewritten kernel. Implementation/correctness results can later supply evaluation feedback; this version does not grow a trusted catalog automatically.
