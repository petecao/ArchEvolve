"""Package-backed simulated diagnostic comparisons. Updated 2026-09-25.

The quantities are summed per-thread elapsed intervals, not primary BFS wall time.
"""
import hashlib
import math
import socket
import statistics
from pathlib import Path

from swdb import artifacts
from swdb.bfs_protocol import _fail, _get, _positive, _integer, _geomean, _timestamp


def _raw(reference, host, *, verify_hash=True):
    path = Path(reference["path"])
    if not path.exists():
        remote = host and host != socket.gethostname().split(".")[0] and str(path).startswith(("/data/", "/data1/"))
        _fail(remote, "diagnostic raw artifact is unavailable locally")
        return None  # Metadata retrieval never pretends to recheck remote raw bytes.
    _fail(path.is_file() and not path.is_symlink() and (not verify_hash or artifacts.file_hash(path) == reference["sha256"]),
          "diagnostic raw artifact changed")
    return path


def _sample(store, primary, package_id, pair, role):
    from swdb import profile_package
    package = _get(store, package_id, "profile_package")
    profile_package.verify(package)
    kind = primary["evidence_kind"]
    _fail("package_version" in package and package.get("evaluation") == primary["id"]
          and package.get("completeness") == ("complete" if kind == "execution" else "fixture")
          and package.get("evidence", {}).get("classification") == kind,
          "selected diagnostic package is incomplete or has another primary/evidence classification")
    profile = _get(store, package.get("region_profile"), "region_profile")
    _fail(profile.get("request", {}).get("fixture") is not True or kind == "contract_fixture",
          "fixture profile cannot support real execution")
    candidate = _get(store, primary["candidate"], "candidate")
    evidence = package["evidence"]
    _fail(evidence.get("evaluation_sha256") == artifacts.digest(primary)
          and evidence.get("region_profile_sha256") == artifacts.digest(profile), "selected diagnostic package evidence changed")
    _fail(not profile_package._profile_check(profile, primary, candidate), "diagnostic profile has incompatible primary context")
    _fail(profile_package._query_evidence(store, package)["state"] != "invalid", "diagnostic package memory evidence is invalid")
    _fail(evidence.get("diagnostic_executions") == profile.get("executions")
          and evidence.get("discovery") == profile.get("discovery"), "package collector evidence differs from its profile")
    chosen = [row for row in profile.get("regions", []) if row.get("id") == pair[role]]
    assembled = [row for row in package.get("regions", []) if row.get("id") == pair[role]]
    _fail(len(chosen) == len(assembled) == 1, "selected diagnostic region is missing or ambiguous")
    row, retained = chosen[0], assembled[0]
    _fail(all(retained.get(key) == row.get(key) for key in
              ("id", "metrics", "scope", "attribution", "basis", "artifact_sha256", "source_artifact_sha256", "text", "source_sha256", "byte_range")),
          "package region differs from its collector observation")
    _fail(row.get("source_artifact_sha256") == candidate["artifact"]["sha256"]
          and hashlib.sha256(row.get("text", "").encode()).hexdigest() == row.get("source_sha256"), "diagnostic region source identity changed")
    timing = primary.get("timing", [])
    _fail(len(timing) == 1, "regional package must identify one primary replay")
    cell = {key: timing[0][key] for key in ("source", "source_position", "repetition")}
    runs = [run for run in profile.get("executions", []) if run.get("kind") == "regions"]
    _fail(len(runs) == 1 and all(runs[0].get(key) == value for key, value in cell.items()),
          "diagnostic region observations differ from the primary source/repetition cell")
    run = runs[0]
    diagnostic = _get(store, run.get("evaluation"), "evaluation")
    _fail(diagnostic.get("outcome", {}).get("state") == "complete" and diagnostic.get("correctness", {}).get("state") == "passed"
          and run.get("correctness") == diagnostic["correctness"] and diagnostic.get("evidence_kind") == kind
          and run.get("evidence_kind") == kind and diagnostic.get("candidate") == candidate["id"]
          and profile_package._context(diagnostic) == profile_package._context(primary), "diagnostic replay lacks compatible independent correctness")
    _fail(diagnostic.get("request", {}).get("fixture") is not True or kind == "contract_fixture", "fixture diagnostic cannot support real execution")
    build = _get(store, diagnostic.get("context", {}).get("candidate_build"), "evaluation")
    definition = build.get("context", {}).get("diagnostic", {})
    _fail(build.get("request", {}).get("fixture") is not True or kind == "contract_fixture",
          "fixture diagnostic compilation cannot support real execution")
    binary = diagnostic.get("build", {})
    _fail(build.get("outcome", {}).get("state") == "complete" and build["outcome"].get("stage") == "candidate_build"
          and build.get("candidate") == candidate["id"] and build.get("evidence_kind") == kind
          and build.get("context", {}).get("candidate_sha256") == candidate["artifact"]["sha256"]
          and build.get("build", {}).get("binary_sha256") == binary.get("binary_sha256")
          and row.get("artifact_sha256") == run.get("binary_sha256") == binary.get("binary_sha256"),
          "diagnostic region lacks its exact source/binary compilation receipt")
    _fail(all(binary.get(key) == primary["build"].get(key) for key in ("model_build", "simulator", "simulator_sha256")),
          "diagnostic replay uses another simulator/model build")
    collector = pair["collector"]
    discovery = definition.get("discovery", {})
    _fail(profile.get("discovery") == discovery and all(discovery.get(key) == collector[key]
              for key in ("backend", "collector", "library_sha256", "pass_sha256"))
          and definition.get("runtime", {}).get("sha256") == collector["runtime_sha256"],
          "diagnostic collector differs from its frozen identity")
    originals = [item for item in definition.get("regions", []) if item.get("id") == row["id"]]
    _fail(len(originals) == 1 and all(originals[0].get(key) == row.get(key) for key in
              ("text", "source_sha256", "byte_range", "source_artifact_sha256")), "selected region differs from compiler discovery")
    attribution = row.get("attribution", {})
    _fail(row.get("basis") == "simulated" and row.get("scope") ==
          "accumulated simulated elapsed per executing thread within " + primary["context"]["roi"]
          and attribution.get("clock") == "m5_rpns" and attribution.get("whole_lexical_region") is True
          and attribution.get("quantity") == definition.get("quantity")
          and attribution.get("inclusive") is True
          and attribution.get("exclusive") == "nested guarded intervals subtracted on the same thread",
          "diagnostic region timing scope or attribution differs")
    log = {"path": run["region_output"], "sha256": run["region_output_sha256"]}
    stages = [stage for stage in diagnostic.get("stages", []) if stage.get("stage") == "simulation"]
    _fail(len(stages) == 1 and log == {"path": stages[0].get("log"), "sha256": stages[0].get("log_sha256")}
          and run.get("output") == log["path"] and run.get("output_sha256") == log["sha256"],
          "diagnostic region report is not bound to its simulation output")
    _fail(_timestamp(stages[0].get("started")) >= _timestamp(primary["context"]["protocol_binding"]["frozen_at"]),
          "diagnostic region observation predates protocol freeze")
    checks = diagnostic["correctness"].get("checks", [])
    _fail(len(checks) == 1 and checks[0].get("passed") is True and checks[0].get("source") == cell["source"]
          and checks[0].get("binary_sha256") == binary["binary_sha256"]
          and checks[0].get("graph_sha256") == primary["context"]["workload"]["canonical_sha256"]
          and checks[0].get("output_sha256") == log["sha256"], "diagnostic correctness is not bound to the reported graph/source/binary")
    host = diagnostic.get("context", {}).get("host")
    raw = _raw(log, host, verify_hash=False)
    for reference in (definition["runtime"], definition["instrumented_source"],
                      {"path": binary["binary"], "sha256": binary["binary_sha256"]}):
        _raw(reference, host)
    metrics = row["metrics"]
    invocations = _integer(metrics.get("invocations"), "diagnostic invocation count")
    inclusive = _positive(metrics.get("inclusive_simulated_seconds"), "diagnostic inclusive seconds")
    exclusive = metrics.get("exclusive_simulated_seconds")
    _fail(type(exclusive) in (int, float) and math.isfinite(exclusive) and 0 <= exclusive <= inclusive,
          "diagnostic exclusive duration is invalid or exceeds inclusive duration")
    if raw:
        from swdb.dx100_diagnostic import counters
        observed, digest = counters(raw, len(definition["regions"]), return_sha256=True)
        _fail(digest == log["sha256"], "diagnostic raw report changed")
        values = observed[definition["regions"].index(originals[0])]
        _fail(values["invocations"] == invocations and values["inclusive_ns"] / 1e9 == inclusive
              and values["exclusive_ns"] / 1e9 == exclusive, "diagnostic region values differ from the raw report")
    duration = inclusive if pair["attribution"] == "inclusive" else exclusive
    _positive(duration, "selected diagnostic duration")
    if pair["scope"] == "per_invocation": duration /= invocations
    return {**cell, "duration_s": duration, "invocations": invocations, "primary_evaluation": primary["id"],
            "primary_binary_sha256": primary["build"]["binary_sha256"], "diagnostic_evaluation": diagnostic["id"],
            "diagnostic_evaluation_sha256": artifacts.digest(diagnostic), "diagnostic_build": build["id"],
            "diagnostic_build_sha256": artifacts.digest(build), "diagnostic_binary_sha256": binary["binary_sha256"],
            "profile_package": package["id"], "package_sha256": package["identity_sha256"],
            "region_profile": profile["id"], "region_profile_sha256": artifacts.digest(profile), "raw_report": log,
            "source_sha256": row["source_sha256"], "source_artifact_sha256": candidate["artifact"]["sha256"],
            "quantity": definition["quantity"], "timing_scope": row["scope"], "attribution": attribution}


def compare(store, a, b, settings, packages):
    _fail(isinstance(packages, dict), "simulated diagnostic comparison requires explicit region_packages")
    components = {}
    for role, evaluation in (("baseline", a), ("candidate", b)):
        components[role] = [_get(store, item["evaluation"], "evaluation") for item in evaluation.get("component_evaluations", [])]
        _fail(components[role], "simulated diagnostic comparison requires aggregated separate primary replays")
    _fail(set(packages) == {item["id"] for rows in components.values() for item in rows}, "region_packages must cover exactly both primary execution grids")
    results = []
    for pair in settings.get("region_pairs", []):
        if pair.get("evidence") != "simulated_diagnostic_profile": continue
        samples = {role: [_sample(store, primary, packages[primary["id"]], pair, role) for primary in rows]
                   for role, rows in components.items()}
        diagnostic_ids = [row["diagnostic_evaluation"] for rows in samples.values() for row in rows]
        _fail(len(diagnostic_ids) == len(set(diagnostic_ids)), "diagnostic replay is reused across distinct comparison cells")
        cells = {role: {(row["source_position"], row["repetition"], row["source"]) for row in rows} for role, rows in samples.items()}
        _fail(cells["baseline"] == cells["candidate"] and all(len(cells[role]) == len(samples[role]) for role in cells),
              "diagnostic comparison has missing, duplicate, or different replay cells")
        positions = sorted({cell[0] for cell in cells["baseline"]})
        ratios = {position: statistics.median(row["duration_s"] for row in samples["baseline"] if row["source_position"] == position)
                  / statistics.median(row["duration_s"] for row in samples["candidate"] if row["source_position"] == position)
                  for position in positions}
        results.append({**pair, "duration_ratio": _positive(_geomean(ratios.values()), "region duration ratio"),
            "per_source_position_ratio": ratios, "samples": samples, "primary_bfs_roi": False, "gain_claim": False,
            "note": "Diagnostic per-thread elapsed ratio; includes waiting and overlap and cannot replace primary BFS timing."})
    return results
