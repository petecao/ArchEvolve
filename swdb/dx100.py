"""Bounded DX100 build, checkpoint, and unverified execution workflows.

Updated: 2026-09-25. Build/smoke evidence never certifies a timed binary.
"""

import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import time
import uuid

import yaml

from swdb import artifacts, bfs_protocol, paths, profile, workflow, yamlio
from swdb.bfs_native import Session, StageFailure, Stopped, _integer, _now
from swdb.cli import Failure, _require_valid

REVISION = "e4fc4afdf894f295442cef3604667a469fab8e62"
ROI = "bfs.dx100.traversal.v1"


def _file(reference, name):
    if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
        raise Failure(f"{name} requires path and sha256")
    if not isinstance(reference["path"], str) or not isinstance(reference["sha256"], str):
        raise Failure(f"{name} path and sha256 must be strings")
    path = Path(reference["path"])
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise Failure(f"{name} must identify an absolute regular file")
    if artifacts.file_hash(path) != reference["sha256"]:
        raise Failure(f"{name} content differs from recorded sha256")
    return path


def _request(args, action):
    store = _require_valid(args.records)
    try:
        text = Path(args.file).read_text()
        if len(text.encode()) > 10 * 1024 * 1024:
            raise Failure("DX100 request exceeds 10 MiB")
        request = yaml.load(text, Loader=yamlio._Loader)
    except yaml.YAMLError as exc:
        request = {"parse_error": str(exc)}
    rid = request.get("id") if isinstance(request, dict) else None
    if not isinstance(rid, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", rid):
        rid = f"dx100-invalid-{uuid.uuid4().hex}"
    if store.get(rid):
        raise Failure("DX100 request ID already exists; retain it and use a new ID")
    data = workflow.record("evaluation", rid, request=request, outcome={"state": "submitted", "stage": "submission", "reason": None},
        stages=[], timing=[], correctness={"state": "unverified", "checks": []},
        profiling={"state": "incomplete", "reasons": ["BFS ROI, regions, and memory metrics require the profile collector."]},
        raw_artifacts=[], gain_claim=False,
        evidence_kind="contract_fixture" if isinstance(request, dict) and request.get("fixture") is True else "execution")
    workflow.persist(args.records, data, getattr(args, "db", None))
    return store, request, data


def _prepare(args, action, store, request, data):
    if not isinstance(request, dict) or request.get("message_version") != "1.0":
        raise Failure("DX100 request requires message_version 1.0")
    fields = {"message_version", "id", "machine", "hardware_target", "model_root", "budget", "fixture"}
    if action == "build":
        fields |= {"fixture_command"}
    elif action == "compile":
        fields |= {"candidate", "build_evaluation", "function", "accelerated", "roi", "fixture_compiler", "diagnostic_regions", "discovery"}
    else:
        fields |= {"simulator", "binary", "workload", "configuration", "checkpoint_manifest", "build_evaluation", "verification", "candidate", "candidate_build", "protocol", "protocol_role", "protocol_trial"}
    if request.keys() - fields:
        raise Failure(f"unknown DX100 request fields: {sorted(request.keys() - fields)}")
    if not isinstance(request.get("fixture", False), bool):
        raise Failure("fixture must be boolean")
    for key in ("machine", "hardware_target", "model_root"):
        if not isinstance(request.get(key), str) or not request[key]:
            raise Failure(f"DX100 request requires {key}")
    target = store.get(request["hardware_target"], "hardware_target")
    machine = store.get(request["machine"], "machine")
    if not target or target["model"]["revision"] != REVISION or target["backend"]["id"] != "dx100-gem5-se":
        raise Failure("DX100 target/model/backend is unsupported")
    host = socket.gethostname().split(".")[0]
    if not machine or machine["hostname"] != host:
        raise Failure("execution host differs from requested machine")
    if host == "mbit10" and not profile.lane_required(machine):
        raise Failure("mbit10 cannot disable socket lane policy")
    claimed = getattr(args, "lane", None)
    if claimed is not None and str(claimed) in {"0", "1"}:
        claimed = f"mbit10-evaluation-node{claimed}"
    lane = profile._verified_lane(machine, claimed)
    model_root = Path(request["model_root"]).resolve()
    if not request.get("fixture"):
        if host != "mbit10" or not model_root.is_relative_to("/data1/yanruj"):
            raise Failure("real DX100 builds/runs require mbit10 source under /data1/yanruj")
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=model_root, text=True, timeout=30).strip()
        if revision != REVISION or subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=model_root, text=True, timeout=30).strip():
            raise Failure("model source is not the clean pinned DX100 revision")
    budget = request.get("budget")
    if not isinstance(budget, dict):
        raise Failure("DX100 request requires explicit budget")
    total = _integer(budget.get("total_seconds"), "budget.total_seconds", maximum=18000 if action == 'execute' else 7200)
    memory = _integer(budget.get("memory_gib"), "budget.memory_gib", maximum=48)
    storage = _integer(budget.get("storage_gib"), "budget.storage_gib", maximum=20)
    if action == "build":
        _integer(budget.get("jobs"), "budget.jobs", maximum=8)
        if storage > 10 or set(budget) != {"total_seconds", "memory_gib", "storage_gib", "jobs"}:
            raise Failure("build budget requires total_seconds,memory_gib,storage_gib<=10,jobs")
    elif action == "compile":
        _integer(budget.get("build_seconds"), "budget.build_seconds", maximum=1800)
        if storage > 10 or set(budget) != {"total_seconds", "memory_gib", "storage_gib", "build_seconds"}:
            raise Failure("candidate compile budget requires total_seconds,memory_gib,storage_gib<=10,build_seconds")
    elif set(budget) != {"total_seconds", "memory_gib", "storage_gib", "checkpoint_seconds", "run_seconds"}:
        raise Failure("execution budget requires total_seconds,memory_gib,storage_gib,checkpoint_seconds,run_seconds")
    destination = Path(args.runs_dir).resolve()
    if host == "mbit10" and not any(destination.is_relative_to(base) for base in (
            "/data1/yanruj/EvolveSWDB_runs", "/data/yanruj/EvolveSWDB_runs")):
        raise Failure("mbit10 raw evidence must use EvolveSWDB_runs storage")
    folder = artifacts.external_directory(destination) / data["id"]
    if folder.is_relative_to(Path(args.records).resolve()):
        raise Failure("DX100 raw evidence must not be inside records")
    folder.mkdir(exist_ok=False)
    data.update(machine=machine["id"], context={"backend": target["backend"]["id"], "target": target["id"],
        "target_sha256": artifacts.digest(target), "model": target["model"], "interface": target["interface"],
        "model_root": str(model_root), "host": host, "lane": lane, "budget": budget,
        "load_average": list(os.getloadavg()), "roi": ROI, "basis": "simulated"})
    data["raw_artifacts"].append({"host": host, "path": str(folder), "kind": f"dx100_{action}"})
    session = Session(args, data, folder, total + (30 if action == "build" and not request.get("fixture") else 0))
    session.install_handlers()
    return session, target, model_root


def _terminate(child):
    if child is None or child.poll() is not None:
        return
    try:
        os.killpg(child.pid, signal.SIGTERM)
        child.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait()
    except ProcessLookupError:
        child.wait()


def _bounded_process(session, name, command, timeout, memory, storage, env=None):
    """Monitor real children and preserve completed evidence on interrupted work."""
    allowed = min(timeout, session.remaining())
    log = session.folder / f"{len(session.data['stages']):03d}-{name}.log"
    session.begin(name, command=list(map(str, command)), timeout_s=allowed, log=str(log))
    start = time.monotonic()
    reason = None
    code = None
    last_storage = 0
    peak_rss_kib = None
    try:
        with log.open("w") as stream:
            session.child = subprocess.Popen(command, cwd=session.folder, env=env, stdout=stream,
                                             stderr=subprocess.STDOUT, start_new_session=True)
            while session.child.poll() is None:
                if time.monotonic() - start >= allowed:
                    raise StageFailure("timed_out", f"{name} exceeded {allowed} seconds")
                session.remaining()
                if sys.platform == "linux":
                    # Include all processes in this child's group. The build helper
                    # separately accounts for its nested compiler process group.
                    rss = subprocess.check_output(["ps", "-eo", "pgid=,rss="], text=True, timeout=10)
                    used = sum(int(row[1]) for line in rss.splitlines() if len(row := line.split()) == 2 and row[0] == str(session.child.pid))
                    peak_rss_kib = max(peak_rss_kib or 0, used)
                    if used > memory * 1024 * 1024:
                        raise StageFailure("budget_exhausted", f"simulator process-group memory budget exhausted: {used} KiB > {memory} GiB")
                if time.monotonic() - last_storage >= 30:
                    directories = [session.folder]
                    build_dir = session.data.get('context', {}).get('build_directory')
                    if build_dir and not Path(build_dir).is_relative_to(session.folder):
                        directories.append(Path(build_dir))
                    used = sum(int(subprocess.check_output(["du", "-sk", str(path)], text=True, timeout=30).split()[0])
                               for path in directories)
                    if used > storage * 1024 * 1024:
                        raise StageFailure("budget_exhausted", "raw artifact storage budget exhausted")
                    last_storage = time.monotonic()
                time.sleep(0.2 if session.data["evidence_kind"] == "contract_fixture" else 2)
            code = session.child.returncode
    except (StageFailure, Stopped, OSError, subprocess.SubprocessError) as exc:
        reason = exc
    finally:
        _terminate(session.child)
        session.child = None
    state = "complete" if code == 0 and reason is None else reason.state if isinstance(reason, StageFailure) else "interrupted" if isinstance(reason, Stopped) else "failed"
    session.finish(state, host_wall_s=time.monotonic() - start, returncode=code,
                   log_sha256=artifacts.file_hash(log), reason=str(reason) if reason else None,
                   sampled_peak_process_group_rss_kib=peak_rss_kib)
    if reason:
        raise reason
    if code != 0:
        raise StageFailure("failed", f"{name} exited with status {code}; see {log}")
    return log


def _finish(args, data, session, error=None):
    if error is not None:
        if isinstance(error, Failure) and "persisted, but query indexing failed" in str(error):
            raise error
        state = error.state if isinstance(error, StageFailure) else "interrupted" if isinstance(error, Stopped) else "failed"
        stage = session.current["stage"] if session and session.current else "validation"
        data["outcome"] = {"state": state, "stage": stage, "reason": str(error)}
        if session and session.current and session.current["state"] == "running":
            session.current.update(state=state, finished=_now(), reason=str(error))
    if session:
        session.restore_handlers()
    return workflow.persist(args.records, data, getattr(args, "db", None))


def build(args):
    store, request, data = _request(args, "build")
    session = None
    error = None
    try:
        session, target, root = _prepare(args, "build", store, request, data)
        budget = request["budget"]
        output = session.folder / "build"
        if request.get("fixture"):
            command = request.get("fixture_command")
            if not isinstance(command, list) or not command or not all(isinstance(part, str) for part in command):
                raise Failure("build fixtures require an explicit fixture_command argument list")
        else:
            if "fixture_command" in request:
                raise Failure("fixture_command cannot execute as real build evidence")
            lane = str(getattr(args, "lane", ""))
            node = lane[-1:] if lane.startswith("mbit10-evaluation-node") else lane
            if node not in {"0", "1"}:
                raise Failure("DX100 build requires --lane 0 or --lane 1")
            command = [sys.executable, str(paths.HOME / "scripts/dx100_build.py"), "--source", str(root),
                "--output", str(output), "--lane", node, "--jobs", str(budget["jobs"]),
                "--wall-seconds", str(budget["total_seconds"]), "--memory-gib", str(budget["memory_gib"]),
                "--storage-gib", str(budget["storage_gib"])]
        data["build"] = {"receipt": str(output / "build-receipt.json"), "model_revision": REVISION}
        try:
            _bounded_process(session, "model_build", command, budget["total_seconds"] + (0 if request.get("fixture") else 20),
                             budget["memory_gib"], 2)
        finally:
            receipt = output / "build-receipt.json"
            if receipt.is_file():
                data["build"].update(receipt_sha256=artifacts.file_hash(receipt), details=json.loads(receipt.read_text()))
                session.save()
        if not request.get("fixture") and data["build"].get("details", {}).get("state") != "completed":
            raise StageFailure("missing_observation", "build helper did not retain a completed build receipt")
        if not request.get("fixture"):
            for reference in data["build"]["details"]["binaries"]:
                _file({"path": reference["path"], "sha256": reference["sha256"]}, "built binary")
            target["backend"].update(readiness="built", build_evidence=[{
                "uri": f"ssh://{data['context']['host']}{data['build']['receipt']}",
                "sha256": data["build"]["receipt_sha256"]}])
            workflow.persist(args.records, target, getattr(args, "db", None))
        data["outcome"] = {"state": "complete", "stage": "build", "reason": "Build evidence only; no BFS execution or correctness verdict."}
    except (Failure, StageFailure, Stopped, OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        error = exc
    return _finish(args, data, session, error)


def compile_candidate(args):
    from swdb.dx100_candidate import compile_candidate as compile_impl
    return compile_impl(args)


def _configuration(request, target, root):
    config = request.get("configuration")
    if not isinstance(config, dict) or set(config) != {"mode", "l3_size_mb", "l3_assoc", "tile_elements"}:
        raise Failure("configuration requires mode,l3_size_mb,l3_assoc,tile_elements")
    if config["mode"] not in {"BASE", "MAA"}:
        raise Failure("DX100 mode must be BASE or MAA")
    size = _integer(config["l3_size_mb"], "l3_size_mb", maximum=64)
    assoc = _integer(config["l3_assoc"], "l3_assoc", maximum=64)
    tile = _integer(config["tile_elements"], "tile_elements")
    if tile not in {1024, 2048, 4096, 8192, 16384, 32768}:
        raise Failure("unsupported DX100 tile size")
    if target["configuration"].get("tile_elements") != tile or target["configuration"].get("guest_cores") != 4:
        raise Failure("request tile/core configuration differs from the selected hardware target")
    ramulator = root / "ext/ramulator2/ramulator2/example_gem5_config.yaml"
    if not ramulator.is_file():
        raise Failure("pinned Ramulator2 configuration is missing")
    settings = ["--cpu-type", "X86O3CPU", "-n", "4", "--mem-size", "16GB", "--sys-clock", "3.2GHz",
        "--cpu-clock", "3.2GHz", "--caches", "--l1d_size=32kB", "--l1d_assoc=8", "--l1d-hwp-type=StridePrefetcher",
        "--l1d_mshrs=16", "--l1d_write_buffers=8", "--l1i_size=32kB", "--l1i_assoc=8", "--l1i-hwp-type=StridePrefetcher",
        "--l1i_mshrs=16", "--l1i_write_buffers=8", "--l2cache", "--l2_size=256kB", "--l2_assoc=4",
        "--l2-hwp-type=StridePrefetcher", "--l2_mshrs=32", "--l2_write_buffers=16", "--l3cache",
        f"--l3_size={size}MB", f"--l3_assoc={assoc}", "--l3_mshrs=256", "--l3_write_buffers=128", "--l3_ports", "4",
        "--cacheline_size=64", "--mem-type", "Ramulator2", "--ramulator-config", str(ramulator),
        "--mem-channels", "2", "--maa_ncbus_width", "32", "--prog-interval=1000"]
    if config["mode"] == "MAA":
        settings += ["--maa", "--maa_num_maas", "1", "--maa_num_tile_elements", str(tile),
                     "--maa_l2_uncacheable", "--maa_l3_uncacheable", "--maa_num_initial_row_table_slices", "32"]
    return settings, {**config, "guest_cores": 4, "guest_memory": "16GB", "cpu": "X86O3CPU",
        "clock_hz": 3200000000, "model_revision": REVISION,
        "cache": {"l1d_kib": 32, "l1i_kib": 32, "l1_assoc": 8, "l2_kib": 256, "l2_assoc": 4,
                  "l3_mib": size, "l3_assoc": assoc, "cacheline_bytes": 64, "prefetcher": "StridePrefetcher"},
        "memory": {"model": "Ramulator2", "channels": 2, "size": "16GB", "configuration_sha256": artifacts.file_hash(ramulator)},
        "cpu_clock": "3.2GHz", "ramulator_config_sha256": artifacts.file_hash(ramulator),
        "command_arguments": settings}


def _correctness(session, request, result_folder, log, completed):
    """Retain sealed ROI and explicit post-ROI verdict, even after interruption."""
    data = session.data
    seal_path = result_folder / "roi-seal.json"
    if not seal_path.is_file():
        data["correctness"]["checks"].append({"state": "unverified", "reason": "No sealed ROI receipt was produced."})
        session.save()
        return
    seal = json.loads(seal_path.read_text())
    if (seal.get("format") != "swdb.dx100.roi-seal.v1"
            or seal.get("execution_binding_sha256") != data["context"]["execution_binding_sha256"]
            or seal.get("driver_sha256") != data["context"]["verification_driver"]["sha256"]
            or seal.get("roi_exit_cause") != "m5_exit instruction encountered"):
        raise StageFailure("incompatible", "sealed ROI does not identify this execution and verification driver")
    stats = _file(seal.get("statistics"), "sealed ROI statistics")
    if stats != result_folder / "roi-stats.txt":
        raise StageFailure("incompatible", "sealed statistics must belong to this execution directory")
    data["context"]["sealed_roi"] = {"path": str(seal_path), "sha256": artifacts.file_hash(seal_path), **seal}
    data["context"]["statistics"] = seal["statistics"]
    _file(request["binary"], "timed BFS binary")
    _file(request["simulator"], "simulator")
    _file(request["workload"]["representation"], "graph representation")
    _file(data["context"]["verification_driver"], "verification driver")
    counters, interval_values = {}, {}
    intervals = ends = 0
    with stats.open(errors="replace") as stream:
        for line in stream:
            if "Begin Simulation Statistics" in line:
                intervals += 1
            if "End Simulation Statistics" in line:
                ends += 1
            match = re.match(r"(\S*maa\S*\.numInst(?:_[A-Z]+)?)\s+(\d+)(?:\s|$)", line)
            if match:
                counters[match[1]] = int(match[2])
            match = re.match(r"(simTicks|finalTick)\s+(\d+)(?:\s|$)", line)
            if match:
                interval_values[match[1]] = match[2]
    if intervals != 1 or ends != 1:
        raise StageFailure("missing_observation", "sealed ROI must contain exactly one guest statistics interval")
    verdicts, trace_ends, sealed_markers, parent_results = [], {}, 0, []
    with log.open(errors="replace") as stream:
        for number, line in enumerate(stream, 1):
            if line.strip() == "SWDB_DX100_ROI_SEALED":
                sealed_markers += 1
            found = re.match(r"^\s*Verification\s*:\s*(PASS|FAIL)\s*$", line)
            if found:
                verdicts.append({"verdict": found[1], "line": number, "after_seal": sealed_markers == 1})
            found = re.fullmatch(r"SWDB_BFS_RESULT source=(\d+) vertices=(\d+) parent_count=(\d+) parent_fnv1a64=([a-f0-9]{16})\s*", line)
            if found:
                parent_results.append({"source": int(found[1]), "vertices": int(found[2]), "parent_count": int(found[3]),
                    "parent_fnv1a64": found[4], "line": number, "after_seal": sealed_markers == 1,
                    "fingerprint_kind": "noncryptographic FNV-1a over little-endian signed32 parent values"})
    terminal = seal.get("verification", {})
    explicit_failure = any(item["verdict"] == "FAIL" for item in verdicts)
    valid = (completed and len(verdicts) == 1 and verdicts[0]["after_seal"] and sealed_markers == 1
             and terminal.get("state") == "finished" and terminal.get("exit_code") == 0
             and terminal.get("exit_cause") == "exiting with last active thread context")
    if data["context"].get("candidate_build"):
        valid = (valid and len(parent_results) == 1 and parent_results[0]["after_seal"]
            and parent_results[0]["source"] == data["context"]["source"]
            and parent_results[0]["vertices"] == parent_results[0]["parent_count"])
    state = "failed" if explicit_failure else "passed" if valid else "unverified"
    from swdb.dx100_coverage import observe
    coverage = observe(log, interval_values, request["configuration"]["tile_elements"])
    trace_ends = coverage["completed_trace_units"]
    acceleration = (request["configuration"]["mode"] == "MAA"
        and any(value > 0 for key, value in counters.items() if key.endswith(".numInst"))
        and all(trace_ends.get(unit, 0) > 0 for unit in ("S", "I", "R", "A")))
    data["correctness"] = {"state": state, "checks": [{"state": state,
        "checker": "dx100.bfs.verifier.v1", "execution": data["id"],
        "binding": data["context"]["execution_binding"],
        "target": data["context"]["target"], "configuration": data["context"]["configuration"],
        "timed_source": data["context"]["timed_source"],
        "verifier_source": data["context"]["verifier_source"],
        "sealed_roi": {"path": str(seal_path), "sha256": artifacts.file_hash(seal_path)},
        "output": {"path": str(log), "sha256": artifacts.file_hash(log)},
        "requested_checks": 1, "observed_verdicts": verdicts, "continuation": terminal,
        "parent_results": parent_results,
        "coverage": {**coverage, "accelerator_executed": acceleration, "instruction_counters": counters},
        "scope": "This execution only; finite graph/source checking is not a proof for all inputs."}]}
    trial = data['context'].get('protocol_trial', {'source_position': 0, 'repetition': 0})
    data['correctness']['checks'][0].update(passed=state == 'passed', source=data['context']['source'], **trial,
        binary_sha256=data['build']['binary_sha256'],
        graph_sha256=data['context'].get('workload', {}).get('canonical_sha256'), output_sha256=artifacts.file_hash(log))
    session.save()
    if explicit_failure:
        raise StageFailure("incorrect", "BFS structural verifier printed FAIL, independently of process exit status")
    if not valid and completed:
        raise StageFailure("missing_observation", "missing, ambiguous, interrupted, or incomplete post-ROI verifier outcome")


def execute(args):
    store, request, data = _request(args, "execute")
    session = None
    error = None
    try:
        session, target, root = _prepare(args, "execute", store, request, data)
        budget = request["budget"]
        checkpoint_seconds = _integer(budget["checkpoint_seconds"], "checkpoint_seconds", maximum=7200)
        run_seconds = _integer(budget["run_seconds"], "run_seconds", maximum=14400)
        session.begin("execution_identity")
        simulator = _file(request.get("simulator"), "simulator")
        binary = _file(request.get("binary"), "BFS binary")
        compiled = None
        if "candidate_build" in request:
            compiled = store.get(request["candidate_build"], "evaluation")
            if (not compiled or compiled.get("outcome", {}).get("state") != "complete"
                    or compiled["outcome"]["stage"] != "candidate_build"
                    or compiled.get("candidate") != request.get("candidate")
                    or compiled["context"].get("model_build") != request.get("build_evaluation")
                    or compiled["evidence_kind"] != data["evidence_kind"]
                    or compiled["context"]["target"] != target["id"]):
                raise Failure("candidate_build does not identify this source/model/evidence kind")
            if request["binary"] != {"path": compiled["build"]["binary"], "sha256": compiled["build"]["binary_sha256"]}:
                raise Failure("candidate binary differs from its compilation receipt")
            for name in ("driver", "m5ops"):
                _file(compiled["build"][name], f"candidate build {name}")
            for reference in compiled.get('context', {}).get('diagnostic', {}).values():
                if isinstance(reference, dict) and set(reference) == {'path', 'sha256'}:
                    _file(reference, 'candidate diagnostic build input')
        if not request.get("fixture"):
            build_id = request.get("build_evaluation")
            if not isinstance(build_id, str):
                raise Failure("real execution requires an identified build_evaluation")
            prior = store.get(build_id, "evaluation")
            if (not prior or prior.get("outcome", {}).get("state") != "complete"
                    or prior["outcome"]["stage"] != "build" or prior["evidence_kind"] != "execution"):
                raise Failure("build_evaluation does not identify a completed real model/BFS build")
            receipt_path = _file({"path": prior["build"]["receipt"], "sha256": prior["build"]["receipt_sha256"]}, "build receipt")
            receipt = json.loads(receipt_path.read_text())
            if receipt.get("revision") != REVISION or receipt.get("state") != "completed":
                raise Failure("build receipt does not match the pinned completed build")
            available = {(ref["path"], ref["sha256"]) for ref in receipt["binaries"]}
            if any((request[key]["path"], request[key]["sha256"]) not in available for key in (("simulator",) if compiled else ("simulator", "binary"))):
                raise Failure("simulator or BFS binary was not produced by the selected build receipt")
        if not os.access(simulator, os.X_OK) or not os.access(binary, os.X_OK):
            raise Failure("simulator and BFS binary must be executable")
        workload = request.get("workload")
        if not isinstance(workload, dict) or set(workload) != {"id", "representation", "source"}:
            raise Failure("smoke workload requires id,representation,source")
        if not isinstance(workload["id"], str) or not workload["id"]:
            raise Failure("workload id must be nonempty")
        source = _integer(workload["source"], "BFS source", minimum=0)
        graph = _file(workload["representation"], "graph representation")
        application = compiled["context"]["application"] if compiled else "dx100-gapbs"
        if store.get(workload["id"], "workload"):
            registered = bfs_protocol.workload_representation(store, workload["id"], application)
            representation = registered["representation"]
            if (representation["path"] != str(graph) or representation["sha256"] != workload["representation"]["sha256"]
                    or source not in registered["sources"]):
                raise Failure("execution graph/source differs from its registered workload")
            data["context"]["workload"] = registered
        source_file = root / "benchmarks/gapbs/src/bfs.cc"
        if source_file.is_file():
            data["context"]["timed_source"] = {"path": str(source_file),
                "sha256": artifacts.file_hash(source_file), "model_revision": REVISION}
        if "candidate" in request:
            candidate = store.get(request["candidate"], "candidate")
            if not candidate:
                raise Failure("unknown candidate source identity")
            artifacts.verify(candidate["artifact"])
            implementation = store.get(candidate['implementation'], 'implementation')
            if compiled:
                if candidate["artifact"]["sha256"] != compiled["context"]["candidate_sha256"]:
                    raise Failure("candidate source differs from its compilation receipt")
                data["context"].update(roi=compiled["context"]["roi"], timed_source=compiled["context"]["timed_source"],
                    verifier_source=compiled["context"]["verifier_source"], candidate_build=compiled["id"],
                    candidate_driver=compiled["context"]["driver"],
                    suppressed_internal_events=compiled["context"]["suppressed_internal_events"])
            else:
                expected_function = 'DOBFS' if binary.name == 'bfs' else 'DOBFSMAA'
                if not request.get('fixture') and implementation.get('function') != expected_function:
                    raise Failure('author executable selection differs from the candidate implementation function')
                code_files = [entry for entry in candidate["artifact"]["files"]
                              if Path(entry["path"]).suffix in {".cc", ".cpp", ".c", ".h", ".hpp", ".S"}]
                if not code_files:
                    raise Failure("candidate has no code to bind to the pinned build")
                for entry in code_files:
                    _file({"path": str(root / artifacts.relative_path(entry["path"])), "sha256": entry["sha256"]},
                          "candidate source in the pinned model build")
            data.update(candidate=candidate["id"], source_snapshot=candidate["source_snapshot"], implementation=candidate["implementation"])
            data["context"]["candidate_sha256"] = candidate["artifact"]["sha256"]
        if any(character.isspace() for character in str(graph)):
            raise Failure("this pinned gem5 option parser cannot safely pass whitespace in graph paths")
        settings, configured = _configuration(request, target, root)
        if compiled:
            flags = compiled['build']['flags']
            # Scalar author diagnostics do not use the API or its tile macros.
            if compiled['context'].get('accelerated_requested') and (
                    f"-DTILE_SIZE={request['configuration']['tile_elements']}" not in flags
                    or '-DNUM_CORES=4' not in flags):
                raise Failure('compiled accelerator tile/core flags differ from the requested model configuration')
        else:
            built_tile = {'bfs_maa': 16384, 'bfs_maa_1K': 1024}.get(binary.name)
            if built_tile and built_tile != request['configuration']['tile_elements']:
                raise Failure('author executable tile size differs from the requested model configuration')
        script = root / "configs/deprecated/example/se.py"
        if not script.is_file():
            raise Failure("pinned simulator entry script is missing")
        options = f"-f {graph} -l -n 1 -v -r {source}"
        binding = {"model_revision": REVISION, "simulator": request["simulator"], "binary": request["binary"],
            "workload": workload, "guest_cores": 4, "guest_memory": "16GB", "options": options,
            "entry_script_sha256": artifacts.file_hash(script), "roi": data["context"]["roi"],
            "candidate_build": compiled["id"] if compiled else None}
        data["context"].update(configuration=configured, backend_configuration=configured, execution_binding=binding,
                              execution_binding_sha256=artifacts.digest(binding), source=source, sources=[source], threads=4)
        data["build"] = {"binary": str(binary), "binary_sha256": request["binary"]["sha256"],
                         "simulator": str(simulator), "simulator_sha256": request["simulator"]["sha256"]}
        if compiled:
            data['build'].update({key: compiled['build'][key] for key in ('compiler', 'compiler_version', 'flags', 'adapter')})
        elif not request.get('fixture'):
            guest_flags = ['-std=c++11', '-O3', '-Wall', '-g3', '-fopenmp', '-DGEM5']
            if binary.name != 'bfs':
                guest_flags += ['-DMAA', '-DNUM_CORES=4', '-DTILE_SIZE=' + ('1024' if binary.name == 'bfs_maa_1K' else '16384')]
            data['build'].update(compiler='g++-13', compiler_version=receipt['environment']['compiler'].splitlines()[:2],
                flags=guest_flags, adapter='dx100.author_artifact.v1')
        env = dict(os.environ, OMP_NUM_THREADS="4", OMP_PROC_BIND="false", OMP_DYNAMIC="FALSE")
        verify = request.get("verification")
        driver = paths.HOME / "scripts/dx100_verify.py"
        if verify is not None:
            if (not isinstance(verify, dict) or set(verify) - {"checker", "max_ticks", "coverage"}
                    or verify.get("checker") != "dx100.bfs.verifier.v1" or "max_ticks" not in verify):
                raise Failure("verification requires checker dx100.bfs.verifier.v1 and max_ticks")
            if type(verify.get("coverage", False)) is not bool:
                raise Failure("verification.coverage must be boolean")
            _integer(verify["max_ticks"], "verification.max_ticks", maximum=10**15)
            if not compiled:
                source_file = root / "benchmarks/gapbs/src/bfs.cc"
                harness = root / "benchmarks/gapbs/src/benchmark.h"
                if not source_file.is_file() or not harness.is_file():
                    raise Failure("timed BFS/verifier source identity is missing")
                data["context"].update(
                    timed_source={"path": str(source_file), "sha256": artifacts.file_hash(source_file), "model_revision": REVISION},
                    verifier_source={"path": str(source_file), "sha256": artifacts.file_hash(source_file),
                        "symbol": "BFSVerifier", "lines": [463, 508],
                        "harness": {"path": str(harness), "sha256": artifacts.file_hash(harness)}})
            data["context"]["verification_driver"] = {"path": str(driver), "sha256": artifacts.file_hash(driver)}
            env.update(SWDB_DX100_MODEL_ROOT=str(root),
                SWDB_DX100_EXECUTION_BINDING_SHA256=data["context"]["execution_binding_sha256"],
                SWDB_DX100_VERIFY_MAX_TICKS=str(verify["max_ticks"]))
        instrumentation = {'treatment': 'source_scope_diagnostic' if compiled and compiled['context'].get('diagnostic') else 'primary',
            'roi': data['context']['roi'], 'suppressed_internal_events': compiled['context']['suppressed_internal_events'] if compiled else [],
            'verification': 'same_guest_post_roi' if verify else 'none',
            'debug_flags': 'MAATrace,MAARangeFuser,MAAIndirect' if verify and verify.get('coverage') else 'MAATrace'}
        data['context'].update(instrumentation=instrumentation, verifier='dx100.bfs.verifier.v1' if verify else None, repetitions=1)
        if request.get('protocol'):
            if not request.get('candidate') or not verify:
                raise Failure('frozen simulation requires candidate identity and exact timed-binary verification')
            bound = bfs_protocol.validate_protocol_for_simulation(store, request, candidate,
                actual_target=target['id'], actual_configuration=configured, actual_build=data['build'],
                actual_instrumentation=instrumentation, actual_threads=4, actual_roi=data['context']['roi'],
                actual_verifier=data['context']['verifier'])
            data['context'].update(bound['context'])
        if not request.get("fixture"):
            env.update(TMPDIR=str(root / ".tmp"), XDG_CACHE_HOME=str(root / ".cache"))
            Path(env["TMPDIR"]).mkdir(exist_ok=True)
            Path(env["XDG_CACHE_HOME"]).mkdir(exist_ok=True)
        session.finish()
        reference = request.get("checkpoint_manifest")
        if reference is not None:
            session.begin("checkpoint_resolution")
            manifest_path = _file(reference, "checkpoint manifest")
            manifest = json.loads(manifest_path.read_text())
            if (not isinstance(manifest, dict) or manifest.get("format") != "swdb.dx100.checkpoint.v1"
                    or manifest.get("binding") != binding):
                raise StageFailure("incompatible", "checkpoint binding differs from exact binary/workload/source/model/options")
            checkpoint = artifacts.verify(manifest["artifact"])
            session.finish()
        else:
            checkpoint = session.folder / "checkpoint"
            checkpoint.mkdir()
            command = [str(simulator), f"--outdir={checkpoint}", str(script), "--cpu-type", "AtomicSimpleCPU",
                       "-n", "4", "--mem-size", "16GB", "--max-checkpoints", "1", "--cmd", str(binary), "--options", options]
            _bounded_process(session, "checkpoint", command, checkpoint_seconds, budget["memory_gib"], budget["storage_gib"], env)
            directories = []
            for path in checkpoint.glob('cpt.*'):
                # Pinned m5.checkpoint creates the literal formatting directory
                # before the C++ serializer expands %d to the actual tick.
                if path.name == 'cpt.%d' and path.is_dir() and not path.is_symlink() and not any(path.iterdir()):
                    continue
                if path.is_symlink() or not path.is_dir() or not re.fullmatch(r'cpt\.[0-9]+', path.name):
                    raise StageFailure('missing_observation', 'checkpoint execution produced an unexpected checkpoint entry')
                directories.append(path)
            if len(directories) != 1:
                raise StageFailure("missing_observation", "checkpoint execution did not produce exactly one checkpoint directory")
            manifest = {"format": "swdb.dx100.checkpoint.v1", "binding": binding,
                        "artifact": artifacts.identify(checkpoint), "evidence_kind": data["evidence_kind"]}
            manifest_path = session.folder / "checkpoint-manifest.json"
            manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        if manifest.get("evidence_kind") != data["evidence_kind"]:
            raise StageFailure("incompatible", "fixture and real checkpoint evidence cannot be mixed")
        data["context"]["checkpoint_manifest"] = {"path": str(manifest_path), "sha256": artifacts.file_hash(manifest_path)}
        session.save()
        # Every input is rechecked after checkpointing; unexpected changes cannot
        # silently substitute a new graph or timed binary before restore.
        _file(request["simulator"], "simulator")
        _file(request["binary"], "BFS binary")
        _file(workload["representation"], "graph representation")
        result_folder = session.folder / "simulation"
        result_folder.mkdir()
        debug_flags = "MAATrace,MAARangeFuser,MAAIndirect" if verify and verify.get("coverage") else "MAATrace"
        data["context"]["debug_flags"] = debug_flags
        command = [str(simulator), f"--debug-flags={debug_flags}", f"--outdir={result_folder}", str(driver if verify else script), *settings,
                   "--cmd", str(binary), "--options", options, "--checkpoint-dir", str(checkpoint), "-r", "1"]
        completed = False
        log = session.folder / f"{len(data['stages']):03d}-simulation.log"
        try:
            _bounded_process(session, "simulation", command, run_seconds, budget["memory_gib"], budget["storage_gib"], env)
            completed = True
        finally:
            if verify is not None:
                _correctness(session, request, result_folder, log, completed)
        session.begin("execution_observations")
        stats = result_folder / ("roi-stats.txt" if verify else "stats.txt")
        causes = []
        with log.open(errors="replace") as stream:
            for line in stream:
                found = re.search(r"Exiting @ tick (\d+) because ([^\r\n]+)", line)
                if found:
                    causes = [found.groups()]
        if not causes or causes[-1][1].strip() != "m5_exit instruction encountered":
            raise StageFailure("missing_observation", "simulator did not report the expected BFS ROI exit")
        if not stats.is_file():
            raise StageFailure("missing_observation", "simulation produced no readable statistics interval")
        with stats.open(errors="replace") as stream:
            if not any("Begin Simulation Statistics" in line for line in stream):
                raise StageFailure("missing_observation", "simulation produced no readable statistics interval")
        actual_config = result_folder / "config.ini"
        if not actual_config.is_file():
            raise StageFailure("missing_observation", "simulation produced no actual configuration file")
        data["context"].update(exit_tick=int(causes[-1][0]), exit_cause=causes[-1][1].strip(),
            actual_configuration={"path": str(actual_config), "sha256": artifacts.file_hash(actual_config)},
            statistics={"path": str(stats), "sha256": artifacts.file_hash(stats)})
        if verify:
            from swdb.dx100_profile import statistics, duration
            intervals = statistics(stats, time.monotonic() + 60)
            if len(intervals) != 1:
                raise StageFailure('missing_observation', 'sealed primary timing requires exactly one interval')
            elapsed = duration(intervals[0])
            trial = data['context'].get('protocol_trial', {'source_position': 0, 'repetition': 0})
            data['timing'] = [{'source': source, **trial, 'duration_s': elapsed['duration_s'], 'roi': data['context']['roi'],
                'basis': 'simulated', 'quantity': 'simulated_roi_seconds', 'binary_sha256': data['build']['binary_sha256'],
                'output': str(log), 'output_sha256': artifacts.file_hash(log), 'statistics_sha256': artifacts.file_hash(stats),
                'verified': data['correctness']['state'] == 'passed', 'evidence_kind': data['evidence_kind']}]
            data['context']['roi_ticks'] = elapsed
        data["raw_artifacts"].append({"kind": "simulation", "artifact": artifacts.identify(result_folder)})
        session.finish()
        data["outcome"] = {"state": "complete", "stage": "execution", "reason": (
            "The exact timed guest passed its post-ROI structural verifier; complete profiling remains required."
            if data["correctness"]["state"] == "passed" else
            "Unverified smoke execution: explicit timed-binary correctness and complete profiling remain required.")}
    except (Failure, StageFailure, Stopped, OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        error = exc
    return _finish(args, data, session, error)
