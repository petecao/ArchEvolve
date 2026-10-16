"""Catalog-independent capability planning before retrieval.

Deterministic semantic grouping, not learned clustering or hardware synthesis.
Source dependency groups and proposed hardware capability groups are distinct.
"""

from copy import deepcopy
from hashlib import sha256
import json

from tools.render_mermaid import RequestError

QUERY_FIELDS = ("operation", "subtype", "address_pattern", "payload_type", "index_width_bits", "require_old_value")


def family(request):
    if request["operation"] == "read" and request["subtype"] == "gather" and request["address_pattern"] in {
            "indirect", "ranged_indirect", "chained_indirect"}:
        return "indexed-read"
    if request["operation"] == "read" and request["subtype"] == "stream_load" and request["address_pattern"] in {
            "sequential", "constant_stride"}:
        return "stream-read"
    return "effect-" + request["operation"] + "-" + request["subtype"]


def partition_key(request):
    # Unknown type/width evidence cannot establish compatibility between accesses.
    uncertain = request.get("missing_workload_evidence") or request["payload_type"] is None or (
        request["address_pattern"] in {"indirect", "ranged_indirect", "chained_indirect"} and request["index_width_bits"] is None)
    return (family(request), request["payload_type"], request["index_width_bits"], request["require_old_value"],
            request["id"] if uncertain else None)


def plan_hardware(case, requests, source_groups):
    """Plan one conjunctive block query per compatible group before seeing a catalog."""
    ids = [r["id"] for r in requests]
    if len(ids) != len(set(ids)):
        raise RequestError("Capability request IDs must be unique before planning.")
    by_access = {a["id"]: a for a in case.get("accesses", [])}
    partitions = {}
    for request in sorted(requests, key=lambda r: r["id"]):
        partitions.setdefault(partition_key(request), []).append(request)
    blocks = []
    for key, members in partitions.items():
        member_ids = [r["id"] for r in members]
        suffix = sha256(json.dumps(member_ids, separators=(",", ":")).encode()).hexdigest()[:10]
        bid = "block-" + key[0] + "-" + suffix
        clauses = {}
        for member in members:
            signature = tuple(member[f] for f in QUERY_FIELDS)
            if signature not in clauses:
                clauses[signature] = {"id": f"{bid}-cap-{len(clauses)+1:02d}",
                                      "query": {f: member[f] for f in QUERY_FIELDS}, "request_ids": []}
            clauses[signature]["request_ids"].append(member["id"])
        statements = sorted({s for r in members for s in r.get("statement_ids", [])})
        unknown = sorted({x for r in members for x in r.get("missing_workload_evidence", [])})
        if any(r.get("statement_binding_status") == "unbound" for r in members):
            unknown.append("source_statement_binding")
        context = []
        for member in members:
            access = by_access.get(member["access_id"], {})
            context.append({"request_id": member["id"], "access_id": member["access_id"],
                "array": member["array"], "statement_ids": deepcopy(member.get("statement_ids", [])),
                "source_locations": deepcopy(member.get("source_locations", [])),
                "statement_binding_status": member.get("statement_binding_status"),
                "mutable_target": member.get("mutable_target", False),
                "address_expression": access.get("reported_index_expression"),
                "operation_mapping_basis": member.get("mapping_basis"),
                "reported_features": {k: deepcopy(access.get(k)) for k in (
                    "reported_mean_index_distance", "reported_mean_byte_stride", "reported_stream_stride_bytes",
                    "reuse_distance", "reuse_frequency", "tile_working_set_bytes", "evidence_refs")}})
        blocks.append({"id": bid, "family": key[0], "member_request_ids": member_ids,
            "member_access_ids": sorted({r["access_id"] for r in members}), "statement_ids": statements,
            "grouping_basis": "same operation family, exact known payload/index types and old-value requirement",
            "grouping_rationale": ("Related indexed-read shapes can request a shared capability superset; each shape remains a separate obligation."
                if key[0] == "indexed-read" else "Compatible streaming operations share a request." if key[0] == "stream-read"
                else "Side-effect operations remain separate from reads and different update subtypes."),
            "status": "proposed_needs_evidence" if unknown else "proposed_capability_group",
            "missing_evidence": unknown, "capability_clauses": list(clauses.values()), "members": context,
            "required_capabilities": {"operations": sorted({r["operation"] for r in members}),
                "subtypes": sorted({r["subtype"] for r in members}),
                "address_patterns": sorted({r["address_pattern"] for r in members}),
                "payload_types": sorted({r["payload_type"] for r in members if r["payload_type"]}),
                "index_width_bits": sorted({r["index_width_bits"] for r in members if r["index_width_bits"] is not None}),
                "require_old_value": key[3], "mutable_read_request_ids": [r["id"] for r in members if r.get("mutable_target") and r["operation"] == "read"]},
            "resource_requirements": {"simultaneous_streams": None, "aggregate_working_set_bytes": None,
                "minimum_tile_capacity": None, "schedule": "unresolved",
                "note": "Do not sum footprints or assume concurrent execution from a grouping; derive lifetimes, reuse and sharing first."},
            "mapping_obligations": ["Preserve per-member address expressions, numeric domains and value identity.",
                "Establish dependencies, ordering, completion, aliases, mutability and CPU/device visibility.",
                "Establish scheduling, resource ownership/capacity and per-thread contexts before sharing one physical instance."],
            "optional_generalizations": [], "hardware_composition_status": "not_established"})
    # Larger repeated capability groups appear first for review, never as a performance ranking.
    blocks.sort(key=lambda b: (-len(b["member_request_ids"]), b["id"]))
    statement_blocks = {}
    for block in blocks:
        for sid in block["statement_ids"]:
            statement_blocks.setdefault(sid, []).append(block["id"])
    dependencies = []
    seen = set()
    for group in source_groups:
        for dep in group["dependencies"]:
            pair = (dep["from_statement"], dep["to_statement"])
            if pair in seen:
                continue
            seen.add(pair)
            dependencies.append({**dep, "from_block_ids": statement_blocks.get(pair[0], []),
                "to_block_ids": statement_blocks.get(pair[1], []), "basis": group["basis"],
                "meaning": "source dependency only, not a hardware wire or permission to reorder"})
    separations = []
    for i, left in enumerate(blocks):
        for right in blocks[i+1:]:
            reasons = []
            if left["family"] != right["family"]:
                reasons.append("different operation/address families; merging would demand additional generality")
            for field in ("payload_types", "index_width_bits", "require_old_value"):
                if left["required_capabilities"][field] != right["required_capabilities"][field]:
                    reasons.append("different " + field)
            if not reasons:
                reasons.append("insufficient type/width evidence to establish compatibility")
            separations.append({"left": left["id"], "right": right["id"], "reasons": reasons})
    return {"format": "hardware-plan-v0.1", "planner": "deterministic_semantic_grouping_v1",
        "kernel_id": case["case_id"], "input_sha256": case.get("input_sha256"),
        "source_binding": deepcopy(case.get("source_binding")), "catalog_used_for_grouping": False,
        "blocks": blocks, "separations": separations, "source_dependencies": dependencies,
        "source_context_groups": deepcopy(source_groups),
        "counts": {"access_requests": len(requests), "planned_blocks": len(blocks),
                   "unique_typed_clauses": sum(len(b["capability_clauses"]) for b in blocks)},
        "scope": "Requests for capability groups, not a physical partition, proved composition or cost-optimal clustering.",
        "generalization_policy": "Minimum observed capability union only; costed generalizations require explicit future proposals."}


def query_block(catalog, block):
    """Conjunctive lookup: one source-scoped design AND one role must cover every clause.

    The current YAML catalog exposes operation queries, so this adapter evaluates
    the typed clauses internally, then intersects evidence by design and role.
    It never unions different catalog designs into a synthesized accelerator.
    """
    from archevolve.hardware_catalog import query_catalog
    results, coverage = [], {}
    for clause in block["capability_clauses"]:
        result = query_catalog(catalog, **clause["query"])
        results.append({"clause_id": clause["id"], "member_request_ids": clause["request_ids"], **result})
        for match in result["matches"]:
            if match["operation"]["support"] == "unknown":
                continue
            key = (match["design_id"], match["operation"]["execution_role"])
            coverage.setdefault(key, {}).setdefault(clause["id"], []).append(match)
    all_ids = {c["id"] for c in block["capability_clauses"]}
    options, partial = [], []
    for (did, role), covered in sorted(coverage.items()):
        missing = sorted(all_ids - set(covered))
        evidence_gaps = sorted({gap for matches in covered.values() for match in matches
                                for gap in match.get("missing_capability_evidence", [])})
        row = {"missing_capability_evidence": evidence_gaps,
               "missing_workload_evidence": deepcopy(block["missing_evidence"]), "design_id": did, "execution_role": role, "covered_clause_ids": sorted(covered), "missing_clause_ids": missing,
               "satisfies_returned_value_request": False if role == "assist" else None,
               "joint_execution_status": "requires_mapping_and_resource_review"}
        if missing:
            row["status"] = "partial_not_a_block_solution"
            partial.append(row)
        else:
            row["status"] = "assist_alternative_not_executor" if role == "assist" else "candidate_cover_needs_evidence" if evidence_gaps or block["missing_evidence"] else "conditional_capability_cover"
            options.append(row)
    return {"block_id": block["id"], "member_request_ids": block["member_request_ids"],
        "capability_results": results, "options": options, "partial_designs": partial,
        "status": "options_for_review" if options else "needs_information_or_explicit_replanning",
        "scope": "Operation evidence for every clause from one catalog record and role. Mapping, resources, mutability and composition remain unproved."}


def planning_artifacts(plan, results):
    """Small source-to-block diagrams. Generated node IDs avoid interpreting input text."""
    import yaml
    requests = [m for b in plan["blocks"] for m in b["members"]]
    requests.sort(key=lambda m: m["request_id"])
    def label(value):
        return str(value).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", " ")
    before = ["flowchart LR", '  db["Hardware catalog"]']
    after = ["flowchart LR", '  db["Hardware catalog: options per planned block"]']
    block_for = {r: i for i, b in enumerate(plan["blocks"]) for r in b["member_request_ids"]}
    for i, member in enumerate(requests):
        text = label(member["request_id"] + ": " + member["array"])
        before += [f'  r{i}["{text}"] --> q{i}["Independent access query"]', f"  q{i} --> db"]
        after += [f'  r{i}["{text}"] --> b{block_for[member["request_id"]]}']
    for i, block in enumerate(plan["blocks"]):
        title = {"indexed-read": "Indexed-read group", "stream-read": "Streaming-read group"}.get(block["family"], "Separate update request")
        text = label(title + " (" + str(len(block["member_request_ids"])) + " access requests)")
        text += "<br/>" + label(", ".join(block["required_capabilities"]["address_patterns"]))
        after += [f'  b{i}["{text}"] --> db']
    lines = ["# Hardware planning before catalog lookup", "", plan["scope"], "",
             "| Proposed block | Source requests | Required shapes | Catalog option status |", "|---|---|---|---|"]
    for block, result in zip(plan["blocks"], results):
        vals = [block["id"], ", ".join(block["member_request_ids"]), ", ".join(block["required_capabilities"]["address_patterns"]), result["status"]]
        lines.append("| " + " | ".join(label(x).replace("|", "\\|") for x in vals) + " |")
    lines += ["", "## Before: independent requests", "", "```mermaid", *before, "```", "",
              "## After: capability planning", "", "```mermaid", *after, "```", "",
              "Grouping suggests shared capabilities, not simultaneous execution, a physical partition or permission to reorder.",
              "Source dependencies, mutable reads, unresolved resources and CPU effects remain in the YAML.",
              "A catalog option must cover every typed clause using one design record and one execution role.",
              "Partial matches are retained as diagnostics, not silently combined into a new accelerator.", "",
              "[Plan](hardware-plan.yaml) · [Catalog results](block-catalog-results.yaml)", ""]
    return {"hardware-plan.yaml": yaml.safe_dump(plan, sort_keys=False),
            "block-catalog-results.yaml": yaml.safe_dump({"format": "block-catalog-results-v0.1", "results": results}, sort_keys=False),
            "planning-before.mmd": "\n".join(before)+"\n", "planning-after.mmd": "\n".join(after)+"\n",
            "planning.md": "\n".join(lines)}
