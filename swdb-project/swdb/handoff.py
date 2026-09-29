"""Render the provisional D06 handoff messages from authoritative records.

Created: 2026-09-27 (Eastern Time).

Three linked messages (profile package, rewrite proposal, evaluation result) are
the provisional collaborator contract of spec decision D06. They are views of
records that already exist; rendering one never runs, changes, or promotes
evidence. The message `format_version` is independent of the record
`schema_version`; see docs/bfs-handoff-contract-v1.md.

Every message names its producer and provenance. Submissions made so far come
from representative test clients; `live_collaborator_integration` is always false
because no Peter/Josh agent has submitted anything.
"""

import collections
import hashlib

from swdb import artifacts, db
from swdb.cli import Failure

FORMAT_VERSION = "1.0"
KINDS = {"profile_package": "profile_package", "rewrite_proposal": "proposal", "evaluation_result": "evaluation"}
PAYLOAD_INLINE_BYTES = 4096


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _ref(store, rid, kind):
    """A stable input reference; a missing record stays visible as missing."""
    if not rid:
        return None
    data = store.get(rid, kind)
    return {"id": rid, "kind": kind, "sha256": artifacts.digest(data) if data else None,
            "state": "present" if data else "missing"}


def _envelope(kind, data, inputs, content, submission=None):
    producer = _mapping(data.get("producer"))
    submitter = _mapping(submission) or producer
    return {
        "format": f"swdb.bfs.handoff.{kind}",
        "format_version": FORMAT_VERSION,
        "id": f"{kind}/{data['id']}",
        "record": {"id": data["id"], "kind": data["kind"], "schema_version": data.get("schema_version"),
                   "sha256": artifacts.digest(data)},
        "producer": producer,
        "provenance": {
            "submission_producer": submitter,
            "test_client": submitter.get("test_client") is True,
            "live_collaborator_integration": False,
            "record_provenance": data.get("provenance", []),
            "statement": ("Submitted by a representative test client; not a live collaborator integration."
                          if submitter.get("test_client") is True else
                          "Produced by the SWDB evaluator/operator; no live collaborator integration."),
        },
        "inputs": [ref for ref in inputs if ref],
        "content": content,
    }


def _text(text, where):
    """Inline short text; longer text becomes an excerpt plus its exact identity."""
    encoded = text.encode()
    if len(encoded) <= PAYLOAD_INLINE_BYTES:
        return text
    return {"excerpt": encoded[:PAYLOAD_INLINE_BYTES].decode(errors="ignore"), "truncated": True,
            "bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest(),
            "full_content": f"swdb get RECORD_ID --format json ({where})"}


def _compact(value, where):
    """Keep structure, identities and short values; large blobs are referenced, not copied."""
    if isinstance(value, str):
        return _text(value, where)
    if isinstance(value, dict):
        return {key: _compact(item, f"{where}.{key}") for key, item in value.items()}
    if isinstance(value, list):
        return [_compact(item, f"{where}[]") for item in value]
    return value


def _payload(payload):
    content = payload.get("content")
    text = content if isinstance(content, str) else None
    return {"kind": payload.get("kind"),
            "sha256": hashlib.sha256(text.encode()).hexdigest() if text is not None else artifacts.digest(content),
            "content": _compact(content, "request.payload.content")}


def profile_package(store, data):
    context = _mapping(data.get("context"))
    evidence = _mapping(data.get("evidence"))
    workload = _mapping(context.get("workload"))
    timing = evidence.get("primary_timing") or []
    strategies = collections.defaultdict(lambda: {"regions": 0, "outcomes": collections.Counter(),
                                                  "performance_guarantee": set()})
    for row in data.get("strategies", []):
        entry = strategies[row.get("strategy")]
        entry["regions"] += 1
        entry["outcomes"][str(row.get("outcome"))] += 1
        entry["performance_guarantee"].add(row.get("performance_guarantee"))
    constraints = _mapping(data.get("constraints"))
    correspondence = _mapping(evidence.get("correspondence"))
    content = {
        "identity": {
            "implementation": data.get("implementation"), "source_snapshot": data.get("source_snapshot"),
            "source_sha256": context.get("source_sha256"), "candidate": data.get("candidate"),
            "evaluation": data.get("evaluation"),
            "workload": {key: workload.get(key) for key in ("id", "family", "canonical_sha256", "num_vertices",
                                                             "num_directed_edges", "directed")},
            "sources": context.get("sources"), "target": context.get("target"),
            "target_configuration": context.get("target_configuration"), "threads": context.get("threads"),
        },
        "roi": {"id": context.get("roi"),
                "primary_quantity": sorted({(t.get("basis"), t.get("quantity")) for t in timing if isinstance(t, dict)}, key=str),
                "primary_trials": len(timing), "primary_binary_sha256": context.get("primary_binary_sha256")},
        "completeness": data.get("completeness"),
        "ranked_regions": {
            "rankings": [{key: ranking.get(key) for key in ("kind", "metric", "inclusive_rule", "coverage", "regions")}
                         for ranking in evidence.get("rankings", [])],
            "regions": [{key: region.get(key) for key in ("id", "kind", "name", "function", "path", "lines",
                                                          "metrics", "basis", "scope", "source_association")}
                        for region in data.get("regions", [])],
            "discovery_coverage": evidence.get("coverage"),
            "correspondence": {"previous_profile": correspondence.get("previous_profile"),
                               "resolved": len(correspondence.get("resolved") or []),
                               "current_unresolved": correspondence.get("current_unresolved"),
                               "region_gain_claim": correspondence.get("region_gain_claim"),
                               "limits": correspondence.get("limits")},
        },
        "dynamic_memory": data.get("dynamic_memory", []),
        "source_build_context": {"build": {key: _mapping(context.get("build")).get(key)
                                           for key in ("compiler", "compiler_version", "flags", "binary_sha256")},
                                 "diagnostic_build": {key: _mapping(evidence.get("diagnostic_build")).get(key)
                                                      for key in ("compiler", "flags", "instrumented_source_sha256")},
                                 "full_application_sha256": _mapping(evidence.get("full_application")).get("sha256")},
        "correctness_and_edit_constraints": {
            "primary_correctness": _mapping(evidence.get("primary_correctness")).get("state"),
            "editable_files": constraints.get("editable_files"),
            "preserve_correctness": constraints.get("preserve_correctness"),
            "preserve_roi": constraints.get("preserve_roi"),
            "protected_inputs": [{key: row.get(key) for key in ("path", "kind")} for row in constraints.get("protections", [])],
        },
        "applicable_strategies": [{"strategy": name, "regions": entry["regions"], "outcomes": dict(entry["outcomes"]),
                                   "performance_guarantee": sorted(entry["performance_guarantee"], key=str)}
                                  for name, entry in sorted(strategies.items(), key=lambda item: str(item[0]))],
        "hardware_interfaces": data.get("hardware"),
        "gain_claim": data.get("gain_claim") is True,
    }
    inputs = [_ref(store, data.get("source_snapshot"), "source_snapshot"), _ref(store, data.get("candidate"), "candidate"),
              _ref(store, data.get("evaluation"), "evaluation"), _ref(store, data.get("region_profile"), "region_profile"),
              _ref(store, workload.get("id"), "workload")]
    candidate = store.get(data.get("candidate"), "candidate") or {}
    proposal = store.get(candidate.get("proposal"), "proposal") or {}
    return _envelope("profile_package", data, inputs, content, submission=proposal.get("producer"))


def rewrite_proposal(store, data):
    request = _mapping(data.get("request"))
    provider = _mapping(data.get("provider"))
    interpretation = _mapping(data.get("interpretation"))
    content = {
        "producer": request.get("producer"),
        "source_profile_package": request.get("profile_package"),
        "target": {key: request.get(key) for key in ("implementation", "source_snapshot", "source_sha256", "regions")},
        "strategy": request.get("strategy"), "intent": request.get("intent"),
        "parameters": _compact(request.get("parameters"), "request.parameters"),
        "requirements": {"constraints": request.get("constraints"),
                         "required_operations": request.get("required_operations", []),
                         "hardware_target": request.get("hardware_target"),
                         "require_executable_backend": request.get("require_executable_backend")},
        "payload": _payload(_mapping(request.get("payload"))),
        "handling": {
            "outcome": data.get("outcome"),
            "provider": {key: provider.get(key) for key in ("kind", "timeout_s", "total_seconds", "max_repairs",
                                                             "budget_usd", "output_format", "edit_format") if key in provider},
            "repair_budget": data.get("repair_budget"),
            "interpretation": {"summary": interpretation.get("interpretation"), "unresolved": interpretation.get("unresolved"),
                               "edit_format": interpretation.get("edit_format", "patch" if interpretation else None),
                               "changed_files": sorted(_mapping(interpretation.get("files")))},
            "attempts": [{key: row.get(key) for key in ("number", "stage", "state", "candidate")}
                         for row in data.get("attempts", [])],
            "candidate": data.get("candidate"),
        },
    }
    inputs = [_ref(store, request.get("profile_package"), "profile_package"),
              _ref(store, request.get("source_snapshot"), "source_snapshot"),
              _ref(store, request.get("hardware_target"), "hardware_target"),
              _ref(store, data.get("candidate"), "candidate")]
    return _envelope("rewrite_proposal", data, inputs, content, submission=request.get("producer"))


def _result_class(data, candidate):
    outcome = _mapping(data.get("outcome"))
    if not candidate:
        return "missing_candidate"
    if outcome.get("state") == "incorrect" or _mapping(data.get("correctness")).get("state") == "failed":
        return "incorrect_candidate"
    if outcome.get("state") != "complete":
        return "incomplete_evaluation"
    return "completed_evaluation"


def evaluation_result(store, data):
    context = _mapping(data.get("context"))
    candidate = store.get(data.get("candidate"), "candidate")
    proposal = store.get(data.get("proposal") or _mapping(candidate).get("proposal"), "proposal") or {}
    frozen = store.get(context.get("protocol"), "protocol") or {}
    sampling = _mapping(_mapping(frozen.get("settings")).get("sampling"))
    comparisons = [row.data for row in store.of_kind("comparison_result")
                   if data["id"] in {row.data.get("candidate_evaluation"), row.data.get("baseline_evaluation")}]
    packages = [row.data for row in store.of_kind("profile_package") if row.data.get("evaluation") == data["id"]]
    checks = _mapping(data.get("correctness")).get("checks") or []
    timing = [row for row in data.get("timing", []) if isinstance(row, dict)]
    stage_counts = collections.Counter((row.get("stage"), row.get("state")) for row in data.get("stages", []))
    gain = any(row.get("gain_claim") is True and row.get("candidate_evaluation") == data["id"] for row in comparisons)
    content = {
        "result_class": _result_class(data, candidate),
        "proposal": proposal.get("id"), "candidate": data.get("candidate"),
        "candidate_state": _mapping(candidate).get("state"),
        "software_hardware_pair": {
            "implementation": data.get("implementation"), "candidate_sha256": context.get("candidate_sha256"),
            "binary_sha256": _mapping(data.get("build")).get("binary_sha256"), "target": context.get("target"),
            "basis": context.get("basis"), "backend_configuration": context.get("backend_configuration"),
            "model": context.get("model"), "threads": context.get("threads"),
        },
        "comparison": {
            "comparison_baseline": data.get("comparison_baseline") or context.get("comparison_baseline"),
            "protocol": context.get("protocol"), "protocol_binding": context.get("protocol_binding"),
            "shared_protocol_bindings": sorted(_mapping(context.get("shared_protocol_bindings"))),
            "protocol_sampling": {key: sampling.get(key) for key in ("repetitions", "collection", "determinism") if key in sampling},
            "results": [{"id": row["id"], "role": "candidate" if row.get("candidate_evaluation") == data["id"] else "baseline",
                         "decision": _mapping(row.get("decision")).get("state"),
                         "roi_speedup": _mapping(row.get("metrics")).get("roi_speedup"),
                         "confidence_interval": _mapping(row.get("metrics")).get("confidence_interval"),
                         "baseline_evaluation": row.get("baseline_evaluation"), "gain_claim": row.get("gain_claim") is True,
                         "evidence_kind": row.get("evidence_kind")} for row in comparisons],
        },
        "stage_outcomes": [{"stage": stage, "state": state, "count": count}
                           for (stage, state), count in sorted(stage_counts.items(), key=lambda item: str(item[0]))],
        "outcome": data.get("outcome"),
        "correctness": {"state": _mapping(data.get("correctness")).get("state"), "verifier": context.get("verifier"),
                        "checks": len(checks), "passed": sum(1 for row in checks if row.get("passed") is True)},
        "roi_measurements": {
            "roi": context.get("roi"),
            "quantities": sorted({(row.get("basis"), row.get("quantity")) for row in timing}, key=str),
            "trials": len(timing), "summary": data.get("summary"),
            "note": "native seconds and simulated ticks/seconds are separate bases and are never compared",
        },
        "instrumentation": context.get("instrumentation"),
        "region_measurements": {"profile_packages": [row["id"] for row in packages],
                                "region_comparisons": [{"comparison": row["id"], "regions": len(row.get("region_comparisons") or [])}
                                                       for row in comparisons]},
        "profiling": data.get("profiling"),
        "raw_artifacts": data.get("raw_artifacts", []),
        "incompleteness": [] if _mapping(data.get("outcome")).get("state") == "complete" else [data.get("outcome")],
        "performance_claim": "frozen_policy_gain" if gain else "none",
        "evidence_kind": data.get("evidence_kind"),
    }
    inputs = [_ref(store, proposal.get("id"), "proposal"), _ref(store, data.get("candidate"), "candidate"),
              _ref(store, context.get("protocol"), "protocol"),
              _ref(store, _mapping(context.get("workload")).get("id"), "workload"),
              _ref(store, _mapping(context.get("pairing")).get("pair_id"), "evaluation_pair"),
              *(_ref(store, row["id"], "profile_package") for row in packages),
              *(_ref(store, row["id"], "comparison_result") for row in comparisons)]
    return _envelope("evaluation_result", data, inputs, content, submission=proposal.get("producer"))


def message(args):
    kind = args.message
    if kind not in KINDS:
        raise Failure(f"unknown handoff message kind: {kind}")
    store = db.query_store(args.records, getattr(args, "db", None))
    data = store.get(args.id, KINDS[kind])
    if data is None:
        raise Failure(f"{KINDS[kind]} record {args.id!r} does not exist")
    return {"profile_package": profile_package, "rewrite_proposal": rewrite_proposal,
            "evaluation_result": evaluation_result}[kind](store, data)
