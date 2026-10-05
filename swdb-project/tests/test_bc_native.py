"""BC on the native evaluator through the kernel plug-in. Created: 2026-10-03 ET (ticket 40).

External compiler fixtures produce fixture durations, never evidence of native
BC performance. Real-compiler checks build the evaluator-owned BC driver around
upstream GAPBS bc.cc and the DX100 scalar-only snapshot on this host; they show
driver integration and BCVerifier reproduction only.
"""

import difflib
import hashlib
import json
import random
import shutil
import socket
import struct
import subprocess
from pathlib import Path

import pytest
import yaml

from conftest import REPO
from testkit.bfs_protocol import _workload_request, _payload, _command, _settings, _sg
from testkit.toolchain import find_cxx, load_script

BC_PROGRAM = r'''#!/usr/bin/env python3
import json, math, os, sys
from pathlib import Path
sys.path.insert(0, REPO)
from swdb.bc_native import reference_scores
mode = os.environ.get("SWDB_NATIVE_FIXTURE", "pass")
tokens = Path(sys.argv[1]).read_text().split()
n = int(tokens[1])
source = int(sys.argv[2])
out = Path(sys.argv[3])
adj = [[] for _ in range(n)]
for i in range(4, len(tokens), 2):
    adj[int(tokens[i])].append(int(tokens[i+1]))
scores, _ = reference_scores(adj, source, "double")
scores = [None if math.isnan(value) else value for value in scores]
if mode == "wrong_score": scores[1] += 0.01
if mode == "nan_score": scores[1] = None
if mode == "short": scores = scores[:-1]
data = {"format": "swdb.bc.native.trial.v1", "source": source,
        "configured_threads": int(os.environ["OMP_NUM_THREADS"]),
        "roi": "bc.complete_call.v1", "duration_s": 0.025, "scores": scores}
if mode == "bfs_format": data["format"] = "swdb.bfs.native.trial.v1"
out.write_text(json.dumps(data))
'''.replace("sys.path.insert(0, REPO)", f"sys.path.insert(0, {str(REPO)!r})")

GRAPH = {"num_vertices": 6, "directed": True,
         "edges": [[0, 1], [0, 2], [1, 3], [2, 3], [3, 4], [4, 5], [1, 4]]}


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@pytest.fixture
def bc_setup(records, tmp_path):
    records.copy_repo()
    runs = tmp_path / "runs"
    created = records.swdb("source-snapshot", "gapbs-bc-brandes", "--runs-dir", runs,
                           "--id", "test-bc-source", "--format", "json")
    assert created.returncode == 0, created.stderr
    snapshot = json.loads(created.stdout)
    packaged = records.swdb("fixture-package", "test-bc-source", "--id", "test-bc-package", "--format", "json")
    assert packaged.returncode == 0, packaged.stderr
    original = (REPO / "apps/gapbs/src/bc.cc").read_text()
    before = "#pragma omp parallel for schedule(dynamic, 64)"
    patch = "".join(difflib.unified_diff(original.splitlines(keepends=True),
                                         original.replace(before, "#pragma omp parallel for schedule(dynamic, 32)", 1)
                                         .splitlines(keepends=True), fromfile="a/src/bc.cc", tofile="b/src/bc.cc"))
    proposal = {"message_version": "1.0", "id": "test-bc-proposal",
                "producer": {"name": "proposal-test", "role": "sw", "test_client": True},
                "profile_package": "test-bc-package", "source_snapshot": "test-bc-source",
                "implementation": "gapbs-bc-brandes", "source_sha256": snapshot["artifact"]["sha256"],
                "intent": "Change a dependency-pass schedule chunk; contract test only.",
                "regions": [snapshot["regions"][0]["id"]],
                "constraints": {"editable_files": ["src/bc.cc"], "preserve_correctness": True, "preserve_roi": True},
                "payload": {"kind": "patch", "content": patch}, "required_operations": []}
    submitted = records.swdb("submit", _payload(tmp_path, "proposal", proposal), "--runs-dir", runs, "--format", "json")
    assert submitted.returncode == 0, submitted.stderr
    candidate = json.loads(submitted.stdout)["candidate"]
    machine = records.read("machines/mbit10.yaml")
    machine.update(id="native-testhost", hostname=socket.gethostname().split(".")[0], lane_required=False)
    records.write("machines/native-testhost.yaml", machine)
    compiler = tmp_path / "fixture-cxx"
    compiler.write_text("#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\n"
                        "if '--version' in sys.argv:\n print('SWDB external compiler contract fixture v1'); sys.exit(0)\n"
                        f"p=Path(sys.argv[sys.argv.index('-o')+1]); p.write_text({BC_PROGRAM!r}); p.chmod(0o755)\n")
    compiler.chmod(0o755)
    base = {"message_version": "1.0", "id": "bc-eval-fixture", "candidate": candidate,
            "machine": "native-testhost", "threads": 1, "sources": [0], "repetitions": 1,
            "roi": "bc.complete_call.v1", "fixture": True, "comparison_baseline": "gapbs-bc-brandes",
            "build": {"compiler": str(compiler), "flags": ["-std=c++11", "-O2"]},
            "budget": {"build_seconds": 10, "run_seconds": 5, "total_seconds": 60},
            "workload": {"family": "contract_fixture", "graph": GRAPH}}

    def request(**changes):
        data = {**base, **changes}
        file = tmp_path / f"{data['id']}.yaml"
        file.write_text(yaml.safe_dump(data))
        return file
    return records, runs, request, base


def _evaluate(setup, mode="pass", **changes):
    records, runs, request, _ = setup
    result = records.swdb("evaluate", request(**changes), "--runs-dir", runs, "--format", "json",
                          env={"SWDB_NATIVE_FIXTURE": mode})
    assert result.stdout, result.stderr
    return result, json.loads(result.stdout)


def test_bc_native_evaluation_uses_the_bc_plugin_and_bcverifier(bc_setup):
    result, data = _evaluate(bc_setup)
    assert result.returncode == 0, result.stderr
    context = data["context"]
    assert context["function"] == "Brandes" and context["roi"] == "bc.complete_call.v1"
    assert context["verifier"] == "swdb.bc.brandes_scores.v1"
    assert context["verifier_sha256"] == _hash(REPO / "swdb/bc_native.py")
    assert context["instrumentation"]["template_sha256"] == _hash(REPO / "tools/bc_native/driver.cc.in")
    assert data["build"]["binary"].endswith("/bc-native")
    assert data["correctness"]["state"] == "passed" and data["outcome"]["state"] == "complete"
    check = data["correctness"]["checks"][0]
    assert check["verifier"] == "swdb.bc.brandes_scores.v1" and check["passed"] is True
    assert check["reachable_vertices"] == 6


@pytest.mark.parametrize("mode, reason", [
    ("wrong_score", "differ from BCVerifier's reference"),
    ("nan_score", "or are not finite"),
    ("short", "length differs"),
])
def test_bc_native_evaluation_rejects_wrong_scores(bc_setup, mode, reason):
    result, data = _evaluate(bc_setup, mode)
    assert result.returncode == 1
    assert data["outcome"]["state"] == "incorrect" and reason in data["outcome"]["reason"]
    assert data["correctness"]["state"] == "failed"


def test_bc_native_evaluation_rejects_a_bfs_trial_format(bc_setup):
    result, data = _evaluate(bc_setup, "bfs_format")
    assert result.returncode == 1 and "wrong format" in data["outcome"]["reason"]


def test_bc_native_evaluation_refuses_a_vacuous_source(bc_setup):
    result, data = _evaluate(bc_setup, sources=[5])
    assert result.returncode == 1
    assert "no outgoing edge" in data["outcome"]["reason"]


def test_bc_native_evaluation_refuses_the_bfs_roi(bc_setup):
    result, data = _evaluate(bc_setup, roi="bfs.complete_call.v1")
    assert result.returncode == 1 and "bc.complete_call.v1" in data["outcome"]["reason"]


def test_bcverifier_reproduction_rules():
    from swdb.bc_native import reference_scores, verify_scores
    adjacency = [[1, 2], [3, 4], [3], [4], [5], []]
    scores, depth = reference_scores(adjacency, 0, "double")
    assert depth == [0, 1, 1, 2, 2, 3]
    assert verify_scores(adjacency, 0, scores, "double")["passed"]
    assert verify_scores(adjacency, 0, scores, "float")["passed"]
    assert not verify_scores(adjacency, 5, [0.0] * 6)["passed"]  # biggest reference score is zero
    assert not verify_scores(adjacency, 6, scores)["passed"]
    assert not verify_scores(adjacency, 0, [True] + scores[1:])["passed"]
    shifted = list(scores)
    shifted[4] += 2 ** -22  # beyond float epsilon after float rounding
    assert not verify_scores(adjacency, 0, shifted, "double")["passed"]
    # Stricter than BCVerifier's '>' test, which accepts NaN at any vertex.
    assert not verify_scores(adjacency, 0, scores[:1] + [None] + scores[2:], "double")["passed"]
    assert not verify_scores(adjacency, 0, scores[:1] + [float("inf")] + scores[2:], "double")["passed"]
    with pytest.raises(ValueError):
        reference_scores(adjacency, 0, "half")


def test_bc_plugin_is_registered_beside_bfs():
    from swdb import kernels
    assert kernels.ids() == ["gapbs-bc", "gapbs-bfs"]
    assert kernels.get("gapbs-bc") is kernels.BC and kernels.by_native_roi("bc.complete_call.v1") is kernels.BC
    assert kernels.by_native_verifier("swdb.bc.brandes_scores.v1") is kernels.BC
    assert kernels.by_native_verifier(None) is kernels.BFS
    assert kernels.BC.check_native_trial([[1], []], 0, {"scores": [1.0, 0.0]}, application="mystery")["passed"] is False


def _bc_workload_request(records, tmp_path, graph, name, sources):
    request = _workload_request(records, tmp_path, graph, name)
    request.update(kernel="gapbs-bc", sources=sources)
    return request


def test_bc_workload_registration_refuses_a_source_without_outgoing_edges(records, tmp_path):
    records.copy_repo()
    refused = _bc_workload_request(records, tmp_path, GRAPH, "bc-graph", [0, 5])
    result = records.swdb("register-workload", _payload(tmp_path, "refused", refused), "--format", "json")
    assert result.returncode == 1 and "outgoing edge" in result.stderr
    accepted = _bc_workload_request(records, tmp_path, GRAPH, "bc-graph", [0, 1])
    workload = _command(records, "register-workload", _payload(tmp_path, "accepted", accepted))
    assert workload["definition"]["kernel"] == "gapbs-bc" and workload["definition"]["sources"] == [0, 1]


def test_sg_out_degrees_read_the_serialized_offsets(tmp_path):
    from swdb.bfs_protocol import _sg_out_degrees
    for width, kind in ((4, "gapbs_sg32le"), (8, "gapbs_sg64le")):
        path = tmp_path / kind
        path.write_bytes(_sg(GRAPH, width))
        assert _sg_out_degrees({"path": str(path), "format": kind}, [0, 1, 5]) == {0: 2, 1: 2, 5: 0}


def test_bc_workloads_reuse_registered_bfs_graphs(records, tmp_path):
    """Kronecker/uniform BC workloads copy a registered BFS workload's exact graph files."""
    records.copy_repo()
    bfs = _workload_request(records, tmp_path, GRAPH, "bfs-graph")
    bfs.update(family="kronecker", sources=[0, 5])
    registered = _command(records, "register-workload", _payload(tmp_path, "bfs", bfs))
    module = load_script(REPO / "scripts/register_bc_workloads.py", "register_bc_workloads")
    from swdb.store import Store
    store = Store(records.path)
    vacuous = module.build_request(store, registered["id"], "bc-kronecker-fixture")
    result = records.swdb("register-workload", _payload(tmp_path, "bc-vacuous", vacuous), "--format", "json")
    assert result.returncode == 1 and "outgoing edge" in result.stderr
    request = module.build_request(store, registered["id"], "bc-kronecker-fixture", sources=[0, 1])
    bc = _command(records, "register-workload", _payload(tmp_path, "bc", request))
    assert bc["definition"]["kernel"] == "gapbs-bc" and bc["definition"]["family"] == "kronecker"
    assert bc["definition"]["canonical_sha256"] == registered["definition"]["canonical_sha256"]
    assert [row["sha256"] for row in bc["definition"]["representations"]] == \
        [row["sha256"] for row in registered["definition"]["representations"]]
    contract = registered["id"]
    with pytest.raises(Exception, match="neither"):
        module.build_request(store, contract, "bc-other", families={"uniform_random"})


def _bc_protocol(records, tmp_path, base):
    request = _bc_workload_request(records, tmp_path, GRAPH, "bc-protocol-graph", [0])
    workload = _command(records, "register-workload", _payload(tmp_path, "bc-register", request))
    settings = _settings(base, workload)
    settings.update(kernel="gapbs-bc", roi="bc.complete_call.v1")
    settings["instrumentation"] = {role: {"template_sha256": _hash(REPO / "tools/bc_native/driver.cc.in"),
                                          "treatment": "included"} for role in ("baseline", "candidate")}
    settings["correctness"]["verifier"] = "swdb.bc.brandes_scores.v1"
    return workload, settings


def test_bc_native_protocol_freezes_and_binds_its_verifier_and_roi(bc_setup, tmp_path):
    records, _, _, base = bc_setup
    workload, settings = _bc_protocol(records, tmp_path, base)
    freeze = {"message_version": "1.0", "id": "bc-native-policy", "version": 1, "settings": settings}
    frozen = _command(records, "freeze-protocol", _payload(tmp_path, "freeze", freeze))
    assert frozen["settings"]["kernel"] == "gapbs-bc" and list(frozen["workload_identities"]) == [workload["id"]]
    for key, value, message in (("verifier", "swdb.bfs.structural.v1", "does not belong to the BC kernel plug-in"),
                                ("roi", "bfs.complete_call.v1", "bc.complete_call.v1 ROI")):
        changed = json.loads(json.dumps(settings))
        if key == "verifier":
            changed["correctness"]["verifier"] = value
        else:
            changed["roi"] = value
        refused = {"message_version": "1.0", "id": f"bc-bad-{key}", "version": 1, "settings": changed}
        result = records.swdb("freeze-protocol", _payload(tmp_path, f"bad-{key}", refused), "--format", "json")
        assert result.returncode == 1 and message in result.stderr


def test_bc_native_protocol_refuses_a_bfs_workload(bc_setup, tmp_path):
    records, _, _, base = bc_setup
    _, settings = _bc_protocol(records, tmp_path, base)
    bfs = _command(records, "register-workload", _payload(tmp_path, "bfs-register",
                                                          _workload_request(records, tmp_path, GRAPH, "bfs-in-bc")))
    settings["workloads"] = [bfs["id"]]
    freeze = {"message_version": "1.0", "id": "bc-mixed-policy", "version": 1, "settings": settings}
    result = records.swdb("freeze-protocol", _payload(tmp_path, "mixed", freeze), "--format", "json")
    assert result.returncode == 1 and "different kernel" in result.stderr


def _random_graph(n, seed):
    rng = random.Random(seed)
    edges = set()
    for _ in range(n * 6):
        u, v = rng.randrange(n), rng.randrange(n)
        if u != v:
            edges |= {(u, v), (v, u)}
    adjacency = [[] for _ in range(n)]
    for u, v in sorted(edges):
        adjacency[u].append(v)
    return adjacency


def _run_driver(binary, adjacency, source, tmp_path, env=None):
    graph = tmp_path / "graph.swdb"
    graph.write_text(f"SWDBGRAPH1 {len(adjacency)} {sum(map(len, adjacency))} 1\n"
                     + "".join(f"{u} {v}\n" for u, row in enumerate(adjacency) for v in row))
    output = tmp_path / "trial.json"
    result = subprocess.run([str(binary), str(graph), str(source), str(output)], capture_output=True, text=True,
                            env=env, timeout=60)
    assert result.returncode == 0, result.stderr
    return json.loads(output.read_text())


def _compile(compiler, source, tmp_path, flags, includes=()):
    wrapper = tmp_path / "driver.cc"
    template = (REPO / "tools/bc_native/driver.cc.in").read_text()
    wrapper.write_text(template.replace("#include SWDB_SOURCE_INCLUDE", "#include " + json.dumps(str(source))))
    binary = tmp_path / "bc-native"
    return subprocess.run([compiler, *flags, *(f"-I{path}" for path in includes), str(wrapper), "-o", str(binary)],
                          capture_output=True, text=True, timeout=300), binary


def test_real_bc_driver_with_upstream_gapbs_passes_the_reproduced_bcverifier(tmp_path):
    compiler = find_cxx()
    if not compiler:
        pytest.skip("C++ compiler unavailable")
    built, binary = _compile(compiler, REPO / "apps/gapbs/src/bc.cc", tmp_path, ["-std=c++11", "-O2"])
    assert built.returncode == 0, built.stderr
    from swdb.bc_native import verify_scores
    for n, seed in ((7, 1), (300, 2), (1500, 3)):
        adjacency = _random_graph(n, seed)
        source = next(u for u, row in enumerate(adjacency) if row)
        observed = _run_driver(binary, adjacency, source, tmp_path)
        assert observed["format"] == "swdb.bc.native.trial.v1" and observed["roi"] == "bc.complete_call.v1"
        assert verify_scores(adjacency, source, observed["scores"], "double")["passed"]
        observed["scores"][source] = observed["scores"][source] / 2
        assert not verify_scores(adjacency, source, observed["scores"], "double")["passed"]
    # Driver integration only; not BC workload acceptance or performance evidence.


def _snapshot_module():
    module = load_script(REPO / "scripts/prepare_dx100_bc_scalar_snapshot.py", "prepare_bc")
    return module


def _without_registered_snapshot(records, snapshot_id):
    """Drop a registered snapshot and every record that cites it, directly or transitively, from
    the temporary records copy, so registration can be tested again (2026-10-04 ET: ticket 41
    registered the real snapshot, and later BC tickets cite it)."""
    removed, files = {snapshot_id}, sorted(records.path.rglob("*.yaml"))
    while True:
        cited = [f for f in files if f.exists() and (f.stem in removed or any(i in f.read_text() for i in removed))]
        new = {f.stem for f in cited} - removed
        for f in cited:
            f.unlink()
        if not new:
            return
        removed |= new


def test_dx100_scalar_bc_snapshot_removes_the_accelerated_code_and_registers(records, tmp_path):
    records.copy_repo()
    module = _snapshot_module()
    _without_registered_snapshot(records, "bc-dx100-scalar-only-20261003-a1.source")
    original = (REPO / "apps/dx100" / module.BC).read_text()
    assert "PBFSMAA" in original and "BrandesMaa" in original
    data = module.materialize(tmp_path / "snapshot", records.path)
    source = Path(data["artifact"]["path"])
    text = (source / module.BC).read_text()
    for removed in ("PBFSMAA", "BrandesMaa", "tiles0", "regs0", "#ifdef MAA"):
        assert removed not in text
    assert "void PBFS(" in text and "bool BCVerifier(" in text
    assert not (source / "benchmarks/gapbs/src/bfs.cc").exists()
    verifier = data["context"]["evaluator"]["verifier"]["code"]
    first, last = verifier["lines"]
    assert text.splitlines()[first - 1].startswith("// Still uses Brandes") and "return all_ok;" in text.splitlines()[last - 2]
    assert data["context"]["build"]["flags"] == "-std=c++11 -O3 -Wall -fopenmp -pthread -DFUNC"
    request = tmp_path / "snapshot.yaml"
    from swdb import yamlio
    request.write_text(yamlio.dumps(data))
    added = records.swdb("add", request)
    assert added.returncode == 0, added.stderr + added.stdout
    with pytest.raises(Exception, match="pinned"):
        module.scalar_source(original.replace("PBFSMAA", "PBFSX", 1))


def test_real_bc_driver_with_the_dx100_scalar_snapshot_passes_float_bcverifier(records, tmp_path):
    compilers = [path for path in (shutil.which("clang++"), "/opt/homebrew/opt/llvm/bin/clang++", shutil.which("g++"))
                 if path and Path(path).exists()]
    records.copy_repo()
    data = _snapshot_module().materialize(tmp_path / "snapshot", records.path)
    source = Path(data["artifact"]["path"])
    includes = [source / "benchmarks/API", source / "benchmarks/gapbs/src"]
    # The DX100 platform atomics require OpenMP; use the first compiler that builds it here.
    binary = None
    for compiler in compilers:
        library = Path(compiler).resolve().parent.parent / "lib"
        flags = ["-std=c++11", "-O2", "-fopenmp", "-DFUNC", f"-L{library}", f"-Wl,-rpath,{library}"]
        built, candidate = _compile(compiler, source / "benchmarks/gapbs/src/bc.cc", tmp_path, flags, includes)
        if built.returncode == 0:
            binary = candidate
            break
    if binary is None:
        pytest.skip("no OpenMP-capable C++ compiler for the DX100 BC source")
    from swdb.bc_native import verify_scores
    adjacency = _random_graph(400, 5)
    source_vertex = next(u for u, row in enumerate(adjacency) if row)
    observed = _run_driver(binary, adjacency, source_vertex, tmp_path,
                           env={"OMP_NUM_THREADS": "4", "TMPDIR": str(tmp_path)})
    assert verify_scores(adjacency, source_vertex, observed["scores"], "float")["passed"]
