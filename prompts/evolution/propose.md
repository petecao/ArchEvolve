# Design mutation request — draft template

Inputs supplied as separately delimited data:
- fixed task/core/policy content pins;
- parent architecture and selected source/capability records;
- workload features with measurement scope and unknowns;
- approved strategy revision;
- current candidate/feedback history and allowed operator/budget.

Propose one interpretable mutation (or one necessary coupled delta) that addresses the supplied issue or explores an explicit alternative. State why the selected regions/mechanisms are relevant. Preserve source identities through the new dataflow. Specify acceptance, result association, completion, storage ownership/reuse, finite capacities and all remaining CPU work.

For parameter changes, cite the legal coupled domain and model coverage. If either is absent, return `needs_information` instead of a supposedly legal setting. For new compositions/components, keep the record `proposed` or `needs_mapping_review` until the corresponding interface/legality work is established.

Return an ordinary YAML proposal record as described in the loop design. Include:
`parent_id`, `parent_sha256`, `strategy_id`, `catalog_sha256`, `workload_sha256`,
`mutation_kind`, `target_region_ids`, `before`, `after`, `preserved_semantics`,
`new_obligations`, `evidence_refs`, `expected_benefit_hypothesis`, `cost_changes`,
`novelty_relative_to_parent`, `status`, and `next_check`.

Do not output a performance score or mark requirements discharged merely because the description is plausible. A bounded information request is a valid outcome.
