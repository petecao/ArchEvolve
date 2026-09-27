"""Bounded DX100 build, checkpoint, and unverified execution workflows.

Updated: 2026-09-26. Build/smoke evidence never certifies a timed binary.
"""

import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import uuid

from swdb import artifacts, bfs_protocol, paths, profile, workflow
from swdb.bfs_native import Session, StageFailure, Stopped, _integer, _now
from swdb.cli import Failure, _require_valid
from swdb.processes import stop_group

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


def _verification_runtime(session):
    """Preserve the exact trusted v2 helpers beyond a later checkout update."""
    folder = session.folder / 'verification-runtime'
    folder.mkdir(exist_ok=False)
    rows = []
    for relative in ('scripts/dx100_verify.py', 'scripts/dx100_host_memory.py',
                     'swdb/dx100_witness.py'):
        source = paths.HOME / relative
        original = {'path': str(source), 'sha256': artifacts.file_hash(source)}
        _file(original, 'trusted verification helper')
        if source.stat().st_size > 1024 * 1024:
            raise Failure('trusted verification helper exceeds 1 MiB')
        contents = source.read_bytes()
        if len(contents) > 1024 * 1024:
            raise Failure('trusted verification helper exceeds 1 MiB')
        destination = folder / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        snapshot = {'path': str(destination), 'sha256': artifacts.file_hash(destination)}
        if snapshot['sha256'] != original['sha256']:
            raise Failure('trusted verification helper changed during snapshot')
        _file(original, 'trusted verification helper')
        rows.append({'source': {'code_root': str(paths.HOME),
                                'repository_relative_path': relative,
                                'copied_sha256': original['sha256']},
                     'snapshot': snapshot})
    for directory in (folder / 'scripts', folder / 'swdb', folder, session.folder):
        descriptor = os.open(str(directory), os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    session.data['context']['verification_runtime'] = {
        'format': 'swdb.dx100.verification-runtime.v1', 'files': rows,
        'source_paths_are_provenance_only': True}
    return folder


def _request(args, action):
    store = _require_valid(args.records)
    text = Path(args.file).read_text()
    if len(text.encode()) > 10 * 1024 * 1024:
        raise Failure("DX100 request exceeds 10 MiB")
    request = workflow.message_from_text(text)
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
    workflow.persist(args.records, data, getattr(args, "db", None), create=True)
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
        fields |= {"simulator", "binary", "workload", "configuration", "checkpoint_manifest", "checkpoint_evaluation", "build_evaluation", "verification", "candidate", "candidate_build", "protocol", "protocol_role", "protocol_trial"}
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
    observation_seconds = 0
    if not request.get('fixture'):
        from swdb.host_observation import attach
        observed = attach(data, folder, paths.HOME, total_seconds=min(15, total))
        observation_seconds = observed['host_wall_s']
    session = Session(args, data, folder, max(0, total - observation_seconds) + (30 if action == "build" and not request.get("fixture") else 0))
    session.install_handlers()
    return session, target, model_root


def _terminate(child):
    stop_group(child, grace_seconds=15)


def _release_gem5_slot():
    """R3 (2026-09-27): close an inherited lane gem5-slot lock after the last gem5.

    A series may pass one flock descriptor so that at most N simulators run in a
    lane while postprocessing overlaps. Without the variable nothing changes.
    """
    value = os.environ.pop("SWDB_GEM5_SLOT_FD", None)
    if value is not None:
        try:
            os.close(int(value))
        except (OSError, ValueError):
            pass


def _bounded_process(session, name, command, timeout, memory, storage, env=None):
    """Monitor real children and preserve completed evidence on interrupted work."""
    allowed = min(timeout, session.remaining())
    log = session.folder / f"{len(session.data['stages']):03d}-{name}.log"
    session.begin(name, command=list(map(str, command)), timeout_s=allowed, log=str(log))
    start = time.monotonic()
    reason = None
    code = None
    last_storage = 0
    last_observation = -5.0
    peak_rss_kib = None
    memory_log = log.with_suffix('.memory.jsonl')
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
                    from swdb.dx100_resources import process_group, observe
                    processes = process_group(session.child.pid)
                    used = sum(row['rss_kib'] for row in processes)
                    peak_rss_kib = max(peak_rss_kib or 0, used)
                    elapsed = time.monotonic() - start
                    if elapsed - last_observation >= 5 or used > memory * 1024 * 1024:
                        observe(memory_log, session.child.pid, processes, start, log,
                                session.folder, session.data['evidence_kind'])
                        last_observation = elapsed
                    if used > memory * 1024 * 1024:
                        raise StageFailure("budget_exhausted", f"simulator process-group memory budget exhausted: {used} KiB > {memory} GiB")
                if time.monotonic() - last_storage >= 30:
                    directories = [session.folder]
                    build_dir = session.data.get('context', {}).get('build_directory')
                    if build_dir and not Path(build_dir).is_relative_to(session.folder):
                        directories.append(Path(build_dir))
                    loader = session.data.get('context', {}).get('loader_input')
                    if loader and loader['provenance']['storage_charge_bytes']:
                        directories.append(Path(loader['alias']['path']))
                    used = sum(int(subprocess.check_output(["du", "-sk", str(path)], text=True, timeout=30).split()[0])
                               for path in directories)
                    if used > storage * 1024 * 1024:
                        raise StageFailure("budget_exhausted", "raw artifact storage budget exhausted")
                    last_storage = time.monotonic()
                time.sleep(0.2 if session.data["evidence_kind"] == "contract_fixture" else
                           min(2, max(0.05, 5 - (time.monotonic() - start - last_observation))))
            code = session.child.returncode
    except (StageFailure, Stopped, OSError, subprocess.SubprocessError) as exc:
        reason = exc
    finally:
        _terminate(session.child)
        session.child = None
        for path, kind in ((memory_log, 'process_group_memory'),
                (session.folder / 'simulation/host-memory-phases.jsonl', 'simulator_host_memory_phases')):
            if path.is_file():
                session.data['raw_artifacts'].append({'host': session.data['context']['host'],
                    'kind': kind, 'path': str(path), 'sha256': artifacts.file_hash(path)})
    state = "complete" if code == 0 and reason is None else reason.state if isinstance(reason, StageFailure) else "interrupted" if isinstance(reason, Stopped) else "failed"
    session.finish(state, host_wall_s=time.monotonic() - start, returncode=code,
                   log_sha256=artifacts.file_hash(log), reason=str(reason) if reason else None,
                   sampled_peak_process_group_rss_kib=peak_rss_kib)
    if reason:
        raise reason
    if code != 0:
        raise StageFailure("failed", f"{name} exited with status {code}; see {log}")
    return log


def _failure_outcome(data, session, error):
    if isinstance(error, Failure) and "persisted, but query indexing failed" in str(error):
        raise error
    state = error.state if isinstance(error, StageFailure) else "interrupted" if isinstance(error, Stopped) else "failed"
    stage = session.current["stage"] if session and session.current else "validation"
    data["outcome"] = {"state": state, "stage": stage, "reason": str(error)}
    if session and session.current and session.current["state"] == "running":
        session.current.update(state=state, finished=_now(), reason=str(error))


def _finish(args, data, session, error=None):
    if error is not None:
        _failure_outcome(data, session, error)
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
    checker = request['verification']['checker']
    witnessed = checker == 'dx100.bfs.verifier.v2'
    seal_path = result_folder / "roi-seal.json"
    if not seal_path.is_file():
        data["correctness"]["checks"].append({"state": "unverified", "reason": "No sealed ROI receipt was produced."})
        session.save()
        return
    seal = json.loads(seal_path.read_text())
    if (seal.get("format") != "swdb.dx100.roi-seal.v1"
            or seal.get("execution_binding_sha256") != data["context"]["execution_binding_sha256"]
            or seal.get("driver_sha256") != data["context"]["verification_driver"]["sha256"]
            or seal.get('host_memory_observer_sha256') != data['context']['host_memory_observer']['sha256']
            or seal.get("roi_exit_cause") != "m5_exit instruction encountered"):
        raise StageFailure("incompatible", "sealed ROI does not identify this execution and verification driver")
    stats = _file(seal.get("statistics"), "sealed ROI statistics")
    if stats != result_folder / "roi-stats.txt":
        raise StageFailure("incompatible", "sealed statistics must belong to this execution directory")
    data["context"]["sealed_roi"] = {"path": str(seal_path), "sha256": artifacts.file_hash(seal_path), **seal}
    data["context"]["statistics"] = seal["statistics"]
    if witnessed:
        parser = data['context']['verification_parser']
        if seal.get('verification_parser') != parser:
            raise StageFailure('incompatible', 'sealed ROI does not identify the selected v2 parser')
        _file(parser, 'verification parser')
        trace = seal.get('verification', {}).get('post_roi_trace', {})
        if trace and trace.get('path') != str(result_folder / 'post-roi-syscalls.log'):
            raise StageFailure('incompatible', 'v2 trace must belong to this exact execution')
        if trace.get('sha256'):
            _file({key: trace[key] for key in ('path', 'sha256')}, 'post-ROI simulator trace')
        if trace:
            data['context']['post_roi_trace'] = trace
    actual_config = result_folder / "config.ini"
    if actual_config.is_file():
        # Collection can use a sealed interval even when verification later
        # fails. Bind the instantiated configuration before that verdict.
        data["context"]["actual_configuration"] = {
            "path": str(actual_config), "sha256": artifacts.file_hash(actual_config)}
    _file(request["binary"], "timed BFS binary")
    _file(request["simulator"], "simulator")
    _file(request["workload"]["representation"], "graph representation")
    if data['context'].get('loader_input'):
        _file(data['context']['loader_input']['alias'], 'serialized loader alias')
    _file(data["context"]["verification_driver"], "verification driver")
    _file({key: data['context']['host_memory_observer'][key] for key in ('path', 'sha256')},
          'host memory observer')
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
    verdicts, trace_ends, sealed_markers, parent_results, completion_times = [], {}, 0, [], []
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
            found = re.fullmatch(r'\s*(Verification Time|Average Time):\s*([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?\d+)?)\s*', line)
            if found:
                value = float(found[2])
                completion_times.append({'kind': found[1], 'seconds': value, 'line': number,
                    'after_seal': sealed_markers == 1, 'finite': math.isfinite(value)})
    terminal = seal.get("verification", {})
    explicit_failure = any(item["verdict"] == "FAIL" for item in verdicts)
    ended = terminal.get('exit_cause') == 'exiting with last active thread context'
    if witnessed:
        ended = (terminal.get('checker') == checker and terminal.get('stop_reason') in {'exit_witness', 'normal_exit'})
    valid = (completed and len(verdicts) == 1 and verdicts[0]["after_seal"] and sealed_markers == 1
             and terminal.get("state") == "finished" and terminal.get("exit_code") == 0 and ended)
    if data["context"].get("candidate_build"):
        valid = (valid and len(parent_results) == 1 and parent_results[0]["after_seal"]
            and parent_results[0]["source"] == data["context"]["source"]
            and parent_results[0]["vertices"] == parent_results[0]["parent_count"])
        if witnessed:
            valid = valid and parent_results[0]['line'] < verdicts[0]['line']
    elif witnessed:
        valid = (valid and len(completion_times) == 2
            and [row['kind'] for row in completion_times] == ['Verification Time', 'Average Time']
            and all(row['after_seal'] and row['finite'] for row in completion_times)
            and verdicts[0]['line'] < completion_times[0]['line'] < completion_times[1]['line'])
    state = "failed" if explicit_failure else "passed" if valid else "unverified"
    from swdb.dx100_coverage import observe
    from swdb.dx100_coverage import TRACE_NAME, TRANSPORT
    trace = result_folder / TRACE_NAME if request['verification'].get('trace_transport') == TRANSPORT else None
    coverage = observe(log, interval_values, request["configuration"]["tile_elements"],
                       trace=trace, deadline=session.deadline)
    if trace is not None:
        data['context']['debug_trace'] = coverage['debug_trace']
    trace_ends = coverage["completed_trace_units"]
    acceleration = (request["configuration"]["mode"] == "MAA"
        and any(value > 0 for key, value in counters.items() if key.endswith(".numInst"))
        and all(trace_ends.get(unit, 0) > 0 for unit in ("S", "I", "R", "A")))
    data["correctness"] = {"state": state, "checks": [{"state": state,
        "checker": checker, "execution": data["id"],
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
    if witnessed:
        check = data['correctness']['checks'][0]
        check['completion_sequence'] = {'kind': 'protected_candidate' if data['context'].get('candidate_build') else 'pinned_author',
            'times': completion_times, 'observed': bool(valid)}
    trial = data['context'].get('protocol_trial', {'source_position': 0, 'repetition': 0})
    data['correctness']['checks'][0].update(passed=state == 'passed', source=data['context']['source'], **trial,
        binary_sha256=data['build']['binary_sha256'],
        graph_sha256=data['context'].get('workload', {}).get('canonical_sha256'), output_sha256=artifacts.file_hash(log))
    if witnessed and valid and not explicit_failure:
        from swdb.dx100_witness import validate_completed_witness
        try:
            validate_completed_witness(data, require_complete_evaluation=False)
        except (Failure, ValueError, TypeError, KeyError, OSError) as exc:
            valid = False
            data['correctness']['state'] = 'unverified'
            data['correctness']['checks'][0].update(state='unverified', passed=False, reason=str(exc))
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
        data['context']['application'] = application
        registered = None
        if store.get(workload["id"], "workload"):
            registered = bfs_protocol.workload_representation(store, workload["id"], application)
            representation = registered["representation"]
            if (representation["path"] != str(graph) or representation["sha256"] != workload["representation"]["sha256"]
                    or source not in registered["sources"]):
                raise Failure("execution graph/source differs from its registered workload")
            data["context"]["workload"] = registered
        if compiled and compiled['context'].get('roi') == 'bfs.complete_call.v1':
            from swdb.dx100_witness import graph_verification_contract
            contract = graph_verification_contract(application)
            verifier_source = compiled['context'].get('verifier_source', {})
            driver_reference = compiled['context'].get('driver', {})
            if (compiled['build'].get('adapter') != 'dx100.complete_call.v2'
                    or compiled['context'].get('graph_verification') != contract
                    or not driver_reference.get('sha256')
                    or any(verifier_source.get(key) != driver_reference.get(key) for key in ('path', 'sha256'))):
                raise Failure('complete-call candidate requires the original-adjacency checker contract; rebuild legacy wrappers')
            if not request.get('fixture') and registered is None:
                raise Failure('original-adjacency candidate checking requires a registered workload')
            data['context']['graph_verification'] = dict(contract)
            data['context']['protected_bfs_verifier'] = compiled['context']['protected_bfs_verifier']
        if 'protocol_trial' in request:
            trial = request['protocol_trial']
            if not isinstance(trial, dict) or set(trial) != {'source_position', 'repetition'}:
                raise Failure('protocol_trial requires source_position and repetition only')
            position = _integer(trial['source_position'], 'protocol_trial.source_position', minimum=0)
            repetition = _integer(trial['repetition'], 'protocol_trial.repetition', minimum=0)
            if registered is None:
                raise Failure('protocol_trial requires a registered ordered workload source list')
            if position >= len(registered['sources']) or registered['sources'][position] != source:
                raise Failure('protocol_trial source_position differs from the registered workload source')
            data['context']['protocol_trial'] = {'source_position': position, 'repetition': repetition}
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
            if candidate.get("proposal"):
                data["proposal"] = candidate["proposal"]
            data["context"]["candidate_sha256"] = candidate["artifact"]["sha256"]
        from swdb.dx100_inputs import resolve as resolve_loader_input
        loader_graph, loader_input = resolve_loader_input(session, args.runs_dir, workload['representation'], application, registered)
        if loader_input:
            data['context']['loader_input'] = loader_input
        if any(character.isspace() for character in str(loader_graph)):
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
        options = f"-f {loader_graph} -l -n 1 -v -r {source}"
        binding = {"model_revision": REVISION, "simulator": request["simulator"], "binary": request["binary"],
            "workload": workload, "guest_cores": 4, "guest_memory": "16GB", "options": options,
            "entry_script_sha256": artifacts.file_hash(script), "roi": data["context"]["roi"],
            "candidate_build": compiled["id"] if compiled else None,
            "modeled_configuration": configured, "hardware_target": target['id']}
        if loader_input:
            binding['loader_representation'] = loader_input['alias']
        data["context"].update(configuration=configured, backend_configuration=configured, execution_binding=binding,
                              execution_binding_sha256=artifacts.digest(binding), source=source, sources=[source], threads=4)
        data["build"] = {"binary": str(binary), "binary_sha256": request["binary"]["sha256"],
                         "simulator": str(simulator), "simulator_sha256": request["simulator"]["sha256"]}
        if request.get("build_evaluation"):
            model_build = store.get(request["build_evaluation"], "evaluation")
            if model_build:
                data["build"]["model_build"] = {"evaluation": model_build["id"], "sha256": artifacts.digest(model_build)}
        if compiled:
            data['build'].update({key: compiled['build'][key] for key in ('compiler', 'compiler_version', 'flags', 'adapter')})
        elif not request.get('fixture'):
            guest_flags = ['-std=c++11', '-O3', '-Wall', '-g3', '-fopenmp', '-DGEM5']
            if binary.name != 'bfs':
                guest_flags += ['-DMAA', '-DNUM_CORES=4', '-DTILE_SIZE=' + ('1024' if binary.name == 'bfs_maa_1K' else '16384')]
            data['build'].update(compiler='g++-13', compiler_version=receipt['environment']['compiler'].splitlines()[:2],
                flags=guest_flags, adapter='dx100.author_artifact.v1')
        env = dict(os.environ, OMP_NUM_THREADS="4", OMP_PROC_BIND="false", OMP_DYNAMIC="FALSE")
        # A caller's environment cannot silently opt into diagnostic tracing.
        env.pop('SWDB_DX100_POST_ROI_TRACE', None)
        verify = request.get("verification")
        driver = paths.HOME / "scripts/dx100_verify.py"
        if verify is not None:
            if (not isinstance(verify, dict) or set(verify) - {"checker", "max_ticks", "coverage", "post_roi_trace", "trace_transport"}
                    or verify.get("checker") not in {"dx100.bfs.verifier.v1", "dx100.bfs.verifier.v2"} or "max_ticks" not in verify):
                raise Failure("verification requires checker dx100.bfs.verifier.v1 or v2 and max_ticks")
            if type(verify.get("coverage", False)) is not bool:
                raise Failure("verification.coverage must be boolean")
            if 'post_roi_trace' in verify and (type(verify['post_roi_trace']) is not str
                    or verify['post_roi_trace'] != 'SyscallBase'):
                raise Failure('verification.post_roi_trace must be SyscallBase when present')
            if verify['checker'] == 'dx100.bfs.verifier.v2' and verify.get('post_roi_trace') != 'SyscallBase':
                raise Failure('v2 verification requires explicit post_roi_trace: SyscallBase')
            if 'trace_transport' in verify and verify['trace_transport'] != 'gem5-gzip.v1':
                raise Failure('verification.trace_transport must be gem5-gzip.v1 when present')
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
            observer = paths.HOME / 'scripts/dx100_host_memory.py'
            if verify['checker'] == 'dx100.bfs.verifier.v2':
                runtime = _verification_runtime(session)
                driver = runtime / 'scripts/dx100_verify.py'
                observer = runtime / 'scripts/dx100_host_memory.py'
                parser = runtime / 'swdb/dx100_witness.py'
                data['context']['verification_parser'] = {'path': str(parser), 'sha256': artifacts.file_hash(parser)}
            data["context"]["verification_driver"] = {"path": str(driver), "sha256": artifacts.file_hash(driver)}
            data['context']['host_memory_observer'] = {'path': str(observer),
                'sha256': artifacts.file_hash(observer), 'sample_interval_seconds': 5,
                'scope': 'host process group and bounded phase observations; no modeled changes'}
            env.update(SWDB_DX100_MODEL_ROOT=str(root),
                SWDB_DX100_EXECUTION_BINDING_SHA256=data["context"]["execution_binding_sha256"],
                SWDB_DX100_CHECKER=verify['checker'],
                SWDB_DX100_VERIFY_MAX_TICKS=str(verify["max_ticks"]))
            if 'post_roi_trace' in verify:
                env['SWDB_DX100_POST_ROI_TRACE'] = verify['post_roi_trace']
        instrumentation = {'treatment': 'source_scope_diagnostic' if compiled and compiled['context'].get('diagnostic') else 'primary',
            'roi': data['context']['roi'], 'suppressed_internal_events': compiled['context']['suppressed_internal_events'] if compiled else [],
            'verification': 'same_guest_post_roi' if verify else 'none',
            'debug_flags': 'MAATrace,MAARangeFuser,MAAIndirect' if verify and verify.get('coverage') else 'MAATrace'}
        if 'graph_verification' in data['context']:
            instrumentation['graph_verification'] = dict(data['context']['graph_verification'])
        if verify and 'trace_transport' in verify:
            data['context']['trace_transport'] = verify['trace_transport']
        if verify and verify['checker'] == 'dx100.bfs.verifier.v2':
            instrumentation['verifier_runtime'] = {
                'driver_sha256': data['context']['verification_driver']['sha256'],
                'parser_sha256': data['context']['verification_parser']['sha256'],
                'observer_sha256': data['context']['host_memory_observer']['sha256']}
        if verify and 'post_roi_trace' in verify:
            instrumentation['post_roi_trace'] = {
                'flag': verify['post_roi_trace'], 'scope': 'post-seal verifier continuation only'}
            if verify['checker'] == 'dx100.bfs.verifier.v2':
                instrumentation['post_roi_trace'].update(output='separate_simulator_trace', format_flags=['FmtFlag'],
                    disabled_format_flags=['FmtTicksOff', 'FmtStackTrace'],
                    disabled_roi_flags=['MAATrace', 'MAARangeFuser', 'MAAIndirect'], chunk_ticks=10**9)
        data['context'].update(instrumentation=instrumentation, verifier=verify['checker'] if verify else None, repetitions=1)
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
        from swdb.dx100_checkpoint import FORMAT, compatibility
        if 'checkpoint_evaluation' in request and reference is None:
            raise Failure('checkpoint_evaluation requires the exact checkpoint_manifest reference')
        if reference is not None:
            session.begin("checkpoint_resolution")
            manifest_path = _file(reference, "checkpoint manifest")
            manifest = json.loads(manifest_path.read_text())
            proof = compatibility(manifest, reference, binding, request, store)
            if proof:
                data['context']['checkpoint_compatibility_proof'] = proof
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
            manifest = {"format": FORMAT, "binding": binding,
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
        if loader_input:
            _file(loader_input['alias'], 'serialized loader alias')
        result_folder = session.folder / "simulation"
        result_folder.mkdir()
        debug_flags = "MAATrace,MAARangeFuser,MAAIndirect" if verify and verify.get("coverage") else "MAATrace"
        data["context"]["debug_flags"] = debug_flags
        trace_options = []
        if verify and verify.get('trace_transport') == 'gem5-gzip.v1':
            from swdb.dx100_coverage import TRACE_NAME
            trace_options = [f'--debug-file={result_folder / TRACE_NAME}']
        command = [str(simulator), f"--debug-flags={debug_flags}", *trace_options, f"--outdir={result_folder}", str(driver if verify else script), *settings,
                   "--cmd", str(binary), "--options", options, "--checkpoint-dir", str(checkpoint), "-r", "1"]
        log = session.folder / f"{len(data['stages']):03d}-simulation.log"
        try:
            try:
                _bounded_process(session, "simulation", command, run_seconds, budget["memory_gib"], budget["storage_gib"], env)
            finally:
                _release_gem5_slot()
        except (Failure, StageFailure, Stopped, OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as simulation_error:
            # A supervisor may end its cleanup grace while postmortem scans a
            # large log. Save the operational failure before that optional work,
            # retaining signal handlers and the original error for finalization.
            _failure_outcome(data, session, simulation_error)
            if verify is not None:
                data['context']['postmortem'] = {'state': 'pending', 'reason': None}
            session.save()
            if verify is not None:
                try:
                    _correctness(session, request, result_folder, log, False)
                except Exception as postmortem_error:
                    if isinstance(postmortem_error, Failure) and "persisted, but query indexing failed" in str(postmortem_error):
                        raise
                    data['context']['postmortem'] = {'state': 'failed', 'reason': str(postmortem_error)}
                else:
                    data['context']['postmortem'] = {'state': 'complete', 'reason': None}
            raise
        else:
            if verify is not None:
                _correctness(session, request, result_folder, log, True)
        _file(workload['representation'], 'graph representation')
        if loader_input:
            _file(loader_input['alias'], 'serialized loader alias')
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
