"""Scalable native BFS evaluator path (evaluator v2, compiled verifier v2).

Created 2026-10-04 ET (ticket 63; ticket 61 decision, option 1). Original SWDB code.

The v1 native evaluator (``swdb.bfs_native``, verifier ``swdb.bfs.structural.v1``)
materializes the registered graph as a Python adjacency, writes a text copy for its
driver, and checks every parent vector in Python. Its fixed input limits (2 M vertices,
32 M directed edges) refuse the scale-22 graphs of design decisions D3/D4. Frozen
protocols and records under v1 keep their meaning; nothing here changes v1.

Evaluator v2 (``EVALUATOR_V2``) is selected only by a protocol that pins it
(``settings.evaluator``) together with the compiled verifier (``VERIFIER_V2``), or by
an unprotocoled request that names it. It differs only outside the ROI:

- the trusted driver (``tools/bfs_native/driver_scalable.cc.in``) maps the registered
  GAPBS SG file directly, with no Python adjacency and no text graph copy;
- the parent vector is written as little-endian int32 to its own file;
- the result check is ``tools/bfs_native/bfs_verify.cc``, compiled by the evaluator
  from repository source with ``-std=c++11 -O2`` (no fast-math), run as a separate
  process. It applies exactly the criterion of ``bfs_native.verify_parents`` (ADR 0001:
  parent tree valid, depths consistent, every reachable vertex reached) and returns the
  same verdict mapping, first-failure reason included;
- after a passed check the parent file is kept gzip-compressed (exact bytes; the raw
  SHA-256 is retained) so a paired receipt can be re-verified from raw output.

The SG file is bound to its registration by SHA-256 before every trial. Registration
proved it loads the registered canonical adjacency (``sg_identity.cc``, exact mmap CSR
and transpose membership), so the hash binding carries that proof.

Limits (memory-bounded, sized for scale 22): at most 2^23 = 8,388,608 vertices,
2^28 = 268,435,456 directed edges, and a 3 GiB SG file. Driver heap outside the
candidate's BFS: (n+1)*8 + m*4 bytes (about 0.55 GB at scale 22, doubled for a directed
graph); verifier heap about 9 bytes per vertex (about 38 MB at scale 22); both map the SG
file read-only.

Evaluator v3 (``EVALUATOR_V3``, ticket 67, 2026-10-04 ET) closes the final code review's open
P3: the v2 driver narrows each returned parent with ``static_cast<int32_t>``, so a candidate
returning a wider element type could have an out-of-range parent truncated into a valid one.
The v3 driver (``tools/bfs_native/driver_scalable_v3.cc.in``) requires an integral element type
of at most 64 bits at compile time and narrows by saturation: a value outside int32 becomes
INT32_MAX or INT32_MIN. Because every graph has at most 2^23 vertices, such a value is out of
range at full width, and its saturated form gets the same verdict and reason from the compiled
verifier as a full-width check would. It records the count in ``parents_saturated``
(trial format ``swdb.bfs.native.trial.v3``). v3 also stores one gzip copy per distinct
verified parent vector in an evaluation (content-addressed by raw SHA-256; a single-thread BFS
returns the same vector on every repetition of a source). The verifier, its criterion and the
ROI are v2's. v2 and every protocol that pins it are unchanged.
"""

import gzip
import hashlib
import json
import os
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from swdb import artifacts, paths
from swdb.cli import Failure

EVALUATOR_V1 = "swdb.native.evaluator.v1"
EVALUATOR_V2 = "swdb.native.evaluator.scalable.v2"
EVALUATOR_V3 = "swdb.native.evaluator.scalable.v3"
EVALUATORS = (EVALUATOR_V1, EVALUATOR_V2, EVALUATOR_V3)
SCALABLE = (EVALUATOR_V2, EVALUATOR_V3)
VERIFIER_V1 = "swdb.bfs.structural.v1"
VERIFIER_V2 = "swdb.bfs.structural.compiled.v2"
TRIAL_FORMAT_V2 = "swdb.bfs.native.trial.v2"
TRIAL_FORMAT_V3 = "swdb.bfs.native.trial.v3"
DRIVER_V2 = paths.HOME / "tools" / "bfs_native" / "driver_scalable.cc.in"
DRIVER_V3 = paths.HOME / "tools" / "bfs_native" / "driver_scalable_v3.cc.in"
DRIVERS = {EVALUATOR_V2: DRIVER_V2, EVALUATOR_V3: DRIVER_V3}
TRIAL_FORMATS = {EVALUATOR_V2: TRIAL_FORMAT_V2, EVALUATOR_V3: TRIAL_FORMAT_V3}
VERIFIER_SOURCE = paths.HOME / "tools" / "bfs_native" / "bfs_verify.cc"
VERIFIER_FLAGS = ["-std=c++11", "-O2"]
MAX_VERTICES = 2 ** 23
MAX_DIRECTED_EDGES = 2 ** 28
MAX_SG_BYTES = 3 * 1024 ** 3
TRIAL_RECORD_LIMIT = 4096
SG_FORMATS = {"gapbs_sg32le": 4, "gapbs_sg64le": 8}


def _fail(condition, message):
    if not condition:
        raise Failure(message)


def evaluator_of_settings(settings):
    """The evaluator a frozen protocol pins; protocols without the key are v1."""
    return settings.get("evaluator", EVALUATOR_V1) if isinstance(settings, dict) else EVALUATOR_V1


def is_scalable(evaluator):
    """Evaluators v2 and v3 share the mmap SG path and the compiled verifier."""
    return evaluator in SCALABLE


def driver_for(evaluator):
    return DRIVERS[evaluator]


def validate_settings(settings, plugin):
    """Bind evaluator and verifier versions to each other (scalable evaluators pin verifier v2)."""
    evaluator = evaluator_of_settings(settings)
    verifier = settings.get("correctness", {}).get("verifier") if isinstance(settings.get("correctness"), dict) else None
    _fail(evaluator in EVALUATORS, f"unsupported native evaluator {evaluator!r}")
    if "evaluator" in settings:
        _fail(settings.get("mode") == "native", "settings.evaluator applies only to native protocols")
    if is_scalable(evaluator) or verifier == VERIFIER_V2:
        _fail(settings.get("mode") == "native" and is_scalable(evaluator) and verifier == VERIFIER_V2
              and getattr(plugin, "native_scalable_verifier", None) == VERIFIER_V2,
              f"{evaluator if is_scalable(evaluator) else EVALUATOR_V2} and {VERIFIER_V2} are pinned together, "
              "for native BFS protocols only")
    return evaluator


def request_evaluator(store, request):
    """Evaluator of one evaluation request: its frozen protocol's, else the request's own."""
    named = request.get("evaluator", None)
    _fail(named is None or named in EVALUATORS, f"unsupported native evaluator {named!r}")
    if request.get("protocol"):
        protocol = store.get(request["protocol"], "protocol")
        _fail(protocol is not None, "frozen protocol is missing")
        pinned = evaluator_of_settings(protocol.get("settings"))
        _fail(named is None or named == pinned, "request evaluator differs from the frozen protocol")
        return pinned
    return named or EVALUATOR_V1


def verifier_identity():
    return {"id": VERIFIER_V2, "source": str(VERIFIER_SOURCE.relative_to(paths.HOME)),
            "source_sha256": artifacts.file_hash(VERIFIER_SOURCE), "flags": list(VERIFIER_FLAGS)}


def _sg_dimensions(path, width):
    with Path(path).open("rb") as handle:
        header = handle.read(1 + 2 * width)
    _fail(len(header) == 1 + 2 * width and header[0] in (0, 1), "invalid SG header")
    m, n = struct.unpack_from("<" + ("q" if width == 8 else "i") * 2, header, 1)
    return n, m, bool(header[0])


def resolve_workload(store, supplied, application):
    """Registered workload facts and its hash-bound SG input, without materializing it."""
    from swdb.bfs_protocol import _get, verify_immutable
    _fail(isinstance(supplied, dict) and set(supplied) == {"id"},
          f"{EVALUATOR_V2} evaluates registered workloads only ({{id: ...}})")
    data = _get(store, supplied["id"], "workload")
    verify_immutable(data)
    definition = data["definition"]
    reps = [rep for rep in definition["representations"] if rep.get("format") in SG_FORMATS]
    _fail(reps, f"{EVALUATOR_V2} requires a registered GAPBS SG representation")
    own = [rep for rep in reps if rep.get("application") == application]
    rep = (own or reps)[0]
    _fail(rep.get("adjacency_verified") is True and rep.get("canonical_sha256") == definition["canonical_sha256"],
          "SG representation has no compatible loaded-adjacency verification")
    path = Path(rep["path"])
    _fail(path.is_absolute() and path.is_file() and not path.is_symlink(),
          "registered SG representation must be an absolute regular file")
    size = path.stat().st_size
    _fail(size <= MAX_SG_BYTES, f"registered SG file exceeds the {EVALUATOR_V2} 3 GiB limit")
    width = SG_FORMATS[rep["format"]]
    n, m, directed = _sg_dimensions(path, width)
    realized = definition["realized"]
    _fail(n == realized["num_vertices"] and m == realized["num_directed_edges"] and directed == realized["directed"],
          "SG header differs from the registered realized dimensions")
    _fail(0 < n <= MAX_VERTICES and 0 <= m <= MAX_DIRECTED_EDGES,
          f"registered graph exceeds the {EVALUATOR_V2} limits ({MAX_VERTICES} vertices, {MAX_DIRECTED_EDGES} directed edges)")
    _fail(artifacts.file_hash(path) == rep["sha256"], "registered SG representation changed since registration")
    graph_input = {"representation": rep["id"], "path": str(path), "sha256": rep["sha256"],
                   "format": rep["format"], "offset_bytes": width, "bytes": size}
    workload = {"id": data["id"], "family": definition["family"], "generator": definition["generator"],
                "representation": {key: rep[key] for key in ("id", "path", "sha256", "format", "application") if key in rep},
                "normalization": "simple graph: remove self loops and duplicates; symmetrize if undirected; sort neighbors",
                "canonical_sha256": definition["canonical_sha256"], "adjacency_order_sha256": definition["canonical_sha256"],
                "num_vertices": n, "num_directed_edges": m, "directed": directed,
                "graph_input": graph_input, "adjacency_basis": "registered_sg_hash_binding"}
    return workload


def compiler():
    found = shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    _fail(found is not None, f"{VERIFIER_V2} requires a C++ compiler")
    return os.path.realpath(found)


def build_command(binary):
    return [compiler(), *VERIFIER_FLAGS, str(VERIFIER_SOURCE), "-o", str(binary)]


def run_verifier(binary, graph_input, source, parents, timeout):
    """One verdict mapping from the compiled verifier; Failure when it cannot run."""
    try:
        done = subprocess.run([str(binary), graph_input["path"], str(graph_input["offset_bytes"]), str(source), str(parents)],
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise Failure(f"{VERIFIER_V2} exceeded its {timeout:.0f} s budget") from None
    _fail(done.returncode == 0, f"{VERIFIER_V2} could not run: {done.stderr.strip()[-500:]}")
    try:
        verdict = json.loads(done.stdout)
    except ValueError:
        raise Failure(f"{VERIFIER_V2} returned no verdict") from None
    _fail(isinstance(verdict, dict) and isinstance(verdict.get("passed"), bool)
          and (verdict["reason"] is None if verdict["passed"] else isinstance(verdict.get("reason"), str))
          and (not verdict["passed"] or type(verdict.get("reachable_vertices")) is int),
          f"{VERIFIER_V2} verdict is malformed")
    return verdict


def check_trial_record(observed, source, threads, roi, vertices, evaluator=EVALUATOR_V2):
    """Shape checks of the small JSON trial record (reason or None)."""
    if observed.get("format") != TRIAL_FORMATS[evaluator]:
        return "missing_observation", "native trial output has the wrong format"
    if evaluator == EVALUATOR_V3 and (type(observed.get("parents_saturated")) is not int
                                      or not 0 <= observed["parents_saturated"] <= vertices):
        return "missing_observation", "native trial output lacks its saturated-parent count"
    if (type(observed.get("source")) is not int or observed["source"] != source or observed.get("roi") != roi
            or type(observed.get("configured_threads")) is not int or observed["configured_threads"] != threads):
        return "incompatible", "native output source, ROI, or configured threads differ from request"
    if (type(observed.get("num_vertices")) is not int or observed["num_vertices"] != vertices
            or observed.get("parents_encoding") != "int32le"):
        return "incompatible", "native output graph size or parent encoding differs from the registered graph"
    return None


def compress_parents(path, retained=None):
    """Keep the exact parent bytes gzip-compressed; returns (gz path, raw sha256, gz sha256).

    With ``retained`` (evaluator v3: a per-evaluation mapping raw sha256 -> (gz path, gz sha256)),
    a vector whose raw bytes were already kept reuses that copy and the new file is removed."""
    path = Path(path)
    raw_hash = artifacts.file_hash(path)
    if retained is not None and raw_hash in retained:
        kept, kept_hash = retained[raw_hash]
        _fail(Path(kept).is_file() and artifacts.file_hash(kept) == kept_hash,
              "retained parent vector changed before reuse")
        path.unlink()
        return Path(kept), raw_hash, kept_hash
    target = path.with_name(path.name + ".gz")
    with path.open("rb") as source, open(target, "xb") as sink:
        with gzip.GzipFile(filename="", mode="wb", fileobj=sink, compresslevel=6, mtime=0) as stream:
            shutil.copyfileobj(source, stream, 1024 * 1024)
    path.unlink()
    gz_hash = artifacts.file_hash(target)
    if retained is not None:
        retained[raw_hash] = (str(target), gz_hash)
    return target, raw_hash, gz_hash


def expand_parents(gz_path, expected_sha256, directory):
    """Decompress retained parents into a temporary file and check their raw hash."""
    handle = tempfile.NamedTemporaryFile(prefix="swdb-parents-", suffix=".i32", dir=directory, delete=False)
    digest = hashlib.sha256()
    try:
        with handle, gzip.open(gz_path, "rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
                handle.write(block)
        _fail(digest.hexdigest() == expected_sha256, "retained parent vector differs from its recorded hash")
        return Path(handle.name)
    except BaseException:
        Path(handle.name).unlink(missing_ok=True)
        raise


def recheck_retained(evaluation, observation, check, source, timeout=600, graph_checked=False):
    """Re-run the evaluation's own compiled verifier on its retained raw output (paired receipts).

    ``graph_checked`` skips re-hashing the SG input when the caller hashed it already."""
    build = evaluation.get("build", {})
    verifier = build.get("verifier", {})
    binary = verifier.get("binary")
    _fail(isinstance(binary, str) and Path(binary).is_file()
          and artifacts.file_hash(binary) == verifier.get("binary_sha256"),
          "the evaluation's compiled verifier binary is unavailable or changed")
    _fail(verifier.get("source_sha256") == evaluation.get("context", {}).get("verifier_sha256"),
          "compiled verifier identity differs from the evaluation context")
    graph_input = evaluation["context"]["workload"]["graph_input"]
    _fail(graph_checked or artifacts.file_hash(graph_input["path"]) == graph_input["sha256"], "registered SG input changed")
    parents = observation.get("parents_output")
    _fail(isinstance(parents, str) and Path(parents).is_file()
          and artifacts.file_hash(parents) == observation.get("parents_gzip_sha256"),
          "retained parent vector is unavailable or changed")
    expanded = expand_parents(parents, observation.get("parents_sha256"), Path(parents).parent)
    try:
        return run_verifier(binary, graph_input, source, expanded, timeout)
    finally:
        expanded.unlink(missing_ok=True)
