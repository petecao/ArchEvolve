"""Bounded DX100 build, checkpoint, and unverified execution workflows.

Updated: 2026-09-25. Build/smoke evidence never certifies a timed binary.
"""

import json
import math
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

from swdb import artifacts, paths, profile, workflow, yamlio
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
    fields |= {"fixture_command"} if action == "build" else {"simulator", "binary", "workload", "configuration", "checkpoint_manifest"}
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
    total = _integer(budget.get("total_seconds"), "budget.total_seconds", maximum=7200)
    memory = _integer(budget.get("memory_gib"), "budget.memory_gib", maximum=48)
    storage = _integer(budget.get("storage_gib"), "budget.storage_gib", maximum=20)
    if action == "build":
        _integer(budget.get("jobs"), "budget.jobs", maximum=8)
        if storage > 10 or set(budget) != {"total_seconds", "memory_gib", "storage_gib", "jobs"}:
            raise Failure("build budget requires total_seconds,memory_gib,storage_gib<=10,jobs")
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
    session = Session(args, data, folder, total + (30 if action == "build" else 0))
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
                    if used > memory * 1024 * 1024:
                        raise StageFailure("budget_exhausted", "simulator process-group memory budget exhausted")
                if time.monotonic() - last_storage >= 30:
                    used = int(subprocess.check_output(["du", "-sk", str(session.folder)], text=True, timeout=30).split()[0])
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
                   log_sha256=artifacts.file_hash(log), reason=str(reason) if reason else None)
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
            _bounded_process(session, "model_build", command, budget["total_seconds"] + 20,
                             budget["memory_gib"], 2)
        finally:
            receipt = output / "build-receipt.json"
            if receipt.is_file():
                data["build"].update(receipt_sha256=artifacts.file_hash(receipt), details=json.loads(receipt.read_text()))
                session.save()
        if not request.get("fixture") and data["build"].get("details", {}).get("state") != "completed":
            raise StageFailure("missing_observation", "build helper did not retain a completed build receipt")
        data["outcome"] = {"state": "complete", "stage": "build", "reason": "Build evidence only; no BFS execution or correctness verdict."}
    except (Failure, StageFailure, Stopped, OSError, ValueError, subprocess.SubprocessError) as exc:
        error = exc
    return _finish(args, data, session, error)


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
        "cpu_clock": "3.2GHz", "ramulator_config_sha256": artifacts.file_hash(ramulator),
        "command_arguments": settings}


def execute(args):
    store, request, data = _request(args, "execute")
    session = None
    error = None
    try:
        session, target, root = _prepare(args, "execute", store, request, data)
        budget = request["budget"]
        checkpoint_seconds = _integer(budget["checkpoint_seconds"], "checkpoint_seconds", maximum=7200)
        run_seconds = _integer(budget["run_seconds"], "run_seconds", maximum=7200)
        session.begin("execution_identity")
        simulator = _file(request.get("simulator"), "simulator")
        binary = _file(request.get("binary"), "BFS binary")
        if not os.access(simulator, os.X_OK) or not os.access(binary, os.X_OK):
            raise Failure("simulator and BFS binary must be executable")
        workload = request.get("workload")
        if not isinstance(workload, dict) or set(workload) != {"id", "representation", "source"}:
            raise Failure("smoke workload requires id,representation,source")
        if not isinstance(workload["id"], str) or not workload["id"]:
            raise Failure("workload id must be nonempty")
        source = _integer(workload["source"], "BFS source", minimum=0)
        graph = _file(workload["representation"], "graph representation")
        if any(character.isspace() for character in str(graph)):
            raise Failure("this pinned gem5 option parser cannot safely pass whitespace in graph paths")
        settings, configured = _configuration(request, target, root)
        script = root / "configs/deprecated/example/se.py"
        if not script.is_file():
            raise Failure("pinned simulator entry script is missing")
        options = f"-f {graph} -l -n 1 -v -r {source}"
        binding = {"model_revision": REVISION, "simulator": request["simulator"], "binary": request["binary"],
            "workload": workload, "guest_cores": 4, "guest_memory": "16GB", "options": options,
            "entry_script_sha256": artifacts.file_hash(script)}
        data["context"].update(configuration=configured, execution_binding=binding,
                              execution_binding_sha256=artifacts.digest(binding), source=source)
        data["build"] = {"binary": str(binary), "binary_sha256": request["binary"]["sha256"],
                         "simulator": str(simulator), "simulator_sha256": request["simulator"]["sha256"]}
        env = dict(os.environ, OMP_NUM_THREADS="4", OMP_PROC_BIND="false", OMP_DYNAMIC="FALSE")
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
            if not isinstance(manifest, dict) or manifest.get("binding") != binding:
                raise StageFailure("incompatible", "checkpoint binding differs from exact binary/workload/source/model/options")
            checkpoint = artifacts.verify(manifest["artifact"])
            session.finish()
        else:
            checkpoint = session.folder / "checkpoint"
            checkpoint.mkdir()
            command = [str(simulator), f"--outdir={checkpoint}", str(script), "--cpu-type", "AtomicSimpleCPU",
                       "-n", "4", "--mem-size", "16GB", "--max-checkpoints", "1", "--cmd", str(binary), "--options", options]
            _bounded_process(session, "checkpoint", command, checkpoint_seconds, budget["memory_gib"], budget["storage_gib"], env)
            directories = [path for path in checkpoint.glob("cpt.*") if path.is_dir()]
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
        command = [str(simulator), "--debug-flags=MAATrace", f"--outdir={result_folder}", str(script), *settings,
                   "--cmd", str(binary), "--options", options, "--checkpoint-dir", str(checkpoint), "-r", "1"]
        log = _bounded_process(session, "simulation", command, run_seconds, budget["memory_gib"], budget["storage_gib"], env)
        session.begin("execution_observations")
        stats = result_folder / "stats.txt"
        output = log.read_text(errors="replace")
        causes = re.findall(r"Exiting @ tick (\d+) because ([^\r\n]+)", output)
        if not causes or causes[-1][1].strip() != "m5_exit instruction encountered":
            raise StageFailure("missing_observation", "simulator did not report the expected BFS ROI exit")
        if not stats.is_file() or "Begin Simulation Statistics" not in stats.read_text(errors="replace"):
            raise StageFailure("missing_observation", "simulation produced no readable statistics interval")
        actual_config = result_folder / "config.ini"
        if not actual_config.is_file():
            raise StageFailure("missing_observation", "simulation produced no actual configuration file")
        data["context"].update(exit_tick=int(causes[-1][0]), exit_cause=causes[-1][1].strip(),
            actual_configuration={"path": str(actual_config), "sha256": artifacts.file_hash(actual_config)},
            statistics={"path": str(stats), "sha256": artifacts.file_hash(stats)})
        data["raw_artifacts"].append({"kind": "simulation", "artifact": artifacts.identify(result_folder)})
        session.finish()
        data["outcome"] = {"state": "complete", "stage": "execution", "reason": "Unverified smoke execution: explicit timed-binary correctness and complete profiling remain required."}
    except (Failure, StageFailure, Stopped, OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        error = exc
    return _finish(args, data, session, error)
