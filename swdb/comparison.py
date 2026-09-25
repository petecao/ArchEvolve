"""Explicit source and evidence pairing, with claim limits. Created 2026-09-25."""

import math

from swdb.cli import Failure


def compare_records(records, implementation, baseline, profile, baseline_profile, protocol):
    """Return a compatible pair; a ratio alone never establishes a profitable candidate."""
    def get(rid, kind):
        record = records.get(rid)
        if record is None or record.get("kind") != kind:
            raise Failure(f"{kind} {rid!r} does not exist")
        return record

    impl = get(implementation, "implementation")
    selected = impl.get("comparison_baseline")
    if selected is not None and baseline is not None and selected != baseline:
        raise Failure("explicit baseline conflicts with the implementation's comparison_baseline")
    baseline = baseline or selected
    if baseline is None:
        raise Failure("comparison baseline is required; source ancestry is not a comparator")
    base = get(baseline, "implementation")
    if impl["kernel"] != base["kernel"]:
        raise Failure("comparison baseline implements a different kernel")
    mine, theirs = get(profile, "profile"), get(baseline_profile, "profile")
    contexts = []
    durations = []
    for owner, evidence in ((impl, mine), (base, theirs)):
        if evidence["implementation"] != owner["id"]:
            raise Failure(f"profile {evidence['id']!r} belongs to a different implementation")
        kernel = get(owner["kernel"], "kernel")
        app = get(owner.get("application", kernel["application"]), "application")
        if not evidence["build"].get("application_commit") or evidence["build"]["application_commit"] != app["source"]["commit"]:
            raise Failure(f"profile {evidence['id']!r} does not name the implementation's application revision")
        if not evidence["complete"] or not any(
                p["part"] == "correctness" and p["outcome"] == "complete" for p in evidence["parts"]):
            raise Failure(f"profile {evidence['id']!r} lacks complete correctness evidence")
        context = evidence.get("extensions", {}).get("comparison_context")
        required = {"protocol", "roi", "target", "workload", "threads", "basis", "evidence_kind"}
        if not isinstance(context, dict) or not required.issubset(context):
            raise Failure(f"profile {evidence['id']!r} lacks explicit comparison context")
        identity_fields = required - {"threads"}
        if (any(not isinstance(context[key], str) or not context[key].strip() for key in identity_fields)
                or type(context["threads"]) is not int or context["threads"] < 1
                or context["basis"] not in {"measured", "simulated"}):
            raise Failure("comparison context contains missing or invalid identity/basis")
        if context["evidence_kind"] not in {"fixture", "execution"}:
            raise Failure("comparison evidence_kind must be fixture or execution")
        if context["protocol"] != protocol:
            raise Failure("selected protocol does not match profile evidence")
        context = {key: context[key] for key in required}
        contexts.append(context)
        timing = [t for t in evidence["timing"] if t["threads"] == context["threads"]]
        if len(timing) != 1:
            raise Failure("comparison needs exactly one timing entry for its declared threads")
        duration = timing[0]["median_s"]
        if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
            raise Failure("comparison duration must be finite and positive")
        # The legacy timing array is native elapsed seconds, never simulated target time.
        if context["basis"] != "measured":
            raise Failure("legacy timing entries cannot represent simulated ROI durations")
        durations.append(duration)
    if mine["input"] != theirs["input"] or mine["machine"] != theirs["machine"] or contexts[0] != contexts[1]:
        raise Failure("incompatible workload, target, threads, ROI, protocol, basis, or evidence kind")
    fixture = contexts[0]["evidence_kind"] == "fixture"
    kernel = get(impl["kernel"], "kernel")
    return {
        "implementation": implementation, "kernel": impl["kernel"],
        "source_ancestor": impl["origin"].get("derived_from"),
        "source_baseline": impl.get("source_baseline", kernel["baseline_implementation"]),
        "comparison_baseline": baseline, "profile": profile, "baseline_profile": baseline_profile,
        "protocol": protocol, "comparison_context": contexts[0],
        "outcome": "fixture_comparison" if fixture else "compatible_pair_policy_pending",
        "gain_claim": False, "fixture_ratio" if fixture else "diagnostic_ratio": durations[1] / durations[0],
        "note": "Fixture timings are not performance evidence." if fixture else
                "Compatible pair only; frozen repetition and profitability policy acceptance remains required.",
    }
