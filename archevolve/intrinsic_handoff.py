"""Draft intrinsic descriptions from catalog contracts, without inventing an ABI."""

from copy import deepcopy
import hashlib
import json

import yaml

from archevolve.mechanisms import render_mechanisms, render_structure
from tools.render_mermaid import RequestError, label, render_candidate

FORMAT = "intrinsic-handoff-v0.1"


def md(value):
    return ("unknown" if value is None else str(value)).replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|").replace("`", "\\`")


def draft_intrinsics(request, candidate):
    """One description per source operation; a documented sequence stays a sequence."""
    operations = []
    for option in candidate["operation_options"]:
        op = option["operation"]
        matches = option["matched_requests"]
        assist = op["execution_role"] == "assist"
        targets = ", ".join(dict.fromkeys(r["array"] for r in matches))
        intent = (f"Configure {op['subtype']} assistance for accesses to {targets}; the program still obtains its required values/updates through its original execution path."
                  if assist else f"Propose {op['subtype']} for the matched accesses to {targets}, subject to the catalog's mapping requirements.")
        realization = deepcopy(op.get("realization", {"kind": None, "description": None, "claim_refs": []}))
        operations.append({
            "id": op["id"], "intent": intent, "execution_role": op["execution_role"],
            "operation": op["operation"], "subtype": op["subtype"], "support": op["support"],
            "realization": realization,
            "logical_inputs": [{"request_id": r["id"], "target_array": r["array"],
                "address_pattern": r["address_pattern"], "requested_payload_type": r["payload_type"],
                "requested_index_width_bits": r["index_width_bits"], "mutable_target": r["mutable_target"],
                "index_width_status": "not_applicable_to_loaded_index_request" if r["address_pattern"] == "sequential" else "requested" if r["index_width_bits"] is not None else "unknown",
                "statement_ids": deepcopy(r["statement_ids"]), "source_locations": deepcopy(r["source_locations"]),
                "statement_binding_status": r["statement_binding_status"],
                "mapping_basis": r["mapping_basis"]} for r in matches],
            "input_scope": "workload_intent_and_design_contract_not_a_concrete_operand_list",
            "design_interface": deepcopy(candidate["software_handoff"]["interface"]),
            "supported_type_constraints": deepcopy(op.get("type_constraints")),
            "datatype_notes": op["datatype_notes"],
            "preconditions": {"design_requirements_ref": "candidate.yaml#requirements",
                "status": "not_discharged", "mutable_target_review_required": any(r["mutable_target"] for r in matches)},
            "postconditions": {"catalog_result": deepcopy(op["result"]),
                "satisfies_program_result": "no_assistance_only" if assist else "conditional_on_mapping_proof",
                "program_equivalence_status": "not_established"},
            "ordering": deepcopy(op["ordering"]), "completion": deepcopy(op["completion"]),
            "limitations": deepcopy(op["limitations"]), "claim_refs": deepcopy(op["claim_refs"]),
            "missing_capability_evidence": deepcopy(option["missing_capability_evidence"]),
            "missing_workload_evidence": sorted({m for r in matches for m in r["missing_workload_evidence"]}),
            "concrete_signature": None, "implementation_ref": None,
        })
    draft = {
        "format": FORMAT, "status": "draft_requires_review", "backend": "offline_contract_projection", "llm_calls": 0,
        "kernel_id": request["kernel_id"], "candidate_id": candidate["id"],
        "catalog_design_id": candidate["catalog_design_id"], "catalog_design_revision": candidate["catalog_design_revision"],
        "provenance": {"input_sha256": request["input_sha256"], "catalog_sha256": request["catalog_sha256"],
            "source_context_sha256": (request["workload_summary"].get("source_context") or {}).get("sha256"),
            "evidence_ref": "candidate.yaml#source_evidence"},
        "operations": operations, "request_groups": deepcopy(candidate["request_groups"]),
        "workload_semantics": {"reported_rmw": deepcopy(request["workload_summary"].get("rmw")),
            "source_binding": deepcopy(request["workload_summary"].get("source_binding")),
            "evidence_status": request["workload_summary"].get("evidence_status")},
        "requirements": deepcopy(candidate["requirements"]), "requirement_status": "not_discharged",
        "parameter_contract": deepcopy(candidate["parameter_contract"]), "selected_configuration": {},
        "mechanism_context": deepcopy(candidate["mechanism_context"]),
        "execution_plan": deepcopy(candidate["execution_plan"]),
        "review_questions": [
            {"id": "placement", "owner": "Peter", "question": "Confirm the matching source statements, region, phase and allowable replacement scope. Manual bindings are proposals; profiling placement is not confirmed."},
            {"id": "abi", "owner": "Peter/Eric", "question": "Specify exact operands, index arithmetic, masks/produced lengths, concrete types, invocation and completion API for each chosen operation or sequence."},
            {"id": "legality", "owner": "Peter/Eric", "question": "Discharge ownership, numeric domains, mutable-load freshness, ordering, repeated-target/concurrency and result validity requirements. Preserve CAS success and queue side effects."},
            {"id": "mechanisms", "owner": "Eric", "question": "Add located internal buffering/coalescing/reordering/issue/dependency/completion details and conditions limiting performance."},
            {"id": "composition", "owner": "Josh/Eric", "question": "Establish whether related requests can share one legal mapping; the workload group and interface view do not prove combined execution."},
            {"id": "implementation", "owner": "Yan-Ru", "question": "After Peter's spec is agreed, choose or synthesize an implementation and verify the rewritten kernel against the frozen correctness oracle."},
        ],
        "readiness": {"description_generated": True, "concrete_abi_agreed": False,
                      "mapping_requirements_discharged": False, "implementation_generated": False,
                      "correctness_verified": False, "performance_evaluated": False},
    }
    validate_draft(draft, candidate)
    return draft


def validate_draft(draft, candidate):
    """Guard critical semantics when projecting the source contracts."""
    def require(condition, message):
        if not condition:
            raise RequestError("Intrinsic draft: " + message)
    require(draft.get("format") == FORMAT and draft.get("status") == "draft_requires_review", "unsupported format/status")
    originals = {o["operation"]["id"]: o["operation"] for o in candidate["operation_options"]}
    projected = draft.get("operations", [])
    ids = [o["id"] for o in projected]
    require(len(ids) == len(set(ids)) and set(ids) == set(originals), "operation IDs must exactly cover candidate options")
    require(draft["requirements"] == candidate["requirements"], "design requirements lost or changed")
    require(draft["parameter_contract"] == candidate["parameter_contract"] and draft["selected_configuration"] == {}, "parameter states changed")
    for item in projected:
        original = originals[item["id"]]
        for field in ("execution_role", "operation", "subtype", "support", "ordering", "completion", "claim_refs", "limitations"):
            require(item[field] == original[field], f"{item['id']} altered {field}")
        require(item["postconditions"]["catalog_result"] == original["result"], "result contract changed")
        require(item["concrete_signature"] is None and item["implementation_ref"] is None, "unreviewed ABI/implementation must stay null")
        require(item["realization"] == original.get("realization", {"kind": None, "description": None, "claim_refs": []}), "sequence/primitive distinction changed")
        require(item["supported_type_constraints"] == original.get("type_constraints"), "type constraints changed")
        if item["execution_role"] == "assist":
            require(item["postconditions"]["satisfies_program_result"] == "no_assistance_only", "assist upgraded to executor")


def description_markdown(draft, candidate):
    lines = ["# Draft intrinsic descriptions", "", f"Candidate: **{md(candidate['catalog_entry'])}** ({md(candidate['status'])}).",
             "", "Generated from located catalog contracts. Peter owns the concrete software spec; Eric resolves hardware constraints. ABI and implementation are pending review.", "",
             "[Candidate and evidence](candidate.yaml) · [Structured draft](intrinsic-draft.yaml) · [Interface diagram](interface.mmd) · [Workload context](context.mmd) · [Mechanism checklist](mechanisms.mmd)", ""]
    for item in draft["operations"]:
        lines += [f"## {md(item['id'])}", "", md(item["intent"]), "",
                  f"Role: **{md(item['execution_role'])}**. Source support: **{md(item['support'])}**. Realization: **{md(item['realization']['kind'] or 'unrecorded')}**.", "",
                  "### Inputs and placement", "", "The following are workload intents. The exact operand list and signature require Peter/Eric's specification.", "",
                  "| Request | Array | Pattern | Requested payload / index bits | Statements |", "|---|---|---|---|---|"]
        for i in item["logical_inputs"]:
            width = "n/a (no loaded-index request)" if i["index_width_status"] == "not_applicable_to_loaded_index_request" else md(i["requested_index_width_bits"])
            lines.append(f"| {md(i['request_id'])} | {md(i['target_array'])} | {md(i['address_pattern'])} | {md(i['requested_payload_type'])} / {width} | {md(', '.join(i['statement_ids']) or 'unbound')} |")
        lines += ["", "Design-wide software contract: " + md(item["design_interface"]["software_supplies"]), "",
                  "Invocation: " + md(item["design_interface"]["invocation"]), "",
                  "### Result and behavior", "",
                  "Result: " + md(item["postconditions"]["catalog_result"]["form"]), "",
                  "Validity: " + md(item["postconditions"]["catalog_result"]["validity"]), "",
                  "Old-value behavior: " + md(item["postconditions"]["catalog_result"]["old_value"]), "",
                  "Ordering: " + md(item["ordering"]["description"]), "",
                  "Completion: " + md(item["completion"]["event"]), "",
                  "Visibility: " + md(item["completion"]["visibility"]), "",
                  "Type evidence: " + md(item["datatype_notes"]), "",
                  "Missing capability evidence: " + md(", ".join(item["missing_capability_evidence"]) or "none in the query; mapping requirements still apply"), "",
                  "Missing workload evidence: " + md(", ".join(item["missing_workload_evidence"]) or "none in the typed query; runtime placement/legality still require review"), ""]
        if item["preconditions"]["mutable_target_review_required"]:
            lines += ["**Mutable target:** establish load freshness and synchronization before buffering or hoisting the access.", ""]
        if item["execution_role"] == "assist":
            lines += ["**Assistance:** this interface does not supply the required program load result or replace its atomic update.", ""]
        lines += ["Limitations:", ""] + (["- " + md(x) for x in item["limitations"]] or ["No additional operation-specific limitations recorded; design requirements still apply."]) + [""]
    lines += ["## Preconditions and legality", "", "The following catalog requirements remain undischarged:", ""]
    lines += [f"- **{md(r['id'])}** ({md(r['scope'])}): {md(r['description'])}" for r in draft["requirements"]]
    lines += ["", "## Related accesses and side effects", "", "A shared request group carries source context; it does not establish hardware fusion.", ""]
    rmw = draft["workload_semantics"]["reported_rmw"] or {}
    primitive = rmw.get("reported_details", {}).get("primitive")
    if primitive:
        lines += ["Reported workload update to preserve: " + md(primitive) + ". This is source/workload intent, not the proposed intrinsic signature.", ""]
    for group in draft["request_groups"]:
        lines += [f"- **{md(group['id'])}**: {md(group['description'])}",
                  "  Covered: " + md(", ".join(group["covered_request_ids"])) + ". Uncovered: " + md(", ".join(group["uncovered_request_ids"]) or "none") + "."]
    lines += ["", "## Internal mechanism information", ""]
    for m in draft["mechanism_context"]["annotations"]:
        lines.append(f"- **{md(m['kind'])}**: {md(m['description'] if m['status'] == 'described' else 'unknown; annotation needed from Eric')}")
    lines += ["", "Missing descriptions do not imply that the hardware lacks the mechanism. No speedup is inferred from operation matching.", "",
              "## Next review", ""]
    lines += [f"- **{md(q['owner'])}**: {md(q['question'])}" for q in draft["review_questions"]]
    return "\n".join(lines) + "\n"


def render_workload_context(request, candidate):
    """Explicit statement relations, distinct from hardware-interface wiring."""
    groups = candidate["request_groups"]
    statements = {s["id"]: s for g in groups for s in g["context_statements"]}
    covered = {sid for o in candidate["operation_options"] for r in o["matched_requests"] for sid in r["statement_ids"]}
    requested = {sid for r in request["capability_requests"] for sid in r["statement_ids"]}
    nodes = {sid: f"s{index}" for index, sid in enumerate(statements)}
    lines = ["flowchart TB", '  notice["Workload statement relations — manual source proposal; no hardware wiring implied"]:::notice']
    for sid, statement in statements.items():
        state = "matched request; legality pending" if sid in covered else "uncovered request" if sid in requested else "context side effect; preserve"
        style = "matched" if sid in covered else "retained"
        lines.append(f'  {nodes[sid]}["{label(sid, statement["code"], state)}"]:::{style}')
    edges = {(e["from_statement"], e["to_statement"]) for g in groups for e in g["dependencies"]}
    for source, target in sorted(edges):
        lines.append(f'  {nodes[source]} -->|"recorded statement relation"| {nodes[target]}')
    if not statements:
        lines.append('  unbound["No bound grouped source context; confirm placement with Peter"]:::retained')
    lines += ["  classDef notice fill:#dbeafe,stroke:#2563eb,color:#172554",
              "  classDef matched fill:#dcfce7,stroke:#16a34a,color:#14532d",
              "  classDef retained fill:#fef3c7,stroke:#d97706,color:#78350f"]
    return "\n".join(lines) + "\n"


def build_handoff_artifacts(request, request_digest):
    artifacts, packages = {}, []
    for index, candidate in enumerate(request["candidates"], 1):
        if candidate.get("catalog_entry") == "cpu-baseline":
            continue
        folder = f"candidate-{index:02d}"
        draft = draft_intrinsics(request, candidate)
        files = {
            "intrinsic-draft.yaml": yaml.safe_dump(draft, sort_keys=False, allow_unicode=True),
            "candidate.yaml": yaml.safe_dump(candidate, sort_keys=False, allow_unicode=True),
            "README.md": description_markdown(draft, candidate),
            "interface.mmd": render_candidate(request, candidate),
            "context.mmd": render_workload_context(request, candidate),
            "mechanisms.mmd": render_mechanisms(candidate),
        }
        from archevolve.hardware_behavior import build_behavior_artifacts
        files.update(build_behavior_artifacts(request, candidate))
        files["README.md"] += "\n[How the accelerator works and its observable semantics](hardware-behavior.md) · [Behavior YAML](hardware-behavior.yaml)\n"
        structure = render_structure(candidate)
        if structure is not None:
            files["structure.mmd"] = structure
            files["README.md"] += "\n[Source-backed logical block paths](structure.mmd) describe the paper's architecture, not a port netlist or a proved mapping of all BFS operations.\n"
        manifest = {"format": FORMAT, "candidate_id": candidate["id"], "hardware_request_sha256": request_digest,
                    "files": {name: hashlib.sha256(content.encode()).hexdigest() for name, content in files.items()}}
        files["manifest.json"] = json.dumps(manifest, indent=2) + "\n"
        for name, content in files.items():
            artifacts[f"{folder}/{name}"] = content
        packages.append({"candidate_id": candidate["id"], "catalog_entry": candidate["catalog_entry"], "folder": folder})
    lines = ["# Candidate intrinsic handoffs", "", "Draft descriptions and source contracts for Peter/Yan-Ru; one option per package. The unchanged CPU comparison needs no new intrinsic.", "",
             "| Option | Package | Draft contract | Interface diagram |", "|---|---|---|---|"]
    for p in packages:
        f = p["folder"]
        lines.append(f"| {md(p['catalog_entry'])} | [Description]({f}/README.md) | [YAML]({f}/intrinsic-draft.yaml) | [Mermaid]({f}/interface.mmd) |")
    lines += ["", "Review one option at a time. A package may list multiple operation alternatives or a documented sequence; it does not declare a composed accelerator or a finalized ABI.", ""]
    artifacts["README.md"] = "\n".join(lines)
    artifacts["manifest.json"] = json.dumps({"format": FORMAT, "packages": packages}, indent=2) + "\n"
    return artifacts
