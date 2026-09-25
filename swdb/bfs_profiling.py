"""Execution-bound automatic BFS source attribution and modeled memory events.

Updated: 2026-09-25. Diagnostic artifacts never replace primary native ROI timing.
"""
import copy
import json
import math
import os
import re
import shutil
import socket
import sys
import uuid
from pathlib import Path

import yaml

from swdb import artifacts, bfs_discovery, bfs_native as native, paths, profile, workflow, yamlio
from swdb.cli import Failure, _require_valid

RUNTIME = paths.HOME / "tools/bfs_profile/runtime.hpp"
METRICS = {
    "Dr": "executed data read references",
    "Dw": "executed data write references",
    "D1mr": "simulated first-level data cache read misses",
    "D1mw": "simulated first-level data cache write misses",
    "DLmr": "simulated last-level data cache read misses",
    "DLmw": "simulated last-level data cache write misses",
}


def parse_callgrind(path):
    """Read collector-produced event totals, not source-derived estimates."""
    events, summary = None, None
    for line in Path(path).read_text(errors="replace").splitlines():
        if line.startswith("events:"):
            events = line.split()[1:]
        elif line.startswith("summary:"):
            try:
                summary = [int(value) for value in line.split()[1:]]
            except ValueError:
                raise Failure("malformed Callgrind summary") from None
    if not events or summary is None or len(summary) > len(events) or any(v < 0 for v in summary):
        raise Failure("Callgrind output lacks a valid event summary")
    return dict(zip(events, summary + [0] * (len(events)-len(summary))))


def _discovery_settings(request, compiler, flags, includes, macro_log):
    settings = request.get("discovery", {})
    if not isinstance(settings, dict):
        raise Failure("discovery must be a mapping")
    choices = [settings.get("library"), "/data1/yanruj/llvm18/lib/libclang.so",
               "/usr/lib/llvm-18/lib/libclang.so.1", "/opt/homebrew/opt/llvm/lib/libclang.dylib"]
    library = next((Path(p) for p in choices if p and Path(p).is_file()), None)
    if library is None:
        raise Failure("libclang is unavailable; supply discovery.library explicitly")
    resource = settings.get("resource_dir")
    if not resource:
        parent = library.parent / "clang"
        found = sorted(parent.glob("*")) if parent.is_dir() else []
        if found: resource = str(found[-1])
    arguments = [f for f in flags if f != "-fopenmp"] + [f"-I{p}" for p in includes]
    # A standalone libclang distribution need not find the GCC C++ standard
    # library chosen by the real compiler. Preserve its reported search paths
    # explicitly rather than silently discovering against another standard library.
    search = re.search(r"#include <\.\.\.> search starts here:\n(.*?)End of search list\.", macro_log.read_text(), re.S)
    if search:
        for line in search.group(1).splitlines():
            entry = line.strip()
            framework = entry.endswith(" (framework directory)")
            if framework: entry = entry.removesuffix(" (framework directory)")
            if entry and Path(entry).is_dir():
                arguments += ["-iframework" if framework else "-isystem", entry]
    # CIndex suppresses OpenMP captured loop bodies. Keep exact feature-selection
    # macro from the actual compiler while disabling only the metadata parser.
    macro = re.search(r"^#define _OPENMP (\d+)$", macro_log.read_text(), re.M)
    if macro: arguments.append("-D_OPENMP=" + macro.group(1))
    arguments += ["-fno-openmp", "-Wno-unknown-pragmas"]
    if resource: arguments += ["-resource-dir", str(resource)]
    extra = settings.get("arguments", [])
    if not isinstance(extra, list) or not all(isinstance(v, str) for v in extra):
        raise Failure("discovery.arguments must be an argument list")
    arguments += extra
    return library, arguments


def _trial_output(output, graph, source, threads):
    if not output.is_file() or output.is_symlink() or output.stat().st_size > graph["num_vertices"]*24+4096:
        raise native.StageFailure("missing_observation", "diagnostic parent output missing or unsafe")
    value = json.loads(output.read_text())
    if (value.get("format") != "swdb.bfs.native.trial.v1" or type(value.get("source")) is not int
            or value["source"] != source or value.get("roi") != native.ROI
            or type(value.get("configured_threads")) is not int or value["configured_threads"] != threads):
        raise native.StageFailure("incompatible", "diagnostic source, ROI, or threads differ")
    check = native.verify_parents(graph["adjacency"], source, value.get("parents"))
    if not check["passed"]: raise native.StageFailure("incorrect", check["reason"])
    duration = value.get("duration_s")
    if isinstance(duration, bool) or not isinstance(duration, (float, int)) or not math.isfinite(duration) or duration <= 0:
        raise native.StageFailure("missing_observation", "diagnostic duration missing or invalid")
    return {"correctness": check, "output_sha256": artifacts.file_hash(output), "diagnostic_wall_seconds": duration}


def _region_observations(path, regions):
    if not path.is_file() or path.is_symlink() or path.stat().st_size > len(regions)*256+4096:
        raise native.StageFailure("missing_observation", "region counter output missing or unsafe")
    value = json.loads(path.read_text())
    if value.get("format") != "swdb.bfs.regions.v1" or value.get("clock") != "CLOCK_THREAD_CPUTIME_ID" or value.get("errors") != 0:
        raise native.StageFailure("missing_observation", "region clock or nested accounting failed")
    rows = value.get("regions")
    if not isinstance(rows, list) or len(rows) != len(regions):
        raise native.StageFailure("missing_observation", "region counter inventory differs")
    for index, row in enumerate(rows):
        if (type(row.get("index")) is not int or row["index"] != index or any(type(row.get(key)) is not int or row[key] < 0
                for key in ("inclusive_ns", "exclusive_ns", "invocations"))
                or row["exclusive_ns"] > row["inclusive_ns"]):
            raise native.StageFailure("missing_observation", "invalid region counters")
    return rows


def _wrapper(source, prefix, start, end, after):
    template = native.DRIVER.read_text()
    template = prefix + "\n" + template.replace("#include SWDB_SOURCE_INCLUDE", "#include " + json.dumps(str(source)))
    template = template.replace("auto parent =", start + "\n        auto parent =")
    template = template.replace("const auto end = std::chrono::steady_clock::now();",
                                end + "\n        const auto end = std::chrono::steady_clock::now();")
    template = template.replace("output.close();", "output.close();\n        " + after)
    return template


def _correspondence(data, prior):
    pairs, matched = [], set()
    for region in data["regions"]:
        candidates = [old for old in prior["regions"] if old["kind"] == region["kind"]
                      and old["source_sha256"] == region["source_sha256"] and old["function"] == region["function"]]
        if len(candidates) == 1:
            pairs.append({"current": region["id"], "previous": candidates[0]["id"], "basis": "identical source fragment and containing function"})
            matched.add(candidates[0]["id"])
    return {"previous_profile": prior["id"], "resolved": pairs,
            "current_unresolved": [r["id"] for r in data["regions"] if r["id"] not in {p["current"] for p in pairs}],
            "previous_unresolved": [r["id"] for r in prior["regions"] if r["id"] not in matched],
            "region_gain_claim": False, "limits": "changed, split, fused, and ambiguous repeated fragments are unresolved; no timings or semantics are inherited"}


def run(args):
    store = _require_valid(args.records)
    try:
        raw = Path(args.file).read_text()
        request = {"parse_error": "profile request exceeds 10 MiB"} if len(raw.encode()) > native.MAX_REQUEST_BYTES else yaml.load(raw, Loader=yamlio._Loader)
    except (yaml.YAMLError, OSError) as error:
        request = {"parse_error": str(error)}
    rid = request.get("id") if isinstance(request, dict) else None
    if not isinstance(rid, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", rid):
        rid = "region-profile-invalid-" + uuid.uuid4().hex
    if store.get(rid): raise Failure("profile ID already exists; use a new ID")
    data = workflow.record("region_profile", rid, request=request,
        outcome={"state": "submitted", "stage": "submission", "reason": None},
        stages=[], regions=[], dynamic_memory=[], executions=[], raw_artifacts=[], reasons=[], gain_claim=False)
    workflow.persist(args.records, data, getattr(args, "db", None), create=True)
    session = None
    try:
        if not isinstance(request, dict) or request.get("message_version") != "1.0":
            raise Failure("bfs-profile requires message_version 1.0")
        if request.get("id") != rid:
            raise Failure("profile id must use the record identifier syntax")
        evaluation = store.get(request.get("evaluation"), "evaluation")
        if not evaluation or evaluation["outcome"]["state"] != "complete" or evaluation["correctness"]["state"] != "passed":
            raise Failure("profiling requires a complete independently checked native evaluation")
        if evaluation["evidence_kind"] != "execution":
            raise Failure("contract-fixture timing cannot authorize an execution profile")
        for key in ("candidate", "source_snapshot", "implementation", "machine"):
            data[key] = evaluation[key]
        data["evaluation"] = evaluation["id"]
        candidate = store.get(data["candidate"], "candidate")
        root = artifacts.verify(candidate["artifact"])
        if artifacts.file_hash(evaluation["build"]["binary"]) != evaluation["build"]["binary_sha256"]:
            raise Failure("primary timed binary changed or is unavailable")
        artifacts.check_protections(root, candidate["protections"])
        native._protect_driver_macros(candidate, root, extra_text=RUNTIME.read_text() +
            "\n#include <valgrind/callgrind.h>\nCALLGRIND_START_INSTRUMENTATION CALLGRIND_STOP_INSTRUMENTATION CALLGRIND_ZERO_STATS CALLGRIND_DUMP_STATS")
        machine = store.get(data["machine"], "machine")
        host = socket.gethostname().split(".")[0]
        if artifacts.digest(machine) != evaluation["context"]["machine_sha256"]:
            raise Failure("machine record changed since the primary evaluation")
        if host != machine["hostname"] or host != evaluation["context"]["host"]:
            raise Failure("profile must execute on the evaluation's native host")
        if host == "mbit10" and not profile.lane_required(machine):
            raise Failure("mbit10 profiles require a socket lane")
        lane = profile._verified_lane(machine, getattr(args, "lane", None))
        if lane and evaluation["context"].get("lane") and lane.split(" ", 1)[0] != evaluation["context"]["lane"].split(" ", 1)[0]:
            raise Failure("profile lane differs from the primary evaluation")
        budget = request.get("budget", {})
        budget = {key: native._seconds(budget.get(key), "budget."+key) for key in
                  ("discovery_seconds", "build_seconds", "run_seconds", "total_seconds")}
        repetitions = native._integer(request.get("repetitions", 1), "repetitions", maximum=100)
        if "memory" in request and not isinstance(request["memory"], bool):
            raise Failure("memory must be boolean")
        folder = artifacts.external_directory(args.runs_dir) / rid
        if host == "mbit10" and not any(base in folder.parents for base in (Path("/data1/yanruj"), Path("/data/yanruj"))):
            raise Failure("mbit10 raw artifacts require /data1/yanruj or /data/yanruj")
        folder.mkdir(exist_ok=False)
        data["raw_artifacts"].append({"host": host, "path": str(folder), "kind": "diagnostic_profile"})
        session = native.Session(args, data, folder, budget["total_seconds"])
        session.install_handlers()
        data["context"] = copy.deepcopy(evaluation["context"])
        data["context"].update(primary_binary_sha256=evaluation["build"]["binary_sha256"],
            primary_evaluation=data["evaluation"], repetitions=repetitions, lane=lane, budget=budget,
            timing_basis="diagnostic accumulated thread CPU seconds; primary ROI wall timing remains in evaluation",
            overhead_treatment="scope instrumentation overhead is included; no synthetic subtraction or gain claim")
        if candidate["artifact"]["sha256"] != evaluation["context"]["candidate_sha256"]:
            raise Failure("evaluation source identity differs from candidate artifact")
        graph_path = Path(evaluation["context"]["workload"]["canonical_path"])
        if artifacts.file_hash(graph_path) != evaluation["context"]["workload"]["canonical_file_sha256"]:
            raise Failure("evaluation canonical graph changed")
        tokens = graph_path.read_text().split()
        n, count, directed = map(int, tokens[1:4])
        if tokens[0] != "SWDBGRAPH1" or len(tokens) != 4+2*count:
            raise Failure("canonical graph representation malformed")
        graph, facts = native.canonical_graph({"graph": {"num_vertices": n, "directed": bool(directed),
            "edges": [[int(tokens[i]), int(tokens[i+1])] for i in range(4,len(tokens),2)]}})
        if facts["canonical_sha256"] != evaluation["context"]["workload"]["canonical_sha256"]:
            raise Failure("canonical graph identity differs")
        compiler, flags, includes, source, adapter = native._compile_settings(evaluation["request"], candidate, root)
        if compiler != evaluation["build"]["compiler"] or flags != evaluation["build"]["flags"]:
            raise Failure("diagnostic build compiler/settings differ from resolved primary build")
        version = session.execute("compiler_identity", [compiler, "--version"], 30)
        if version.read_text(errors="replace").splitlines()[:2] != evaluation["build"]["compiler_version"]:
            raise Failure("compiler version changed since primary evaluation")
        macro = session.execute("preprocessor_identity", [compiler, *flags, "-dM", "-E", "-v", "-x", "c++", "/dev/null"], 30)
        library, arguments = _discovery_settings(request, compiler, flags, includes, macro)
        discovery_request = folder / "discovery-request.json"
        discovery_request.write_text(json.dumps({"source": str(source), "arguments": arguments, "library": str(library)}))
        discovery_output = folder / "discovery.json"
        session.execute("source_discovery", [sys.executable, str(Path(bfs_discovery.__file__)), str(discovery_request), str(discovery_output)], budget["discovery_seconds"])
        discovered = json.loads(discovery_output.read_text())
        rows = discovered.pop("regions")
        if not rows: raise native.StageFailure("missing_observation", "compiler found no supported source regions")
        if len(rows) > 10000: raise Failure("source region inventory exceeds 10000 supported scopes")
        data["discovery"] = discovered
        data["discovery"]["library_sha256"] = artifacts.file_hash(library.resolve())
        data["discovery"]["pass_sha256"] = artifacts.file_hash(bfs_discovery.__file__)
        data["discovery"]["collector_sha256"] = artifacts.file_hash(__file__)
        diagnostic_source = folder / "instrumented_bfs.cc"
        diagnostic_source.write_bytes(bfs_discovery.instrument(source, rows))
        runtime = folder / "runtime.hpp"
        runtime.write_bytes(RUNTIME.read_bytes())
        prefix = f'#define SWDB_REGION_COUNT {len(rows)}\n#include ' + json.dumps(str(runtime))
        driver = folder / "regions_driver.cc"
        driver.write_text(_wrapper(diagnostic_source, prefix, "::swdb_profile::start();", "::swdb_profile::stop();",
            '::swdb_profile::write((std::string(argv[3]) + ".regions.json").c_str());'))
        binary = folder / "bfs-regions"
        command = [compiler, *flags, *(f"-I{p}" for p in includes), str(driver), "-o", str(binary)]
        data["build"] = {"compiler": compiler, "compiler_version": evaluation["build"]["compiler_version"], "flags": flags,
            "command": command, "wrapper_sha256": artifacts.file_hash(driver), "runtime_sha256": artifacts.file_hash(runtime),
            "instrumented_source_sha256": artifacts.file_hash(diagnostic_source)}
        session.execute("region_build", command, budget["build_seconds"])
        binary_hash = artifacts.file_hash(binary)
        data["artifacts"] = {"primary_binary_sha256": evaluation["build"]["binary_sha256"],
            "region_binary": {"path": str(binary), "sha256": binary_hash, "difference": "automatic source scope guards; original build flags retained"}}
        for row in rows:
            row["path"] = source.relative_to(root).as_posix()
            row.update(metrics={"inclusive_thread_cpu_seconds": 0.0, "exclusive_thread_cpu_seconds": 0.0, "invocations": 0},
                       basis="measured", scope="accumulated within diagnostic complete-call ROI", artifact_sha256=binary_hash,
                       source_artifact_sha256=candidate["artifact"]["sha256"])
        for row in rows:
            enclosing = [function for function in rows if function["kind"] == "function"
                         and function["byte_range"][0] <= row["byte_range"][0]
                         and function["byte_range"][1] >= row["byte_range"][1]]
            if enclosing:
                function = min(enclosing, key=lambda f: f["byte_range"][1]-f["byte_range"][0])
                row["function_region"] = function["id"]
                row["referenced_types"] = list(function.get("referenced_types", []))
        data["regions"] = rows
        env = dict(os.environ, **evaluation["build"]["execution_environment"])
        threads = evaluation["context"]["threads"]
        for repetition in range(repetitions):
            for position, source_id in enumerate(evaluation["context"]["sources"]):
                output = folder / f"regions-{repetition}-{position}.json"
                if artifacts.file_hash(binary) != binary_hash or artifacts.file_hash(graph_path) != evaluation["context"]["workload"]["canonical_file_sha256"]:
                    raise Failure("diagnostic binary or graph changed")
                session.execute("region_execution", [str(binary), str(graph_path), str(source_id), str(output)], budget["run_seconds"], env)
                check = _trial_output(output, graph, source_id, threads)
                counters = _region_observations(Path(str(output)+".regions.json"), rows)
                for row, observed in zip(rows, counters):
                    row["metrics"]["inclusive_thread_cpu_seconds"] += observed["inclusive_ns"] / 1e9
                    row["metrics"]["exclusive_thread_cpu_seconds"] += observed["exclusive_ns"] / 1e9
                    row["metrics"]["invocations"] += observed["invocations"]
                for function in rows:
                    if function["kind"] == "function":
                        function["metrics"]["exclusive_function_thread_cpu_seconds"] = sum(
                            r["metrics"]["exclusive_thread_cpu_seconds"] for r in rows
                            if r.get("function_region") == function["id"])
                data["executions"].append({"kind": "regions", "source": source_id, "source_position": position,
                    "repetition": repetition, "binary_sha256": binary_hash, "output": str(output),
                    "region_output": str(output)+".regions.json", "region_output_sha256": artifacts.file_hash(str(output)+".regions.json"), **check})
                session.save()
        if request.get("correspondence"):
            prior = store.get(request["correspondence"], "region_profile")
            if not prior: raise Failure("correspondence profile does not exist")
            if prior.get("implementation") != data["implementation"]:
                raise Failure("correspondence profile belongs to a different implementation")
            data["correspondence"] = _correspondence(data, prior)
        if request.get("memory", True):
            try:
                _memory(session, data, request, source, includes, compiler, flags, graph_path, graph, env, budget)
            except (Failure, native.StageFailure, OSError, ValueError) as error:
                data["reasons"].append("dynamic memory collection: " + str(error))
        else:
            data["reasons"].append("dynamic memory collection disabled by request")
        if not data["dynamic_memory"]:
            data["dynamic_memory"] = [{"metric": metric, "available": False, "reason": data["reasons"][-1]} for metric in METRICS]
        data["reasons"] += ["source coverage: " + item for item in discovered["limitations"]]
        if discovered["unresolved"]: data["reasons"].append("some compiler source regions could not be safely instrumented")
        artifacts.verify(candidate["artifact"])
        data["outcome"] = {"state": "partial", "stage": "profiling", "reason": "bounded source attribution; see explicit coverage and metric limits"}
    except (Failure, native.StageFailure, native.Stopped, OSError, ValueError) as error:
        if isinstance(error, Failure) and "persisted, but query indexing failed" in str(error): raise
        state = "interrupted" if isinstance(error, native.Stopped) else error.state if isinstance(error, native.StageFailure) else "failed"
        data["outcome"] = {"state": state, "stage": session.current["stage"] if session and session.current else "validation", "reason": str(error)}
        data["reasons"].append(str(error))
        if session and session.current and session.current["state"] == "running":
            session.current.update(state=state, finished=native._now(), reason=str(error))
    finally:
        if session: session.kill(); session.restore_handlers()
    return workflow.persist(args.records, data, getattr(args, "db", None))


def _memory(session, data, request, source, includes, compiler, flags, graph_path, graph, env, budget):
    settings = request.get("memory_model", {})
    if not isinstance(settings, dict): raise Failure("memory_model must be a mapping")
    valgrind = shutil.which(settings.get("collector", "valgrind"))
    if valgrind is None: raise Failure("Valgrind is unavailable; hardware counters are not substituted")
    model = {"I1": settings.get("I1", "32768,8,64"), "D1": settings.get("D1", "49152,12,64"), "LL": settings.get("LL", "25165824,12,64")}
    if any(not isinstance(v, str) or not re.fullmatch(r"[1-9][0-9]*,[1-9][0-9]*,[1-9][0-9]*", v) for v in model.values()):
        raise Failure("cache model must specify positive size,associativity,line_bytes")
    version = session.execute("memory_collector_identity", [valgrind, "--version"], 30)
    collector = {"name": "Callgrind", "version": version.read_text().strip(), "cache_model": model,
                 "initial_state": "instrumentation starts at ROI; caches initially empty", "hardware_counters": False,
                 "thread_policy": "collection enabled for all threads; instrumentation globally bounded to ROI; combined thread dump"}
    folder = session.folder
    driver = folder / "memory_driver.cc"
    driver.write_text(_wrapper(source, '#include <valgrind/callgrind.h>',
        "CALLGRIND_START_INSTRUMENTATION; CALLGRIND_ZERO_STATS;",
        "CALLGRIND_STOP_INSTRUMENTATION; CALLGRIND_DUMP_STATS;", ""))
    binary = folder / "bfs-memory"
    memory_flags = list(flags)
    if "-g" not in memory_flags: memory_flags.append("-g")
    command = [compiler, *memory_flags, *(f"-I{p}" for p in includes), str(driver), "-o", str(binary)]
    session.execute("memory_build", command, budget["build_seconds"])
    binary_hash = artifacts.file_hash(binary)
    data["artifacts"]["memory_binary"] = {"path": str(binary), "sha256": binary_hash, "flags": memory_flags,
        "wrapper_sha256": artifacts.file_hash(driver), "difference": "original candidate source; client ROI guards and debug info, no region guards"}
    for position, source_id in enumerate(data["context"]["sources"]):
        output = folder / f"memory-{position}.json"
        raw = folder / f"callgrind-{position}.out"
        command = [valgrind, "--tool=callgrind", "--cache-sim=yes", "--collect-atstart=yes", "--instr-atstart=no", "--separate-threads=no",
                   *(f"--{key}={value}" for key,value in model.items()), f"--callgrind-out-file={raw}",
                   str(binary), str(graph_path), str(source_id), str(output)]
        session.execute("memory_execution", command, budget["run_seconds"], env)
        check = _trial_output(output, graph, source_id, data["context"]["threads"])
        nonzero = []
        for file in sorted(folder.glob(raw.name+"*")):
            events = parse_callgrind(file)
            if events.get("Ir", 0): nonzero.append((file, events))
        if len(nonzero) != 1:
            raise native.StageFailure("missing_observation", "expected exactly one nonempty explicit Callgrind ROI dump")
        file, events = nonzero[0]
        execution = {"kind": "memory", "source": source_id, "source_position": position, "repetition": 0,
            "binary_sha256": binary_hash, "output": str(output), "raw_artifact": str(file),
            "raw_sha256": artifacts.file_hash(file), "collector": collector, **check}
        data["executions"].append(execution)
        for metric, definition in METRICS.items():
            available = metric in events
            data["dynamic_memory"].append({"metric": metric, "available": available,
                "value": events.get(metric), "unit": "references" if metric in ("Dr", "Dw") else "misses",
                "definition": definition, "basis": "simulated", "scope": "ROI", "attribution_granularity": "whole BFS call",
                "collector": collector, "artifact_sha256": binary_hash, "source_artifact_sha256": data["context"]["candidate_sha256"],
                "execution": {"source": source_id, "source_position": position, "repetition": 0},
                "raw_artifact": str(file), "raw_sha256": artifacts.file_hash(file),
                "limitations": "instrumented dynamic references and modeled cache misses; not native hardware counters, address traces, per-region metrics, or causal bottleneck proof"})
        session.save()


def query(args):
    store = _require_valid(args.records)
    data = store.get(args.id, "region_profile")
    if not data: raise Failure("region profile does not exist")
    if getattr(args, "evaluation", None) and args.evaluation != data.get("evaluation"):
        raise Failure("requested evaluation differs from this profile's execution identity")
    requested = getattr(args, "kind", None)
    regions = [r for r in data["regions"] if (requested is None or r["kind"] == requested)
               and r.get("metrics", {}).get("invocations", 0) > 0]
    metric = "exclusive_function_thread_cpu_seconds" if requested == "function" else "exclusive_thread_cpu_seconds"
    regions.sort(key=lambda r: r["metrics"].get(metric, r["metrics"]["exclusive_thread_cpu_seconds"]), reverse=True)
    return {"profile": data["id"], "evaluation": data.get("evaluation"), "candidate": data.get("candidate"),
        "context": data.get("context"), "outcome": data["outcome"], "regions": regions,
        "ranking": {"metric": metric, "unit": "seconds", "scope": "accumulated across diagnostic executions",
                    "inclusive": "nested source scopes overlap; do not sum inclusive values", "unexecuted": "discovered but unexecuted scopes remain in the durable record"},
        "correspondence": data.get("correspondence"), "dynamic_memory": data["dynamic_memory"],
        "coverage": data.get("discovery"), "reasons": data["reasons"], "gain_claim": False}
