"""Exact evidence assembly and bidirectional strategy lookup. Updated 2026-09-25."""

import copy
import hashlib
import math
from pathlib import Path

from swdb import artifacts, db, strategy, workflow
from swdb.bfs_protocol import _fail, _get, _integer, _request
from swdb.cli import Failure, _require_valid


def _context(evaluation):
    context = evaluation["context"]
    return {"source_sha256": context["candidate_sha256"],
            "canonical_graph_sha256": context["workload"]["canonical_sha256"],
            "sources": context["sources"], "target": context["target"],
            "target_configuration": context.get("backend_configuration", context.get("configuration", {})),
            "threads": context["threads"], "roi": context["roi"]}


def _number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def _timing_quantity(region):
    metrics = region.get("metrics", {})
    if not (_number(metrics.get("invocations")) and metrics["invocations"] > 0 and region.get("scope")):
        return None
    for quantity, basis in (("thread_cpu", "measured"), ("simulated", "simulated")):
        names = [f"{attribution}_{quantity}_seconds" for attribution in ("inclusive", "exclusive")]
        if region.get("basis") == basis and all(_number(metrics.get(name)) for name in names):
            return quantity
    return None


def verify(package):
    """Check sealed assemblies while leaving the original explicit fixtures compatible."""
    if "package_version" not in package:
        return
    original = copy.deepcopy(package)
    expected = original.pop("identity_sha256", None)
    original["id"] = original.get("requested_id")
    _fail(artifacts.digest(original) == expected and package["id"] ==
          f"{original['requested_id']}.v{original['package_version']}.{expected[:16]}",
          "profile package content differs from its retained identity")


def _profile_check(profile, evaluation, candidate):
    reasons = []
    for key in ("evaluation", "candidate", "implementation", "machine"):
        expected = evaluation["id"] if key == "evaluation" else evaluation[key]
        if profile.get(key) != expected:
            reasons.append(f"region profile has incompatible {key}")
    try:
        if _context(profile) != _context(evaluation):
            reasons.append("region profile has incompatible source/workload/target/sources/threads/ROI")
    except (KeyError, TypeError):
        reasons.append("region profile lacks exact context identity")
    if profile.get("context", {}).get("primary_binary_sha256") != evaluation.get("build", {}).get("binary_sha256"):
        reasons.append("region profile names a different or unidentified primary binary")
    if profile.get("source_snapshot") != candidate["source_snapshot"]:
        reasons.append("region profile names a different source ancestor")
    return reasons


def _region(row, root):
    row = copy.deepcopy(row)
    path = Path(row.get("path", ""))
    path = path if path.is_absolute() else root / artifacts.relative_path(str(path))
    try:
        relative = path.resolve().relative_to(root)
    except ValueError:
        raise Failure("region source lies outside the current candidate snapshot") from None
    _fail(path.is_file() and not path.is_symlink(), "region source file is unavailable")
    raw = path.read_bytes()
    extent = row.get("byte_range")
    _fail(isinstance(extent, list) and len(extent) == 2 and all(type(v) is int for v in extent)
          and 0 <= extent[0] < extent[1] <= len(raw), "region lacks a valid current-source byte extent")
    fragment = raw[extent[0]:extent[1]]
    _fail(hashlib.sha256(fragment).hexdigest() == row.get("source_sha256"), "region source extent is stale")
    _fail(fragment.decode(errors="replace") == row.get("text"), "region source text is stale")
    row.update(path=relative.as_posix(), source_association="verified_current_candidate")
    return row


def _static_rows(store, chosen, impl):
    """Reuse the established semantic legality rules; never infer unknown facts."""
    if chosen["target"] == "access_pattern":
        for pattern in impl["access_patterns"]:
            yield {**strategy.entry(chosen, *strategy.pattern_outcome(chosen, pattern)),
                   "implementation": impl["id"], "pattern": pattern["id"], "loop": pattern["loop"],
                   "code": pattern.get("code"), "match_basis": "static_applicability"}
    elif chosen["target"] == "loop":
        for loop in impl["loops"]:
            ids = db.loop_and_children(impl, loop["id"])
            patterns = [p for p in impl["access_patterns"] if p["loop"] in ids]
            reasons, unknown = [], []
            for pattern in patterns:
                _, why, missing = strategy.pattern_outcome(chosen, pattern)
                reasons.extend(f"{pattern['id']}: {s}" for s in why)
                unknown.extend(f"{pattern['id']}.{s}" for s in missing)
            outcome = "illegal" if reasons else "undetermined" if unknown or not patterns else "legal"
            extra = [] if patterns else ["loop and its children have no recorded access patterns"]
            yield {**strategy.entry(chosen, outcome, reasons, unknown, extra), "implementation": impl["id"],
                   "loop": loop["id"], "code": loop.get("code"), "match_basis": "static_applicability"}
    else:
        yield {**strategy.entry(chosen, "undetermined", [], []), "implementation": impl["id"],
               "match_basis": "static_applicability"}


def _forward(store, impl, regions, unchanged):
    found = []
    for chosen in sorted((r.data for r in store.of_kind("strategy")), key=lambda s: s["id"]):
        static = list(_static_rows(store, chosen, impl))
        for region in regions:
            matches = []
            if unchanged:
                for row in static:
                    code = row.get("code") or {}
                    lines = code.get("lines")
                    if chosen["target"] == "input" or (code.get("path") == region["path"] and lines
                            and max(lines[0], region["lines"][0]) <= min(lines[1], region["lines"][1])):
                        matches.append(row)
            if matches:
                for row in matches:
                    item = copy.deepcopy(row)
                    item.update(region=region["id"], source_correspondence="unchanged_application_snapshot",
                                strategy_sha256=artifacts.digest(chosen), performance_guarantee=False,
                                effect=copy.deepcopy(chosen["effect"]), preconditions=copy.deepcopy(chosen["preconditions"]),
                                common_intrinsics=chosen.get("common_intrinsics", []),
                                measured_outcomes=None, hardware_support={"state": "unknown",
                                    "reason": "Strategy records do not encode executable operation requirements."})
                    item["semantic_outcome"] = item["outcome"]
                    if item["outcome"] == "legal" and item["check_by_hand"]:
                        item["outcome"] = "undetermined"
                    found.append(item)
            else:
                found.append({**strategy.entry(chosen, "undetermined", [], ["current_region_semantics"]),
                              "implementation": impl["id"], "region": region["id"],
                              "source_correspondence": "unresolved_after_rewrite" if not unchanged else "no_static_pattern_association",
                              "strategy_sha256": artifacts.digest(chosen), "match_basis": "unresolved_applicability",
                              "effect": copy.deepcopy(chosen["effect"]), "preconditions": copy.deepcopy(chosen["preconditions"]),
                              "common_intrinsics": chosen.get("common_intrinsics", []),
                              "hardware_support": {"state": "unknown", "reason": "No checked operation requirements for this region."},
                              "measured_outcomes": None, "performance_guarantee": False})
    return found


def _memory(rows):
    available = []
    for row in rows:
        if row.get("available") is not True:
            continue
        if not (_number(row.get("value")) and row.get("basis") in {"measured", "simulated"}
                and all(row.get(key) for key in ("metric", "unit", "definition", "scope", "collector", "execution", "artifact_sha256"))):
            continue
        available.append(row)
    return available


def _check_observations(profile, evaluation, candidate):
    """Bind diagnostics to actual executions rather than accepting standalone numbers."""
    reasons = []
    executions = profile.get("executions", [])
    fixture = profile.get("request", {}).get("fixture") is True
    for kind in ("regions", "memory"):
        matching = [run for run in executions if run.get("kind") == kind]
        expected = {(position, source) for position, source in enumerate(evaluation["context"]["sources"])}
        covered = {(run.get("source_position"), run.get("source")) for run in matching}
        if not expected <= covered:
            reasons.append(f"{kind} observations do not cover the requested source sequence")
        for run in matching:
            for path_key, hash_key in (("output", "output_sha256"),
                                       ("region_output", "region_output_sha256") if kind == "regions" else ("raw_artifact", "raw_sha256")):
                try:
                    path = Path(run[path_key])
                    valid = path.is_file() and artifacts.file_hash(path) == run[hash_key]
                except (KeyError, OSError, TypeError):
                    valid = False
                if not valid:
                    reasons.append(f"{kind} execution has unavailable or changed {path_key}")
    for region in profile.get("regions", []):
        if region.get("source_artifact_sha256") != candidate["artifact"]["sha256"] or not any(
                run.get("kind") == "regions" and run.get("binary_sha256") == region.get("artifact_sha256")
                for run in executions):
            reasons.append(f"region {region.get('id')} has no matching source/binary execution")
    for row in profile.get("dynamic_memory", []):
        if row.get("available") is not True:
            continue
        reference = row.get("execution")
        matching = [run for run in executions if run.get("kind") == "memory" and isinstance(reference, dict)
                    and all(run.get(key) == reference.get(key) for key in ("source", "source_position", "repetition"))
                    and run.get("binary_sha256") == row.get("artifact_sha256")
                    and run.get("raw_sha256") == row.get("raw_sha256")
                    and run.get("raw_artifact") == row.get("raw_artifact")]
        if row.get("source_artifact_sha256") != candidate["artifact"]["sha256"] or len(matching) != 1:
            reasons.append(f"memory metric {row.get('metric')} has no matching source/binary/raw execution")
    if not fixture:
        for name in ("region_binary", "memory_binary"):
            binary = profile.get("artifacts", {}).get(name, {})
            try:
                valid = artifacts.file_hash(binary["path"]) == binary["sha256"]
            except (KeyError, OSError, TypeError):
                valid = False
            if not valid:
                reasons.append(f"diagnostic {name} is unavailable or changed")
    return reasons


def assemble(args):
    request = _request(args)
    store = _require_valid(args.records)
    version = _integer(request.get("version", 1), "version")
    previous = [r.data for r in store.of_kind("profile_package") if r.data.get("requested_id") == request["id"]]
    _fail(not previous or version > max(p["package_version"] for p in previous), "package changes require a newer version")
    evaluation = _get(store, request.get("evaluation"), "evaluation")
    candidate = _get(store, evaluation.get("candidate"), "candidate")
    impl = _get(store, request.get("implementation"), "implementation")
    _fail(impl["id"] == evaluation["implementation"] == candidate["implementation"], "requested implementation differs from evaluation")
    _fail(candidate["artifact"]["sha256"] == evaluation["context"]["candidate_sha256"], "evaluation source identity differs from candidate")
    _fail(request.get("context") == _context(evaluation), "requested exact source/workload/target/sources/threads/ROI differs from evaluation")
    root = artifacts.verify(candidate["artifact"])
    machine = _get(store, evaluation.get("machine"), "machine")
    if evaluation["context"].get("machine_sha256"):
        _fail(artifacts.digest(machine) == evaluation["context"]["machine_sha256"], "machine metadata changed after evaluation")
    original = _get(store, candidate["source_snapshot"], "source_snapshot")
    reasons, regions, dynamic = [], [], []
    profile = store.get(request.get("region_profile"), "region_profile")
    if request.get("region_profile") and profile is None:
        reasons.append("requested region profile is unavailable")
    elif profile is None:
        reasons.append("function/loop discovery and dynamic-memory profiling are unavailable")
    else:
        incompatible = _profile_check(profile, evaluation, candidate)
        reasons.extend(incompatible)
        if not incompatible:
            reasons.extend(_check_observations(profile, evaluation, candidate))
            for row in profile["regions"]:
                try:
                    regions.append(_region(row, root))
                except (Failure, OSError, KeyError, TypeError) as exc:
                    reasons.append(f"region {row.get('id', '<unknown>')}: {exc}")
            dynamic = copy.deepcopy(profile["dynamic_memory"])
            if profile["outcome"]["state"] not in {"complete", "partial"}:
                reasons.append("diagnostic profiling did not complete")
    selected = request.get("selected_regions")
    if selected is not None:
        _fail(isinstance(selected, list) and all(isinstance(r, str) for r in selected), "selected_regions must be IDs")
        _fail(set(selected) <= {r["id"] for r in regions}, "selected region is unavailable in compatible profiling evidence")
    for kind in ("function", "loop"):
        if not any(r.get("kind") == kind and _timing_quantity(r) for r in regions):
            reasons.append(f"automatically discovered {kind} timing is unavailable")
    if not _memory(dynamic):
        reasons.append("no available dynamic memory observation with collector/execution identity")
    timing = evaluation.get("timing", [])
    basis = evaluation["context"].get("basis")
    quantity = {"measured": "native_roi_wall_seconds", "simulated": "simulated_roi_seconds"}.get(basis)
    if not timing or quantity is None or not all(_number(row.get("duration_s")) and row["duration_s"] > 0
            and row.get("roi") == evaluation["context"]["roi"]
            and row.get("basis") == basis and row.get("quantity") == quantity
            and row.get("binary_sha256") == evaluation["build"].get("binary_sha256") for row in timing):
        reasons.append("primary evaluation lacks identified ROI timing")
    if not {(position, source) for position, source in enumerate(evaluation["context"]["sources"])} <= {
            (row.get("source_position"), row.get("source")) for row in timing}:
        reasons.append("primary ROI timing does not cover the requested source sequence")
    fixture = (evaluation.get("evidence_kind") != "execution" or evaluation.get("request", {}).get("fixture") is True
               or (profile or {}).get("request", {}).get("fixture") is True)
    classification = "contract_fixture" if fixture else "execution"
    completeness = "incomplete" if reasons else "fixture" if fixture else "complete"
    context = copy.deepcopy(request["context"])
    context.update(primary_binary_sha256=evaluation["build"].get("binary_sha256"),
                   workload=copy.deepcopy(evaluation["context"]["workload"]),
                   build=copy.deepcopy(evaluation["build"]))
    source_id = f"{request['id']}.v{version}.source"
    snapshot = workflow.record("source_snapshot", source_id, implementation=impl["id"],
        application=original["application"], revision=original["revision"], artifact=copy.deepcopy(candidate["artifact"]),
        context=copy.deepcopy(candidate["context"]), regions=copy.deepcopy(regions), protections=copy.deepcopy(candidate["protections"]))
    evidence = {"classification": classification, "evaluation_sha256": artifacts.digest(evaluation),
                "region_profile_sha256": artifacts.digest(profile) if profile else None,
                "primary_correctness": copy.deepcopy(evaluation.get("correctness")),
                "primary_timing": copy.deepcopy(evaluation.get("timing")),
                "discovery": copy.deepcopy((profile or {}).get("discovery", {})),
                "diagnostic_executions": copy.deepcopy((profile or {}).get("executions", [])),
                "diagnostic_build": copy.deepcopy((profile or {}).get("build", {})),
                "correspondence": copy.deepcopy((profile or {}).get("correspondence", {})),
                "coverage": {"scope": (profile or {}).get("discovery", {}).get("scope", "unavailable"),
                             "limitations": (profile or {}).get("discovery", {}).get("limitations", []),
                             "unresolved": (profile or {}).get("discovery", {}).get("unresolved", [])},
                "full_application": copy.deepcopy(candidate["artifact"]),
                "supporting_sources": [f for f in candidate["artifact"]["files"] if Path(f["path"]).suffix in {".h", ".hpp", ".cc", ".cpp"}],
                "selected_regions": selected or [r["id"] for r in regions]}
    evidence["rankings"] = []
    for kind in ("function", "loop"):
        for quantity in ("thread_cpu", "simulated"):
            metric = f"exclusive_{quantity}_seconds"
            ranked = sorted((r for r in regions if r["kind"] == kind and _timing_quantity(r) == quantity),
                            key=lambda r: (-r["metrics"][metric], r["id"]))
            if ranked:
                evidence["rankings"].append({"kind": kind, "metric": metric,
                    "regions": [r["id"] for r in ranked], "inclusive_rule": "nested source extents overlap; do not sum inclusive duration",
                    "coverage": "limited to the explicitly discovered and executed source extents"})
    target = store.get(context["target"], "hardware_target")
    hardware = {"state": "known" if target else "unknown", "target": target,
                "operations": [r.data for r in store.of_kind("operation") if target and r.id in target["operations"]],
                "reason": None if target else "No accelerator interface is declared for this target."}
    hardware["machine"] = {"id": machine["id"], "sha256": artifacts.digest(machine), "cpu": machine.get("cpu", {})}
    hardware["intrinsic_interfaces"] = []
    cpu = machine.get("cpu", {})
    for intrinsic in store.of_kind("intrinsic"):
        value = intrinsic.data
        supported = "unknown"
        if value["isa_family"] == "x86" and cpu.get("architecture") == "x86_64" and isinstance(cpu.get("flags"), list):
            supported = "supported" if set(value["isa_extensions"]) <= set(cpu["flags"]) else "unsupported"
        hardware["intrinsic_interfaces"].append({"id": intrinsic.id, "header": value["header"],
            "isa_family": value["isa_family"], "isa_extensions": value["isa_extensions"], "machine_support": supported,
            "build_support": "unknown", "basis": "recorded machine flags; no compilation of this proposed intrinsic"})
    package = workflow.record("profile_package", request["id"], requested_id=request["id"], package_version=version,
        implementation=impl["id"], source_snapshot=source_id, candidate=candidate["id"], evaluation=evaluation["id"],
        context=context, completeness=completeness, regions=regions, dynamic_memory=dynamic,
        constraints={"protections": copy.deepcopy(candidate["protections"]), "preserve_correctness": True,
                     "preserve_roi": True, "verification": copy.deepcopy(impl.get("verification")),
                     "editable_files": sorted({r["path"] for r in regions})}, evidence=evidence, reasons=reasons,
        strategies=_forward(store, impl, regions, candidate["artifact"]["sha256"] == original["artifact"]["sha256"]),
        hardware=hardware, gain_claim=False)
    if profile:
        package["region_profile"] = profile["id"]
    package["identity_sha256"] = artifacts.digest(package)
    package["id"] = f"{request['id']}.v{version}.{package['identity_sha256'][:16]}"
    workflow.persist(args.records, snapshot, args.db, create=True)
    return workflow.persist(args.records, package, args.db, create=True)


def strategies(args):
    store = _require_valid(args.records)
    package = _get(store, args.package, "profile_package")
    verify(package)
    matches = copy.deepcopy(package.get("strategies", []))
    if args.region:
        _fail(args.region in {r["id"] for r in package["regions"]}, "region is absent from package")
        matches = [r for r in matches if r["region"] == args.region]
    return {"profile_package": package["id"], "context": package["context"], "matches": matches,
            "performance_guarantee": False, "classification": package["evidence"].get("classification")}


def regions(args):
    store = _require_valid(args.records)
    chosen = _get(store, args.strategy, "strategy")
    static = [row for impl in store.of_kind("implementation") for row in _static_rows(store, chosen, impl.data)
              if row["outcome"] != "illegal"]
    packages = [_get(store, args.package, "profile_package")] if args.package else [r.data for r in store.of_kind("profile_package")]
    profiled = []
    for package in packages:
        verify(package)
        for row in package.get("strategies", []):
            if row["strategy"] == chosen["id"] and row["outcome"] != "illegal":
                profiled.append({**copy.deepcopy(row), "profile_package": package["id"],
                                 "context": package["context"], "evidence_classification": package["evidence"]["classification"],
                                 "package_completeness": package["completeness"],
                                 "profile_support": "compatible_profile_evidence" if package["completeness"] == "complete" else "incomplete_or_fixture"})
    return {"strategy": chosen["id"], "strategy_sha256": artifacts.digest(chosen), "effect": chosen["effect"],
            "static_matches": static, "profiled_matches": profiled, "performance_guarantee": False}
