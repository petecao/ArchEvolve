"""Durable native kernel evaluation with evaluator-owned result checking.

Updated: 2026-09-26. Real timing, fixture timing, and profiling remain distinct.
2026-10-03 ET (ticket 38): the entry point, ROI, trusted driver, trial format and
independent result check come from the candidate kernel's plug-in
(``swdb.kernels``); BFS keeps its exact former constants and verifier.
2026-10-04 ET (ticket 63): a protocol (or unprotocoled request) that pins
``swdb.native.evaluator.scalable.v2`` takes the scalable BFS path of
``swdb.bfs_native_scalable`` (mmap SG driver, compiled verifier). Everything else,
including every v1 protocol and record, keeps this module's v1 behavior.
"""

import copy
import datetime
import hashlib
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
from bisect import bisect_left
from pathlib import Path

from swdb import artifacts, kernels, paths, profile, workflow
from swdb import bfs_native_scalable as scalable
from swdb.cli import Failure, _require_valid
from swdb.store import Store
from swdb.vocab import load_all

# BFS aliases kept for scripts that pin the BFS driver template; new code asks
# the kernel plug-in (kernels.BFS.native_roi / native_driver).
ROI = "bfs.complete_call.v1"
DRIVER = paths.HOME / "tools" / "bfs_native" / "driver.cc.in"
MAX_REQUEST_BYTES = 10 * 1024 * 1024
MAX_VERTICES = 2_000_000
MAX_DIRECTED_EDGES = 32_000_000
MAX_GRAPH_BYTES = 512 * 1024 * 1024
RUNTIME_INHERITED = ("OMP_THREAD_LIMIT", "OMP_WAIT_POLICY", "GOMP_SPINCOUNT", "GOMP_CPU_AFFINITY")


def controlled_environment(threads):
    return {"OMP_NUM_THREADS": str(_integer(threads, "threads")), "OMP_DYNAMIC": "FALSE",
            "OMP_PROC_BIND": "close", "OMP_PLACES": "cores"}


def validate_runtime_policy(policy, threads):
    """Validate declared runtime inputs; null means unset, never unknown."""
    controlled = controlled_environment(threads)
    if not isinstance(policy, dict) or set(policy) != {"version", "environment"} or type(policy["version"]) is not int or policy["version"] != 1:
        raise Failure("native_runtime requires version 1 and its exact environment map")
    environment = policy["environment"]
    if not isinstance(environment, dict) or set(environment) != set(controlled) | set(RUNTIME_INHERITED):
        raise Failure("native_runtime requires all eight declared runtime inputs")
    if any(value is not None and (not isinstance(value, str) or not value or "\0" in value or len(value) > 4096)
           for value in environment.values()):
        raise Failure("native_runtime values must be nonempty strings or explicit null")
    if any(environment[key] != value for key, value in controlled.items()):
        raise Failure("native_runtime controlled inputs differ from the declared threads/binding")
    limit = environment['OMP_THREAD_LIMIT']
    if limit is not None and (not re.fullmatch(r'\s*\+?[0-9]+\s*', limit, re.ASCII)
                              or not threads <= int(limit) <= 2**32 - 1):
        raise Failure("native_runtime OMP_THREAD_LIMIT must be a positive 32-bit integer at least the declared threads")
    waiting = environment['OMP_WAIT_POLICY']
    if waiting is not None and not re.fullmatch(r'\s*(ACTIVE|PASSIVE)\s*', waiting, re.ASCII | re.IGNORECASE):
        raise Failure("native_runtime OMP_WAIT_POLICY must be ACTIVE, PASSIVE, or unset")
    return policy


def runtime_environment(threads, policy=None, *, environ=None, required=False):
    """Construct one child environment and retain exactly its eight runtime inputs."""
    environment = dict(os.environ if environ is None else environ)
    if policy is None:
        if required:
            raise Failure("native runtime inputs are unknown; a new supported calibration/protocol is required")
        policy = {"version": 1, "environment": {**controlled_environment(threads),
                  **{key: environment.get(key) for key in RUNTIME_INHERITED}}}
    validate_runtime_policy(policy, threads)
    for key, value in policy["environment"].items():
        if value is None:
            environment.pop(key, None)
        else:
            environment[key] = value
    return environment, copy.deepcopy(policy)


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


def observation_bytes(path, limit, label):
    """Bind an observation hash to exactly the bounded bytes being checked."""
    path = Path(path)
    if not path.is_file() or path.is_symlink() or path.stat().st_size > limit:
        raise StageFailure("missing_observation", f"{label} missing, unsafe, or oversized")
    with path.open("rb") as handle:
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise StageFailure("missing_observation", f"{label} exceeds its byte bound")
    return raw, hashlib.sha256(raw).hexdigest()


def json_observation(path, limit, label):
    raw, digest = observation_bytes(path, limit, label)
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise StageFailure("missing_observation", f"{label} must be a JSON object")
    return value, digest


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
        if path.stat().st_size > MAX_GRAPH_BYTES:
            raise Failure("graph_file exceeds the native evaluator's 512 MiB input limit")
        # Hash exactly the bytes supplied to the parser. Separate hash/read opens
        # can associate changed adjacency with an earlier representation hash.
        with path.open("rb") as handle:
            raw = handle.read(MAX_GRAPH_BYTES + 1)
        if len(raw) > MAX_GRAPH_BYTES:
            raise Failure("graph_file exceeds the native evaluator's 512 MiB input limit")
        actual = hashlib.sha256(raw).hexdigest()
        if workload.get("graph_sha256") != actual:
            raise Failure("graph_file content does not match graph_sha256")
        graph = json.loads(raw)
        representation = {"kind": "json_graph", "path": str(path), "sha256": actual}
    if not isinstance(graph, dict):
        raise Failure("workload requires graph or a hashed graph_file")
    n = _integer(graph.get("num_vertices"), "graph.num_vertices", maximum=MAX_VERTICES)
    directed = graph.get("directed")
    if not isinstance(directed, bool):
        raise Failure("graph.directed must be explicit boolean")
    if "adjacency" in graph:
        if "edges" in graph:
            raise Failure("graph must use either edges or adjacency")
        adjacency = graph["adjacency"]
        if not isinstance(adjacency, list) or len(adjacency) != n:
            raise Failure("graph.adjacency must contain one bounded row per vertex")
        count = 0
        for u, row in enumerate(adjacency):
            if not isinstance(row, list):
                raise Failure("graph.adjacency rows must be lists")
            count += len(row)
            if count > MAX_DIRECTED_EDGES:
                raise Failure("normalized graph exceeds the supported directed edge limit")
            previous = -1
            for v in row:
                _integer(v, "adjacency destination", minimum=0, maximum=n-1)
                if v == u or v <= previous:
                    raise Failure("graph.adjacency must be sorted, distinct, and free of self loops")
                previous = v
        if not directed:
            for u, row in enumerate(adjacency):
                for v in row:
                    reverse = adjacency[v]
                    position = bisect_left(reverse, u)
                    if position == len(reverse) or reverse[position] != u:
                        raise Failure("undirected graph.adjacency must be symmetric")
    else:
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


def read_canonical_graph(path):
    """Read the evaluator's bounded sorted adjacency without edge-pair objects."""
    path = Path(path)
    if path.stat().st_size > MAX_GRAPH_BYTES:
        raise Failure("canonical graph exceeds the native evaluator's 512 MiB input limit")
    with path.open() as handle:
        header = handle.readline(256).split()
        if len(header) != 4 or header[0] != "SWDBGRAPH1":
            raise Failure("canonical graph representation malformed")
        try:
            n, count, directed = map(int, header[1:])
        except ValueError:
            raise Failure("canonical graph header must contain integers") from None
        _integer(n, "canonical graph vertices", maximum=MAX_VERTICES)
        _integer(count, "canonical graph edges", minimum=0, maximum=MAX_DIRECTED_EDGES)
        if directed not in (0, 1):
            raise Failure("canonical graph directed flag must be zero or one")
        adjacency = [[] for _ in range(n)]
        previous_source = -1
        for _ in range(count):
            try:
                u, v = map(int, handle.readline(64).split())
            except ValueError:
                raise Failure("canonical graph edge must contain two integers") from None
            _integer(u, "canonical edge source", minimum=0, maximum=n-1)
            if u < previous_source:
                raise Failure("canonical graph source rows must be ordered")
            adjacency[u].append(v)
            previous_source = u
        if handle.read(1):
            raise Failure("canonical graph has trailing data")
    return canonical_graph({"graph": {"num_vertices": n, "directed": bool(directed),
                                      "adjacency": adjacency}})


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


def _compile_settings(request, candidate, root, plugin=None):
    context = candidate["context"]
    refs = context["code"]
    ref = refs[0] if isinstance(refs, list) else refs
    if ref.get("root") != "application":
        raise Failure("native evaluator requires an application-backed candidate")
    source = root / artifacts.relative_path(ref["path"])
    if not source.is_file():
        raise Failure(f"candidate {(plugin or kernels.BFS).name} translation unit is missing")
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


def _protect_driver_macros(candidate, root, *, extra_text="", driver=None):
    """Reject preprocessor substitution of the trusted driver after source inclusion.

    Scan all UTF-8 candidate inputs, including .inc files and extensionless
    headers. Splicing and comment removal precede directive recognition, matching
    the relevant preprocessing phases. This does not claim to sandbox hostile C++.
    """
    template = Path(driver or DRIVER).read_text()
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
    if request.get("roi") not in kernels.native_rois():
        raise Failure(f"native evaluator only supports the protected ROI {' or '.join(kernels.native_rois())}")
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
    steps = evaluation_steps(args)
    while True:
        try:
            next(steps)
        except StopIteration as finished:
            return finished.value


def evaluation_steps(args, *, request=None, pairing=None, reuse=None, deadline=None):
    """Shared collector: yield after preparation and each independently checked trial.

    A paired coordinator supplies the next scheduled slot with send(). Serial
    evaluation consumes the same steps without supplying pairing metadata.
    """
    store = _require_valid(args.records)
    if request is None:
        raw = Path(args.file).read_text()
        if len(raw.encode()) > MAX_REQUEST_BYTES:
            raise Failure("evaluation request exceeds 10 MiB")
        request = workflow.message_from_text(raw)
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
        plugin = kernels.get(implementation.get("kernel"))
        if plugin is None:
            raise Failure(f"native evaluation has no kernel plug-in for {implementation.get('kernel')!r}; "
                          + kernels.BFS.native_entry_error())
        if not plugin.native_entry_supported(implementation, candidate):
            raise Failure(plugin.native_entry_error())
        if request["roi"] != plugin.native_roi:
            raise Failure(f"native {plugin.name} evaluation only supports the protected ROI {plugin.native_roi}")
        evaluator = scalable.request_evaluator(store, request)
        v2 = evaluator == scalable.EVALUATOR_V2
        if v2 and getattr(plugin, "native_scalable_verifier", None) != scalable.VERIFIER_V2:
            raise Failure(f"{scalable.EVALUATOR_V2} supports the BFS kernel only")
        driver_template = scalable.DRIVER_V2 if v2 else plugin.native_driver
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
        if host == "mbit10" and threads > 16:
            raise Failure("mbit10 evaluations permit at most 16 threads per socket job")
        lane = profile._verified_lane(machine, getattr(args, "lane", None))
        preflight = None
        if host == 'mbit10':
            from swdb.dispatch_preflight import check
            preflight = check(args.runs_dir, lane)
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
        if deadline is not None:
            session.deadline = min(session.deadline, deadline)
        if pairing is None:
            session.install_handlers()
        session.begin("source_resolution")
        root = artifacts.verify(candidate["artifact"])
        artifacts.check_protections(root, candidate["protections"])
        _protect_driver_macros(candidate, root, driver=driver_template)
        compiler, flags, includes, source, adapter = _compile_settings(request, candidate, root, plugin)
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
                           "function": plugin.native_function,
                           "source_revision": candidate["context"]["source"]["commit"],
                           "application": candidate["context"]["application"], "adapter": adapter,
                           "target": machine["id"], "machine_sha256": artifacts.digest(machine),
                           "threads": threads, "sources": sources, "repetitions": repetitions,
                           "roi": plugin.native_roi, "protocol": request.get("protocol"), "basis": "measured",
                           "process_policy": "one fresh process per source and repetition; graph construction before ROI",
                           "verifier": scalable.VERIFIER_V2 if v2 else plugin.native_verifier,
                           "verifier_sha256": artifacts.file_hash(scalable.VERIFIER_SOURCE) if v2 else plugin.native_verifier_sha256(),
                           "backend_configuration": request.get("target_configuration", {}),
                           "instrumentation": {"template_sha256": artifacts.file_hash(driver_template), "treatment": "included"},
                           "host": host, "architecture": platform.machine(), "lane": lane,
                           "load_average": list(os.getloadavg()), "budget": budget}
        if v2:
            data["context"]["evaluator"] = evaluator
            data["context"]["process_policy"] = ("one fresh process per source and repetition; graph mapped "
                                                 "from the registered SG file before ROI")
        if preflight is not None:
            data['context']['dispatch_preflight'] = preflight
        if pairing is not None:
            data["context"]["pairing"] = copy.deepcopy(pairing)
        if host == 'mbit10' and not request.get('fixture'):
            from swdb.host_observation import attach
            attach(data, folder, paths.HOME, total_seconds=min(15, session.remaining()))
        session.finish()
        session.begin("workload_resolution")
        supplied_workload = request.get("workload")
        registered_representation = None
        if v2:
            workload = scalable.resolve_workload(store, supplied_workload, data["context"]["application"])
            canonical, graph_input = None, workload["graph_input"]
            vertices = workload["num_vertices"]
        elif isinstance(supplied_workload, dict) and set(supplied_workload) == {"id"}:
            try:
                from swdb.bfs_protocol import materialize_workload
            except ImportError:
                raise Failure("registered-workload materialization is unavailable") from None
            supplied_workload = materialize_workload(store, supplied_workload["id"])
            registered_representation = supplied_workload["registered_representation"]
        if not v2:
            canonical, workload = canonical_graph(supplied_workload)
            if registered_representation is not None:
                workload["representation"] = registered_representation
            vertices = canonical["num_vertices"]
        if any(source >= vertices for source in sources):
            raise Failure(f"requested {plugin.name} source outside canonical graph")
        if v2:
            graph_path = Path(graph_input["path"])
            workload.update(sources=sources)
        else:
            graph_path = folder / "graph.swdb"
            with graph_path.open("w") as output:
                output.write(f"SWDBGRAPH1 {canonical['num_vertices']} {workload['num_directed_edges']} {int(canonical['directed'])}\n")
                for u, neighbors in enumerate(canonical["adjacency"]):
                    for v in neighbors:
                        output.write(f"{u} {v}\n")
            workload.update(sources=sources, canonical_path=str(graph_path), canonical_file_sha256=artifacts.file_hash(graph_path))
        data["context"]["workload"] = workload
        frozen_runtime = None
        if request.get("protocol"):
            try:
                from swdb.bfs_protocol import validate_protocol_for_evaluation
            except ImportError:
                raise Failure("frozen protocol validation is unavailable") from None
            data["context"]["protocol_binding"] = validate_protocol_for_evaluation(
                store, request, candidate, actual_build={"compiler": compiler, "flags": flags, "adapter": adapter},
                actual_lane=lane, actual_instrumentation=data["context"]["instrumentation"],
                actual_collection=pairing["collection"] if pairing else None)
            frozen_runtime = store.get(request["protocol"], "protocol")["settings"].get("native_runtime")
        env, actual_runtime = runtime_environment(threads, frozen_runtime,
            required=bool(request.get("protocol")) and request.get("fixture") is not True)
        session.finish()
        wrapper = build_folder / "native_driver.cc"
        template = Path(driver_template).read_text()
        wrapper.write_text(template.replace("#include SWDB_SOURCE_INCLUDE", "#include " + json.dumps(str(source))))
        binary = build_folder / plugin.native_binary
        command = [compiler, *flags, *(f"-I{p}" for p in includes), str(wrapper), "-o", str(binary)]
        data["build"] = {"directory": str(build_folder), "compiler": compiler, "flags": flags, "command": command,
                         "wrapper_sha256": artifacts.file_hash(wrapper), "template_sha256": artifacts.file_hash(driver_template)}
        if reuse is None:
            version_log = session.execute("compiler_identity", [compiler, "--version"], min(30, budget["build_seconds"]))
            data["build"]["compiler_version"] = version_log.read_text(errors="replace").splitlines()[:2]
            session.execute("build", command, budget["build_seconds"])
        else:
            if (reuse["candidate"] != candidate["id"] or reuse["build"]["compiler"] != compiler
                    or reuse["build"]["flags"] != flags or reuse["build"].get("native_runtime") != actual_runtime):
                raise Failure("A/A executable reuse requires identical candidate and build settings")
            session.begin("build_reuse", evaluation=reuse["id"])
            data["build"] = copy.deepcopy(reuse["build"])
            data["build"]["reused_from_evaluation"] = reuse["id"]
            binary = Path(data["build"]["binary"])
            if artifacts.file_hash(binary) != data["build"]["binary_sha256"]:
                raise Failure("reused A/A binary changed after preparation")
            session.finish()
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise Failure("build did not produce an executable")
        data["build"].update(binary=str(binary), binary_sha256=artifacts.file_hash(binary))
        artifacts.verify(candidate["artifact"])
        data["build"]["execution_environment"] = controlled_environment(threads)
        data["build"]["native_runtime"] = actual_runtime
        if v2:
            # The evaluator's own result check: compiled from repository source with
            # fixed flags and the host C++ compiler, never with request settings.
            identity = scalable.verifier_identity()
            verifier_binary = build_folder / "bfs-verify"
            verifier_command = scalable.build_command(verifier_binary)
            session.execute("verifier_build", verifier_command, min(300, budget["build_seconds"]))
            if not verifier_binary.is_file() or artifacts.file_hash(scalable.VERIFIER_SOURCE) != identity["source_sha256"]:
                raise Failure("compiled verifier build failed or its source changed")
            data["build"]["verifier"] = {**identity, "compiler": verifier_command[0], "command": verifier_command,
                                         "binary": str(verifier_binary),
                                         "binary_sha256": artifacts.file_hash(verifier_binary)}
        session.save()
        slot = yield data
        for repetition in range(repetitions):
            for position, source in enumerate(sources):
                if pairing is not None and (not isinstance(slot, dict)
                        or slot.get("repetition") != repetition or slot.get("source_position") != position
                        or slot.get("source") != source or slot.get("role") != pairing["role"]):
                    raise Failure("paired collector received an unexpected scheduled trial")
                trial = len(data["timing"])
                output = folder / f"trial-{repetition}-{position}.json"
                if artifacts.file_hash(binary) != data["build"]["binary_sha256"]:
                    raise Failure("timed binary changed after build")
                if v2:
                    if artifacts.file_hash(graph_path) != graph_input["sha256"]:
                        raise Failure("registered SG input changed before execution")
                    parents_path = folder / f"trial-{repetition}-{position}.parents.i32"
                    command = [str(binary), str(graph_path), str(graph_input["offset_bytes"]), str(source),
                               str(output), str(parents_path)]
                else:
                    if artifacts.file_hash(graph_path) != workload["canonical_file_sha256"]:
                        raise Failure("protected canonical graph changed before execution")
                    command = [str(binary), str(graph_path), str(source), str(output)]
                session.execute("execution", command,
                                budget["run_seconds"], env, repetition=repetition, source_position=position, source=source)
                executed = copy.deepcopy(session.current)
                session.begin("correctness", repetition=repetition, source_position=position, source=source)
                if v2:
                    observed, output_hash = json_observation(output, scalable.TRIAL_RECORD_LIMIT, "trial record")
                    problem = scalable.check_trial_record(observed, source, threads, plugin.native_roi, vertices)
                    if problem:
                        raise StageFailure(*problem)
                else:
                    observed, output_hash = json_observation(output, plugin.native_output_limit(canonical["num_vertices"]),
                                                            "parent/timing output" if plugin is kernels.BFS else "result/timing output")
                    if observed.get("format") != plugin.native_trial_format:
                        raise StageFailure("missing_observation", "native trial output has the wrong format")
                    if (type(observed.get("source")) is not int or observed["source"] != source
                            or observed.get("roi") != plugin.native_roi or type(observed.get("configured_threads")) is not int
                            or observed["configured_threads"] != threads):
                        raise StageFailure("incompatible", "native output source, ROI, or configured threads differ from request")
                duration = observed.get("duration_s")
                if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
                    raise StageFailure("missing_observation", "native ROI duration must be positive and finite")
                observation = {"source": source, "source_position": position, "repetition": repetition,
                               "duration_s": duration, "roi": plugin.native_roi, "basis": "measured", "quantity": "native_roi_wall_seconds",
                               "binary_sha256": data["build"]["binary_sha256"], "output": str(output),
                               "output_sha256": output_hash, "verified": False,
                               "evidence_kind": data["evidence_kind"]}
                if pairing is not None:
                    observation["pairing"] = {**copy.deepcopy(slot), "pair_id": pairing["pair_id"],
                        "started": executed["started"], "finished": executed["finished"],
                        "execution_log": executed["log"], "execution_log_sha256": executed["log_sha256"]}
                data["timing"].append(observation)
                if v2:
                    if not parents_path.is_file() or parents_path.is_symlink():
                        raise StageFailure("missing_observation", "parent vector output missing or unsafe")
                    parents_hash = artifacts.file_hash(parents_path)
                    if artifacts.file_hash(graph_path) != graph_input["sha256"]:
                        raise Failure("registered SG input changed before verification")
                    if artifacts.file_hash(data["build"]["verifier"]["binary"]) != data["build"]["verifier"]["binary_sha256"]:
                        raise Failure("compiled verifier changed after build")
                    check = scalable.run_verifier(data["build"]["verifier"]["binary"], graph_input, source,
                                                  parents_path, max(1.0, min(budget["run_seconds"] * 5, session.remaining())))
                    if artifacts.file_hash(parents_path) != parents_hash:
                        raise Failure("parent vector changed during verification")
                    retained, raw_hash, gz_hash = scalable.compress_parents(parents_path)
                    observation.update(parents_output=str(retained), parents_sha256=raw_hash, parents_gzip_sha256=gz_hash)
                    check["parents_sha256"] = raw_hash
                else:
                    check = plugin.check_native_trial(canonical["adjacency"], source, observed,
                                                      application=data["context"]["application"])
                session.remaining()
                check.update(source=source, source_position=position, repetition=repetition, trial=trial,
                             output_sha256=observation["output_sha256"], binary_sha256=observation["binary_sha256"],
                             graph_sha256=workload["canonical_sha256"], verifier=data["context"]["verifier"])
                if pairing is not None:
                    check["pairing"] = copy.deepcopy(observation["pairing"])
                data["correctness"]["checks"].append(check)
                observation["verified"] = check["passed"]
                session.finish("complete" if check["passed"] else "failed", reason=check["reason"])
                if not check["passed"]:
                    data["correctness"]["state"] = "failed"
                    raise StageFailure("incorrect", check["reason"])
                slot = yield data
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
