"""Same-request catalog comparison, separate from candidate budget and performance."""

from copy import deepcopy

import yaml

from archevolve.evidence_select import claim_closure
from archevolve.hardware_catalog import inspect_design, query_catalog
from archevolve.intrinsic_handoff import md
from archevolve.mechanisms import mechanism_context
from tools.render_mermaid import RequestError


def compare_designs(request, catalog, design_ids=None):
    ids = list(design_ids) if design_ids is not None else list(dict.fromkeys(
        c["catalog_design_id"] for c in request["candidates"] if "catalog_design_id" in c))
    if len(ids) != len(set(ids)):
        raise RequestError("Comparison design IDs must be unique.")
    designs = []
    reads = [r for r in request["capability_requests"] if r["operation"] == "read"]
    for did in ids:
        design = inspect_design(catalog, did)
        queries, options = [], {}
        for r in request["capability_requests"]:
            q = query_catalog(catalog, operation=r["operation"], subtype=r["subtype"],
                address_pattern=r["address_pattern"], require_old_value=r["require_old_value"],
                payload_type=r["payload_type"], index_width_bits=r["index_width_bits"], design_id=did)
            queries.append({"request_id": r["id"], "workload_request": deepcopy(r), **q})
            for match in q["matches"]:
                options.setdefault(match["operation_id"], {"operation": match["operation"]})
        execute, assist, unproven = [], [], []
        for r in reads:
            matches = next(q for q in queries if q["request_id"] == r["id"])["matches"]
            if not r["missing_workload_evidence"] and any(m["operation"]["execution_role"] == "execute" and m["status"] == "conditional_executor" for m in matches):
                execute.append(r["id"])
            if any(m["operation"]["execution_role"] == "assist" and m["operation"]["support"] != "unknown" for m in matches):
                assist.append(r["id"])
            if r["missing_workload_evidence"] or any(m["status"] == "needs_evidence" for m in matches):
                unproven.append(r["id"])
        designs.append({"design_id": did, "revision": design["revision"], "record_kind": design["record_kind"],
            "summary": design["summary"], "interface": deepcopy(design["interface"]),
            "conditionally_matched_read_requests": execute, "assisted_read_requests": assist,
            "read_requests_needing_evidence": unproven, "queries": queries,
            "mechanism_context": mechanism_context(design), "parameter_contract": deepcopy(design["parameters"]),
            "requirements": deepcopy(design["requirements"]), "limitations": deepcopy(design["limitations"]),
            "source_evidence": claim_closure(catalog, design, list(options.values()))})
    fetchers = [d["design_id"] for d in designs if d["conditionally_matched_read_requests"]]
    return {"format": "hardware-comparison-v0.1", "kernel_id": request["kernel_id"],
            "input_sha256": request["input_sha256"], "catalog_sha256": request["catalog_sha256"],
            "scope": "Same typed requests, source contracts and mechanism gaps. No performance ranking or legal combined mapping.",
            "designs": designs, "conditional_read_executor_designs": fetchers,
            "selected_second_fetcher_status": "pending_Eric_selection_and_mechanism_annotations",
            "performance_evaluated": False, "speedup": None,
            "workload_evidence_ref": "hardware-request.yaml#workload_summary",
            "model_inputs_needed": ["Per-region/phase active working set and access distribution",
                "Request buffering/grouping/reordering and dependency scheduling",
                "Memory service/cache/bandwidth conditions and concurrency",
                "Interface/setup costs and completion/visibility behavior",
                "Source, workload, trial and ROI binding for measurements"]}


def build_comparison_artifacts(request, catalog, design_ids=None):
    comparison = compare_designs(request, catalog, design_ids)
    lines = ["# Hardware interface comparison", "", comparison["scope"], "",
             "Eric's newly selected second fetcher is pending. Existing designs can be inspected here; assistance is a different role from returned-load execution. Missing mechanism data prevents a scheduling/performance comparison.", "",
             "| Design | Conditional read matches | Assistance matches | Reads needing evidence | Internal details missing |", "|---|---|---|---|---|"]
    for d in comparison["designs"]:
        lines.append(f"| {md(d['design_id'])} | {md(', '.join(d['conditionally_matched_read_requests']) or 'none')} | {md(', '.join(d['assisted_read_requests']) or 'none')} | {md(', '.join(d['read_requests_needing_evidence']) or 'none')} | {md(', '.join(d['mechanism_context']['missing_kinds']) or 'none in checklist; model still needed')} |")
    for d in comparison["designs"]:
        lines += ["", "## " + md(d["design_id"]), "", md(d["summary"]), "",
                  "Inputs: " + md(d["interface"]["software_supplies"]), "",
                  "Invocation: " + md(d["interface"]["invocation"]), "",
                  "Outputs: " + md(d["interface"]["outputs"]), "",
                  "| Request | Matching operation / status / role | Exclusions |", "|---|---|---|"]
        for q in d["queries"]:
            matches = "; ".join(f"{m['operation_id']} / {m['status']} / {m['operation']['execution_role']}" for m in q["matches"]) or "no match"
            excluded = "; ".join(f"{m['operation_id']}: {m['reason']}" for m in q["excluded"]) or "none"
            lines.append(f"| {md(q['request_id'])} | {md(matches)} | {md(excluded)} |")
    lines += ["", "[Full comparison YAML](hardware-comparison.yaml) retains operation/type constraints, located evidence, parameters and mapping requirements.", "",
              "To compare a newly curated design, supply repeated `--compare-design` IDs with the DX100 reference. Comparison retrieval is independent of the diagram candidate budget.", ""]
    return {"hardware-comparison.yaml": yaml.safe_dump(comparison, sort_keys=False, allow_unicode=True),
            "hardware-comparison.md": "\n".join(lines)}
