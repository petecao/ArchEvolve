"""Bind explicit manual/source statements without inventing profiling context."""

from copy import deepcopy

from archevolve.hardware_catalog import indexed, references, require, text
from tools.render_mermaid import mapping, sequence


def validate_context(context):
    mapping(context, "source context")
    kernel = mapping(context.get("kernel"), "source context.kernel")
    for field in ("revision", "source_file", "feature_function_proposal"):
        text(kernel.get(field), "source context.kernel." + field)
    text(context.get("analysis_origin"), "source context.analysis_origin")
    statements = indexed(context.get("statements"), "source context.statements")
    for sid, statement in statements.items():
        text(statement.get("code"), f"statements.{sid}.code")
        location = mapping(statement.get("location"), f"statements.{sid}.location")
        require(location.get("file") == kernel["source_file"], "Context statement file differs from context kernel.")
        start, end = location.get("start_line"), location.get("end_line")
        require(type(start) is int and type(end) is int and 0 < start <= end, "Statement line bounds must be positive ordered integers.")
        references(statement.get("related_statement_ids", []), statements, f"statements.{sid}.related_statement_ids")
    bindings = sequence(context.get("access_bindings", []), "source context.access_bindings")
    seen = set()
    for binding in bindings:
        mapping(binding, "source context.access binding")
        text(binding.get("array"), "access binding.array")
        require(binding.get("purpose") in {"read", "update"}, "Access binding purpose must be read or update.")
        key = (binding["array"], binding["purpose"])
        require(key not in seen, "Duplicate array/purpose source binding.")
        seen.add(key)
        references(binding.get("statement_ids"), statements, "access binding.statement_ids", nonempty=True)
    groups = indexed(context.get("request_groups", []), "source context.request_groups")
    for gid, group in groups.items():
        text(group.get("description"), f"request_groups.{gid}.description")
        references(group.get("statement_ids"), statements, f"request_groups.{gid}.statement_ids", nonempty=True)
    return context


def bind_context(case, context, digest, source_ref):
    """Revision matching is not independent verification of the profiled binary."""
    validate_context(context)
    result = deepcopy(case)
    kernel, supplied = case["kernel"], context["kernel"]
    mismatches = [field for field, expected, actual in (
        ("revision", case["source_binding"]["reported_revision"], supplied["revision"]),
        ("source_file", kernel.get("source_file"), supplied["source_file"]),
        ("function", kernel.get("function"), supplied["feature_function_proposal"])) if expected != actual]
    if case["source_binding"]["status"] == "conflicting_reported_revisions":
        mismatches.append("profiling_source_revision")
    result["source_context"] = {"status": "not_bound" if mismatches else "bound_manual_source_review",
        "ref": source_ref, "sha256": digest, "analysis_origin": context["analysis_origin"],
        "mismatched_fields": mismatches, "profile_statement_binding": "not_confirmed_by_Peter",
        "record": deepcopy(context)}
    return result


def request_statement_context(case, array, purpose):
    context = case.get("source_context", {})
    if context.get("status") != "bound_manual_source_review":
        return {"statement_ids": [], "source_locations": [], "statement_binding_status": "unbound"}
    record = context["record"]
    bindings = [b for b in record.get("access_bindings", []) if b["array"] == array and b["purpose"] == purpose]
    ids = bindings[0]["statement_ids"] if bindings else []
    by_id = {s["id"]: s for s in record["statements"]}
    return {"statement_ids": deepcopy(ids), "source_locations": [deepcopy(by_id[s]["location"]) for s in ids],
            "statement_binding_status": "manual_source_proposal" if ids else "unbound"}


def request_groups(case, requests):
    """Group by explicit dependency context, never by just similar feature labels."""
    context = case.get("source_context", {})
    result, covered = [], set()
    if context.get("status") == "bound_manual_source_review":
        statements = {s["id"]: s for s in context["record"]["statements"]}
        for group in context["record"].get("request_groups", []):
            ids = set(group["statement_ids"])
            related = [r for r in requests if ids.intersection(r["statement_ids"])]
            if not related:
                continue
            covered.update(r["id"] for r in related)
            result.append({"id": group["id"], "description": group["description"],
                "request_ids": [r["id"] for r in related], "statement_ids": deepcopy(group["statement_ids"]),
                "dependencies": [{"from_statement": dep, "to_statement": sid} for sid in group["statement_ids"]
                                 for dep in statements[sid].get("related_statement_ids", []) if dep in ids],
                "context_statements": [deepcopy(statements[sid]) for sid in group["statement_ids"]],
                "basis": "explicit_manual_source_group", "hardware_composition_status": "not_established"})
    for r in requests:
        if r["id"] not in covered:
            result.append({"id": "single-" + r["id"], "description": "Single ungrouped capability request.",
                           "request_ids": [r["id"]], "statement_ids": deepcopy(r["statement_ids"]),
                           "dependencies": [], "context_statements": [], "basis": "singleton_no_context_group",
                           "hardware_composition_status": "not_established"})
    return result


def candidate_groups(groups, options):
    """Show matched coverage and retained CPU effects; do not silently fuse operations."""
    covered = {r["id"] for o in options for r in o["matched_requests"]}
    result = []
    for group in groups:
        matches = [r for r in group["request_ids"] if r in covered]
        if matches:
            item = deepcopy(group)
            item["covered_request_ids"] = matches
            item["uncovered_request_ids"] = [r for r in group["request_ids"] if r not in covered]
            item["joint_execution_status"] = "requires_mapping_and_composition_review"
            result.append(item)
    return result
