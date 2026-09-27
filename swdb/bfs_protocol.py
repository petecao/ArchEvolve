"""Canonical BFS workloads and immutable comparison policy. Updated 2026-09-26.

2026-09-27 (R10): one simulator execution may bind to several frozen protocols
only when every protocol-relevant identity actually matches. The execution names
each additional protocol explicitly (``shared_protocols``) and retains one exact
binding per protocol; aggregation and comparison select the binding they use.
"""

import copy
import datetime
import hashlib
import json
import math
import random
import re
import statistics
import struct
from bisect import bisect_left
from pathlib import Path

from swdb import artifacts, workflow
from swdb.cli import Failure, _require_valid
from swdb.problems import Problem

NORMALIZATION = {"remove_self_loops": True, "deduplicate": True, "sort_neighbors": True,
                 "symmetrize_undirected": True}
MAX_EDGES = 5_000_000
MAX_VERTICES = 2_000_000
MAX_FILE_BYTES = 512 * 1024 * 1024


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _fail(condition, message):
    if not condition:
        raise Failure(message)


def _integer(value, name, minimum=1):
    _fail(type(value) is int and value >= minimum, f"{name} must be an integer >= {minimum}")
    return value


def _positive(value, name, minimum=0):
    _fail(type(value) in (int, float) and math.isfinite(value) and value > minimum,
          f"{name} must be finite and greater than {minimum}")
    return value


def _text(value, name):
    _fail(isinstance(value, str) and bool(value.strip()), f"{name} must be nonempty text")
    return value


def _request(args):
    try:
        _fail(args.file.stat().st_size <= 10 * 1024 * 1024, "request exceeds 10 MiB")
        request = workflow.message_from_text(args.file.read_text())
    except OSError as exc:
        raise Failure(f"cannot read request: {exc}") from None
    _fail(isinstance(request, dict), "request must be a mapping")
    _fail(not request.get("parse_error"), str(request.get("parse_error")))
    _fail(request.get("message_version") == "1.0", "request needs message_version 1.0")
    _fail(isinstance(request.get("id"), str) and re.fullmatch(r"[a-z0-9][a-z0-9._-]*", request["id"]),
          "request needs a valid record id")
    return request


def _get(store, rid, kind):
    data = store.get(rid, kind)
    _fail(data is not None, f"{kind} {rid!r} does not exist")
    return data


def _canonical(graph):
    from swdb.bfs_native import canonical_graph

    return canonical_graph({"graph": graph})[0]


def _sg_graph(raw, width, edge_limit=None):
    """Read the actual unweighted GAPBS binary format, including inverse CSR."""
    offset_format = "i" if width == 4 else "q"
    _fail(len(raw) >= 1 + 2 * width and raw[0] in (0, 1), "invalid SG header")
    directed = bool(raw[0])
    m, n = struct.unpack_from("<" + offset_format * 2, raw, 1)
    _fail(0 < n <= MAX_VERTICES and 0 <= m <= (MAX_EDGES if edge_limit is None else edge_limit),
          "SG dimensions exceed parser limits")
    block_bytes = (n + 1) * width + m * 4
    _fail(len(raw) == 1 + 2 * width + block_bytes * (2 if directed else 1), "truncated or trailing SG data")

    def csr(position):
        offsets = [item[0] for item in struct.iter_unpack("<" + offset_format, raw[position:position + (n+1)*width])]
        position += (n + 1) * width
        _fail(offsets[0] == 0 and offsets[-1] == m and all(0 <= a <= b <= m for a, b in zip(offsets, offsets[1:])),
              "invalid SG CSR offsets")
        rows = [[item[0] for item in struct.iter_unpack("<i", memoryview(raw)[position+offsets[u]*4:position+offsets[u+1]*4])]
                for u in range(n)]
        for u, row in enumerate(rows):
            _fail(all(0 <= v < n and v != u for v in row), "SG neighbor is outside graph or a self loop")
            _fail(all(a < b for a, b in zip(row, row[1:])), "SG adjacency must already be sorted and deduplicated")
        return rows

    position = 1 + 2 * width
    outgoing = csr(position)
    if directed:
        incoming = csr(position + block_bytes)
        # Both CSR blocks have exactly m distinct arcs. Membership therefore
        # proves inverse equivalence without constructing another edge list.
        for v, row in enumerate(incoming):
            for u in row:
                at = bisect_left(outgoing[u], v)
                _fail(at < len(outgoing[u]) and outgoing[u][at] == v,
                      "SG inverse adjacency does not match outgoing edges")
    return {"num_vertices": n, "directed": directed,
            "adjacency": outgoing}


def _representation(rep, normalization, parser=None, allow_streaming=True):
    from swdb.bfs_native import MAX_DIRECTED_EDGES

    _fail(isinstance(rep, dict), "representation must be a mapping")
    _text(rep.get("id"), "representation.id")
    path = Path(_text(rep.get("path"), "representation.path"))
    _fail(path.is_absolute() and path.is_file() and not path.is_symlink(), "representation must be an absolute regular file")
    size = path.stat().st_size
    actual = artifacts.file_hash(path)
    _fail(rep.get("sha256") == actual, "representation content hash differs from its declaration")
    kind = rep.get("format")
    _fail(normalization == NORMALIZATION, "unsupported graph normalization; use the declared simple-graph policy")
    description = {key: rep[key] for key in ("id", "path", "sha256", "format", "application") if key in rep}
    if kind in {"gapbs_sg32le", "gapbs_sg64le"}:
        width = 4 if kind == "gapbs_sg32le" else 8
        with path.open("rb") as handle:
            header = handle.read(1 + width*2)
        dimensions = struct.unpack_from("<" + ("i" if width == 4 else "q")*2, header, 1) if len(header) == 1+width*2 else (0, 0)
        edge_limit = MAX_EDGES if allow_streaming else MAX_DIRECTED_EDGES
        large = size > MAX_FILE_BYTES or dimensions[0] > edge_limit or dimensions[1] > MAX_VERTICES
        if large or parser is not None:
            _fail(allow_streaming, "registered graph exceeds native materialization limits; use its external SG representation")
            from swdb.sg_stream import inspect
            canonical = inspect(path, width, parser)
            _fail(artifacts.file_hash(path) == actual, "representation changed during streaming verification")
            description.update(canonical_sha256=canonical["canonical_sha256"], bytes=size,
                               loader="swdb.gapbs-representation.v1", adjacency_verified=True,
                               verification=canonical["verification"])
            return canonical, description
    _fail(size <= MAX_FILE_BYTES, "non-SG representation exceeds the 512 MiB parser limit")
    raw = path.read_bytes()
    _fail(hashlib.sha256(raw).hexdigest() == actual, "representation changed during materialization")
    try:
        if kind in {"gapbs_sg32le", "gapbs_sg64le"}:
            graph = _sg_graph(raw, 4 if kind == "gapbs_sg32le" else 8, edge_limit)
        elif kind == "json_graph":
            graph = json.loads(raw)
        elif kind == "edge_list":
            n = _integer(rep.get("num_vertices"), "representation.num_vertices")
            _fail(isinstance(rep.get("directed"), bool), "edge-list directed flag must be explicit")
            edges = []
            for line in raw.decode().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                tokens = line.split()
                _fail(len(tokens) == 2, "edge-list lines must contain exactly two vertex IDs")
                edges.append([int(tokens[0]), int(tokens[1])])
                _fail(len(edges) <= MAX_EDGES, "edge list exceeds the parser edge limit")
            graph = {"num_vertices": n, "directed": rep["directed"], "edges": edges}
        else:
            raise Failure(f"unsupported graph representation {kind!r}")
    except (ValueError, UnicodeError, struct.error) as exc:
        raise Failure(f"invalid graph representation: {exc}") from None
    if kind not in {"gapbs_sg32le", "gapbs_sg64le"}:
        _fail(isinstance(graph, dict) and isinstance(graph.get("edges"), list)
              and len(graph["edges"]) <= MAX_EDGES, "graph exceeds the parser edge limit or has no edge list")
    canonical = _canonical(graph)
    if kind == "edge_list":
        description.update(num_vertices=graph["num_vertices"], directed=graph["directed"])
    description.update(canonical_sha256=artifacts.digest(canonical), bytes=len(raw),
                       loader="swdb.gapbs-representation.v1", adjacency_verified=True)
    return canonical, description


def _identity_payload(data):
    fields = ["requested_id", "version", "supersedes", "invalidated_comparisons"]
    fields += ["definition"] if data["kind"] == "workload" else ["settings", "workload_identities", "frozen_at", "state"]
    return {key: data[key] for key in fields}


def verify_immutable(data):
    try:
        fingerprint = artifacts.digest(_identity_payload(data))
    except (KeyError, TypeError, ValueError):
        raise Failure("incomplete immutable workload/protocol identity") from None
    _fail(fingerprint == data.get("identity_sha256") and data["id"] == data["requested_id"] + "." + fingerprint[:16],
          f"{data['kind']} content changed after registration/freeze")
    return fingerprint


def validate_record(record, ctx):
    """Cross-record validation hook: raw `add` cannot admit a mismatched freeze hash."""
    try:
        verify_immutable(record.data)
        _fail(not any(other.id != record.id and other.data.get("requested_id") == record.data.get("requested_id")
                      and other.data.get("version") == record.data.get("version") for other in ctx.store.of_kind(record.kind)),
              "immutable logical name/version already exists; use a new version with supersedes")
        if record.kind == "protocol":
            _validate_settings(record.data["settings"], ctx.store)
            for wid, digest in record.data["workload_identities"].items():
                _fail(verify_immutable(_get(ctx.store, wid, "workload")) == digest, "frozen workload identity changed")
    except (Failure, KeyError, TypeError, ValueError) as exc:
        yield Problem(record.rel, "identity_sha256", str(exc))


def _version(request, store, kind):
    version = _integer(request.get("version", 1), "version")
    previous = request.get("supersedes")
    invalidated = []
    if previous:
        old = _get(store, previous, kind)
        verify_immutable(old)
        _fail(version > old["version"], "a replacement must increase the version")
        for row in store.of_kind("comparison_result"):
            comparison = row.data
            protocol = store.get(comparison.get("protocol"), "protocol")
            if comparison.get("protocol") == previous or (kind == "workload" and protocol and previous in protocol["workload_identities"]):
                invalidated.append(row.id)
    return version, previous, sorted(invalidated)


def _save_immutable(args, request, kind, **fields):
    store = _require_valid(args.records)
    version, previous, invalidated = _version(request, store, kind)
    prior_names = [row for row in store.of_kind(kind) if row.data.get("requested_id") == request["id"]]
    _fail(not prior_names or previous in {row.id for row in prior_names},
          "changing an existing workload/protocol name requires supersedes and a newer version")
    _fail(version == 1 or previous is not None, "version greater than one requires supersedes")
    data = workflow.record(kind, request["id"], requested_id=request["id"], version=version,
                           supersedes=previous, invalidated_comparisons=invalidated, **fields)
    data["identity_sha256"] = artifacts.digest(_identity_payload(data))
    data["id"] += "." + data["identity_sha256"][:16]
    _fail(store.get(data["id"]) is None, "immutable record already exists; use get or a new version")
    return workflow.persist(args.records, data, getattr(args, "db", None), create=True)


def register_workload(args):
    request = _request(args)
    store = _require_valid(args.records)
    kernel = _get(store, request.get("kernel"), "kernel")
    _fail(kernel["id"] == "gapbs-bfs", "BFS workload registration requires the shared BFS kernel")
    family = _text(request.get("family"), "family")
    generator = request.get("generator")
    _fail(isinstance(generator, dict) and isinstance(generator.get("parameters"), dict), "generator parameters are required")
    _text(generator.get("name"), "generator.name")
    _text(generator.get("revision"), "generator.revision")
    _fail(request.get("normalization") == NORMALIZATION, "normalization must declare the supported simple graph policy")
    sources = request.get("sources")
    _fail(isinstance(sources, list) and len(sources) > 0, "actual ordered BFS sources are required")
    representations = request.get("representations")
    _fail(isinstance(representations, list) and representations, "representations must be a nonempty list")
    rows, reference, ids = [], None, set()
    for rep in representations:
        canonical, row = _representation(rep, request["normalization"], request.get("parser"))
        _get(store, rep.get("application"), "application")
        expected_format = {"gapbs": "gapbs_sg64le", "dx100-gapbs": "gapbs_sg32le"}.get(rep["application"])
        if row["format"].startswith("gapbs_sg") and expected_format:
            _fail(row["format"] == expected_format, "serialized offset width conflicts with the application's loader")
        _fail(row["id"] not in ids, "representation IDs must be unique")
        ids.add(row["id"])
        if reference is None:
            reference = canonical
        reference_hash = reference.get("canonical_sha256") if reference.get("_streaming") else artifacts.digest(reference)
        _fail(row["canonical_sha256"] == reference_hash, "representations do not load equivalent canonical adjacency")
        rows.append(row)
    for source in sources:
        _fail(_integer(source, "source", 0) < reference["num_vertices"], "source vertex is outside the graph")
    if reference.get("_streaming"):
        realized = reference["realized"]
    else:
        degrees = [len(row) for row in reference["adjacency"]]
        incoming = {v for row in reference["adjacency"] for v in row}
        realized = {"num_vertices": reference["num_vertices"], "num_directed_edges": sum(degrees),
                    "directed": reference["directed"],
                    "isolated_vertices": sum(degree == 0 and u not in incoming for u, degree in enumerate(degrees)),
                    "minimum_out_degree": min(degrees), "maximum_out_degree": max(degrees)}
    definition = {"kernel": kernel["id"], "family": family, "generator": generator,
                  "normalization": NORMALIZATION, "sources": sources, "representations": rows,
                  "canonical_sha256": reference_hash, "canonical_format": "swdb.bfs.adjacency.v1",
                  "realized": realized,
                  "metadata_basis": "operator_declared", "adjacency_basis": "parsed_representation"}
    return _save_immutable(args, request, "workload", definition=definition)


def materialize_workload(store, workload_id):
    data = _get(store, workload_id, "workload")
    verify_immutable(data)
    definition = data["definition"]
    canonical, representation = _representation(definition["representations"][0], definition["normalization"], allow_streaming=False)
    _fail(artifacts.digest(canonical) == definition["canonical_sha256"], "registered adjacency changed")
    graph = {"num_vertices": canonical["num_vertices"], "directed": canonical["directed"],
             "adjacency": canonical["adjacency"]}
    return {"id": data["id"], "family": definition["family"], "generator": definition["generator"],
            "graph": graph, "loaded_adjacency_sha256": definition["canonical_sha256"],
            "registered_representation": representation}


def workload_representation(store, workload_id, application):
    """Select the already adjacency-verified serialized input for a backend loader."""
    data = _get(store, workload_id, "workload")
    verify_immutable(data)
    definition = data["definition"]
    matches = [rep for rep in definition["representations"] if rep.get("application") == application
               and rep["format"] in {"gapbs_sg32le", "gapbs_sg64le"}]
    _fail(len(matches) == 1, "workload needs exactly one serialized representation for the selected application")
    rep = matches[0]
    path = Path(rep["path"])
    _fail(path.is_absolute() and path.is_file() and not path.is_symlink()
          and artifacts.file_hash(path) == rep["sha256"], "registered serialized representation is unavailable or changed")
    _fail(rep.get("adjacency_verified") is True and rep["canonical_sha256"] == definition["canonical_sha256"],
          "serialized representation has no compatible loaded-adjacency verification")
    return {"id": data["id"], "workload_sha256": data["identity_sha256"], "canonical_sha256": definition["canonical_sha256"],
            "sources": definition["sources"], "realized": definition["realized"], "representation": copy.deepcopy(rep)}


def _simulation_identity(settings, store, *, required=False, check_files=False):
    """Pin the completed model build while leaving future rewrite binaries open."""
    if settings.get("mode") == "native":
        return None
    identity = settings.get("simulation_identity")
    if identity is None:
        _fail(not required, "simulated protocol lacks simulation_identity; freeze a superseding protocol")
        return None
    _fail(isinstance(identity, dict) and identity.get("version") == "1.0", "unsupported simulation_identity")
    reference = identity.get("model_build", {})
    _fail(isinstance(reference, dict), "simulation_identity.model_build must be a record reference")
    model = _get(store, reference.get("evaluation"), "evaluation")
    _fail(reference.get("sha256") == artifacts.digest(model), "frozen model build record changed")
    _fail(model.get("outcome", {}).get("state") == "complete" and model["outcome"].get("stage") == "build"
          and model.get("evidence_kind") in {"execution", "contract_fixture"}, "frozen model build is incomplete or unclassified")
    details = model.get("build", {}).get("details", {})
    binaries = details.get("binaries", [])
    _fail(isinstance(binaries, list) and all(isinstance(row, dict) for row in binaries), "model build binary inventory is invalid")
    simulator = identity.get("simulator", {})
    _fail(isinstance(simulator, dict) and set(simulator) == {"path", "sha256"}
          and isinstance(simulator["path"], str) and isinstance(simulator["sha256"], str)
          and re.fullmatch(r"[0-9a-f]{64}", simulator["sha256"])
          and any(all(row.get(key) == simulator[key] for key in simulator) for row in binaries),
          "frozen simulator is absent from the model build receipt")
    _fail(all(target["configuration"]["model_revision"] == details.get("revision")
              for target in settings["targets"].values()), "frozen target revision differs from model build")
    if model["evidence_kind"] == "execution":
        _fail(details.get("state") == "completed" and model.get("request", {}).get("fixture") is not True,
              "frozen model build does not contain completed execution evidence")
        _fail(all(target["id"] == model.get("context", {}).get("target") for target in settings["targets"].values()),
              "frozen simulator targets differ from model build target")
        _fail(any(Path(row.get("path", "")).name == "libramulator.so" for row in binaries),
              "frozen model build lacks the Ramulator runtime library identity")
    if check_files:
        references = [simulator] + [row for row in binaries if ".so" in Path(row.get("path", "")).name]
        build = model.get("build", {})
        if model["evidence_kind"] == "execution":
            references.append({"path": build["receipt"], "sha256": build["receipt_sha256"]})
            if build.get("runtime_dependencies"):
                references.append(build["runtime_dependencies"])
        for item in references:
            path = Path(item["path"])
            _fail(path.is_file() and not path.is_symlink() and artifacts.file_hash(path) == item["sha256"],
                  "frozen simulator/runtime/build receipt file is missing or changed")
        if model["evidence_kind"] == "execution":
            _fail(artifacts.digest(json.loads(Path(build["receipt"]).read_text())) == artifacts.digest(details),
                  "frozen model build details differ from its receipt")
    references = settings.get("reference_artifacts")
    reference_mode = settings.get("mode") == "artifact_reference" or all(
        build.get("adapter") == "dx100.author_artifact.v1" for build in settings.get("builds", {}).values())
    _fail(not reference_mode or isinstance(references, dict), "fixed reference protocol requires reference_artifacts for both roles")
    if references is not None:
        _fail(isinstance(references, dict) and set(references) == {"baseline", "candidate"},
              "reference_artifacts requires both roles")
        for role, item in references.items():
            _fail(isinstance(item, dict), "reference_artifacts role must be a source/binary mapping")
            candidate = _get(store, item.get("candidate"), "candidate")
            source = _get(store, candidate.get("source_snapshot"), "source_snapshot")
            _fail(item.get("candidate_sha256") == artifacts.digest(candidate)
                  and item.get("source_snapshot") == source["id"]
                  and item.get("source_snapshot_sha256") == artifacts.digest(source)
                  and item.get("source_artifact_sha256") == candidate.get("artifact", {}).get("sha256"),
                  "frozen reference source identity changed")
            _fail(candidate.get("artifact_role") == "source_baseline" and not candidate.get("proposal"),
                  "fixed reference must retain unchanged catalog source")
            validate_baseline_source(store, candidate)
            binary = item.get("binary", {})
            _fail(isinstance(binary, dict) and set(binary) == {"path", "sha256"}
                  and any(all(row.get(key) == binary[key] for key in binary) for row in binaries),
                  "frozen reference binary is absent from the model build receipt")
    return model


def _simulation_build(settings, store, role, candidate, build, classification, *, check_files=False):
    model = _simulation_identity(settings, store, required=True, check_files=check_files)
    identity = settings["simulation_identity"]
    _fail(model["evidence_kind"] == classification, "simulation and frozen model have different evidence classifications")
    _fail(build.get("model_build") == identity["model_build"]
          and {"path": build.get("simulator"), "sha256": build.get("simulator_sha256")} == identity["simulator"],
          "actual simulator/model build differs from frozen simulation_identity")
    if settings.get("reference_artifacts"):
        reference = settings["reference_artifacts"][role]
        _fail(candidate["id"] == reference["candidate"]
              and {"path": build.get("binary"), "sha256": build.get("binary_sha256")} == reference["binary"],
              "actual reference source/binary differs from frozen reference_artifacts")


ACCELERATOR_CASES = {"executed", "full_tiles", "tail_tiles", "competing_parent_updates"}


def accelerator_cases(check):
    """Typed observations only; a source label or context string is not execution."""
    coverage = check.get("coverage", {})
    if not isinstance(coverage, dict):
        return set()
    counters, units = coverage.get("instruction_counters", {}), coverage.get("completed_trace_units", {})
    if not isinstance(counters, dict) or not isinstance(units, dict):
        return set()
    positive = lambda value: type(value) in (int, float) and math.isfinite(value) and value > 0
    executed = (coverage.get("accelerator_executed") is True
                and any(isinstance(key, str) and key.endswith(".numInst") and positive(value) for key, value in counters.items())
                and all(positive(units.get(unit)) for unit in ("S", "I", "R", "A")))
    if not executed:
        return set()
    observed = {"executed"}
    for name in ACCELERATOR_CASES - {"executed"}:
        item = coverage.get(name)
        if isinstance(item, dict) and item.get("state") == "observed" and type(item.get("count")) is int and item["count"] > 0:
            observed.add(name)
    return observed


def _validate_settings(settings, store, *, require_simulation_identity=False):
    _fail(isinstance(settings, dict), "settings must be a mapping")
    mode = settings.get("mode")
    _fail(mode in {"native", "artifact_reference", "controlled_simulator"}, "unsupported comparison mode")
    _fail(_get(store, settings.get("kernel"), "kernel")["id"] == "gapbs-bfs", "BFS protocols require the shared BFS kernel")
    _text(settings.get("roi"), "roi")
    _integer(settings.get("threads"), "threads")
    if "native_runtime" in settings:
        from swdb.bfs_native import validate_runtime_policy
        _fail(mode == "native", "native_runtime applies only to native protocols")
        validate_runtime_policy(settings["native_runtime"], settings["threads"])
    workloads = settings.get("workloads")
    _fail(isinstance(workloads, list) and workloads and all(isinstance(wid, str) for wid in workloads)
          and len(set(workloads)) == len(workloads), "unique workload IDs are required")
    for wid in workloads:
        workload = _get(store, wid, "workload")
        verify_immutable(workload)
        _fail(workload["definition"]["kernel"] == settings["kernel"], "workload realizes a different kernel")
    for name in ("targets", "builds", "instrumentation"):
        _fail(isinstance(settings.get(name), dict) and set(settings[name]) == {"baseline", "candidate"},
              f"{name} needs explicit baseline and candidate definitions")
    for role in ("baseline", "candidate"):
        target, build = settings["targets"][role], settings["builds"][role]
        _fail(isinstance(target, dict) and isinstance(target.get("configuration"), dict), "target configuration is required")
        _text(target.get("id"), "target.id")
        if mode == "native":
            machine = _get(store, target["id"], "machine")
            _fail(target.get("machine_sha256") == artifacts.digest(machine), "frozen native machine record changed")
            if machine.get("lane_required"):
                _fail(isinstance(target["configuration"].get("lane"), str)
                      and re.fullmatch(r"mbit10-evaluation-node[01]", target["configuration"]["lane"]),
                      "lane-managed native target must freeze its exact socket lane")
        else:
            _fail(all(key in target["configuration"] for key in ("cpu", "cache", "memory", "clock_hz", "model_revision")),
                  "simulated targets must describe CPU, cache, memory, clock, and model revision")
            _positive(target["configuration"]["clock_hz"], "simulated clock_hz")
        _fail(isinstance(build, dict) and isinstance(build.get("flags"), list) and all(isinstance(f, str) for f in build["flags"]),
              "build flags must be an argument list")
        _text(build.get("compiler"), "build.compiler")
        _text(build.get("adapter"), "build.adapter")
        _fail(isinstance(build.get("compiler_version"), list) and build["compiler_version"], "build.compiler_version is required")
        _fail(isinstance(settings["instrumentation"][role], dict) and settings["instrumentation"][role], "instrumentation treatment is required")
        _text(settings["instrumentation"][role].get("treatment"), "instrumentation.treatment")
    if mode == "native":
        _fail(settings["targets"]["baseline"] == settings["targets"]["candidate"], "native comparison requires the same configured target")
    if mode == "controlled_simulator":
        a, b = (settings["targets"][role]["configuration"] for role in ("baseline", "candidate"))
        _fail(all(a[key] == b[key] for key in ("cpu", "cache", "memory", "clock_hz", "model_revision")),
              "controlled simulator comparison must match CPU/cache/memory/clock/model")
    differences = settings.get("differences")
    _fail(isinstance(differences, dict) and set(differences) == {"software", "accelerator", "configuration"}
          and all(isinstance(values, list) and all(isinstance(value, str) and value.strip() for value in values)
                  for values in differences.values()), "software/accelerator/configuration differences must be enumerated")
    if settings["targets"]["baseline"] != settings["targets"]["candidate"]:
        _fail(bool(differences["configuration"] or differences["accelerator"]), "different targets need disclosed differences")
    correctness = settings.get("correctness")
    _fail(isinstance(correctness, dict) and correctness.get("coverage") == "every_timed_trial", "correctness must cover every timed trial")
    _text(correctness.get("verifier"), "correctness.verifier")
    _fail(isinstance(correctness.get("required_cases"), list), "correctness.required_cases is required")
    accelerator = correctness.get("required_accelerator_cases")
    if accelerator is not None:
        _fail(mode != "native" and isinstance(accelerator, dict) and set(accelerator) == {"baseline", "candidate"}
              and all(isinstance(values, list) and all(isinstance(value, str) for value in values)
                      and len(values) == len(set(values)) and set(values) <= ACCELERATOR_CASES for values in accelerator.values()),
              "required_accelerator_cases needs unique supported per-role typed observations")
    fixed_reference = mode == "artifact_reference" or (mode != "native" and all(
        value.get("adapter") == "dx100.author_artifact.v1" for value in settings["builds"].values()))
    if require_simulation_identity and fixed_reference:
        _fail(accelerator is not None and accelerator["baseline"] == [] and "executed" in accelerator["candidate"],
              "author reference must require candidate accelerator execution with no scalar acceleration requirement")
    sampling = settings.get("sampling")
    _fail(isinstance(sampling, dict), "sampling policy is required")
    # R11 (2026-09-27): a simulated policy may fix one replay per ordered source
    # only by declaring the deterministic-replay basis and naming its evidence.
    determinism = sampling.get("determinism")
    if determinism is not None:
        _fail(mode != "native" and isinstance(determinism, dict) and set(determinism) == {"basis", "evidence"}
              and determinism["basis"] == "deterministic_simulator_replay.v1"
              and isinstance(determinism["evidence"], str) and determinism["evidence"].strip(),
              "one-replay sampling needs a simulated deterministic-replay basis and named evidence")
    _integer(sampling.get("repetitions"), "repetitions", 5 if mode == "native" else 1 if determinism else 2)
    _fail(sampling.get("aggregation") == "geomean_source_median_ratio", "unsupported sampling aggregate")
    _fail(sampling.get("warmups") == 0, "this backend currently supports zero untimed warmups; declare zero")
    policy = settings.get("profitability")
    _fail(isinstance(policy, dict), "profitability policy is required")
    _positive(policy.get("minimum_speedup"), "minimum_speedup", 1)
    _positive(policy.get("maximum_relative_spread"), "maximum_relative_spread")
    _fail(policy.get("confidence") == 0.95 and policy.get("bootstrap_resamples") == 2000,
          "supported confidence policy is the 95 percent interval with 2000 bootstrap resamples")
    _integer(policy.get("bootstrap_seed"), "bootstrap_seed", 0)
    collection = sampling.get("collection")
    analysis = sampling.get("analysis")
    if collection is not None or analysis is not None:
        from swdb.bfs_native_pair import ANALYSIS, collection_policy
        _fail(mode == "native" and analysis == ANALYSIS, "paired sampling requires its versioned native block analysis")
        collection_policy(collection)
        _fail(policy["minimum_speedup"] == 1.05 and policy["bootstrap_seed"] == 20260925,
              "paired profitability retains the 1.05 floor and seed 20260925")
    pairs = settings.get("region_pairs", [])
    _fail(isinstance(pairs, list), "region_pairs must be a list")
    for pair in pairs:
        _fail(isinstance(pair, dict), "region correspondence must be a mapping")
        for field in ("semantic_region", "baseline", "candidate"):
            _text(pair.get(field), f"region_pairs.{field}")
        _fail(pair.get("scope") in {"per_invocation", "accumulated"}
              and pair.get("attribution") in {"inclusive", "exclusive"}, "region correspondence needs duration and attribution scopes")
        if pair.get("evidence") is not None:
            native_diagnostic = mode == "native" and pair["evidence"] == "native_diagnostic_profile.v1"
            _fail(native_diagnostic or (mode != "native" and pair["evidence"] == "simulated_diagnostic_profile"),
                  "unsupported region evidence kind")
            collector = pair.get("collector", {})
            if native_diagnostic:
                _fail(isinstance(collector, dict) and collector.get("backend") == "libclang-cindex"
                      and collector.get("clock") == "CLOCK_THREAD_CPUTIME_ID"
                      and all(isinstance(collector.get(key), str) and re.fullmatch(r"[0-9a-f]{64}", collector[key])
                              for key in ("library_sha256", "pass_sha256", "collector_sha256", "runtime_sha256")),
                      "native region pairs require the exact thread CPU diagnostic collector identity")
                repetitions = _integer(pair.get("diagnostic_repetitions"), "diagnostic_repetitions")
                _fail(repetitions <= min(10, sampling["repetitions"]),
                      "diagnostic repetitions exceed the primary cell grid or collector bound")
            else:
                _fail(isinstance(collector, dict) and collector.get("backend") == "libclang-cindex" and collector.get("collector") == "dx100.m5_rpns.source_scopes.v1"
                      and all(isinstance(collector.get(key), str) and re.fullmatch(r"[0-9a-f]{64}", collector[key])
                              for key in ("library_sha256", "pass_sha256", "runtime_sha256")),
                      "simulated region pairs require the exact diagnostic collector identity")
        _fail(not require_simulation_identity or mode == "native" or pair.get("evidence") == "simulated_diagnostic_profile",
              "new simulated region comparisons require package-backed diagnostic evidence")
    _fail(len({pair['diagnostic_repetitions'] for pair in pairs
               if pair.get('evidence') == 'native_diagnostic_profile.v1'}) <= 1,
          'one native profile package requires one diagnostic repetition policy')
    _simulation_identity(settings, store, required=require_simulation_identity)


def freeze_protocol(args):
    request = _request(args)
    store = _require_valid(args.records)
    settings = copy.deepcopy(request.get("settings"))
    if isinstance(settings, dict) and settings.get("mode") == "native":
        for target in settings.get("targets", {}).values():
            if isinstance(target, dict):
                target["machine_sha256"] = artifacts.digest(_get(store, target.get("id"), "machine"))
    try:
        _validate_settings(settings, store, require_simulation_identity=True)
        if settings["mode"] == "native":
            from swdb.bfs_native import validate_runtime_policy
            validate_runtime_policy(settings.get("native_runtime"), settings["threads"])
    except (KeyError, TypeError, ValueError) as exc:
        raise Failure(f"invalid protocol settings: {exc}") from None
    identities = {wid: verify_immutable(_get(store, wid, "workload")) for wid in settings["workloads"]}
    return _save_immutable(args, request, "protocol", settings=settings, workload_identities=identities,
                           frozen_at=_now(), state="frozen")


def verified_native_lane(value, machine):
    """Normalize only the exact persisted receipt emitted by the host lane verifier."""
    from swdb.profile import lane_required
    if not lane_required(machine):
        return value
    hostname = re.escape(machine["hostname"])
    matched = re.fullmatch(
        rf"({hostname}-evaluation-node([01])) \(verified: affinity, bind:\2, lease held, generation ([0-9]+)\)",
        value if isinstance(value, str) else "")
    _fail(matched is not None, "verified socket lane receipt is missing or malformed")
    lane, node, _generation = matched.groups()
    _fail(any(row.get("node") == int(node) for row in machine.get("numa_nodes", [])),
          "verified socket lane is absent from the target machine")
    return lane


def validate_baseline_source(store, candidate):
    """Bind the baseline bytes to its selected catalog implementation, not ancestry."""
    selected = _get(store, candidate.get("implementation"), "implementation")
    source = _get(store, candidate.get("source_snapshot"), "source_snapshot")
    context = store.source_context(selected)
    _fail(source.get("implementation") == selected["id"]
          and all(row.get("context", {}).get("application") == context["application"]
                  and row.get("context", {}).get("function") == context["function"]
                  and row.get("context", {}).get("source", {}).get("commit") == context["source"]["commit"]
                  for row in (candidate, source)), "baseline differs from the selected implementation source context")
    expected = artifacts.identify(artifacts.source_root(store, selected))
    _fail(all(row.get("artifact", {}).get("sha256") == expected["sha256"]
              and row.get("artifact", {}).get("files") == expected["files"] for row in (candidate, source)),
          "baseline artifact differs from the selected implementation source")


def validate_protocol_for_evaluation(store, request, candidate, actual_build=None, actual_lane=None, actual_instrumentation=None,
                                    actual_collection=None):
    if request.get("protocol") is None:
        return None
    protocol = _get(store, request["protocol"], "protocol")
    digest = verify_immutable(protocol)
    settings = protocol["settings"]
    _validate_settings(settings, store)
    _fail(settings["sampling"].get("collection") == actual_collection,
          "actual collection method differs from the frozen sampling policy")
    role = request.get("protocol_role")
    _fail(role in {"baseline", "candidate"}, "protocol_role must select baseline or candidate")
    workload_request = request.get("workload")
    _fail(isinstance(workload_request, dict), "registered workload mapping is required")
    wid = workload_request.get("id")
    _fail(wid in protocol["workload_identities"], "workload is outside the frozen protocol")
    workload = _get(store, wid, "workload")
    _fail(verify_immutable(workload) == protocol["workload_identities"][wid], "frozen workload changed")
    from swdb.bfs_native import canonical_graph
    canonical, _ = canonical_graph(materialize_workload(store, wid) if set(workload_request) == {"id"} else workload_request)
    _fail(artifacts.digest(canonical) == workload["definition"]["canonical_sha256"], "requested adjacency differs from frozen workload")
    _fail(request.get("sources") == workload["definition"]["sources"], "source sequence differs from frozen workload")
    _fail(request.get("threads") == settings["threads"] and request.get("repetitions") == settings["sampling"]["repetitions"],
          "threads/repetitions differ from frozen settings")
    if request.get("fixture") is not True or "native_runtime" in settings:
        from swdb.bfs_native import validate_runtime_policy
        validate_runtime_policy(settings.get("native_runtime"), settings["threads"])
    _fail(request.get("roi", "bfs.complete_call.v1") == settings["roi"], "ROI differs from frozen settings")
    target = settings["targets"][role]
    _fail(request.get("machine") == target["id"] and request.get("target_configuration", {}) == target["configuration"],
          "target or configuration differs from frozen settings")
    if "lane" in target["configuration"]:
        machine = _get(store, target["id"], "machine")
        _fail(verified_native_lane(actual_lane, machine) == target["configuration"]["lane"],
              "verified socket lane differs from frozen target")
    _fail(_get(store, candidate["implementation"], "implementation")["kernel"] == settings["kernel"], "candidate kernel differs from protocol")
    if role == "baseline":
        validate_baseline_source(store, candidate)
    if actual_build is not None:
        expected = settings["builds"][role]
        _fail(all(actual_build.get(key) == expected[key] for key in ("compiler", "flags", "adapter")), "actual build differs from frozen settings")
    if actual_instrumentation is not None:
        _fail(actual_instrumentation == settings["instrumentation"][role], "actual instrumentation differs from frozen treatment")
    return {"protocol": protocol["id"], "frozen_sha256": digest, "workload_id": wid,
            "workload_sha256": workload["identity_sha256"], "role": role,
            "frozen_at": protocol["frozen_at"], "bound_at": _now(), "settings_sha256": artifacts.digest(settings)}


def protocol_binding(context, protocol_id):
    """Return the exact binding an execution retains for one frozen protocol (R10)."""
    if context.get("protocol_binding", {}).get("protocol") == protocol_id:
        return context["protocol_binding"]
    shared = context.get("shared_protocol_bindings") or {}
    _fail(isinstance(shared, dict), "shared protocol bindings are malformed")
    return shared.get(protocol_id, {})


def _timestamp(value):
    try:
        timestamp = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        _fail(timestamp.tzinfo is not None, "evidence timestamp needs a time zone")
        return timestamp
    except (ValueError, AttributeError):
        raise Failure("invalid evidence timestamp") from None


def validate_protocol_for_simulation(store, request, candidate, *, actual_target,
                                     actual_configuration, actual_build, actual_instrumentation,
                                     actual_threads, actual_roi, actual_verifier):
    """Bind one actual simulator traversal to a frozen source/repetition cell.

    Returns None for an explicitly diagnostic request without a protocol. A
    campaign later aggregates separate completed executions; this helper never
    turns a requested repetition count into completed evidence.
    """
    if not request.get("protocol"):
        _fail("shared_protocols" not in request, "shared protocols require a primary frozen protocol")
        return None
    shared_ids = request.get("shared_protocols")
    if shared_ids is not None:
        _fail(isinstance(shared_ids, list) and shared_ids and len(set(shared_ids)) == len(shared_ids)
              and all(isinstance(pid, str) for pid in shared_ids) and request["protocol"] not in shared_ids,
              "shared_protocols must name distinct additional frozen protocols")
        arguments = dict(actual_target=actual_target, actual_configuration=actual_configuration,
                         actual_build=actual_build, actual_instrumentation=actual_instrumentation,
                         actual_threads=actual_threads, actual_roi=actual_roi, actual_verifier=actual_verifier)
        single = {key: value for key, value in request.items() if key != "shared_protocols"}
        primary = validate_protocol_for_simulation(store, single, candidate, **arguments)
        main_settings = _get(store, request["protocol"], "protocol")["settings"]
        role = request.get("protocol_role")
        specific = ("protocol", "protocol_binding")
        bindings = {}
        for pid in shared_ids:
            other = validate_protocol_for_simulation(store, {**single, "protocol": pid}, candidate, **arguments)
            other_settings = _get(store, pid, "protocol")["settings"]
            # Every identity that decides this role's traversal must match; the
            # policies may differ only in their other role and disclosures.
            for key in ("kernel", "workloads", "roi", "threads", "sampling", "correctness", "simulation_identity"):
                _fail(artifacts.digest(other_settings.get(key)) == artifacts.digest(main_settings.get(key)),
                      f"shared protocol {key} differs; one execution cannot satisfy both")
            for key in ("targets", "builds", "instrumentation", "reference_artifacts"):
                _fail(artifacts.digest(other_settings.get(key, {}).get(role))
                      == artifacts.digest(main_settings.get(key, {}).get(role)),
                      f"shared protocol {role} {key} differs; one execution cannot satisfy both")
            _fail(artifacts.digest({k: v for k, v in other["context"].items() if k not in specific})
                  == artifacts.digest({k: v for k, v in primary["context"].items() if k not in specific}),
                  "shared protocol binds a different actual traversal")
            bindings[pid] = other["binding"]
        primary["context"]["shared_protocol_bindings"] = bindings
        return primary
    frozen = _get(store, request["protocol"], "protocol")
    fingerprint = verify_immutable(frozen)
    settings = frozen["settings"]
    _validate_settings(settings, store)
    _fail(settings["mode"] in {"artifact_reference", "controlled_simulator"}, "simulator execution requires a simulated protocol")
    role = request.get("protocol_role")
    _fail(role in {"baseline", "candidate"}, "protocol_role must be baseline or candidate")
    workload_request = request.get("workload", {})
    wid = workload_request.get("id")
    _fail(wid in frozen["workload_identities"], "simulation workload is outside frozen settings")
    workload = _get(store, wid, "workload")
    _fail(verify_immutable(workload) == frozen["workload_identities"][wid], "registered simulation workload changed")
    definition = workload["definition"]
    trial = request.get("protocol_trial")
    _fail(isinstance(trial, dict) and set(trial) == {"source_position", "repetition"},
          "simulation requires an explicit protocol_trial source_position/repetition")
    position = _integer(trial["source_position"], "source_position", 0)
    repetition = _integer(trial["repetition"], "repetition", 0)
    _fail(position < len(definition["sources"]) and repetition < settings["sampling"]["repetitions"], "simulation trial is outside frozen coverage")
    source = definition["sources"][position]
    _fail(type(workload_request.get("source")) is int and workload_request["source"] == source,
          "simulation source differs from its frozen source position")
    app = store.application_of(_get(store, candidate["implementation"], "implementation"))
    representation = workload_representation(store, wid, app["id"])["representation"]
    _fail(workload_request.get("representation") == {"path": representation["path"], "sha256": representation["sha256"]},
          "simulation representation differs from registered loaded adjacency")
    target = settings["targets"][role]
    _fail(actual_target == target["id"] and artifacts.digest(actual_configuration) == artifacts.digest(target["configuration"]),
          "actual simulator target/configuration differs from frozen settings")
    _fail(actual_threads == settings["threads"] and actual_roi == settings["roi"] and actual_verifier == settings["correctness"]["verifier"],
          "actual simulator threads/ROI/verifier differs from frozen settings")
    expected_build = settings["builds"][role]
    _fail(all(artifacts.digest(actual_build.get(key)) == artifacts.digest(expected_build[key])
              for key in ("compiler", "compiler_version", "flags", "adapter")), "actual simulator guest build differs from frozen settings")
    _simulation_build(settings, store, role, candidate, actual_build,
                      "contract_fixture" if request.get("fixture") else "execution", check_files=True)
    _fail(artifacts.digest(actual_instrumentation) == artifacts.digest(settings["instrumentation"][role]),
          "actual simulator instrumentation differs from frozen treatment")
    _fail(_get(store, candidate["implementation"], "implementation")["kernel"] == settings["kernel"], "simulation candidate kernel differs")
    if role == "baseline":
        validate_baseline_source(store, candidate)
    binding = {"protocol": frozen["id"], "frozen_sha256": fingerprint, "workload_id": wid,
               "workload_sha256": workload["identity_sha256"], "role": role, "frozen_at": frozen["frozen_at"],
               "bound_at": _now(), "settings_sha256": artifacts.digest(settings)}
    return {"binding": binding, "build": copy.deepcopy(actual_build), "context": {
        "protocol": frozen["id"], "protocol_binding": binding, "protocol_trial": copy.deepcopy(trial),
        "target": actual_target, "backend_configuration": copy.deepcopy(actual_configuration),
        "instrumentation": copy.deepcopy(actual_instrumentation), "adapter": actual_build["adapter"],
        "threads": actual_threads, "roi": actual_roi, "verifier": actual_verifier, "basis": "simulated",
        "sources": [source], "repetitions": 1, "candidate_sha256": candidate["artifact"]["sha256"],
        "workload": {"id": wid, "canonical_sha256": definition["canonical_sha256"], "sources": [source],
                     "family": definition["family"], "representation": copy.deepcopy(representation)}}}


def aggregate_evaluations(args):
    """Retain a complete sample grid or an explicit failed aggregation of real trials."""
    request = _request(args)
    store = _require_valid(args.records)
    _fail(store.get(request["id"]) is None, "aggregation ID already exists")
    ids = request.get("evaluations")
    _fail(isinstance(ids, list) and ids and all(isinstance(rid, str) for rid in ids), "evaluations must be a nonempty ID list")
    data = workflow.record("evaluation", request["id"], request=copy.deepcopy(request),
        outcome={"state": "submitted", "stage": "aggregation", "reason": None}, stages=[], timing=[],
        correctness={"state": "unverified", "checks": []}, profiling={"state": "component_profiles", "regions": []},
        raw_artifacts=[], component_evaluations=[], gain_claim=False, evidence_kind="contract_fixture")
    try:
        _fail(len(ids) == len(set(ids)), "aggregation has duplicate execution IDs")
        components = []
        for rid in ids:
            component = _get(store, rid, "evaluation")
            data["component_evaluations"].append({"evaluation": rid, "sha256": artifacts.digest(component)})
            components.append(component)
        first = components[0]
        frozen = _get(store, request.get("protocol"), "protocol")
        verify_immutable(frozen)
        _validate_settings(frozen["settings"], store)
        _fail(frozen["settings"]["mode"] != "native", "native evaluations already own their sample grid")
        role = request.get("protocol_role")
        _fail(role in {"baseline", "candidate"}, "aggregation needs an explicit protocol_role")
        for key in ("candidate", "proposal", "source_snapshot", "implementation", "machine", "comparison_baseline", "profile_package"):
            if key in first: data[key] = first[key]
        data["build"] = copy.deepcopy(first["build"])
        data["context"] = copy.deepcopy(first["context"])
        data["context"]["component_bindings"] = {}
        data["context"]["component_contexts"] = {}
        data["evidence_kind"] = first["evidence_kind"]
        if first.get("request", {}).get("fixture") is True: data["request"]["fixture"] = True
        wid = first["context"]["workload"]["id"]
        workload = _get(store, wid, "workload")
        _fail(wid in frozen["workload_identities"] and verify_immutable(workload) == frozen["workload_identities"][wid], "aggregation workload is not frozen")
        definition = workload["definition"]
        cells = set()
        expected = {(position, rep) for position in range(len(definition["sources"]))
                    for rep in range(frozen["settings"]["sampling"]["repetitions"])}
        common_keys = ("target", "backend_configuration", "instrumentation", "adapter", "threads", "roi", "verifier", "basis", "candidate_sha256", "model", "interface")
        earliest = None
        cases = set()
        for component in components:
            context = component["context"]
            _fail(component.get("outcome", {}).get("state") == "complete" and component.get("correctness", {}).get("state") == "passed", "component execution failed, is incomplete, or lacks correctness")
            _fail(not component.get("component_evaluations"), "nested aggregation is not an actual distinct simulator execution")
            _fail(all(component.get(key) == first.get(key) for key in ("candidate", "implementation", "source_snapshot", "machine", "evidence_kind")), "component candidate/source/machine/evidence identities differ")
            _fail(artifacts.digest(component["build"]) == artifacts.digest(first["build"]), "component timed binaries or build/model identity differ")
            _fail(all(artifacts.digest(context.get(key)) == artifacts.digest(first["context"].get(key)) for key in common_keys), "component target/configuration/ROI/source identity differs")
            binding = protocol_binding(context, frozen["id"])
            _fail(binding.get("protocol") == frozen["id"] and binding.get("frozen_sha256") == frozen["identity_sha256"]
                  and binding.get("settings_sha256") == artifacts.digest(frozen["settings"]) and binding.get("role") == role
                  and binding.get("workload_id") == wid and binding.get("workload_sha256") == workload["identity_sha256"],
                  "component lacks this exact protocol/workload/role binding")
            bound = _timestamp(binding.get("bound_at"))
            _fail(bound >= _timestamp(frozen["frozen_at"]), "component predates protocol freeze")
            earliest = min(earliest, bound) if earliest else bound
            trial = context.get("protocol_trial", {})
            cell = (trial.get("source_position"), trial.get("repetition"))
            _fail(all(type(v) is int for v in cell) and cell in expected and cell not in cells, "component trial cell is missing, duplicate, or outside the frozen sample grid")
            source = definition["sources"][cell[0]]
            _fail(context.get("sources") == [source] and context.get("repetitions") == 1
                  and context.get("workload", {}).get("canonical_sha256") == definition["canonical_sha256"], "component does not identify one actual frozen graph/source traversal")
            _fail(len(component.get("timing", [])) == 1, "each component must contain one actual timed traversal")
            row = copy.deepcopy(component["timing"][0])
            _fail((row.get("source_position"), row.get("repetition")) == cell and row.get("source") == source, "component timing does not match its assigned source/repetition cell")
            checks = component["correctness"]["checks"]
            _fail(len(checks) == 1 and checks[0].get("passed") is True
                  and all(checks[0].get(key) == row.get(key) for key in ("source", "source_position", "repetition", "binary_sha256", "output_sha256"))
                  and checks[0].get("graph_sha256") == definition["canonical_sha256"], "component structural check is not linked to its exact timed graph/source/binary/output")
            _fail(row.get("binary_sha256") == component["build"].get("binary_sha256") and row.get("verified") is True
                  and row.get("basis") == "simulated" and row.get("quantity") == "simulated_roi_seconds" and row.get("roi") == frozen["settings"]["roi"], "component duration is not verified simulated ROI time")
            _fail(component.get("request", {}).get("fixture") is not True or component["evidence_kind"] == "contract_fixture", "fixture component was relabeled real execution")
            cells.add(cell)
            data["timing"].append(row)
            data["correctness"]["checks"].append(copy.deepcopy(checks[0]))
            data["stages"].extend({**copy.deepcopy(stage), "component_evaluation": component["id"]} for stage in component["stages"])
            data["raw_artifacts"].extend(copy.deepcopy(component.get("raw_artifacts", [])))
            data["context"]["component_bindings"][component["id"]] = copy.deepcopy(context.get("execution_binding"))
            data["context"]["component_contexts"][component["id"]] = copy.deepcopy(context)
            cases.update(context.get("correctness_cases", []))
        _fail(cells == expected, "aggregation is missing required frozen source/repetition executions")
        data["context"].update(sources=definition["sources"], repetitions=frozen["settings"]["sampling"]["repetitions"], correctness_cases=sorted(cases))
        data["context"]["workload"]["sources"] = definition["sources"]
        # R10: the aggregate belongs to this one protocol, even when its
        # components also retain exact bindings for another matching policy.
        data["context"]["protocol_binding"] = copy.deepcopy(protocol_binding(first["context"], frozen["id"]))
        data["context"]["protocol"] = frozen["id"]
        data["context"].pop("shared_protocol_bindings", None)
        data["context"]["protocol_binding"]["bound_at"] = earliest.isoformat()
        data["context"].pop("protocol_trial", None)
        data["request"]["protocol"] = frozen["id"]
        data["correctness"]["state"] = "passed"
        data["outcome"] = {"state": "complete", "stage": "aggregation", "reason": "Exact completed simulator executions; no synthetic repetitions."}
        _evaluation_samples(store, data, frozen, role)
    except (Failure, KeyError, TypeError, ValueError, OverflowError, OSError) as exc:
        data["outcome"] = {"state": "incompatible", "stage": "aggregation", "reason": str(exc)}
        data["correctness"]["state"] = "unverified"
    return workflow.persist(args.records, data, getattr(args, "db", None), create=True)


def _check_verifier_identity(evaluation, store=None):
    """Bind individual verdicts to the declared checker, including v2 witnesses."""
    context = evaluation.get('context', {})
    verifier = context.get("verifier")
    checks = evaluation.get("correctness", {}).get("checks", [])
    _fail(isinstance(verifier, str) and verifier and checks,
          "correctness verifier or individual checks are missing")
    _fail(all(check.get("checker", check.get("verifier")) == verifier
              and all(check[key] == verifier for key in ("checker", "verifier") if key in check)
              for check in checks), "individual correctness checker differs from evaluation verifier")
    # Retain historical records, but do not qualify the old mutable-Graph
    # checker through v1 or an aggregate that merely copies a newer context.
    build = evaluation.get('build', {})
    if context.get('roi') == 'bfs.complete_call.v1' and (
            verifier.startswith('dx100.') or context.get('candidate_build')
            or str(build.get('adapter', '')).startswith('dx100.complete_call.')):
        from swdb.dx100_witness import graph_verification_contract, WitnessError
        try:
            contract = graph_verification_contract(context.get('application'))
        except WitnessError as exc:
            raise Failure('complete-call original-adjacency qualification failed: ' + str(exc)) from None
        _fail(build.get('adapter') == 'dx100.complete_call.v2'
              and artifacts.digest(context.get('graph_verification')) == artifacts.digest(contract)
              and artifacts.digest(context.get('instrumentation', {}).get('graph_verification')) == artifacts.digest(contract),
              'complete-call candidate lacks the original-adjacency checker treatment; legacy record is retained but cannot qualify')
        driver, oracle = context.get('candidate_driver', {}), context.get('verifier_source', {})
        _fail(isinstance(driver, dict) and isinstance(oracle, dict)
              and isinstance(driver.get('path'), str) and Path(driver['path']).is_absolute()
              and '..' not in Path(driver['path']).parts and isinstance(driver.get('sha256'), str)
              and re.fullmatch(r'[a-f0-9]{64}', driver['sha256'])
              and all(oracle.get(key) == driver[key] for key in ('path', 'sha256')),
              'complete-call original-adjacency checker differs from compiled wrapper')
    components = evaluation.get("component_evaluations", [])
    if not components:
        if verifier.startswith('dx100.'):
            from swdb.dx100_coverage import validate_trace
            validate_trace(evaluation)
        if verifier == "dx100.bfs.verifier.v2":
            from swdb.dx100_witness import validate_record_witness
            validate_record_witness(evaluation)
        return
    _fail(store is not None, "aggregate correctness requires its actual component records")
    retained = []
    seen = set()
    for identity in components:
        component = _get(store, identity["evaluation"], "evaluation")
        _fail(component["id"] not in seen and not component.get("component_evaluations")
              and component.get("context", {}).get("verifier") == verifier
              and artifacts.digest(component) == identity["sha256"], "aggregate component evidence changed or identity differs")
        seen.add(component["id"])
        _check_verifier_identity(component, store)
        retained.extend(component["correctness"]["checks"])
    _fail(retained == checks, "aggregate checks differ from actual component correctness")


def _evaluation_samples(store, evaluation, protocol, role):
    settings = protocol["settings"]
    _fail(evaluation.get("outcome", {}).get("state") == "complete", "evaluation is incomplete or failed")
    _fail(evaluation.get("correctness", {}).get("state") == "passed", "evaluation lacks passed correctness")
    _check_verifier_identity(evaluation, store)
    context = evaluation.get("context", {})
    components = evaluation.get("component_evaluations", [])
    if components:
        _fail(settings["mode"] != "native", "native evaluations cannot masquerade as simulator aggregates")
        component_ids = [item["evaluation"] for item in components]
        _fail(len(set(component_ids)) == len(component_ids), "aggregate repeats a component execution")
        retained_timing, retained_checks, retained_stages = [], [], []
        for identity in components:
            component = _get(store, identity["evaluation"], "evaluation")
            _fail(artifacts.digest(component) == identity["sha256"], "aggregate component evidence changed")
            _fail(not component.get("component_evaluations"), "nested aggregates are not separate simulator executions")
            _fail(component.get("outcome", {}).get("state") == "complete"
                  and component.get("correctness", {}).get("state") == "passed", "aggregate retains a failed component")
            _fail(all(component.get(key) == evaluation.get(key) for key in
                      ("candidate", "implementation", "source_snapshot", "machine", "evidence_kind"))
                  and artifacts.digest(component.get("build")) == artifacts.digest(evaluation.get("build")),
                  "aggregate source/binary identity differs from its components")
            component_context = component.get("context", {})
            _fail(all(artifacts.digest(component_context.get(key)) == artifacts.digest(context.get(key)) for key in
                      ("target", "backend_configuration", "instrumentation", "adapter", "threads", "roi", "verifier", "basis", "candidate_sha256", "model", "interface")),
                  "aggregate target/configuration differs from its components")
            component_binding = protocol_binding(component_context, protocol["id"])
            _fail(component_binding.get("protocol") == protocol["id"]
                  and component_binding.get("frozen_sha256") == protocol["identity_sha256"]
                  and component_binding.get("settings_sha256") == artifacts.digest(settings)
                  and component_binding.get("role") == role, "aggregate component has another frozen policy or role")
            _fail(len(component.get("timing", [])) == 1 and len(component.get("correctness", {}).get("checks", [])) == 1,
                  "aggregate component is not one actual traversal")
            _fail(artifacts.digest(context.get("component_contexts", {}).get(component["id"])) == artifacts.digest(component.get("context")),
                  "aggregate component context changed")
            _fail(artifacts.digest(context.get("component_bindings", {}).get(component["id"])) == artifacts.digest(component.get("context", {}).get("execution_binding")),
                  "aggregate component execution binding changed")
            retained_timing.extend(component.get("timing", []))
            retained_checks.extend(component.get("correctness", {}).get("checks", []))
            retained_stages.extend({**stage, "component_evaluation": component["id"]} for stage in component.get("stages", []))
        _fail(artifacts.digest(retained_timing) == artifacts.digest(evaluation.get("timing"))
              and artifacts.digest(retained_checks) == artifacts.digest(evaluation["correctness"].get("checks"))
              and artifacts.digest(retained_stages) == artifacts.digest(evaluation.get("stages")),
              "aggregate observations differ from their actual component evidence")
    binding = context.get("protocol_binding", {})
    _fail(isinstance(binding, dict) and binding.get("protocol") == protocol["id"]
          and binding.get("frozen_sha256") == protocol["identity_sha256"]
          and binding.get("settings_sha256") == artifacts.digest(settings) and binding.get("role") == role,
          "evaluation has no matching immutable protocol binding")
    _fail(context.get("protocol") == protocol["id"] and evaluation.get("request", {}).get("protocol") == protocol["id"],
          "evaluation request/context contradict the bound protocol")
    _fail(_timestamp(binding.get("bound_at")) >= _timestamp(protocol["frozen_at"]), "evaluation predates protocol freeze")
    starts = [stage.get("started") for stage in evaluation.get("stages", []) if stage.get("started")]
    _fail(starts and min(map(_timestamp, starts)) >= _timestamp(protocol["frozen_at"]), "evaluation started before protocol freeze")
    candidate = _get(store, evaluation.get("candidate"), "candidate")
    _fail(candidate["implementation"] == evaluation.get("implementation")
          and candidate["artifact"]["sha256"] == context.get("candidate_sha256"), "timed candidate identity differs from source artifact")
    implementation = _get(store, candidate["implementation"], "implementation")
    _fail(implementation["kernel"] == settings["kernel"], "evaluation realizes a different kernel")
    if role == "baseline":
        validate_baseline_source(store, candidate)
    workload = context.get("workload", {})
    wid = workload.get("id")
    _fail(wid in protocol["workload_identities"] and binding.get("workload_id") == wid, "evaluation workload is outside protocol")
    registered = _get(store, wid, "workload")
    _fail(verify_immutable(registered) == protocol["workload_identities"][wid]
          and binding.get("workload_sha256") == registered["identity_sha256"], "evaluation workload registration changed")
    definition = registered["definition"]
    _fail(workload.get("canonical_sha256") == definition["canonical_sha256"], "evaluation graph differs from registered adjacency")
    _fail(context.get("sources") == definition["sources"] and workload.get("sources") == definition["sources"],
          "evaluation source sequence differs from frozen workload")
    _fail(context.get("threads") == settings["threads"] and context.get("repetitions") == settings["sampling"]["repetitions"],
          "evaluation threads/repetitions differ from protocol")
    _fail(context.get("roi") == settings["roi"], "evaluation semantic ROI differs from protocol")
    target = settings["targets"][role]
    _fail(context.get("target") == target["id"] and context.get("backend_configuration", {}) == target["configuration"],
          "evaluation target configuration differs from protocol")
    if settings["mode"] == "native":
        _fail(context.get("machine_sha256") == target["machine_sha256"], "native target machine identity changed")
        if "lane" in target["configuration"]:
            machine = _get(store, target["id"], "machine")
            _fail(verified_native_lane(context.get("lane"), machine) == target["configuration"]["lane"],
                  "verified socket lane differs from frozen target")
    build = evaluation.get("build", {})
    expected = settings["builds"][role]
    if settings["mode"] == "native" and (evaluation.get("evidence_kind") != "contract_fixture" or "native_runtime" in settings):
        from swdb.bfs_native import controlled_environment, validate_runtime_policy
        policy = validate_runtime_policy(settings.get("native_runtime"), settings["threads"])
        validate_runtime_policy(build.get("native_runtime"), settings["threads"])
        _fail(build["native_runtime"] == policy, "evaluation runtime inputs differ from the frozen native policy")
        _fail(build.get("execution_environment") == controlled_environment(settings["threads"]),
              "evaluation controlled runtime inputs contradict the native policy")
    _fail(all(build.get(key) == expected[key] for key in ("compiler", "flags", "compiler_version"))
          and context.get("adapter") == expected["adapter"], "evaluation build differs from frozen build definition")
    if settings["mode"] != "native":
        _simulation_build(settings, store, role, candidate, build, evaluation.get("evidence_kind"))
        if evaluation.get("evidence_kind") == "execution":
            bindings = list(context.get("component_bindings", {}).values()) if components else [context.get("execution_binding", {})]
            _fail(bindings and all(row.get("simulator") == settings["simulation_identity"]["simulator"]
                                  and row.get("binary") == {"path": build.get("binary"), "sha256": build.get("binary_sha256")}
                                  for row in bindings), "simulation execution binding contradicts frozen build")
    _fail(context.get("instrumentation") == settings["instrumentation"][role], "instrumentation differs from frozen treatment")
    _fail(context.get("verifier") == settings["correctness"]["verifier"], "correctness verifier differs from frozen coverage")
    _fail(set(settings["correctness"]["required_cases"]).issubset(set(context.get("correctness_cases", []))),
          "required correctness cases have no evidence")
    binary = build.get("binary_sha256")
    _fail(isinstance(binary, str) and re.fullmatch(r"[0-9a-f]{64}", binary), "timed binary identity is missing")
    basis = "measured" if settings["mode"] == "native" else "simulated"
    quantity = "native_roi_wall_seconds" if basis == "measured" else "simulated_roi_seconds"
    classification = evaluation.get("evidence_kind")
    _fail(classification in {"execution", "contract_fixture"}, "evaluation evidence classification is missing")
    _fail(evaluation.get("request", {}).get("fixture") is not True or classification == "contract_fixture",
          "a fixture evaluation cannot be relabeled execution evidence")
    _fail(context.get("basis") == basis, "native and simulated evidence cannot be divided")
    checks = evaluation["correctness"].get("checks", [])
    _fail(all(check.get("passed") is True for check in checks), "evaluation retains a failed or unverified correctness case")
    expected_cells = {(position, repetition) for position in range(len(definition["sources"]))
                      for repetition in range(settings["sampling"]["repetitions"])}
    observations = {}
    for observation in evaluation.get("timing", []):
        cell = (observation.get("source_position"), observation.get("repetition"))
        _fail(cell in expected_cells and cell not in observations, "timing coverage has duplicate or unexpected cells")
        source = definition["sources"][cell[0]]
        _fail(observation.get("source") == source and observation.get("binary_sha256") == binary
              and observation.get("verified") is True, "timed source/binary is unverified or inconsistent")
        _fail(observation.get("roi") == settings["roi"] and observation.get("basis") == basis
              and observation.get("quantity") == quantity and observation.get("evidence_kind") == classification,
              "timing quantity, scope, basis, or evidence classification differs from protocol")
        matching = [check for check in checks if check.get("source_position") == cell[0]
                    and check.get("repetition") == cell[1]]
        _fail(len(matching) == 1 and matching[0].get("passed") is True
              and matching[0].get("source") == source and matching[0].get("binary_sha256") == binary
              and matching[0].get("graph_sha256") == definition["canonical_sha256"]
              and matching[0].get("output_sha256") == observation.get("output_sha256"),
              "correctness is not linked to this timed graph/source/binary/output")
        required_accelerator = settings["correctness"].get("required_accelerator_cases", {}).get(role, [])
        _fail(set(required_accelerator) <= accelerator_cases(matching[0]),
              "timed replay lacks required typed accelerator coverage")
        observations[cell] = _positive(observation.get("duration_s"), "ROI duration")
    _fail(set(observations) == expected_cells, "missing timed source/repetition coverage")
    return {position: [observations[position, repetition] for repetition in range(settings["sampling"]["repetitions"])]
            for position in range(len(definition["sources"]))}, wid, classification


def _geomean(values):
    return math.exp(statistics.mean(math.log(value) for value in values))


def _statistics(baseline, candidate, policy, sampling=None):
    ratios = {position: statistics.median(baseline[position]) / statistics.median(candidate[position]) for position in baseline}
    for ratio in ratios.values():
        _positive(ratio, "representable source duration ratio")
    spreads = {role: {position: (max(values) - min(values)) / statistics.median(values)
                      for position, values in samples.items()} for role, samples in (("baseline", baseline), ("candidate", candidate))}
    _fail(all(math.isfinite(value) for rows in spreads.values() for value in rows.values()),
          "timing spread exceeds representable numeric range")
    rng = random.Random(policy["bootstrap_seed"])
    draws = []
    paired = sampling is not None and sampling.get("analysis") == "paired_repetition_block_bootstrap.v1"
    count = len(next(iter(baseline.values())))
    if paired:
        _fail(all(len(values) == count for role in (baseline, candidate) for values in role.values()),
              "paired bootstrap requires complete equal repetition blocks")
    for _ in range(policy["bootstrap_resamples"]):
        resampled = []
        blocks = rng.choices(range(count), k=count) if paired else None
        for position in baseline:
            a, b = baseline[position], candidate[position]
            aa, bb = ([a[index] for index in blocks], [b[index] for index in blocks]) if paired else (
                rng.choices(a, k=len(a)), rng.choices(b, k=len(b)))
            resampled.append(statistics.median(aa) / statistics.median(bb))
        draws.append(_geomean(resampled))
    draws.sort()
    lower, upper = draws[49], draws[1949]
    return {"roi_speedup": _geomean(ratios.values()),
            "per_source_position_speedup": {str(position): ratio for position, ratio in ratios.items()},
            "confidence_interval": {"confidence": 0.95, "lower": lower, "upper": upper,
                                    "method": "paired_repetition_block_bootstrap.v1" if paired else
                                        "independent per-source bootstrap of median ratios", "resamples": 2000},
            "relative_spread": {role: {str(position): value for position, value in rows.items()}
                                for role, rows in spreads.items()}}


def _region_comparisons(a, b, settings, store=None, packages=None):
    results = []
    diagnostic_kinds = {"simulated_diagnostic_profile", "native_diagnostic_profile.v1"}
    if any(pair.get("evidence") in diagnostic_kinds for pair in settings.get("region_pairs", [])):
        from swdb.bfs_region_comparison import compare
        _fail(store is not None, "diagnostic region comparison requires record context")
        results.extend(compare(store, a, b, settings, packages))
    for pair in settings.get("region_pairs", []):
        if pair.get("evidence") in diagnostic_kinds:
            continue
        durations = []
        for role, evaluation in (("baseline", a), ("candidate", b)):
            regions = evaluation.get("profiling", {}).get("regions", [])
            rows = [row for row in regions if row.get("id") == pair[role]]
            _fail(len(rows) == 1, "selected corresponding region is missing or ambiguous")
            row = rows[0]
            _fail(row.get("semantic_region") == pair["semantic_region"] and row.get("scope") == pair["scope"]
                  and row.get("attribution") == pair["attribution"] and row.get("roi") == settings["roi"],
                  "corresponding region boundaries or attribution scopes differ")
            _fail(row.get("binary_sha256") == evaluation["build"]["binary_sha256"]
                  and row.get("workload_sha256") == evaluation["context"]["workload"]["canonical_sha256"],
                  "region identity differs from the timed binary/workload")
            _fail(row.get("basis") == evaluation["context"]["basis"], "region timing basis differs from evaluation")
            _integer(row.get("invocations"), "region invocation count")
            durations.append(_positive(row.get("duration_s"), "region duration"))
        ratio = _positive(durations[0] / durations[1], "representable region duration ratio")
        results.append({**pair, "duration_ratio": ratio, "primary_bfs_roi": False,
                        "gain_claim": False, "note": "Scoped region ratio; the primary BFS result is reported separately."})
    return results


def compare_evaluations(args):
    request = _request(args)
    store = _require_valid(args.records)
    _fail(store.get(request["id"]) is None, "comparison result ID already exists; retained outcomes are immutable")
    data = workflow.record("comparison_result", request["id"], request=copy.deepcopy(request),
                           decision={"state": "rejected", "reasons": []}, gain_claim=False,
                           evidence_kind="unknown", metrics={}, region_comparisons=[], finished_at=_now())
    try:
        protocol = _get(store, request.get("protocol"), "protocol")
        data.update(protocol=protocol["id"], protocol_sha256=verify_immutable(protocol))
        _validate_settings(protocol["settings"], store)
        baseline = _get(store, request.get("baseline_evaluation"), "evaluation")
        candidate = _get(store, request.get("candidate_evaluation"), "evaluation")
        data.update(baseline_evaluation=baseline["id"], candidate_evaluation=candidate["id"])
        selected = _get(store, request.get("comparison_baseline"), "implementation")
        data["comparison_baseline"] = selected["id"]
        _fail(baseline.get("implementation") == selected["id"], "baseline evaluation does not belong to the explicitly selected implementation")
        _fail(candidate.get("comparison_baseline") in {None, selected["id"]}, "comparison conflicts with the evaluation's selected baseline")
        ancestry = _get(store, candidate.get("candidate"), "candidate")
        data["source_ancestor"] = ancestry["implementation"]
        a, wid, evidence_kind = _evaluation_samples(store, baseline, protocol, "baseline")
        b, other_wid, other_kind = _evaluation_samples(store, candidate, protocol, "candidate")
        _fail(wid == other_wid, "baseline and candidate evaluate different workloads")
        _fail(evidence_kind == other_kind, "execution evidence cannot be paired with a contract fixture")
        sampling = protocol["settings"]["sampling"]
        pair_identity = None
        if sampling.get("collection") is not None:
            from swdb.bfs_native_pair import validate_receipt
            pair_identity = validate_receipt(store, baseline, candidate, protocol["settings"])
        else:
            _fail(not any(row.get("context", {}).get("pairing") for row in (baseline, candidate)),
                  "paired evidence cannot use an independent serial analysis")
        data["evidence_kind"] = evidence_kind
        data["evaluation_identities"] = {baseline["id"]: artifacts.digest(baseline), candidate["id"]: artifacts.digest(candidate)}
        data["region_comparisons"] = _region_comparisons(baseline, candidate, protocol["settings"], store, request.get("region_packages"))
        data["metrics"] = _statistics(a, b, protocol["settings"]["profitability"], sampling)
        if pair_identity is not None:
            data["metrics"]["paired_collection"] = pair_identity
        data["metrics"]["workload"] = wid
        data["metrics"]["attribution"] = ("artifact_configuration_pair" if protocol["settings"]["mode"] == "artifact_reference" else
            "software_on_fixed_target" if protocol["settings"]["targets"]["baseline"] == protocol["settings"]["targets"]["candidate"] else
            "joint_hardware_software")
        data["metrics"]["disclosed_differences"] = protocol["settings"]["differences"]
        if evidence_kind == "contract_fixture":
            data["decision"] = {"state": "fixture_comparison", "reasons": ["Contract fixture durations are not empirical performance evidence."]}
            data["metrics"]["fixture_ratio"] = data["metrics"].pop("roi_speedup")
        else:
            limit = protocol["settings"]["profitability"]["maximum_relative_spread"]
            noisy = any(value > limit for values in data["metrics"]["relative_spread"].values() for value in values.values())
            interval = data["metrics"]["confidence_interval"]
            gain = interval["lower"] > protocol["settings"]["profitability"]["minimum_speedup"]
            state = "inconclusive" if noisy else "gain" if gain else "regression" if interval["upper"] < 1 else "no_gain"
            data["decision"] = {"state": state, "reasons": ["Timing spread exceeds the frozen threshold."] if noisy else []}
            data["gain_claim"] = state == "gain"
    except (Failure, KeyError, TypeError, ValueError, OverflowError, OSError) as exc:
        data["decision"] = {"state": "rejected", "reasons": [str(exc)]}
        data["gain_claim"] = False
        data["metrics"] = {}
        data["region_comparisons"] = []
    data["finished_at"] = _now()
    return workflow.persist(args.records, data, getattr(args, "db", None), create=True)
