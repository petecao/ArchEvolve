"""Evidence-based BFS acceptance reporting; never dispatches work. Updated 2026-09-25."""

import copy
import math
import socket
from types import SimpleNamespace
from pathlib import Path

from swdb import artifacts, bfs_protocol as protocol, db, profile_package
from swdb.cli import Failure, _require_valid

SOURCES = ("dx100-bfs-scalar", "gapbs-bfs-do")
FAMILIES = ("kronecker", "uniform_random")
CASES = {
    ("dx100-bfs-scalar", "instruction"): ("natural_language", "simulated", True),
    ("dx100-bfs-scalar", "supplied_code"): ("patch", "measured", False),
    ("gapbs-bfs-do", "instruction"): ("structured_instructions", "measured", False),
    ("gapbs-bfs-do", "supplied_code"): ("annotated_source", "simulated", True),
}
REVISION = "e4fc4afdf894f295442cef3604667a469fab8e62"


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _real(evaluation):
    return (evaluation.get("evidence_kind") == "execution"
            and isinstance(evaluation.get("request"), dict)
            and evaluation["request"].get("fixture") is not True)


def _artifact_refs(data):
    """Explicit hashed paths only; prose and record IDs are not filesystem paths."""
    if isinstance(data, dict):
        if isinstance(data.get("path"), str) and isinstance(data.get("sha256"), str):
            yield data["path"], data["sha256"], "directory" if "files" in data else "file"
        for path_key, hash_key in (("output", "output_sha256"), ("binary", "binary_sha256"),
                                   ("raw_artifact", "raw_sha256"), ("region_output", "region_output_sha256"),
                                   ("diff", "diff_sha256"), ("canonical_path", "canonical_file_sha256"),
                                   ("receipt", "receipt_sha256")):
            if isinstance(data.get(path_key), str) and isinstance(data.get(hash_key), str):
                yield data[path_key], data[hash_key], "file"
        for value in data.values():
            yield from _artifact_refs(value)
    elif isinstance(data, list):
        for value in data:
            yield from _artifact_refs(value)


def _availability(records, host):
    result = []
    local = socket.gethostname().split(".")[0]
    for name, expected, kind in sorted(set(ref for record in records for ref in _artifact_refs(record))):
        path = Path(name)
        if not path.is_absolute():
            continue
        state = "remote_unverified" if host and host != local else "missing"
        if path.exists():
            try:
                actual = artifacts.identify(path)["sha256"] if kind == "directory" else artifacts.file_hash(path)
                state = "verified" if actual == expected else "changed"
            except (Failure, OSError):
                state = "unreadable"
        result.append({"path": name, "sha256": expected, "kind": kind, "state": state, "host": host})
    return result


def _correctness(evaluation):
    reasons = []
    if evaluation.get("correctness", {}).get("state") != "passed":
        return ["timed evaluation lacks passed independent correctness"]
    binary = evaluation.get("build", {}).get("binary_sha256")
    context = evaluation.get("context", {})
    checks = evaluation["correctness"].get("checks", [])
    if context.get("basis") == "simulated":
        bindings = (context.get("component_bindings", {}) if evaluation.get("component_evaluations") else
                    {evaluation["id"]: context.get("execution_binding")})
        timings = evaluation.get("timing", [])
        for timing in timings:
            matched = [c for c in checks if c.get("state") == "passed" and c.get("passed") is True
                       and c.get("checker") == "dx100.bfs.verifier.v1" and bindings.get(c.get("execution"))
                       and profile_package._same(c.get("binding"), bindings[c["execution"]])
                       and c.get("binding", {}).get("binary", {}).get("sha256") == binary
                       and c.get("graph_sha256") == context.get("workload", {}).get("canonical_sha256")
                       and all(c.get(k) == timing.get(k) for k in ("source", "source_position", "repetition", "binary_sha256", "output_sha256"))
                       and c.get("sealed_roi", {}).get("sha256") and c.get("output", {}).get("sha256") == timing.get("output_sha256")]
            if len(matched) != 1:
                reasons.append("simulator correctness is not tied to each timed binary, sealed ROI, and execution")
                break
        if not timings:
            reasons.append("simulator correctness has no timed traversal coverage")
    else:
        for timing in evaluation.get("timing", []):
            matched = [c for c in checks if c.get("passed") is True and c.get("binary_sha256") == binary
                       and c.get("graph_sha256") == context.get("workload", {}).get("canonical_sha256")
                       and all(c.get(k) == timing.get(k) for k in ("source", "source_position", "repetition", "output_sha256"))]
            if len(matched) != 1:
                reasons.append("native structural correctness does not uniquely cover each timed trial")
                break
        if not checks:
            reasons.append("independent correctness checks are missing")
    return reasons


def _acceleration(evaluation):
    if evaluation.get("context", {}).get("basis") != "simulated" or not _real(evaluation):
        return {"executed": False, "cases": {}, "reason": "requires the real simulated DX100 target"}
    observed_checks = []
    for check in evaluation.get("correctness", {}).get("checks", []):
        coverage = check.get("coverage", {})
        counters = coverage.get("instruction_counters", {})
        completed = coverage.get("completed_trace_units", {})
        observed = (coverage.get("accelerator_executed") is True
                    and any(k.endswith(".numInst") and type(v) in (int, float) and v > 0 for k, v in counters.items())
                    and all(type(completed.get(k)) in (int, float) and completed[k] > 0 for k in ("S", "I", "R", "A")))
        if observed:
            observed_checks.append(check)
    if observed_checks and not _correctness(evaluation):
        cases = {}
        for name in ("full_tiles", "tail_tiles", "competing_parent_updates"):
            observations = [check["coverage"].get(name) for check in observed_checks]
            cases[name] = any(isinstance(item, dict) and item.get("state") == "observed"
                              and type(item.get("count")) is int and item["count"] > 0 for item in observations)
        return {"executed": True, "cases": cases, "executions": [check["execution"] for check in observed_checks], "reason": None}
    return {"executed": False, "cases": {}, "reason": "no matching positive instruction and completed-unit trace evidence"}


def _packages(store, evaluation):
    if evaluation.get("component_evaluations"):
        accepted, rejected = [], []
        for ref in evaluation["component_evaluations"]:
            component = store.get(ref["evaluation"], "evaluation")
            if not component or component.get("component_evaluations") or artifacts.digest(component) != ref["sha256"]:
                rejected.append({"id": ref["evaluation"], "reasons": ["aggregate profile component is missing, nested, or changed"]})
                return [], rejected
            packages, failed = _packages(store, component)
            rejected.extend(failed)
            if not packages:
                rejected.append({"id": component["id"], "reasons": ["component has no complete exact real profile package"]})
                return [], rejected
            accepted.extend(packages)
        return accepted, rejected
    accepted, rejected = [], []
    for record in store.of_kind("profile_package"):
        package = record.data
        if package.get("evaluation") != evaluation["id"]:
            continue
        reasons = []
        try:
            profile_package.verify(package)
            if package.get("completeness") != "complete" or package.get("evidence", {}).get("classification") != "execution":
                reasons.append("profile collection is incomplete or a fixture")
            if package.get("evidence", {}).get("evaluation_sha256") != artifacts.digest(evaluation):
                reasons.append("package evaluation identity is stale")
            diagnostic = store.get(package.get("region_profile"), "region_profile")
            if not diagnostic or package.get("evidence", {}).get("region_profile_sha256") != artifacts.digest(diagnostic):
                reasons.append("package diagnostic profile identity is stale or missing")
            if not profile_package._memory(package.get("dynamic_memory", [])):
                reasons.append("dynamic memory observations are unavailable")
            if not all(any(r.get("kind") == kind and profile_package._timing_quantity(r) for r in package.get("regions", []))
                       for kind in ("function", "loop")):
                reasons.append("executed function/loop timing is missing")
            if package.get("candidate") != evaluation.get("candidate"):
                reasons.append("package names another candidate")
        except (Failure, KeyError, TypeError, ValueError) as exc:
            reasons.append(str(exc))
        if reasons:
            rejected.append({"id": record.id, "reasons": reasons})
        else:
            accepted.append(package)
    return accepted, rejected


def _comparison(store, comparison, allowed, mode=None):
    reasons = []
    try:
        p = protocol._get(store, comparison.get("protocol"), "protocol")
        protocol.verify_immutable(p)
        protocol._validate_settings(p["settings"], store)
        if p["id"] not in allowed:
            reasons.append("comparison uses a missing or superseded current protocol")
        if mode and p["settings"]["mode"] != mode:
            reasons.append("comparison mode does not match its declared obligation")
        if comparison.get("protocol_sha256") != p["identity_sha256"]:
            reasons.append("comparison freeze identity is stale")
        a = protocol._get(store, comparison.get("baseline_evaluation"), "evaluation")
        b = protocol._get(store, comparison.get("candidate_evaluation"), "evaluation")
        if comparison.get("evaluation_identities") != {a["id"]: artifacts.digest(a), b["id"]: artifacts.digest(b)}:
            reasons.append("comparison input evaluations changed or lack content identities")
        left, wid, kind = protocol._evaluation_samples(store, a, p, "baseline")
        right, other, other_kind = protocol._evaluation_samples(store, b, p, "candidate")
        if wid != other or kind != "execution" or other_kind != "execution" or not _real(a) or not _real(b):
            reasons.append("comparison is not a compatible pair of real executions")
        if comparison.get("comparison_baseline") != a.get("implementation"):
            reasons.append("comparison does not name its actual explicit baseline")
        if comparison.get("decision", {}).get("state") not in {"gain", "regression", "no_gain", "inconclusive"}:
            reasons.append("comparison has no valid empirical policy decision")
        metrics = protocol._statistics(left, right, p["settings"]["profitability"])
        recorded = comparison.get("metrics", {}).get("roi_speedup")
        if type(recorded) not in (int, float) or not math.isfinite(recorded) or not math.isclose(recorded, metrics["roi_speedup"], rel_tol=1e-12):
            reasons.append("recorded ROI ratio differs from its immutable evaluation samples")
        attribution = ("artifact_configuration_pair" if p["settings"]["mode"] == "artifact_reference" else
                       "software_on_fixed_target" if p["settings"]["targets"]["baseline"] == p["settings"]["targets"]["candidate"] else
                       "joint_hardware_software")
        if comparison.get("metrics", {}).get("attribution") != attribution or not profile_package._same(
                comparison.get("metrics", {}).get("disclosed_differences"), p["settings"]["differences"]):
            reasons.append("comparison causal attribution does not match its software/hardware/configuration differences")
        regions = protocol._region_comparisons(a, b, p["settings"])
        if not profile_package._same(comparison.get("region_comparisons"), regions):
            reasons.append("recorded region ratios differ from their selected scope and attribution")
        limit = p["settings"]["profitability"]["maximum_relative_spread"]
        noisy = any(value > limit for rows in metrics["relative_spread"].values() for value in rows.values())
        gain = not noisy and metrics["confidence_interval"]["lower"] > p["settings"]["profitability"]["minimum_speedup"]
        expected_state = ("inconclusive" if noisy else "gain" if gain else
                          "regression" if metrics["confidence_interval"]["upper"] < 1 else "no_gain")
        if comparison.get("decision", {}).get("state") != expected_state:
            reasons.append("recorded decision does not follow the frozen profitability policy")
        for key in ("confidence_interval", "relative_spread", "per_source_position_speedup"):
            if not profile_package._same(comparison.get("metrics", {}).get(key), metrics[key]):
                reasons.append(f"recorded {key} differs from the actual sample calculation")
        if bool(comparison.get("gain_claim")) != gain:
            reasons.append("recorded gain claim does not follow the frozen profitability policy")
        return {"id": comparison["id"], "qualified": not reasons, "reasons": reasons, "protocol": p["id"],
                "mode": p["settings"]["mode"], "baseline_evaluation": a["id"], "candidate_evaluation": b["id"],
                "comparison_baseline": a.get("implementation"), "candidate_implementation": b.get("implementation"),
                "workload": wid, "gain": gain and not reasons, "metrics": metrics,
                "differences": p["settings"]["differences"], "decision": comparison["decision"]}
    except (Failure, KeyError, TypeError, ValueError, OverflowError, AttributeError) as exc:
        reasons.append(str(exc))
        return {"id": comparison["id"], "qualified": False, "reasons": reasons,
                "protocol": comparison.get("protocol"), "decision": comparison.get("decision"), "gain": False}


def _evaluation(store, evaluation, comparisons, current):
    reasons = []
    if not _real(evaluation): reasons.append("contract fixtures do not satisfy real execution acceptance")
    if evaluation.get("outcome", {}).get("state") != "complete": reasons.append("evaluation is incomplete or failed")
    reasons.extend(_correctness(evaluation))
    packages, rejected = _packages(store, evaluation)
    if not packages: reasons.append("no complete real profile package matches this exact evaluation")
    associated = [result for result in comparisons if result.get("candidate_evaluation") == evaluation["id"]]
    eligible = [result for result in associated if result["qualified"] and result.get("protocol") in current]
    if not eligible: reasons.append("no compatible current frozen comparison")
    candidate = store.get(evaluation.get("candidate"), "candidate")
    source = store.get((candidate or {}).get("source_snapshot"), "source_snapshot")
    if not candidate or not source or candidate["artifact"]["sha256"] == source["artifact"]["sha256"]:
        reasons.append("no actual changed candidate source artifact")
    proposal = store.get(evaluation.get("proposal") or (candidate or {}).get("proposal"), "proposal")
    original_package = store.get((proposal or {}).get("request", {}).get("profile_package"), "profile_package")
    if not original_package or original_package.get("completeness") != "complete" or original_package.get("evidence", {}).get("classification") != "execution":
        reasons.append("proposal did not consume a complete real source profile package")
    context = evaluation.get("context", {})
    if context.get("basis") == "measured" and any(flag.startswith("-DMAA") for flag in evaluation.get("build", {}).get("flags", [])):
        reasons.append("functional accelerator host runtime cannot satisfy native or simulated accelerator acceptance")
    diagnostics = [store.get(package.get("region_profile"), "region_profile") for package in packages]
    inputs = [evaluation, *packages, *(item for item in diagnostics if item), *([candidate] if candidate else [])]
    availability = _availability(inputs, context.get("host"))
    if any(ref["state"] in {"changed", "missing", "unreadable"} for ref in availability):
        reasons.append("required local raw/source artifacts are missing, unreadable, or changed")
    return {"evaluation": evaluation["id"], "proposal": (proposal or {}).get("id"), "candidate": (candidate or {}).get("id"),
            "qualified": not reasons, "reasons": reasons, "outcome": evaluation.get("outcome"),
            "correctness": evaluation.get("correctness"), "basis": context.get("basis"),
            "profile_packages": [p["id"] for p in packages], "rejected_packages": rejected,
            "comparisons": associated, "acceleration": _acceleration(evaluation), "artifacts": availability,
            "external_verification": "verified" if availability and all(ref["state"] == "verified" for ref in availability) else "unverified"}


def report(args):
    request = protocol._request(args)
    store = _require_valid(args.records)
    index = args.db or db.default_path(args.records)
    if db.is_stale(args.records, index): db.build(args.records, index)
    current = request.get("candidate_protocols", [])
    references = {name: request.get(name, []) for name in ("artifact_reference_comparisons", "controlled_reference_comparisons")}
    for name, values in {"candidate_protocols": current, **references}.items():
        protocol._fail(isinstance(values, list) and all(isinstance(v, str) for v in values) and len(values) == len(set(values)), f"{name} must contain unique record IDs")
    missing = [rid for rid in current if store.get(rid, "protocol") is None]
    results = [_comparison(store, r.data, current) for r in store.of_kind("comparison_result")]
    evaluations = {}
    for record in store.of_kind("evaluation"):
        if record.data.get("implementation") not in SOURCES or not record.data.get("candidate"):
            continue
        try:
            evaluations[record.id] = _evaluation(store, record.data, results, current)
        except (Failure, KeyError, TypeError, ValueError, OverflowError, AttributeError) as exc:
            evaluations[record.id] = {"evaluation": record.id, "proposal": record.data.get("proposal"),
                "candidate": record.data.get("candidate"), "qualified": False,
                "reasons": ["incomplete or malformed retained evidence: " + str(exc)],
                "outcome": record.data.get("outcome"), "correctness": record.data.get("correctness"),
                "basis": record.data.get("context", {}).get("basis"), "profile_packages": [], "rejected_packages": [],
                "comparisons": [], "acceleration": {"executed": False, "cases": {}}, "artifacts": [],
                "external_verification": "unverified"}
    cells = []
    for source in SOURCES:
        for route in ("instruction", "supplied_code"):
            payload, basis, accelerated = CASES[source, route]
            for family in FAMILIES:
                attempts = []
                for rid, observation in evaluations.items():
                    evaluation = store.get(rid, "evaluation")
                    proposal = store.get(observation["proposal"], "proposal") if observation["proposal"] else None
                    wid = _mapping(evaluation.get("context", {}).get("workload")).get("id")
                    workload = store.get(wid, "workload")
                    requested_payload = _mapping(_mapping((proposal or {}).get("request")).get("payload"))
                    if evaluation.get("implementation") != source or not proposal or requested_payload.get("kind") != payload:
                        continue
                    if not workload or workload["definition"]["family"] != family:
                        continue
                    item = copy.deepcopy(observation)
                    if item["basis"] != basis:
                        item["reasons"].append("execution basis does not satisfy the assigned source/payload case")
                    if accelerated and not item["acceleration"]["executed"]:
                        item["reasons"].append("the assigned case has no affirmative accelerator execution")
                    expected_mode = "controlled_simulator" if accelerated else "native"
                    if not any(c.get("qualified") and c.get("mode") == expected_mode for c in item["comparisons"]):
                        item["reasons"].append("case lacks its required native or controlled-simulator comparison")
                    if not any(c.get("qualified") and c.get("comparison_baseline") == source for c in item["comparisons"]):
                        item["reasons"].append("case lacks its explicit appropriate unaccelerated source baseline")
                    item["qualified"] = not item["reasons"]
                    attempts.append(item)
                qualified = [a for a in attempts if a["qualified"]]
                cells.append({"starting_implementation": source, "route": route, "payload": payload, "graph_family": family,
                    "required_basis": basis, "accelerator_required": accelerated, "state": "satisfied_by_retained_metadata" if qualified else "incomplete",
                    "attempts": attempts, "reasons": [] if qualified else ["no qualifying current execution for this required cell"]})
    reference_results = {}
    for name, ids in references.items():
        mode = "artifact_reference" if name.startswith("artifact") else "controlled_simulator"
        rows = []
        for rid in ids:
            comp = store.get(rid, "comparison_result")
            if not comp:
                rows.append({"id": rid, "qualified": False, "reasons": ["comparison record is missing"]}); continue
            row = _comparison(store, comp, [comp.get("protocol")], mode)
            if row["qualified"]:
                for eid in (row["baseline_evaluation"], row["candidate_evaluation"]):
                    evaluation = store.get(eid, "evaluation")
                    if _correctness(evaluation) or not _packages(store, evaluation)[0]:
                        row["reasons"].append("reference pair lacks exact correctness or complete execution profiling")
                    candidate = store.get(evaluation.get("candidate"), "candidate")
                    source = store.get((candidate or {}).get("source_snapshot"), "source_snapshot")
                    if not candidate or not source or candidate["artifact"]["sha256"] != source["artifact"]["sha256"]:
                        row["reasons"].append("reference comparison does not retain unchanged fixed source identities")
                accelerated = store.get(row["candidate_evaluation"], "evaluation")
                if not _acceleration(accelerated)["executed"]:
                    row["reasons"].append("reference accelerated side lacks actual DX100 execution")
                workload = store.get(row["workload"], "workload")["definition"]
                if mode == "artifact_reference" and not (workload["family"] == "uniform_random"
                        and workload["generator"]["revision"] == REVISION
                        and workload["generator"]["parameters"].get("scale") == 22
                        and workload["generator"]["parameters"].get("edge_factor") == 16
                        and workload["realized"]["num_vertices"] == 2**22 and workload["realized"]["directed"] is True):
                    row["reasons"].append("artifact case is not the pinned uniform scale22 degree16 directed workload")
                if mode == "artifact_reference":
                    for role, eid, size, ways, enable in (("baseline", row["baseline_evaluation"], 10, 20, "BASE"),
                                                         ("candidate", row["candidate_evaluation"], 8, 16, "MAA")):
                        context = store.get(eid, "evaluation").get("context", {})
                        config = context.get("backend_configuration", {})
                        expected = {"mode": enable, "l3_size_mb": size, "l3_assoc": ways,
                                    "guest_cores": 4, "guest_memory": "16GB", "cpu": "X86O3CPU", "cpu_clock": "3.2GHz"}
                        if context.get("model", {}).get("revision") != REVISION or any(config.get(k) != v for k, v in expected.items()):
                            row["reasons"].append(f"{role} does not retain the authors' exact BASE/MAA configuration")
                record_set = [store.get(row["baseline_evaluation"], "evaluation"), accelerated]
                reference_packages = [package for evaluation in record_set for package in _packages(store, evaluation)[0]]
                record_set.extend(reference_packages)
                record_set.extend(store.get(package["region_profile"], "region_profile") for package in reference_packages)
                row["artifacts"] = _availability(record_set, accelerated.get("context", {}).get("host"))
                if any(ref["state"] in {"missing", "changed", "unreadable"} for ref in row["artifacts"]):
                    row["reasons"].append("reference raw evidence is unavailable or changed")
                row["qualified"] = not row["reasons"]
            rows.append(row)
        reference_results[name] = {"state": "satisfied_by_retained_metadata" if rows and all(r["qualified"] for r in rows) else "incomplete", "comparisons": rows}
    acceleration = []
    for source in SOURCES:
        ids_by_family = {family: set() for family in FAMILIES}
        for cell in cells:
            if cell["starting_implementation"] != source: continue
            for attempt in cell["attempts"]:
                if attempt["qualified"] and attempt["acceleration"]["executed"]:
                    ids_by_family[cell["graph_family"]].add(attempt["candidate"])
        shared = set.intersection(*ids_by_family.values())
        acceleration.append({"starting_implementation": source, "candidate_ids": sorted(shared),
                             "state": "satisfied_by_retained_metadata" if shared else "incomplete"})
    gains = [c for cell in cells for attempt in cell["attempts"] if attempt["qualified"]
             for c in attempt["comparisons"] if c.get("gain") and c.get("comparison_baseline") == cell["starting_implementation"]]
    all_cells = all(c["state"] != "incomplete" for c in cells)
    all_acceleration = all(a["state"] != "incomplete" for a in acceleration)
    all_reference = all(r["state"] != "incomplete" for r in reference_results.values())
    good = [a for c in cells for a in c["attempts"] if a["qualified"]]
    criterion = {f"AC{i:02d}": {"state": "incomplete", "reason": "required demonstration evidence has not been established"} for i in range(1, 21)}
    def mark(number, condition, reason):
        criterion[f"AC{number:02d}"] = {"state": "satisfied_by_retained_metadata" if condition else "incomplete", "reason": reason}
    source_records = [store.get(source, "implementation") for source in SOURCES]
    mark(1, all(source_records) and {store.application_of(s)["id"] for s in source_records} == {"gapbs", "dx100-gapbs"}, "shared BFS source contexts are queried independently")
    mark(2, bool(good), "complete real packages retain discovered function/loop rankings and coverage")
    mark(4, bool(good), "qualifying packages contain dynamic memory observations tied to diagnostic execution")
    mark(6, all_cells, "all eight fixed source/payload/family cells must qualify")
    mark(7, bool(good), "qualifying cells require a changed candidate and retained proposal chain")
    case_names = ("full_tiles", "tail_tiles", "competing_parent_updates")
    accelerated_good = [a for a in good if a["acceleration"]["executed"]]
    mark(10, bool(accelerated_good) and all(any(a["acceleration"]["cases"].get(case) for a in accelerated_good) for case in case_names),
         "timed structural checks plus observed full/tail/parent-update cases are required")
    mark(11, all_acceleration, "one identical correct accelerated candidate per source must cover both families")
    mark(12, any(a["basis"] == "measured" for a in good), "real native CPU execution requires independent checks and complete dynamic profiling")
    mark(13, bool(good), "qualified cases retain primary ROI separately from diagnostic region and memory quantities")
    mark(15, all_reference, "artifact-reference and controlled-reference comparisons are distinct obligations")
    mark(16, all_cells, "every accepted cell binds its actual workload and settings to a current immutable pre-execution protocol")
    mark(17, bool(gains), "at least one generated correct candidate must pass its frozen profitability policy against its unaccelerated source baseline")
    mark(18, all_cells and all_reference and all_acceleration, "all required cases, reference obligations, failures, and regressions must be accounted for")
    accepted_packages = {pid: store.get(pid, "profile_package") for a in good for pid in a["profile_packages"]}
    new_regions = []
    for package in accepted_packages.values():
        diagnostic = store.get(package.get("region_profile"), "region_profile")
        previous = store.get((diagnostic or {}).get("correspondence", {}).get("previous_profile"), "region_profile")
        if not previous or not _real(store.get(previous.get("evaluation"), "evaluation") or {}):
            continue
        old_functions = {r.get("function") for r in previous["regions"] if r.get("kind") == "function"}
        old_regions = {(r.get("kind"), r.get("function"), r.get("source_sha256")) for r in previous["regions"]}
        rankings = package["evidence"].get("rankings", [])
        top = {rid for ranking in rankings for rid in ranking["regions"][:5]}
        for region in package["regions"]:
            introduced = region.get("function") not in old_functions
            if region["kind"] == "loop" and not introduced:
                loops = lambda rows: [r for r in rows if r.get("kind") == "loop" and r.get("function") == region.get("function")]
                introduced = (len(loops(package["regions"])) > len(loops(previous["regions"]))
                              and ("loop", region.get("function"), region.get("source_sha256")) not in old_regions)
            if introduced and region["id"] in top and profile_package._timing_quantity(region):
                new_regions.append({"profile_package": package["id"], "region": region["id"]})
    mark(3, bool(new_regions), "a new helper or loop absent from prior compiler discovery must appear among the five highest measured regions of its kind")
    criterion["AC03"]["evidence"] = new_regions
    query_checks = []
    for package in accepted_packages.values():
        forward = package.get("strategies", [])
        if not forward or any(row.get("performance_guarantee") is not False for row in forward): continue
        reverse = profile_package.regions(SimpleNamespace(records=args.records, strategy=forward[0]["strategy"], package=package["id"]))
        if reverse["profiled_matches"] and reverse["performance_guarantee"] is False:
            query_checks.append(package["id"])
    mark(5, bool(query_checks), "forward applicability and reverse package-bound matches preserve unresolved conditions without performance promises")
    criterion["AC05"]["evidence"] = query_checks
    rejected_proposals = [r.data for r in store.of_kind("proposal") if r.data.get("outcome", {}).get("state") in {"rejected", "failed", "unresolved"}]
    rejected_groups = {"source": [], "operations": [], "protected": []}
    for proposal in rejected_proposals:
        reason = str(proposal["outcome"].get("reason", "")).lower()
        request_data = proposal.get("request", {})
        request_data = request_data if isinstance(request_data, dict) else {}
        source = store.get(request_data.get("source_snapshot"), "source_snapshot")
        if source and request_data.get("source_sha256") != source["artifact"]["sha256"]:
            rejected_groups["source"].append(proposal["id"])
        if any(term in reason for term in ("operation", "capabilit", "unsupported")) and request_data.get("required_operations"):
            rejected_groups["operations"].append(proposal["id"])
        if "protected" in reason and any(term in reason for term in ("verifier", "evaluator", "roi")):
            rejected_groups["protected"].append(proposal["id"])
    mark(8, all(rejected_groups.values()), "stale source, unsupported operation, and protected verifier/ROI requests must retain explicit non-success records")
    criterion["AC08"]["evidence"] = rejected_groups
    failures = {name: [] for name in ("build_failure", "verifier_failure_exit_zero", "timeout", "budget_exhausted", "missing_observation", "regression")}
    for record in store.of_kind("evaluation"):
        data = record.data
        state = data.get("outcome", {}).get("state")
        if state == "failed" and "build" in data.get("outcome", {}).get("stage", ""): failures["build_failure"].append(record.id)
        if state == "incorrect" and any(stage.get("returncode") == 0 for stage in data.get("stages", [])):
            failures["verifier_failure_exit_zero"].append(record.id)
        for label, outcome in (("timeout", "timed_out"), ("budget_exhausted", "budget_exhausted"), ("missing_observation", "missing_observation")):
            if state == outcome: failures[label].append(record.id)
    failures["regression"] = [r.id for r in store.of_kind("comparison_result") if r.data.get("decision", {}).get("state") == "regression"]
    mark(9, all(failures.values()), "all required failure and unfavorable-result categories must remain retrievable")
    criterion["AC09"]["evidence"] = failures
    independent_baselines = []
    for record in store.of_kind("comparison_result"):
        comparison = record.data
        if comparison.get("source_ancestor") == comparison.get("comparison_baseline"): continue
        if comparison.get("decision", {}).get("state") not in {"fixture_comparison", "gain", "no_gain", "regression", "inconclusive"}: continue
        try:
            p = protocol._get(store, comparison.get("protocol"), "protocol")
            for role, key in (("baseline", "baseline_evaluation"), ("candidate", "candidate_evaluation")):
                protocol._evaluation_samples(store, protocol._get(store, comparison.get(key), "evaluation"), p, role)
            independent_baselines.append(record.id)
        except (Failure, KeyError, TypeError, ValueError): pass
    mark(14, bool(independent_baselines), "a retained compatible comparison must resolve a baseline different from source ancestry; fixtures prove this contract only")
    criterion["AC14"]["evidence"] = independent_baselines
    supported = [r.id for r in store.of_kind("hardware_target") if r.data["backend"]["readiness"] in {"built", "verified"}
                 and r.data["backend"]["build_evidence"] and r.data["operations"]
                 and all((store.get(op, "operation") or {}).get("support") == "source_supported" for op in r.data["operations"])]
    mark(19, bool(supported) and all_acceleration, "declared operation support must be backed by an executable backend and actual accelerated candidate runs")
    criterion["AC19"]["evidence"] = supported
    handoff = request.get("handoff", {})
    proposal_ids = {a["proposal"] for a in good}
    producers = [store.get(rid, "proposal").get("request", {}).get("producer", {}) for rid in proposal_ids]
    handoff_artifacts = _availability([handoff], socket.gethostname().split(".")[0])
    contracts = {"profile_package": "1.0", "rewrite_proposal": "1.0", "evaluation_result": "1.0"}
    handoff_ok = (all_cells and {p.get("role") for p in producers} >= {"sw", "hw"}
                  and all(p.get("test_client") is True for p in producers)
                  and handoff.get("live_collaborator_integration") is False
                  and handoff.get("contracts") == contracts and set(handoff.get("examples", [])) >= proposal_ids
                  and bool(handoff_artifacts) and all(a["state"] == "verified" for a in handoff_artifacts))
    mark(20, handoff_ok, "versioned linked handoff artifacts and real labeled SW/HW test-client submissions are required; live collaborator integration is not claimed")
    history = {kind: [{"id": r.id, "outcome": r.data.get("outcome"), "decision": r.data.get("decision"),
                       "evidence_kind": r.data.get("evidence_kind"), "request": r.data.get("request"),
                       "attempts": r.data.get("attempts"), "record_sha256": artifacts.digest(r.data)} for r in store.of_kind(kind)]
               for kind in ("proposal", "evaluation", "comparison_result")}
    assigned = {attempt["evaluation"] for cell in cells for attempt in cell["attempts"]}
    result = {"message_version": "1.0", "id": request["id"], "request": request, "matrix": cells,
              "source_acceleration_minima": acceleration, "reference_obligations": reference_results,
              "qualifying_candidate_gains": gains, "criteria": criterion, "history": history,
              "unassigned_evaluations": [value for key, value in evaluations.items() if key not in assigned],
              "comparison_assessments": results,
              "missing_protocols": missing, "live_collaborator_integration": False, "handoff_artifacts": handoff_artifacts,
              "acceptance": "incomplete", "gain_claim": any(a["external_verification"] == "verified"
                  and any(c.get("gain") for c in a["comparisons"]) for a in good),
              "limits": ["Unestablished contract, changed-source, and collaborator handoff criteria remain incomplete.",
                         "Remote raw artifacts remain unverified on a host that cannot read them.",
                         "No gain over the authors' accelerated implementation is required."]}
    all_criteria = all(item["state"] == "satisfied_by_retained_metadata" for item in criterion.values())
    external_verified = (bool(good) and all(a["external_verification"] == "verified" for a in good)
                         and all(all(ref["state"] == "verified" for ref in c.get("artifacts", []))
                                 for obligation in reference_results.values() for c in obligation["comparisons"]))
    result["acceptance"] = "complete" if all_criteria and external_verified and not missing else "incomplete"
    result["external_verification_complete"] = external_verified
    result["identity_sha256"] = artifacts.digest(result)
    return result
