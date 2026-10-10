"""Offline reference checks for an evolution-loop design, not a search runtime.

No generation, benchmark execution, API calls or archive/prompt promotion occurs.
Callers must authenticate/resolve the content pins and evidence referenced by rows.
"""

from math import isfinite
import re


COHORT_PINS = ("task_sha256", "catalog_sha256", "workload_bundle_sha256", "roi_sha256", "baseline_sha256", "environment_sha256",
               "evaluator_sha256", "cost_model_sha256", "assumption_set_sha256", "aggregation_sha256")
COHORT_FIELDS = (*COHORT_PINS, "evidence_tier", "target_kind", "latency_unit", "area_unit", "area_convention")
EDITABLE_SECTIONS = {"search_focus", "mutation_preferences", "reasoning_guidance", "example_refs"}
PROMPT_PINS = ("core_sha256", "task_sha256", "policy_sha256")
PROMPT_FIELDS = {"strategy_id", "parent_strategy_id", *PROMPT_PINS, "editable", "feedback_refs"}


def is_sha(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))


def finite_number(value, *, positive=False):
    return type(value) in (int, float) and isfinite(value) and (value > 0 if positive else value >= 0)


def validate_cohort(cohort):
    if not isinstance(cohort, dict) or any(not is_sha(cohort.get(k)) for k in COHORT_PINS):
        raise ValueError("Comparison cohort needs complete content pins.")
    if cohort.get("evidence_tier") not in {"analytical_planning", "target_measured"}:
        raise ValueError("Choose one evidence tier; placeholder/illustrative is not rankable.")
    if cohort["evidence_tier"] == "analytical_planning" and cohort.get("target_kind") != "analytical_model":
        raise ValueError("Planning estimates must retain their analytical-model basis.")
    if cohort["evidence_tier"] == "target_measured" and cohort.get("target_kind") not in {"simulator", "hardware"}:
        raise ValueError("Target measurements must distinguish simulator from hardware execution.")
    if cohort.get("latency_unit") != "ms" or cohort.get("area_unit") != "mm2":
        raise ValueError("Normalize latency to ms and area to mm2 before comparison.")
    if cohort.get("area_convention") not in {"incremental_accelerator", "total_system"}:
        raise ValueError("Declare one common area convention.")


def exclusion_reasons(row, cohort):
    """Validate record-level eligibility; this does not prove referenced evidence true."""
    reasons = []
    if row.get("status") != "completed":
        reasons.append("evaluation_not_completed")
    if row.get("design_role") not in {"cpu_control", "accelerator_candidate"}:
        reasons.append("unknown_design_role")
    if not is_sha(row.get("candidate_sha256")) or row.get("candidate_sha256") != row.get("evaluated_candidate_sha256"):
        reasons.append("candidate_content_unbound")
    if row.get("target_refuted") is not False:
        reasons.append("target_refuted_or_status_unknown")
    evidence = row.get("cohort", {})
    if not isinstance(evidence, dict) or any(evidence.get(k) != cohort[k] for k in COHORT_FIELDS):
        reasons.append("different_or_incomplete_comparison_cohort")
    if row.get("placeholder_fields") != []:
        reasons.append("placeholder_or_unspecified_fields")
    if row.get("model_applicability") != "in_domain":
        reasons.append("unbound_or_out_of_domain_model")
    if row.get("metrics_complete") is not True:
        reasons.append("incomplete_cost_or_performance")
    if row.get("execution_witness") != "pass":
        reasons.append("missing_intended_path_witness")
    if not finite_number(row.get("latency_ms"), positive=True):
        reasons.append("invalid_or_unknown_latency")
    if not finite_number(row.get("area_mm2")):
        reasons.append("invalid_or_unknown_area")
    elif row["area_mm2"] == 0 and (cohort["area_convention"] != "incremental_accelerator" or row.get("design_role") != "cpu_control"):
        reasons.append("zero_area_only_valid_for_incremental_cpu_control")
    if not isinstance(row.get("evidence_refs"), list) or not row["evidence_refs"] or not all(isinstance(x, str) and x.strip() for x in row["evidence_refs"]):
        reasons.append("missing_evidence_refs")
    if cohort["evidence_tier"] == "target_measured":
        if row.get("correctness") != "target_pass" or row.get("execution_witness") != "pass":
            reasons.append("missing_target_correctness_or_witness")
        if row.get("legality") != "discharged":
            reasons.append("target_legality_not_discharged")
        if row.get("evidence_kind") != "target_measurement":
            reasons.append("wrong_evidence_kind")
    else:
        if row.get("correctness") != "functional_model_pass":
            reasons.append("missing_functional_precheck")
        if row.get("legality") not in {"discharged", "conditional_reviewed"}:
            reasons.append("unreviewed_mapping")
        if row.get("evidence_kind") != "analytical_model":
            reasons.append("wrong_evidence_kind")
    return reasons


def pareto_frontier(rows, cohort):
    """Minimize point latency and area within one explicitly fixed comparison cohort.

    Equal points both survive. No statistical confidence, knee, preference or
    whole-program hardware correctness is inferred by this mathematical filter.
    """
    validate_cohort(cohort)
    eligible, excluded, seen = [], {}, set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Evaluation records must be mappings.")
        cid = row.get("candidate_id")
        if not isinstance(cid, str) or not cid or cid in seen:
            raise ValueError("Aggregate trials into uniquely identified candidate records before selection.")
        seen.add(cid)
        reasons = exclusion_reasons(row, cohort)
        if reasons:
            excluded[cid] = reasons
        else:
            eligible.append(row)
    frontier = []
    for row in eligible:
        dominated = any(
            other["latency_ms"] <= row["latency_ms"] and other["area_mm2"] <= row["area_mm2"] and
            (other["latency_ms"] < row["latency_ms"] or other["area_mm2"] < row["area_mm2"])
            for other in eligible)
        if not dominated:
            frontier.append(row["candidate_id"])
    return {"evidence_tier": cohort["evidence_tier"], "eligible_ids": sorted(r["candidate_id"] for r in eligible),
            "frontier_ids": sorted(frontier), "excluded": excluded,
            "status": "point_frontier_for_review" if frontier else "no_rankable_candidates",
            "selected_winner": None,
            "scope": "Record-level policy and point dominance only; evidence authentication, uncertainty and preferences are external."}


def validate_prompt_revision(parent, child):
    """Only propose a versioned strategy change; never promote or run its text."""
    for record in (parent, child):
        if not isinstance(record, dict) or set(record) != PROMPT_FIELDS:
            raise ValueError("Unexpected strategy envelope fields.")
        if not all(is_sha(record[k]) for k in PROMPT_PINS):
            raise ValueError("Strategy must identify fixed core/task/policy content.")
        if not isinstance(record["strategy_id"], str) or not record["strategy_id"]:
            raise ValueError("Strategy ID required.")
        if record["parent_strategy_id"] is not None and (not isinstance(record["parent_strategy_id"], str) or not record["parent_strategy_id"]):
            raise ValueError("Parent strategy ID must be text or null for a seed.")
        if not isinstance(record["feedback_refs"], list) or not all(isinstance(x, str) and x.strip() for x in record["feedback_refs"]):
            raise ValueError("Feedback references must be a list of nonempty IDs.")
        if not isinstance(record["editable"], dict) or set(record["editable"]) != EDITABLE_SECTIONS:
            raise ValueError("Only the declared strategy sections are editable.")
        if not isinstance(record["editable"]["search_focus"], str) or not record["editable"]["search_focus"].strip():
            raise ValueError("Search focus must be nonempty text.")
        for key in EDITABLE_SECTIONS - {"search_focus"}:
            value = record["editable"][key]
            if not isinstance(value, list) or not all(isinstance(x, str) and x.strip() for x in value):
                raise ValueError("Strategy list sections require text/reference entries.")
    if any(parent[k] != child[k] for k in PROMPT_PINS):
        raise ValueError("Prompt adaptation cannot change the fixed core, task or evaluation policy.")
    if child["parent_strategy_id"] != parent["strategy_id"] or child["strategy_id"] == parent["strategy_id"]:
        raise ValueError("New strategy requires a distinct ID and exact parent lineage.")
    refs = child["feedback_refs"]
    if not isinstance(refs, list) or not refs or not all(isinstance(x, str) and x.strip() for x in refs):
        raise ValueError("A strategy update must cite the feedback motivating it.")
    changed = sorted(k for k in EDITABLE_SECTIONS if parent["editable"][k] != child["editable"][k])
    if not changed:
        raise ValueError("No strategy change proposed.")
    return {"status": "structurally_valid_pending_review_and_paired_trial", "changed_sections": changed,
            "promoted": False,
            "scope": "Envelope/lineage checks only; free-text meaning and referenced evidence require review."}
