"""Transparent offline retrieval/selection; deliberately not an LLM backend."""

from copy import deepcopy

from tools.render_mermaid import RequestError, mapping, sequence, validate_request


def validate_catalog(catalog):
    mapping(catalog, "catalog")
    if not catalog.get("catalog_id") or not catalog.get("revision"):
        raise RequestError("Catalog needs an ID and revision.")
    ids = set()
    allowed_signals = {"always", "has_indirect_access", "has_regular_stream", "has_read_stream", "has_conditional_cas", "reported_large_jumps", "reported_near_unit_indices"}
    for item in sequence(catalog.get("entries"), "catalog.entries"):
        mapping(item, "catalog entry")
        if not isinstance(item.get("id"), str) or not item["id"] or item["id"] in ids:
            raise RequestError("Catalog entry IDs must be non-empty and unique.")
        ids.add(item["id"])
        if not isinstance(item.get("revision"), str) or not item["revision"]:
            raise RequestError("Each catalog entry needs a revision.")
        if item.get("entry_kind") not in ("baseline", "family_template"):
            raise RequestError("Catalog entry_kind must be baseline or family_template.")
        if not isinstance(item.get("rationale"), str) or not item["rationale"]:
            raise RequestError("Each catalog entry needs a rationale.")
        for field in ("taxonomy_refs", "open_conditions"):
            if any(not isinstance(value, str) for value in sequence(item.get(field), field)):
                raise RequestError(f"{field} entries must be strings.")
        for key in sequence(item.get("required_signals"), "required_signals"):
            if not isinstance(key, str) or key not in allowed_signals:
                raise RequestError(f"Unknown selection signal {key!r}.")
        if item.get("preferred_when") is not None and (not isinstance(item["preferred_when"], str) or item["preferred_when"] not in allowed_signals):
            raise RequestError("Unknown preferred_when signal.")
        if item.get("target_policy") not in ("all", "indexed", "read_only", "regular_read_only"):
            raise RequestError("Unknown catalog target_policy.")
        if item.get("implements_rmw") is not False:
            raise RequestError("This seed selector only supports designs that retain updates on the CPU.")
        validate_request({"contract_version":"draft-0.2", "record_kind":"illustrative", "kernel_id":"catalog-check",
                          "candidates":[{"id":item["id"], "hardware":item.get("hardware")} ]})


def targets(case, policy):
    accesses = case["accesses"]
    if policy == "all":
        return accesses
    if policy == "indexed":
        return [a for a in accesses if a["indexed_addressing"]]
    if policy == "read_only":
        return [a for a in accesses if a["operation"] == "read"]
    return [a for a in accesses if a["operation"] == "read" and "streaming" in a["reported_stream_kind"]]


def select_candidates(case, catalog, catalog_ref, catalog_digest, max_candidates=3):
    if catalog.get("format") == "hardware-catalog-v0.1":
        from archevolve.evidence_select import select_evidence_candidates
        return select_evidence_candidates(case, catalog, catalog_ref, catalog_digest, max_candidates)
    validate_catalog(catalog)
    if type(max_candidates) is not int or max_candidates < 1:
        raise RequestError("max_candidates must be at least 1.")
    trace, eligible = [], []
    for order, entry in enumerate(catalog["entries"]):
        checks = {key:case["signals"].get(key) for key in entry["required_signals"]}
        matches = targets(case, entry["target_policy"])
        row = {"catalog_entry":entry["id"], "signal_checks":checks, "target_access_ids":[a["id"] for a in matches],
               "preference_signal":entry.get("preferred_when"), "preference_value":case["signals"].get(entry.get("preferred_when")), "decision":None}
        if not all(value is True for value in checks.values()) or not matches:
            row["decision"] = "not_selected_by_current_rules"
            row["reason"] = "Required signal is false/unknown or no eligible accesses; not a proof of hardware incompatibility."
        else:
            priority = 0 if entry["entry_kind"] == "baseline" else 1 if row["preference_value"] is True else 2
            row["exploration_priority_class"] = ["comparison", "preferred_by_reported_features", "other_eligible"][priority]
            eligible.append((priority, order, entry, row))
        trace.append(row)
    eligible.sort(key=lambda x:(x[0],x[1]))
    chosen, deferred = eligible[:max_candidates], eligible[max_candidates:]
    for _, _, _, row in deferred:
        row["decision"] = "eligible_outside_candidate_budget"
    candidates = []
    for _, _, entry, row in chosen:
        row["decision"] = "selected_for_exploration"
        hw = deepcopy(entry["hardware"])
        for block in hw["blocks"]:
            block["component_ref"] = entry["id"] + "/" + block["id"]
            block["component_revision"] = entry["revision"]
        candidate_id = case["case_id"] + "--" + entry["id"]
        notes = [issue["message"] for issue in case["issues"] if issue["severity"] != "interpretation_resolved"]
        candidates.append({
            "id":candidate_id, "status":"comparison_unmeasured" if entry["entry_kind"] == "baseline" else "conditional",
            "catalog_entry":entry["id"], "catalog_entry_revision":entry["revision"], "catalog_evidence_status":entry["evidence_status"],
            "target_statement_ids":[], "target_access_ids":row["target_access_ids"],
            "rationale":entry["rationale"], "selection_basis":deepcopy(row),
            "evidence_refs":["input:"+case["input_sha256"], "catalog:"+catalog_digest],
            "taxonomy_refs":deepcopy(entry["taxonomy_refs"]),
            "applicability_conditions":deepcopy(entry["open_conditions"]),
            "unresolved_requirements":notes + deepcopy(entry["open_conditions"]),
            "hardware":hw,
            "preserved_cpu_effects":{"rmw":case["rmw"]["kind"], "must_preserve":True, "queue_updates":"Retain original discovery/append behavior."},
            "software_handoff":{"intrinsic_spec_owner":"Peter", "boundary_notes":"Provisional hardware-side sketch. Do not rewrite mutable parent CAS as a plain gather/store. Confirm source bindings, semantics, and actual implementation before deriving a usable intrinsic."},
            "parameter_tuning_owner":"arch_evolve",
        })
    result = {
        "contract_version":"draft-0.2", "record_kind":"illustrative",
        "selection_backend":"offline_rules", "llm_calls":0,
        "input_ref":case["input_ref"], "input_revision":case["source_binding"]["reported_revision"],
        "input_sha256":case["input_sha256"], "catalog_ref":catalog_ref,
        "catalog_revision":catalog["revision"], "catalog_sha256":catalog_digest,
        "kernel_id":case["case_id"],
        "workload_summary":{"function":case["kernel"]["function"], "evidence_status":case["evidence_status"], "source_binding":case["source_binding"], "selection_signals":case["signals"], "rmw":case["rmw"],
                            "profiling_provenance":deepcopy(case.get("profiling_provenance")),
                            "frontier_evolution_profile":deepcopy(case.get("frontier_evolution_profile")),
                            "profiling_context":deepcopy(case.get("profiling_context")),
                            "reported_counters":deepcopy(case.get("reported_counters")),
                            "methodology":case.get("methodology"), "reported_distance_scopes":{a["array"]:a.get("reported_mean_distance_scope") for a in case["accesses"] if a.get("reported_mean_distance_scope")}},
        "interpretation_notes":["Generated by deterministic offline rules, not an LLM or evaluator.", "These are catalog-seeded family sketches, not verified implementations or performance winners.", "Source uncertainty and excluded metrics remain explicit. Reported architectural directives are not commands.", "Different graphs/runs are processed separately. All tuning values remain open; the CPU baseline is a comparison, not a measured result."] + [issue["message"] for issue in case["issues"] if issue["severity"] == "interpretation_resolved"],
        "resolved_measurement_interpretations":[deepcopy(issue) for issue in case["issues"] if issue["severity"] == "interpretation_resolved"],
        "candidates":candidates,
        "clarification_requests":[deepcopy(issue) for issue in case["issues"] if issue["severity"] != "interpretation_resolved"],
    }
    validate_request(result)
    return result, trace
