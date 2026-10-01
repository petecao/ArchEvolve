"""Map BFS features to Eric's operation evidence, never to invented hardware.

The diagrams are software-facing operation contract views. They are not a
physical partition/netlist and do not assert that retrieved operations compose.
"""

from copy import deepcopy
import re
from textwrap import shorten

from archevolve.hardware_catalog import query_catalog, validate_catalog
from archevolve.mechanisms import mechanism_context
from archevolve.workload_context import candidate_groups, request_groups, request_statement_context
from tools.render_mermaid import RequestError, validate_request


def payload_type(access):
    if access.get("width_status") == "unresolved_conflict":
        return None
    match = re.search(r"\b(u?int(?:32|64)|float(?:32|64))(?:_t)?\b", access.get("reported_element_type") or "")
    return match[1] if match else None


def capability_requests(case):
    """Explicit BFS mapping hypotheses; regularity statistics do not erase indirection."""
    requests, gaps = [], []
    by_array = {a["array"]:a for a in case["accesses"]}
    loop = case.get("reported_loop_structure") or {}
    inner_domain = str(loop.get("inner_level", {}).get("domain", ""))

    def add(access, operation, subtype, pattern, index_bits, basis, purpose):
        dtype = payload_type(access)
        missing = []
        if dtype is None:
            missing.append("workload_payload_type")
        if pattern in {"indirect", "ranged_indirect", "chained_indirect"} and index_bits is None:
            missing.append("workload_index_width")
        requests.append({"id":f"{access['id']}-{purpose}", "access_id":access["id"], "array":access["array"],
                         "purpose":purpose, "operation":operation, "subtype":subtype, "address_pattern":pattern,
                         "payload_type":dtype, "index_width_bits":index_bits, "require_old_value":False,
                         "mapping_basis":basis, "mapping_status":"proposed_from_reported_pattern",
                         "missing_workload_evidence":missing,
                         **request_statement_context(case, access["array"], purpose),
                         "mutable_target":access["operation"] == "read_modify_write"})

    for access in case["accesses"]:
        bits = None
        index_expression = access.get("reported_index_expression") or ""
        index_array = index_expression.split("[", 1)[0].strip()
        index_access = by_array.get(index_array)
        if index_access and index_access.get("diagram_element_bytes"):
            bits = index_access["diagram_element_bytes"] * 8
        if access["array"] == "g.out_neighbors_" and "VertexOffsets" in inner_domain:
            offset = by_array.get("VertexOffsets", {})
            bits = offset.get("diagram_element_bytes")
            bits = bits * 8 if bits else None
            pattern = "ranged_indirect"
            basis = "Reported CSR row bounds plus segmented neighbor traversal; range realization/continuation still needs mapping proof."
        elif access["indexed_addressing"]:
            pattern = "indirect"
            basis = "Reported loaded-index expression; near-unit measured distance does not turn this into a proven stream."
        elif "streaming" in access["reported_stream_kind"]:
            pattern = "sequential"
            basis = "Reported sequential stream; actual bounds/stride and source binding remain requirements."
        else:
            gaps.append({"id":access["id"]+"-shape", "message":"Address shape cannot be mapped to the catalog without more evidence.", "access_id":access["id"]})
            continue
        if access["operation"] in {"read", "read_modify_write"}:
            add(access, "read", "stream_load" if pattern == "sequential" else "gather", pattern, bits, basis, "read")
        if access["operation"] == "read_modify_write":
            if access.get("rmw_subtype") == "conditional_compare_and_swap":
                add(access, "read_modify_write", "cas", pattern, bits,
                    "Original conditional CAS requires comparison/update semantics and success handling; returned old values are not a substitute.", "update")
            else:
                gaps.append({"id":access["id"]+"-update", "message":"Exact update subtype is unknown; no wildcard RMW substitution was requested.", "access_id":access["id"]})
        elif access["operation"] not in {"read", "unknown"}:
            gaps.append({"id":access["id"]+"-operation", "message":"No exact operation mapping implemented for this update kind.", "access_id":access["id"]})
    return requests, gaps


def claim_closure(catalog, design, options):
    refs = set()
    def collect(value):
        if isinstance(value, dict):
            refs.update(value.get("claim_refs", []))
            for key, child in value.items():
                if key != "claim_refs": collect(child)
        elif isinstance(value, list):
            for child in value: collect(child)
    collect(design["interface"])
    collect(design["requirements"])
    collect(design["parameters"])
    collect(design.get("internal_mechanisms", []))
    collect(design.get("performance_hypotheses", []))
    for option in options: collect(option["operation"])
    sources = set(design["source_refs"])
    for ref in refs: sources.update(catalog["claims"][ref]["source_refs"])
    return {"claims":{ref:deepcopy(catalog["claims"][ref]) for ref in sorted(refs)},
            "sources":{ref:deepcopy(catalog["sources"][ref]) for ref in sorted(sources)}}


def interface_view(design, options):
    """One abstract box per catalog operation; no inferred internal wiring."""
    blocks = []
    for option in options:
        op = option["operation"]
        input_excerpt = shorten(design["interface"]["software_supplies"], width=145, placeholder=" ... [full contract in YAML]")
        blocks.append({
            "id":op["id"], "component_ref":design["id"]+":"+op["id"], "component_revision":design["revision"],
            "view_kind":"software_operation_contract_not_physical_block",
            "function":f"{op['operation']} / {op['subtype']} [{op['execution_role']}; {op['support']}]",
            "input_contract_scope":"design_wide_catalog_interface_not_an_operand_signature",
            "inputs":[{"id":"software_supplies", "payload":"Design-wide: " + input_excerpt,
                       "full_payload_contract":design["interface"]["software_supplies"],
                       "type":None, "element_bytes":None, "endpoint_role":"host-facing"}],
            "outputs":[{"id":"catalog_result", "payload":op["result"]["form"] + (" (assistance only; not the requested program result)" if op["execution_role"] == "assist" else ""),
                        "type":None, "element_bytes":None, "endpoint_role":"host-facing"}],
            "behavior":{"ordering":op["ordering"]["description"], "completion":op["completion"]["event"],
                        "visibility":op["completion"]["visibility"], "result_validity":op["result"]["validity"]},
            "parameters":[{"name":p["id"], "state":"open", "value":None, "unit":p["unit"],
                           "allowed_values_or_range":deepcopy(p["domain"]), "constraint_evidence_refs":deepcopy(p["claim_refs"])}
                          for p in design["parameters"] if p["state"] == "open"],
            "reference_parameters":[deepcopy(p) for p in design["parameters"] if p["state"] == "fixed_reference"],
            "unknown_parameters":[deepcopy(p) for p in design["parameters"] if p["state"] == "unknown"],
            "operation_contract":deepcopy(op), "software_interface":deepcopy(design["interface"]),
            "missing_capability_evidence":deepcopy(option["missing_capability_evidence"]),
            "requested_payload_types":sorted({r["payload_type"] for r in option["matched_requests"] if r["payload_type"]}),
            "requested_index_width_bits":sorted({r["index_width_bits"] for r in option["matched_requests"] if r["index_width_bits"]}),
        })
    return {"blocks":blocks, "connections":[],
            "view_notice":"Independent catalog operation interfaces. No physical port widths, component composition or unlisted connections are established by this drawing."}


def select_evidence_candidates(case, catalog, catalog_ref, catalog_digest, max_candidates=4):
    validate_catalog(catalog)
    if type(max_candidates) is not int or max_candidates < 1:
        raise RequestError("max_candidates must be at least 1, including the CPU comparison.")
    requests, gaps = capability_requests(case)
    workload_groups = request_groups(case, requests)
    designs = {d["id"]:d for d in catalog["designs"]}
    groups, trace = {}, []
    for request in requests:
        result = query_catalog(catalog, operation=request["operation"], subtype=request["subtype"],
                               address_pattern=request["address_pattern"], payload_type=request["payload_type"],
                               index_width_bits=request["index_width_bits"], require_old_value=request["require_old_value"])
        row = {"request":deepcopy(request), "query":result["query"], "matches":deepcopy(result["matches"]), "excluded":deepcopy(result["excluded"])}
        trace.append(row)
        if not result["matches"] or all(m["operation"]["support"] == "unknown" for m in result["matches"]):
            gaps.append({"id":request["id"]+"-coverage", "message":"No catalog match supplies this exact requested capability; inspect exclusions and remaining evidence gaps.", "request_id":request["id"]})
        for match in result["matches"]:
            # Unknown support is retained in trace; it is not promoted to an interface option.
            if match["operation"]["support"] == "unknown":
                continue
            op, design = match["operation"], designs[match["design_id"]]
            bucket = ("mapping_reference" if design["record_kind"] == "mapping" else
                      request["purpose"] + ("_execute" if op["execution_role"] == "execute" else "_assist"))
            group = groups.setdefault((design["id"], bucket), {"design":design, "bucket":bucket, "options":{}})
            option = group["options"].setdefault(op["id"], {"operation":deepcopy(op), "catalog_status":match["status"],
                    "missing_capability_evidence":deepcopy(match["missing_capability_evidence"]), "matched_requests":[]})
            option["missing_capability_evidence"] = sorted(set(option["missing_capability_evidence"]) | set(match["missing_capability_evidence"]))
            if option["missing_capability_evidence"]:
                option["catalog_status"] = "needs_evidence"
            option["matched_requests"].append(deepcopy(request))

    preferred_pattern = "indirect" if case["signals"].get("reported_large_jumps") else "sequential" if case["signals"].get("reported_near_unit_indices") else None
    def order(group):
        options = list(group["options"].values())
        missing = sum(len(o["missing_capability_evidence"]) + sum(len(r["missing_workload_evidence"]) for r in o["matched_requests"]) for o in options)
        code = any(o["operation"]["support"] == "code_observed" for o in options)
        return (missing > 0, not code, group["design"]["id"])
    # Reserve exploration diversity before filling remaining slots. This is not performance ranking.
    buckets = ["read_execute", "update_execute", "read_assist", "mapping_reference", "update_assist"]
    ordered = []
    lanes = {bucket:sorted([g for g in groups.values() if g["bucket"] == bucket], key=order) for bucket in buckets}
    while any(lanes.values()):
        for bucket in buckets:
            if lanes[bucket]: ordered.append(lanes[bucket].pop(0))
    selected = ordered[:max_candidates-1]
    selection = []
    for group in ordered:
        selection.append({"design_id":group["design"]["id"], "scope":group["bucket"],
                          "operation_ids":sorted(group["options"]),
                          "decision":"selected_for_exploration" if any(group is g for g in selected) else "eligible_outside_candidate_budget"})

    baseline = {"id":case["case_id"]+"--cpu-baseline", "catalog_entry":"cpu-baseline", "status":"comparison_unmeasured",
                "rationale":"Keep unchanged TDStep as the comparison. This does not assert that an accelerator is better.",
                "target_access_ids":[a["id"] for a in case["accesses"]], "target_statement_ids":[],
                "hardware":{"blocks":[{"id":"existing-cpu", "component_ref":"existing-software-baseline", "function":"Original TDStep including conditional CAS and queue updates.",
                                         "inputs":[], "outputs":[], "parameters":[]}], "connections":[]},
                "software_handoff":{"intrinsic_spec_owner":"Peter", "boundary_notes":"No new intrinsic for the unchanged baseline."}}
    candidates = [baseline]
    for group in selected:
        design = group["design"]
        options = list(group["options"].values())
        options.sort(key=lambda o:(not any(r["address_pattern"] == preferred_pattern for r in o["matched_requests"]) if preferred_pattern else False, o["operation"]["id"]))
        missing = sorted({x for o in options for x in o["missing_capability_evidence"]} |
                         {x for o in options for r in o["matched_requests"] for x in r["missing_workload_evidence"]})
        bucket = group["bucket"]
        update_offload = bucket == "update_execute"
        status = "needs_evidence" if missing else "mapping_reference" if bucket == "mapping_reference" else "assistance_only" if bucket.endswith("assist") else "conditional"
        candidates.append({
            "id":case["case_id"]+"--"+design["id"]+"--"+bucket, "catalog_entry":design["id"]+":"+bucket,
            "status":status, "catalog_design_id":design["id"], "catalog_design_revision":design["revision"], "catalog_record_kind":design["record_kind"],
            "candidate_scope":bucket, "rationale":"Source-scoped operation matches for this workload. This is an interface exploration option, not a composed accelerator, legal rewrite, or performance winner.",
            "target_access_ids":sorted({r["access_id"] for o in options for r in o["matched_requests"]}),
            "target_statement_ids":sorted({sid for o in options for r in o["matched_requests"] for sid in r["statement_ids"]}),
            "request_groups":candidate_groups(workload_groups, options),
            "mechanism_context":mechanism_context(design),
            "operation_options":deepcopy(options), "missing_evidence":missing,
            "source_evidence":claim_closure(catalog, design, options),
            "requirements":deepcopy(design["requirements"]), "requirement_status":"not_discharged_by_retrieval",
            "limitations":deepcopy(design["limitations"]), "parameter_contract":deepcopy(design["parameters"]), "selected_configuration":{},
            "unresolved_requirements":[i["message"] for i in case["issues"] if i["severity"] != "interpretation_resolved"] +
                                      ["Establish workload mapping, ownership/aliasing, concurrency, numeric domains, result validity and completion/visibility; read labels do not imply immutable memory.",
                                       "The catalog is not a physical building-block library; these operation options have not been proved composable."],
            "hardware":interface_view(design, options),
            "execution_plan":{"rmw":"potential_offload_only_after_CAS_mapping_proof" if update_offload else "retain_original_CPU_update",
                              "source_unchanged":True, "queue_updates":"Retain discovery and append semantics; no rewrite has been generated."},
            "software_handoff":{"intrinsic_spec_owner":"Peter", "interface":deepcopy(design["interface"]),
                                "boundary_notes":"Use the exact operation result/validity/ordering/completion contracts and source requirements. Assist is not execute; old values are not CAS; type domains do not prove valid indices. No C signature is synthesized here."},
        })
    questions = [deepcopy(i) for i in case["issues"] if i["severity"] != "interpretation_resolved"] + gaps
    request = {
        "contract_version":"draft-0.2", "record_kind":"illustrative", "selection_backend":"offline_evidence_lookup", "llm_calls":0,
        "representation":"source_scoped_operation_interface_views", "input_ref":case["input_ref"], "input_sha256":case["input_sha256"],
        "input_revision":case["source_binding"]["reported_revision"], "catalog_ref":catalog_ref, "catalog_revision":catalog["revision"], "catalog_sha256":catalog_digest,
        "kernel_id":case["case_id"], "capability_requests":requests,
        "request_groups":workload_groups,
        "workload_summary":{key:deepcopy(case.get(key)) for key in ("kernel", "source_binding", "source_context", "evidence_status", "rmw", "profiling_provenance", "frontier_evolution_profile", "profiling_context", "reported_counters", "methodology")},
        "interpretation_notes":["Offline evidence retrieval and explicit exploration ordering; no LLM or evaluator calls.",
                                "Each box is a catalog operation interface, not an inferred physical component. Unconnected operation options are not a proved composition.",
                                "Reference sizes are preserved as references, not chosen tuning values. Unknown domains stay unknown.",
                                "Mutable read targets are not assumed immutable. CAS support is queried separately; assistance and fetch-old behavior do not establish CAS execution.",
                                "One slot each for reads, update execution and read assistance is considered before remaining alternatives, subject to budget. Within scopes, evidence completeness/code support precede stable IDs; none is a performance rank."],
        "candidates":candidates, "clarification_requests":questions,
        "selection_policy":{"preferred_read_shape_for_display":preferred_pattern, "category_order":buckets, "max_candidates_including_baseline":max_candidates},
    }
    validate_request(request)
    return request, {"capability_queries":trace, "candidate_selection":selection,
        "scope":"Matching evidence and remaining conditions only. Unsupported/unknown operations are retained; no performance or composition proof."}
