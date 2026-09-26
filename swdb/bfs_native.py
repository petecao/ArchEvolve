"""Durable native BFS evaluation with evaluator-owned result checking.

Updated: 2026-09-25. Real timing, fixture timing, and profiling remain distinct.
"""

import copy
import datetime
import json
import math
import os
import platform
import re
import shlex
import shutil
import signal
import socket
import statistics
import subprocess
import time
import uuid
from collections import deque
from pathlib import Path

import yaml

from swdb import artifacts, paths, profile, workflow, yamlio
from swdb.cli import Failure, _require_valid
from swdb.store import Store
from swdb.vocab import load_all

ROI = "bfs.complete_call.v1"
DRIVER = paths.HOME / "tools" / "bfs_native" / "driver.cc.in"
MAX_REQUEST_BYTES = 10 * 1024 * 1024
MAX_VERTICES = 2_000_000
MAX_DIRECTED_EDGES = 32_000_000


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Stopped(Exception):
    pass


class StageFailure(Exception):
    def __init__(self, state, message):
        self.state = state
        super().__init__(message)


def _integer(value, name, minimum=1, maximum=None):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise Failure(f"{name} must be an integer >= {minimum}")
    if maximum is not None and value > maximum:
        raise Failure(f"{name} exceeds the supported limit {maximum}")
    return value


def _seconds(value, name):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0:
        raise Failure(f"{name} must be positive and finite")
    return float(value)


def canonical_graph(workload):
    """Validate and normalize a bounded graph without relying on a candidate loader.

    The family/generator metadata is retained as declared, not inferred from edges.
    An external JSON file carries the same graph mapping as an inline graph.
    """
    if not isinstance(workload, dict):
        raise Failure("workload must be a mapping")
    graph = workload.get("graph")
    representation = {"kind": "inline_graph", "sha256": None}
    if "graph_file" in workload:
        if graph is not None:
            raise Failure("workload must use either graph or graph_file")
        path = Path(workload["graph_file"])
        if not path.is_absolute() or path.is_symlink() or not path.is_file():
            raise Failure("graph_file must be an absolute regular file, not a symlink")
        if path.stat().st_size > 512 * 1024 * 1024:
            raise Failure("graph_file exceeds the native evaluator's 512 MiB input limit")
        actual = artifacts.file_hash(path)
        if workload.get("graph_sha256") != actual:
            raise Failure("graph_file content does not match graph_sha256")
        graph = json.loads(path.read_text())
        representation = {"kind": "json_graph", "path": str(path), "sha256": actual}
    if not isinstance(graph, dict):
        raise Failure("workload requires graph or a hashed graph_file")
    n = _integer(graph.get("num_vertices"), "graph.num_vertices", maximum=MAX_VERTICES)
    directed = graph.get("directed")
    if not isinstance(directed, bool):
        raise Failure("graph.directed must be explicit boolean")
    edges = graph.get("edges")
    if not isinstance(edges, list) or len(edges) > MAX_DIRECTED_EDGES:
        raise Failure("graph.edges must be a bounded list of vertex pairs")
    adjacency = [set() for _ in range(n)]
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 2:
            raise Failure("each edge must contain two vertex IDs")
        u = _integer(edge[0], "edge source", minimum=0, maximum=n-1)
        v = _integer(edge[1], "edge destination", minimum=0, maximum=n-1)
        # GAPBS builds simple graphs: discard self loops and duplicate edges.
        if u != v:
            adjacency[u].add(v)
            if not directed:
                adjacency[v].add(u)
    adjacency = [sorted(row) for row in adjacency]
    m = sum(map(len, adjacency))
    if m > MAX_DIRECTED_EDGES:
        raise Failure("normalized graph exceeds the supported directed edge limit")
    canonical = {"format": "swdb.bfs.adjacency.v1", "directed": directed,
                 "num_vertices": n, "adjacency": adjacency}
    digest = artifacts.digest(canonical)
    expected = workload.get("loaded_adjacency_sha256")
    if expected is not None and expected != digest:
        raise Failure("canonical loaded adjacency differs from requested identity")
    if representation["sha256"] is None:
        representation["sha256"] = artifacts.digest(graph)
    facts = {"id": workload.get("id"), "family": workload.get("family", "unspecified"),
             "generator": workload.get("generator"), "representation": representation,
             "normalization": "simple graph: remove self loops and duplicates; symmetrize if undirected; sort neighbors",
             "canonical_sha256": digest, "adjacency_order_sha256": digest,
             "num_vertices": n, "num_directed_edges": m, "directed": directed}
    return canonical, facts


def verify_parents(adjacency, source, parents):
    """Exact structural BFS criterion; range checks always precede parent indexing."""
    n = len(adjacency)
    if isinstance(source, bool) or not isinstance(source, int) or not 0 <= source < n:
        return {"passed": False, "reason": "source outside graph"}
    if not isinstance(parents, list) or len(parents) != n:
        return {"passed": False, "reason": "parent vector length differs from vertex count"}
    for v, parent in enumerate(parents):
        if isinstance(parent, bool) or not isinstance(parent, int) or not -1 <= parent < n:
            return {"passed": False, "reason": f"parent[{v}] is not an integer in [-1, n)"}
    if parents[source] != source:
        return {"passed": False, "reason": "source must be its own parent"}
    depth = [-1] * n
    depth[source] = 0
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v in adjacency[u]:
            if depth[v] == -1:
                depth[v] = depth[u] + 1
                queue.append(v)
    # Check all selected parent edges in O(V+E), rather than searching high-degree
    # parent adjacency once per child (which can be quadratic for a star graph).
    parent_edge = [False] * n
    for u, neighbors in enumerate(adjacency):
        for v in neighbors:
            if parents[v] == u:
                parent_edge[v] = True
    for v, d in enumerate(depth):
        p = parents[v]
        if d == -1:
            if p != -1:
                return {"passed": False, "reason": f"unreachable vertex {v} has a parent"}
        elif v != source:
            if p < 0:
                return {"passed": False, "reason": f"reachable vertex {v} has no parent"}
            if not parent_edge[v]:
                return {"passed": False, "reason": f"parent edge absent for vertex {v}"}
            if depth[p] + 1 != d:
                return {"passed": False, "reason": f"parent depth is wrong for vertex {v}"}
    return {"passed": True, "reason": None, "reachable_vertices": sum(d >= 0 for d in depth)}


class Session:
    """Persist before starting children and after every completed stage."""
    def __init__(self, args, data, folder, budget):
        self.args, self.data, self.folder = args, data, folder
        self.deadline = time.monotonic() + budget
        self.child = None
        self.current = None
        self.handlers = {}

    def save(self):
        return workflow.persist(self.args.records, self.data, getattr(self.args, "db", None))

    def remaining(self):
        left = self.deadline - time.monotonic()
        if left <= 0:
            raise StageFailure("budget_exhausted", "total evaluation execution budget exhausted")
        return left

    def install_handlers(self):
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            self.handlers[sig] = signal.signal(sig, self.stop)

    def restore_handlers(self):
        for sig, handler in self.handlers.items():
            signal.signal(sig, handler)

    def stop(self, signum, frame):
        raise Stopped(f"interrupted by {signal.Signals(signum).name}")

    def kill(self):
        if self.child is not None:
            try:
                os.killpg(self.child.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            self.child.wait()
            self.child = None

    def begin(self, name, **details):
        self.remaining()
        self.current = {"stage": name, "state": "running", "started": _now(), **details}
        self.data["stages"].append(self.current)
        self.data["outcome"] = {"state": "running", "stage": name, "reason": None}
        self.save()

    def finish(self, state="complete", **details):
        self.current.update(state=state, finished=_now(), **details)
        self.save()

    def execute(self, name, command, timeout, env=None, **details):
        allowed = min(timeout, self.remaining())
        log = self.folder / f"{len(self.data['stages']):03d}-{name}.log"
        self.begin(name, command=list(map(str, command)), timeout_s=allowed, log=str(log), **details)
        elapsed_start = time.monotonic()
        try:
            with log.open("w") as output:
                self.child = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT,
                                              cwd=self.folder, env=env, start_new_session=True)
                try:
                    code = self.child.wait(timeout=allowed)
                except subprocess.TimeoutExpired:
                    self.kill()
                    state = "budget_exhausted" if allowed < timeout else "timed_out"
                    self.finish(state, reason=f"{name} exceeded {allowed:.3f} seconds",
                                host_wall_s=time.monotonic() - elapsed_start, returncode=None)
                    raise StageFailure(state, self.current["reason"]) from None
                finally:
                    self.kill()
            self.finish("complete" if code == 0 else "failed", returncode=code,
                        host_wall_s=time.monotonic() - elapsed_start,
                        log_sha256=artifacts.file_hash(log))
            if code != 0:
                raise StageFailure("failed", f"{name} exited with status {code}; see {log}")
        except Stopped:
            self.kill()
            raise
        return log


def _compile_settings(request, candidate, root):
    context = candidate["context"]
    refs = context["code"]
    ref = refs[0] if isinstance(refs, list) else refs
    if ref.get("root") != "application":
        raise Failure("native evaluator requires an application-backed candidate")
    source = root / artifacts.relative_path(ref["path"])
    if not source.is_file():
        raise Failure("candidate BFS translation unit is missing")
    build = request.get("build", {})
    if not isinstance(build, dict):
        raise Failure("build must be a mapping")
    compiler = build.get("compiler", context["build"]["compiler"])
    if not isinstance(compiler, str) or not compiler.strip():
        raise Failure("compiler must name one executable")
    executable = shutil.which(compiler)
    if executable is None:
        raise Failure(f"compiler is unavailable: {compiler}")
    flags = build.get("flags", context["build"]["flags"])
    if isinstance(flags, str):
        flags = shlex.split(flags)
    if not isinstance(flags, list) or not all(isinstance(f, str) for f in flags):
        raise Failure("build.flags must be an argument list or flag string")
    # Only compiler options that cannot replace the source, driver, linker entry,
    # or protected headers belong to this native adapter. Unknown options need a
    # new explicitly supported build contract, rather than shell interpretation.
    allowed = re.compile(r"-(?:std=c\+\+(?:11|14|17|20)|O[0-3sg]|g[0-3]?|Wall|Wextra|Wno-[A-Za-z0-9_-]+|"
                         r"fopenmp|pthread|march=[A-Za-z0-9_+.-]+|mtune=[A-Za-z0-9_+.-]+|m(?:avx|sse)[A-Za-z0-9_.-]*|"
                         r"D(?:FUNC|NUM_CORES=\d+|TILE_SIZE=\d+))")
    for flag in flags:
        if not allowed.fullmatch(flag):
            raise Failure(f"unsupported/protected native build flag: {flag}")
    dx100 = (root / "benchmarks" / "API" / "MAA_functional.hpp").is_file()
    if dx100 and "-DFUNC" not in flags:
        flags = [*flags, "-DFUNC"]
    includes = [source.parent]
    if dx100:
        includes.append(root / "benchmarks" / "API")
    return executable, flags, includes, source, "dx100_scalar_func" if dx100 else "gapbs_native"


def _protect_driver_macros(candidate, root, *, extra_text=""):
    """Reject preprocessor substitution of the trusted driver after source inclusion.

    Scan all UTF-8 candidate inputs, including .inc files and extensionless
    headers. Splicing and comment removal precede directive recognition, matching
    the relevant preprocessing phases. This does not claim to sandbox hostile C++.
    """
    template = DRIVER.read_text()
    suffix = template.split("#undef main", 1)[1] + "\n" + extra_text
    identifiers = set(re.findall(r"\b[A-Za-z_]\w*\b", suffix)) | {"main", "_OPENMP"}
    trusted_headers = {Path(name).name for name in re.findall(r"#include <([^>]+)>", template + "\n" + extra_text)} | {"omp.h"}
    lexical = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/')

    def strip_comment(match):
        text = match.group()
        return re.sub(r"[^\n]", " ", text) if text.startswith(("//", "/*")) else text

    for item in candidate["artifact"]["files"]:
        path = root / item["path"]
        if path.name in trusted_headers:
            raise Failure(f"candidate input shadows trusted driver header: {item['path']}")
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        text = re.sub(r"\\\r?\n", "", text)
        text = lexical.sub(strip_comment, text)
        for name in re.findall(r"^\s*#\s*(?:define|undef)\s+([A-Za-z_]\w*)", text, re.M):
            if name in identifiers:
                raise Failure(f"candidate preprocessor directive can alter protected driver identifier {name}: {item['path']}")


def _request(request):
    if not isinstance(request, dict) or request.get("message_version") != workflow.VERSION:
        raise Failure("evaluation requires message_version 1.0")
    if not isinstance(request.get("id"), str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", request["id"]):
        raise Failure("evaluation id must use the record identifier syntax")
    for key in ("candidate", "machine"):
        if not isinstance(request.get(key), str) or not request[key]:
            raise Failure(f"evaluation requires {key}")
    threads = _integer(request.get("threads"), "threads", maximum=1024)
    repetitions = _integer(request.get("repetitions"), "repetitions", maximum=10000)
    sources = request.get("sources")
    if not isinstance(sources, list) or not sources:
        raise Failure("sources must be an explicit nonempty ordered list")
    for source in sources:
        _integer(source, "source", minimum=0)
    if len(sources) * repetitions > 10000:
        raise Failure("evaluation exceeds the 10000-trial limit")
    if request.get("roi") != ROI:
        raise Failure(f"native evaluator only supports the protected ROI {ROI}")
    if "fixture" in request and not isinstance(request["fixture"], bool):
        raise Failure("fixture must be an explicit boolean")
    budget = request.get("budget")
    if not isinstance(budget, dict):
        raise Failure("evaluation requires explicit build_seconds, run_seconds, total_seconds budgets")
    budget = {key: _seconds(budget.get(key), f"budget.{key}")
              for key in ("build_seconds", "run_seconds", "total_seconds")}
    return threads, repetitions, sources, budget


def build_directory(request, host, rid, raw_folder, records):
    """Reserve a unique external build directory, honoring the lab disk policy."""
    supplied = request.get("build_directory")
    if supplied is not None and (not isinstance(supplied, str) or not Path(supplied).is_absolute()):
        raise Failure("build_directory must be an absolute external directory")
    directory = Path(supplied) if supplied is not None else (
        Path("/data1/yanruj/EvolveSWDB_builds") / rid if host == "mbit10" else raw_folder / "build")
    directory = directory.resolve()
    if directory == paths.HOME or paths.HOME in directory.parents:
        raise Failure("build_directory must be outside the repository")
    records = Path(records).resolve()
    if directory == records or records in directory.parents:
        raise Failure("build_directory must be outside records")
    if host == "mbit10" and Path("/data1/yanruj") not in directory.parents:
        raise Failure("mbit10 builds must live under /data1/yanruj")
    directory.mkdir(parents=True, exist_ok=False)
    return directory


def run(args):
    """Public `swdb evaluate REQUEST --runs-dir DIR` boundary."""
    store = _require_valid(args.records)
    try:
        raw = Path(args.file).read_text()
        if len(raw.encode()) > MAX_REQUEST_BYTES:
            raise Failure("evaluation request exceeds 10 MiB")
        request = yaml.load(raw, Loader=yamlio._Loader)
    except yaml.YAMLError as error:
        request = {"parse_error": str(error)}
    rid = request.get("id") if isinstance(request, dict) else None
    if not isinstance(rid, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", rid):
        rid = f"evaluation-invalid-{uuid.uuid4().hex}"
    if store.get(rid):
        raise Failure(f"evaluation ID {rid!r} already exists; use a new ID to retain earlier evidence")
    data = workflow.record("evaluation", rid, request=request,
        outcome={"state": "submitted", "stage": "submission", "reason": None}, stages=[],
        timing=[], correctness={"state": "unverified", "checks": []},
        profiling={"state": "unavailable", "reasons": ["automatic function attribution not collected",
                    "automatic loop attribution not collected", "dynamic memory observations not collected"]},
        raw_artifacts=[], gain_claim=False, evidence_kind="contract_fixture" if isinstance(request, dict) and request.get("fixture") is True else "execution")
    workflow.persist(args.records, data, getattr(args, "db", None), create=True)
    session = None
    try:
        threads, repetitions, sources, budget = _request(request)
        candidate = store.get(request["candidate"], "candidate")
        if not candidate or candidate["state"] == "incomplete":
            raise Failure("candidate is missing or incomplete")
        implementation = store.get(candidate["implementation"], "implementation")
        if (implementation.get("kernel") != "gapbs-bfs" or implementation.get("function") != "DOBFS"
                or candidate["context"].get("function", implementation["function"]) != "DOBFS"):
            raise Failure("native complete-call adapter supports the identified DOBFS entry point only")
        data.update(candidate=candidate["id"],
                    source_snapshot=candidate["source_snapshot"], implementation=candidate["implementation"])
        if candidate.get("proposal"):
            data["proposal"] = candidate["proposal"]
        proposal = store.get(candidate.get("proposal"), "proposal")
        if proposal and proposal.get("profile_package"):
            data["profile_package"] = proposal["profile_package"]
        machine = store.get(request["machine"], "machine")
        if not machine:
            raise Failure("native target machine does not exist")
        data["machine"] = machine["id"]
        host = socket.gethostname().split(".")[0]
        if machine["hostname"] != host:
            raise Failure(f"current host {host!r} differs from machine {machine['hostname']!r}")
        if host == "mbit10" and not profile.lane_required(machine):
            raise Failure("mbit10 evaluations cannot disable socket-lane policy")
        lane = profile._verified_lane(machine, getattr(args, "lane", None))
        available_cpus = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else os.cpu_count()
        if available_cpus is not None and threads > available_cpus:
            raise Failure("requested threads exceed this process's available CPUs")
        if host == "mbit10":
            destination = Path(args.runs_dir).resolve()
            if not any(base == destination or base in destination.parents for base in
                       (Path("/data1/yanruj"), Path("/data/yanruj"))):
                raise Failure("mbit10 outputs must live under /data1/yanruj or /data/yanruj")
        folder = artifacts.external_directory(args.runs_dir) / rid
        if Path(args.records).resolve() == folder or Path(args.records).resolve() in folder.parents:
            raise Failure("evaluation raw output must not be inside records")
        folder.mkdir(exist_ok=False)
        data["raw_artifacts"].append({"host": host, "path": str(folder), "kind": "evaluation_run"})
        build_folder = build_directory(request, host, rid, folder, args.records)
        data["raw_artifacts"].append({"host": host, "path": str(build_folder), "kind": "evaluation_build"})
        session = Session(args, data, folder, budget["total_seconds"])
        session.install_handlers()
        session.begin("source_resolution")
        root = artifacts.verify(candidate["artifact"])
        artifacts.check_protections(root, candidate["protections"])
        _protect_driver_macros(candidate, root)
        compiler, flags, includes, source, adapter = _compile_settings(request, candidate, root)
        impl = copy.deepcopy(store.get(candidate["implementation"], "implementation"))
        impl["build"]["flags"] = shlex.join(flags)
        vocabs, _ = load_all(paths.VOCAB)
        profile._check_isa(impl, machine, store, vocabs.get("isa_extensions", []))
        baseline = request.get("comparison_baseline") or candidate["context"].get("comparison_baseline")
        if baseline:
            selected = store.get(baseline, "implementation")
            if not selected or selected["kernel"] != impl["kernel"]:
                raise Failure("explicit comparison baseline is missing or realizes a different kernel")
            data["comparison_baseline"] = baseline
        data["context"] = {"candidate_sha256": candidate["artifact"]["sha256"],
                           "function": "DOBFS",
                           "source_revision": candidate["context"]["source"]["commit"],
                           "application": candidate["context"]["application"], "adapter": adapter,
                           "target": machine["id"], "machine_sha256": artifacts.digest(machine),
                           "threads": threads, "sources": sources, "repetitions": repetitions,
                           "roi": ROI, "protocol": request.get("protocol"), "basis": "measured",
                           "process_policy": "one fresh process per source and repetition; graph construction before ROI",
                           "verifier": "swdb.bfs.structural.v1", "verifier_sha256": artifacts.file_hash(__file__),
                           "backend_configuration": request.get("target_configuration", {}),
                           "instrumentation": {"template_sha256": artifacts.file_hash(DRIVER), "treatment": "included"},
                           "host": host, "architecture": platform.machine(), "lane": lane,
                           "load_average": list(os.getloadavg()), "budget": budget}
        session.finish()
        session.begin("workload_resolution")
        supplied_workload = request.get("workload")
        if isinstance(supplied_workload, dict) and set(supplied_workload) == {"id"}:
            try:
                from swdb.bfs_protocol import materialize_workload
            except ImportError:
                raise Failure("registered-workload materialization is unavailable") from None
            supplied_workload = materialize_workload(store, supplied_workload["id"])
        canonical, workload = canonical_graph(supplied_workload)
        if any(source >= canonical["num_vertices"] for source in sources):
            raise Failure("requested BFS source outside canonical graph")
        graph_path = folder / "graph.swdb"
        with graph_path.open("w") as output:
            output.write(f"SWDBGRAPH1 {canonical['num_vertices']} {workload['num_directed_edges']} {int(canonical['directed'])}\n")
            for u, neighbors in enumerate(canonical["adjacency"]):
                for v in neighbors:
                    output.write(f"{u} {v}\n")
        workload.update(sources=sources, canonical_path=str(graph_path), canonical_file_sha256=artifacts.file_hash(graph_path))
        data["context"]["workload"] = workload
        if request.get("protocol"):
            try:
                from swdb.bfs_protocol import validate_protocol_for_evaluation
            except ImportError:
                raise Failure("frozen protocol validation is unavailable") from None
            data["context"]["protocol_binding"] = validate_protocol_for_evaluation(
                store, request, candidate, actual_build={"compiler": compiler, "flags": flags, "adapter": adapter},
                actual_lane=lane, actual_instrumentation=data["context"]["instrumentation"])
        session.finish()
        wrapper = build_folder / "native_driver.cc"
        template = DRIVER.read_text()
        wrapper.write_text(template.replace("#include SWDB_SOURCE_INCLUDE", "#include " + json.dumps(str(source))))
        binary = build_folder / "bfs-native"
        command = [compiler, *flags, *(f"-I{p}" for p in includes), str(wrapper), "-o", str(binary)]
        data["build"] = {"directory": str(build_folder), "compiler": compiler, "flags": flags, "command": command,
                         "wrapper_sha256": artifacts.file_hash(wrapper), "template_sha256": artifacts.file_hash(DRIVER)}
        version_log = session.execute("compiler_identity", [compiler, "--version"], min(30, budget["build_seconds"]))
        data["build"]["compiler_version"] = version_log.read_text(errors="replace").splitlines()[:2]
        session.execute("build", command, budget["build_seconds"])
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise Failure("build did not produce an executable")
        data["build"].update(binary=str(binary), binary_sha256=artifacts.file_hash(binary))
        artifacts.verify(candidate["artifact"])
        env = dict(os.environ)
        env.update(OMP_NUM_THREADS=str(threads), OMP_DYNAMIC="FALSE", OMP_PROC_BIND="close", OMP_PLACES="cores")
        data["build"]["execution_environment"] = {name: env[name] for name in
                                                   ("OMP_NUM_THREADS", "OMP_DYNAMIC", "OMP_PROC_BIND", "OMP_PLACES")}
        session.save()
        for repetition in range(repetitions):
            for position, source in enumerate(sources):
                trial = len(data["timing"])
                output = folder / f"trial-{repetition}-{position}.json"
                if artifacts.file_hash(binary) != data["build"]["binary_sha256"]:
                    raise Failure("timed binary changed after build")
                if artifacts.file_hash(graph_path) != workload["canonical_file_sha256"]:
                    raise Failure("protected canonical graph changed before execution")
                session.execute("execution", [str(binary), str(graph_path), str(source), str(output)],
                                budget["run_seconds"], env, repetition=repetition, source_position=position, source=source)
                session.begin("correctness", repetition=repetition, source_position=position, source=source)
                if not output.is_file() or output.is_symlink() or output.stat().st_size > canonical["num_vertices"] * 24 + 4096:
                    raise StageFailure("missing_observation", "missing, unsafe, or oversized parent/timing output")
                observed = json.loads(output.read_text())
                if not isinstance(observed, dict) or observed.get("format") != "swdb.bfs.native.trial.v1":
                    raise StageFailure("missing_observation", "native trial output has the wrong format")
                if (type(observed.get("source")) is not int or observed["source"] != source
                        or observed.get("roi") != ROI or type(observed.get("configured_threads")) is not int
                        or observed["configured_threads"] != threads):
                    raise StageFailure("incompatible", "native output source, ROI, or configured threads differ from request")
                duration = observed.get("duration_s")
                if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
                    raise StageFailure("missing_observation", "native ROI duration must be positive and finite")
                observation = {"source": source, "source_position": position, "repetition": repetition,
                               "duration_s": duration, "roi": ROI, "basis": "measured", "quantity": "native_roi_wall_seconds",
                               "binary_sha256": data["build"]["binary_sha256"], "output": str(output),
                               "output_sha256": artifacts.file_hash(output), "verified": False,
                               "evidence_kind": data["evidence_kind"]}
                data["timing"].append(observation)
                check = verify_parents(canonical["adjacency"], source, observed.get("parents"))
                session.remaining()
                check.update(source=source, source_position=position, repetition=repetition, trial=trial,
                             output_sha256=observation["output_sha256"], binary_sha256=observation["binary_sha256"],
                             graph_sha256=workload["canonical_sha256"], verifier="swdb.bfs.structural.v1")
                data["correctness"]["checks"].append(check)
                observation["verified"] = check["passed"]
                session.finish("complete" if check["passed"] else "failed", reason=check["reason"])
                if not check["passed"]:
                    data["correctness"]["state"] = "failed"
                    raise StageFailure("incorrect", check["reason"])
        session.begin("aggregation")
        artifacts.verify(candidate["artifact"])
        if artifacts.file_hash(binary) != data["build"]["binary_sha256"]:
            raise Failure("timed binary changed during evaluation")
        session.remaining()
        data["correctness"]["state"] = "passed"
        data["summary"] = {"trials": len(data["timing"]),
                           "median_roi_seconds": statistics.median(t["duration_s"] for t in data["timing"]),
                           "by_source_position": [{"source_position": i, "source": source,
                               "median_roi_seconds": statistics.median(t["duration_s"] for t in data["timing"] if t["source_position"] == i)}
                               for i, source in enumerate(sources)], "gain_claim": False}
        session.finish()
        data["outcome"] = {"state": "complete", "stage": "evaluation", "reason": None}
    except (Failure, StageFailure, Stopped, OSError, ValueError, subprocess.SubprocessError) as error:
        if isinstance(error, Failure) and "persisted, but query indexing failed" in str(error):
            raise
        state = "interrupted" if isinstance(error, Stopped) else error.state if isinstance(error, StageFailure) else "failed"
        stage = session.current["stage"] if session and session.current else "validation"
        data["outcome"] = {"state": state, "stage": stage, "reason": str(error)}
        if session and session.current and session.current["state"] == "running":
            session.current.update(state=state, finished=_now(), reason=str(error))
    finally:
        if session:
            session.kill()
            session.restore_handlers()
    return workflow.persist(args.records, data, getattr(args, "db", None))
