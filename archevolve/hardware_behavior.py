"""Describe observable hardware semantics separately from acceleration hypotheses."""

from copy import deepcopy

import yaml

from archevolve.intrinsic_handoff import md
from tools.render_mermaid import RequestError

FORMAT = "hardware-behavior-v0.1"


def describe_behavior(request, candidate):
    """Project exact contracts; internal annotations do not widen operation support."""
    mechanisms = deepcopy(candidate["mechanism_context"])
    described = [m for m in mechanisms["annotations"] if m["status"] == "described"]
    hypotheses = [{**deepcopy(h), "basis": "catalog_conditional_hypothesis", "evaluated": False}
                  for h in mechanisms["performance_hypotheses"]]
    # These are generic proposed benefits, explicitly reasoning rather than new
    # architecture facts. Unknown annotations cannot trigger such a hypothesis.
    if not hypotheses:
        for kind, description, conditions, limits in (
            ("coalescing", "Grouping eligible accesses may reduce redundant memory requests while preserving each logical consumer.",
             ["Multiple reads share a group within the source-described admission window", "The original result association and duplicate consumers are retained"],
             ["Address diversity and finite group/offset capacity", "Translation, cache routing and downstream service behavior"]),
            ("issue_policy", "Source-described issue scheduling may expose independent memory work and improve useful service overlap.",
             ["Enough independent, ready requests under a legal mapping", "Memory resources can serve the selected requests concurrently"],
             ["Producer dependencies, admission stalls and transport backpressure", "Setup/wait overhead and downstream scheduling; fairness is not implied"]),
        ):
            refs = sorted({ref for m in described if m["kind"] == kind for ref in m["claim_refs"]})
            if refs:
                hypotheses.append({"id": "proposed-benefit-" + kind, "description": description,
                    "workload_conditions": conditions, "limiting_factors": limits, "claim_refs": refs,
                    "basis": "derived_reasoning_from_located_mechanism_not_a_measured_result", "evaluated": False})
    operations = []
    for option in candidate["operation_options"]:
        op = option["operation"]
        operations.append({"operation_id": op["id"], "operation": op["operation"], "subtype": op["subtype"],
            "execution_role": op["execution_role"], "support": op["support"],
            "realization": deepcopy(op.get("realization")),
            "requests": [{key: deepcopy(r[key]) for key in (
                "id", "array", "address_pattern", "payload_type", "index_width_bits", "mutable_target", "statement_ids")}
                for r in option["matched_requests"]],
            "result": deepcopy(op["result"]), "ordering": deepcopy(op["ordering"]),
            "completion": deepcopy(op["completion"]), "type_constraints": deepcopy(op.get("type_constraints")),
            "missing_capability_evidence": deepcopy(option["missing_capability_evidence"]),
            "claim_refs": deepcopy(op["claim_refs"]), "limitations": deepcopy(op["limitations"])})
    record = {"format": FORMAT, "status": "draft_requires_mapping_review", "llm_calls": 0,
        "candidate_id": candidate["id"], "kernel_id": request["kernel_id"],
        "design_id": candidate["catalog_design_id"], "design_revision": candidate["catalog_design_revision"],
        "catalog_revision": request["catalog_revision"], "catalog_sha256": request["catalog_sha256"],
        "input_sha256": request["input_sha256"],
        "semantic_scope": "Observable contract for the selected source-scoped operations, conditional on mapping requirements; not a new ABI or whole-accelerator composition.",
        "software_interface": deepcopy(candidate["software_handoff"]["interface"]),
        "desired_observable_semantics": operations,
        "internal_mechanisms": mechanisms["annotations"],
        "internal_scope": "Located edition-specific descriptions; annotation list is not an executable state machine or complete timing policy.",
        "why_it_may_accelerate": hypotheses,
        "missing_mechanism_kinds": deepcopy(mechanisms["missing_kinds"]),
        "unknown_annotations": [m["id"] for m in mechanisms["annotations"] if m["status"] == "unknown"],
        "implementation_requirements": deepcopy(candidate["requirements"]),
        "requirement_status": "not_discharged_by_description",
        "parameter_contract": deepcopy(candidate["parameter_contract"]), "selected_configuration": {},
        "execution_plan": deepcopy(candidate["execution_plan"]),
        "workload_context": deepcopy(candidate["request_groups"]),
        "requested_model_observations": [
            "Logical read count, eligible grouping count and distinct memory request count, with exact scope",
            "Producer readiness, admission stalls, occupancy and independent requests outstanding",
            "Request issue, transport retry, response arrival, result placement and storage release as separate events",
            "Cache/memory route, service latency/bandwidth and address distribution under the actual configuration",
            "Host submission, waits, consumption and required CPU effect completion costs"],
        "model_observation_status": "requested_not_measured",
        "source_evidence": deepcopy(candidate["source_evidence"]),
        "proof_status": {"description_only": True, "hardware_correctness_certified": False,
                         "workload_equivalence_proved": False, "performance_evaluated": False},
    }
    validate_behavior(record, candidate)
    return record


def validate_behavior(record, candidate):
    """Prevent a prose handoff from silently promoting support or completion."""
    def require(condition, message):
        if not condition:
            raise RequestError("Hardware behavior: " + message)
    require(record.get("format") == FORMAT, "unsupported format")
    originals = {o["operation"]["id"]: o["operation"] for o in candidate["operation_options"]}
    ids = [o["operation_id"] for o in record["desired_observable_semantics"]]
    require(len(ids) == len(set(ids)) and set(ids) == set(originals), "operation coverage changed")
    for item in record["desired_observable_semantics"]:
        op = originals[item["operation_id"]]
        for field in ("support", "execution_role", "result", "ordering", "completion"):
            require(item[field] == op[field], "source operation semantics changed: " + field)
    evidence = record["source_evidence"]["claims"]
    for hypothesis in record["why_it_may_accelerate"]:
        require(bool(hypothesis["claim_refs"]) and set(hypothesis["claim_refs"]) <= set(evidence), "hypothesis has unlocated evidence")
        require(hypothesis["evaluated"] is False, "hypothesis promoted to measured result")
    require(record["implementation_requirements"] == candidate["requirements"], "mapping obligations changed")
    require(record["parameter_contract"] == candidate["parameter_contract"] and record["selected_configuration"] == {}, "reference/tuning values changed")


def render_behavior(record):
    lines = ["# How this accelerator works", "", f"**{md(record['design_id'])} / {md(record['design_revision'])}**", "",
             "[Machine-readable behavior](hardware-behavior.yaml) · [Intrinsic draft](intrinsic-draft.yaml)", "",
             "## What software asks hardware to do", "", md(record["software_interface"]["software_supplies"]), "",
             "Invocation: " + md(record["software_interface"]["invocation"]), "",
             "## What software must observe", ""]
    for op in record["desired_observable_semantics"]:
        lines += [f"### {md(op['operation_id'])}", "",
                  f"Role: **{md(op['execution_role'])}**; support: **{md(op['support'])}**.", "",
                  "Workload targets: " + md(", ".join(dict.fromkeys(r["array"] for r in op["requests"]))) + ".", "",
                  "Result and validity: " + md(op["result"]["form"]) + "; " + md(op["result"]["validity"]), "",
                  "Ordering/association: " + md(op["ordering"]["description"]), "",
                  "Completion: " + md(op["completion"]["event"]), "",
                  "Visibility: " + md(op["completion"]["visibility"]), ""]
        if op["execution_role"] == "assist":
            lines += ["**Assistance:** the program still obtains its required value and executes its update through the CPU path.", ""]
    lines += ["## Internal mechanism", "", record["internal_scope"], ""]
    for m in record["internal_mechanisms"]:
        description = m["description"] if m["status"] == "described" else "unknown in this source-scoped handoff"
        lines += [f"- **{md(m['id'])} / {md(m['kind'])}**: {md(description)}",
                  "  Evidence: " + md(", ".join(m["claim_refs"]) or "none; do not infer support") + "."]
    lines += ["", "## Why it may help", "", "These are conditional hypotheses, not speedup estimates or timing specifications.", ""]
    for h in record["why_it_may_accelerate"]:
        lines += ["- " + md(h["description"]), "  Basis: " + md(h["basis"]) + ".",
                  "  Conditions: " + md("; ".join(h["workload_conditions"])) + ".",
                  "  Limits: " + md("; ".join(h["limiting_factors"])) + "."]
    if not record["why_it_may_accelerate"]:
        lines += ["No source-supported payoff hypothesis is supplied. More mechanism evidence is needed."]
    lines += ["", "## Implementation and evaluation obligations", "",
              "Keep acceptance, payload readiness, memory visibility, storage reuse and CPU final effects distinct. Resolve the source contracts and these obligations before executable mapping:", ""]
    lines += [f"- **{md(r['id'])}** ({md(r['scope'])}): {md(r['description'])}" for r in record["implementation_requirements"]]
    lines += ["", "Reference settings are not selected workload parameters. Parent freshness/ownership and synchronization remain requirements; a read label does not establish immutable data.", "",
              "Suggested future measurements (not collected here):", ""]
    lines += ["- " + md(x) for x in record["requested_model_observations"]]
    lines += ["", "## Source edition and limits", "",
              f"Catalog revision {md(record['catalog_revision'])}; SHA-256 {record['catalog_sha256']}.", "",
              "Claims, locators, URLs and source hashes are retained in the YAML. Local code or a finite illustrative scaffold does not establish every published configuration, global fairness, coherence, timing or end-to-end correctness.", ""]
    return "\n".join(lines)


def build_behavior_artifacts(request, candidate):
    record = describe_behavior(request, candidate)
    return {"hardware-behavior.yaml": yaml.safe_dump(record, sort_keys=False, allow_unicode=True),
            "hardware-behavior.md": render_behavior(record)}
