"""Evaluator v2: compiled BFS verifier and scalable driver. Created 2026-10-04 ET (ticket 63).

Differential tests: the compiled verifier (tools/bfs_native/bfs_verify.cc) and
swdb.bfs_native.verify_parents return the same verdict mapping, first-failure
reason included, on fixture graphs and on mutated parent vectors. The end-to-end
paired test uses an external compiler contract fixture for the candidate (fixture
durations, never performance evidence) and the real host compiler for the verifier.
"""

import copy
import json
import random
import shutil
import struct
import subprocess
from collections import deque
from pathlib import Path

import pytest

from conftest import REPO, make_records
from testkit.proposals import build_proposal_setup
from testkit.bfs_native import build_evaluation_setup
from testkit.bfs_protocol import _command, _payload, _settings, _sg, _workload_request
from swdb import artifacts
from swdb.bfs_native import verify_parents
from testkit.bfs_native_scalable import COMPILER, FIXTURE_CANDIDATE, PROGRAM_V2, _bfs, _graphs, _rows

pytestmark = pytest.mark.skipif(COMPILER is None, reason="C++ compiler unavailable")


def _depths(adjacency, source):
    depth = [-1] * len(adjacency)
    depth[source] = 0
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v in adjacency[u]:
            if depth[v] == -1:
                depth[v] = depth[u] + 1
                queue.append(v)
    return depth


def _compiled(binary, sg_path, width, source, parents, tmp_path):
    file = tmp_path / "parents.i32"
    file.write_bytes(struct.pack("<" + "i" * len(parents), *parents))
    done = subprocess.run([str(binary), str(sg_path), str(width), str(source), str(file)],
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def _mutations(adjacency, source, parents, rng):
    """Named mutated parent vectors; each must be rejected by both verifiers."""
    n = len(adjacency)
    depth = _depths(adjacency, source)
    reachable = [v for v in range(n) if depth[v] > 0]
    unreachable = [v for v in range(n) if depth[v] < 0]
    incoming = [set() for _ in range(n)]
    for u, row in enumerate(adjacency):
        for v in row:
            incoming[v].add(u)
    cases = {}
    if reachable:
        v = rng.choice(reachable)
        non_neighbors = [w for w in range(n) if w not in incoming[v] and w != v]
        if non_neighbors:
            wrong = list(parents)
            wrong[v] = rng.choice(non_neighbors)
            cases["wrong_parent"] = wrong
        missing = list(parents)
        missing[v] = -1
        cases["reachable_without_parent"] = missing
        same_or_deeper = [w for w in incoming[v] if depth[w] >= depth[v]]
        if same_or_deeper:
            deep = list(parents)
            deep[v] = same_or_deeper[0]
            cases["parent_depth_wrong"] = deep
    if unreachable:
        marked = list(parents)
        marked[rng.choice(unreachable)] = source
        cases["unreachable_marked_reached"] = marked
    edges = [(a, b) for a in reachable for b in adjacency[a] if depth[b] > 0 and a in adjacency[b]]
    if edges:
        a, b = edges[0]
        cycle = list(parents)
        cycle[a], cycle[b] = b, a
        cases["cycle"] = cycle
    others = [w for w in range(n) if w != source]
    lost = list(parents)
    lost[source] = -1 if rng.random() < 0.5 else rng.choice(others)
    cases["source_not_own_parent"] = lost
    out_of_range = list(parents)
    out_of_range[rng.randrange(n)] = n
    cases["parent_out_of_range"] = out_of_range
    below = list(parents)
    below[rng.randrange(n)] = -2
    cases["parent_below_minus_one"] = below
    cases["too_short"] = parents[:-1]
    cases["too_long"] = parents + [-1]
    return cases


@pytest.mark.parametrize("width", [4, 8])
@pytest.mark.parametrize("name", list(_graphs()))
def test_compiled_verifier_matches_verify_parents(verifier, tmp_path, name, width):
    graph = _graphs()[name]
    adjacency = _rows(graph)
    sg_path = tmp_path / f"{name}.sg"
    sg_path.write_bytes(_sg(graph, width))
    rng = random.Random(f"{name}-{width}")
    n = graph["num_vertices"]
    for source in sorted({0, n - 1, rng.randrange(n)}):
        for reverse in (False, True):   # two distinct valid parent trees both pass
            parents = _bfs(adjacency, source, reverse)
            expected = verify_parents(adjacency, source, parents)
            assert expected["passed"] is True
            assert _compiled(verifier, sg_path, width, source, parents, tmp_path) == expected
        parents = _bfs(adjacency, source)
        for case, mutated in _mutations(adjacency, source, parents, rng).items():
            expected = verify_parents(adjacency, source, mutated)
            assert expected["passed"] is False, case
            assert _compiled(verifier, sg_path, width, source, mutated, tmp_path) == expected, case
        # Wrong source: a valid tree for one source checked against another.
        other = (source + 1) % n
        expected = verify_parents(adjacency, other, parents)
        assert expected["passed"] is False
        assert _compiled(verifier, sg_path, width, other, parents, tmp_path) == expected
    for source in (-1, n):
        expected = verify_parents(adjacency, source, _bfs(adjacency, 0))
        assert expected == {"passed": False, "reason": "source outside graph"}
        assert _compiled(verifier, sg_path, width, source, _bfs(adjacency, 0), tmp_path) == expected
    # Random single-entry corruption: the two verifiers agree on every verdict.
    base = _bfs(adjacency, 0)
    for _ in range(60):
        mutated = list(base)
        mutated[rng.randrange(n)] = rng.randrange(-2, n + 1)
        assert _compiled(verifier, sg_path, width, 0, mutated, tmp_path) == verify_parents(adjacency, 0, mutated)


def test_compiled_verifier_refuses_malformed_inputs_without_a_verdict(verifier, tmp_path):
    graph = _graphs()["path"]
    good = _sg(graph, 4)
    parents = tmp_path / "parents.i32"
    parents.write_bytes(struct.pack("<6i", *_bfs(_rows(graph), 0)))
    for name, raw in {"truncated": good[:-1], "trailing": good + b"\0", "header": b"\x02" + good[1:],
                      "neighbor": good[:-4] + struct.pack("<i", 99)}.items():
        path = tmp_path / f"{name}.sg"
        path.write_bytes(raw)
        done = subprocess.run([str(verifier), str(path), "4", "0", str(parents)], capture_output=True, text=True)
        assert done.returncode == 3 and done.stdout == "", name
    path = tmp_path / "good.sg"
    path.write_bytes(good)
    done = subprocess.run([str(verifier), str(path), "8", "0", str(parents)], capture_output=True, text=True)
    assert done.returncode == 3


def _driver(tmp_path, source, flags=(), compiler=None):
    wrapper = tmp_path / "driver.cc"
    template = (REPO / "tools/bfs_native/driver_scalable.cc.in").read_text()
    wrapper.write_text(template.replace("#include SWDB_SOURCE_INCLUDE", "#include " + json.dumps(str(source))))
    binary = tmp_path / "driver"
    built = subprocess.run([compiler or COMPILER, "-std=c++11", "-O2", *flags, str(wrapper), "-o", str(binary)],
                           capture_output=True, text=True)
    assert built.returncode == 0, built.stderr[-3000:]
    return binary


@pytest.mark.parametrize("directed", [False, True])
def test_scalable_driver_maps_sg_and_its_output_passes_both_verifiers(verifier, tmp_path, directed):
    source_file = tmp_path / "fixture.cc"
    source_file.write_text(FIXTURE_CANDIDATE)
    binary = _driver(tmp_path, source_file)
    graph = _graphs()["directed" if directed else "split"]
    adjacency = _rows(graph)
    for width in (4, 8):
        sg = tmp_path / f"g{width}.sg"
        sg.write_bytes(_sg(graph, width))
        record, parents = tmp_path / "trial.json", tmp_path / "trial.parents.i32"
        done = subprocess.run([str(binary), str(sg), str(width), "3", str(record), str(parents)],
                              capture_output=True, text=True)
        assert done.returncode == 0, done.stderr
        observed = json.loads(record.read_text())
        assert observed["format"] == "swdb.bfs.native.trial.v2" and observed["num_vertices"] == graph["num_vertices"]
        assert observed["parents_bytes"] == parents.stat().st_size == 4 * graph["num_vertices"]
        vector = list(struct.unpack(f"<{graph['num_vertices']}i", parents.read_bytes()))
        assert vector == _bfs(adjacency, 3)
        done = subprocess.run([str(verifier), str(sg), str(width), "3", str(parents)], capture_output=True, text=True)
        assert json.loads(done.stdout) == verify_parents(adjacency, 3, vector)
    broken = _driver(tmp_path, source_file, ["-DSWDB_BROKEN"])
    record, parents = tmp_path / "broken.json", tmp_path / "broken.i32"
    subprocess.run([str(broken), str(sg), "8", "3", str(record), str(parents)], check=True)
    vector = list(struct.unpack(f"<{graph['num_vertices']}i", parents.read_bytes()))
    done = subprocess.run([str(verifier), str(sg), "8", "3", str(parents)], capture_output=True, text=True)
    assert json.loads(done.stdout) == verify_parents(adjacency, 3, vector)
    assert json.loads(done.stdout)["passed"] is False


@pytest.mark.parametrize("application", ["gapbs", "dx100"])
def test_scalable_driver_builds_the_real_baseline_sources(verifier, tmp_path, application):
    """Mac (arm64) build of both baseline applications; mbit10 (x86_64) builds them in the campaign."""
    if application == "gapbs":
        source, includes, flags = REPO / "apps/gapbs/src/bfs.cc", [REPO / "apps/gapbs/src"], []
    else:
        source = REPO / "apps/dx100/benchmarks/gapbs/src/bfs.cc"
        includes, flags = [source.parent, REPO / "apps/dx100/benchmarks/API"], ["-DFUNC"]
    if not source.is_file():
        pytest.skip("application source unavailable")
    # The baselines build with GCC and -fopenmp (the DX100 fork's source is GCC-only).
    gcc = next((shutil.which(name) for name in ("g++-16", "g++-15", "g++-14", "g++-13", "g++")
                if shutil.which(name) and "clang" not in subprocess.run(
                    [shutil.which(name), "--version"], capture_output=True, text=True).stdout.lower()), None)
    if gcc is None:
        pytest.skip("GCC unavailable")
    flags += ["-fopenmp"]
    binary = _driver(tmp_path, source, [*flags, *(f"-I{p}" for p in includes)], compiler=gcc)
    graph = _graphs()["undirected"]
    width = 4 if application == "dx100" else 8
    sg = tmp_path / "g.sg"
    sg.write_bytes(_sg(graph, width))
    record, parents = tmp_path / "trial.json", tmp_path / "trial.i32"
    done = subprocess.run([str(binary), str(sg), str(width), "0", str(record), str(parents)],
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    done = subprocess.run([str(verifier), str(sg), str(width), "0", str(parents)], capture_output=True, text=True)
    verdict = json.loads(done.stdout)
    vector = list(struct.unpack(f"<{graph['num_vertices']}i", parents.read_bytes()))
    assert verdict == verify_parents(_rows(graph), 0, vector) and verdict["passed"] is True


# --- public evaluator path --------------------------------------------------------------


def _v2_settings(base, workload):
    settings = _settings(base, workload)
    template = artifacts.file_hash(REPO / "tools/bfs_native/driver_scalable.cc.in")
    settings["evaluator"] = "swdb.native.evaluator.scalable.v2"
    settings["correctness"]["verifier"] = "swdb.bfs.structural.compiled.v2"
    settings["instrumentation"] = {role: {"template_sha256": template, "treatment": "included"}
                                   for role in ("baseline", "candidate")}
    collection = {"method": "native_paired.v1", "order_seed": 20260926}
    settings["sampling"].update(collection=collection, analysis="paired_repetition_block_bootstrap.v1")
    settings["profitability"].update(minimum_speedup=1.05, bootstrap_seed=20260925, maximum_relative_spread=10)
    return settings, collection


@pytest.fixture(scope="module")
def v2_seed(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("v2-seed")
    records = make_records(tmp)
    setup = build_evaluation_setup(build_proposal_setup(records, tmp), tmp)
    _, runs, _, base = setup
    compiler = Path(base["build"]["compiler"])
    compiler.write_text("#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\n"
                        "if '--version' in sys.argv:\n print('SWDB external compiler contract fixture v1'); sys.exit(0)\n"
                        f"p=Path(sys.argv[sys.argv.index('-o')+1]); p.write_text({PROGRAM_V2!r}); p.chmod(0o755)\n")
    workload = _command(records, "register-workload", _payload(tmp, "workload",
                        _workload_request(records, tmp, base["workload"]["graph"])))
    result = records.swdb("baseline-candidate", "test-source", "--id", "v2-source-baseline",
                         "--runs-dir", runs, "--format", "json")
    assert result.returncode == 0, result.stderr
    baseline = json.loads(result.stdout)["id"]
    settings, collection = _v2_settings(base, workload)
    frozen = _command(records, "freeze-protocol", _payload(tmp, "policy", {
        "message_version": "1.0", "id": "v2-policy", "version": 1, "settings": settings}))
    request = {"message_version": "1.0", "id": "v2-pair", "collection": collection, "budget": {"total_seconds": 600}}
    for role in ("baseline", "candidate"):
        request[role] = {**copy.deepcopy(base), "id": "v2." + role,
            "candidate": baseline if role == "baseline" else base["candidate"], "protocol_role": role,
            "protocol": frozen["id"], "workload": {"id": workload["id"]},
            "sources": workload["definition"]["sources"], "repetitions": 5,
            "budget": {"build_seconds": 120, "run_seconds": 30, "total_seconds": 600}}
    pair = records.swdb("evaluate-pair", _payload(tmp, "pair", request), "--runs-dir", runs, "--format", "json")
    assert pair.returncode == 0, pair.stdout + pair.stderr
    pair = json.loads(pair.stdout)
    comparison = {"message_version": "1.0", "id": "v2-comparison", "protocol": frozen["id"],
                  "baseline_evaluation": pair["baseline_evaluation"], "candidate_evaluation": pair["candidate_evaluation"],
                  "comparison_baseline": "gapbs-bfs-do"}
    return records, runs, request, pair, frozen, comparison, workload


@pytest.fixture
def v2_setup(records, v2_seed):
    seed, *data = v2_seed
    shutil.copytree(seed.path, records.path, dirs_exist_ok=True)
    return records, *copy.deepcopy(data)


def test_v2_pair_verifies_every_trial_with_the_compiled_verifier(v2_setup, tmp_path):
    records, runs, request, pair, frozen, comparison, workload = v2_setup
    assert pair["outcome"]["state"] == "complete"
    evaluation = json.loads(records.swdb("get", pair["candidate_evaluation"], "--format", "json").stdout)
    context, build = evaluation["context"], evaluation["build"]
    assert context["evaluator"] == "swdb.native.evaluator.scalable.v2"
    assert context["verifier"] == "swdb.bfs.structural.compiled.v2"
    assert context["verifier_sha256"] == artifacts.file_hash(REPO / "tools/bfs_native/bfs_verify.cc")
    assert build["verifier"]["flags"] == ["-std=c++11", "-O2"]
    assert context["workload"]["graph_input"]["format"] == "gapbs_sg64le"
    assert not any(Path(row["path"], "graph.swdb").exists() for row in evaluation["raw_artifacts"])
    checks = evaluation["correctness"]["checks"]
    assert len(checks) == 10 and all(c["passed"] and c["verifier"] == context["verifier"] for c in checks)
    for observation in evaluation["timing"]:
        assert observation["parents_output"].endswith(".parents.i32.gz") and Path(observation["parents_output"]).is_file()
    result = _command(records, "compare-evaluations", _payload(tmp_path, "compare", comparison))
    assert result["decision"]["state"] == "fixture_comparison", result["decision"]


def test_v2_comparison_rejects_a_changed_retained_parent_vector(v2_setup, tmp_path):
    import gzip
    records, runs, request, pair, frozen, comparison, workload = v2_setup
    evaluation = json.loads(records.swdb("get", pair["candidate_evaluation"], "--format", "json").stdout)
    retained = Path(evaluation["timing"][0]["parents_output"])
    original = retained.read_bytes()
    try:
        vector = bytearray(gzip.decompress(original))
        vector[4:8] = struct.pack("<i", 4)
        retained.write_bytes(gzip.compress(bytes(vector)))
        result = _command(records, "compare-evaluations", _payload(tmp_path, "compare", comparison), succeeds=False)
        assert result["decision"]["state"] == "rejected"
        assert "retained parent vector" in result["decision"]["reasons"][0]
    finally:
        retained.write_bytes(original)


def test_v2_incorrect_candidate_is_rejected_by_the_compiled_verifier(v2_setup, tmp_path):
    records, runs, request, pair, frozen, comparison, workload = v2_setup
    request = copy.deepcopy(request)
    request["id"] = "v2-incorrect-pair"
    for role in ("baseline", "candidate"):
        request[role]["id"] = "v2-incorrect." + role
    result = records.swdb("evaluate-pair", _payload(tmp_path, "incorrect", request), "--runs-dir", runs,
                         "--format", "json", env={"SWDB_NATIVE_FIXTURE": "unreachable_marked"})
    assert result.returncode == 1 and json.loads(result.stdout)["outcome"]["state"] != "complete"
    failed = []
    for role in ("baseline", "candidate"):
        got = records.swdb("get", "v2-incorrect." + role, "--format", "json")
        if got.returncode == 0:
            evaluation = json.loads(got.stdout)
            failed += [(evaluation["outcome"]["state"], check) for check in evaluation["correctness"]["checks"]
                       if not check["passed"]]
    assert failed, "no evaluation retained a failed check"
    state, check = failed[0]
    assert state == "incorrect" and check["verifier"] == "swdb.bfs.structural.compiled.v2"
    assert check["reason"] == "unreachable vertex 4 has a parent"


def test_v2_settings_pin_evaluator_and_verifier_together(v2_setup, tmp_path):
    records, runs, request, pair, frozen, comparison, workload = v2_setup
    settings = copy.deepcopy(frozen["settings"])
    settings["correctness"]["verifier"] = "swdb.bfs.structural.v1"
    refused = records.swdb("freeze-protocol", _payload(tmp_path, "mixed", {
        "message_version": "1.0", "id": "mixed-policy", "version": 1, "settings": settings}), "--format", "json")
    assert refused.returncode == 1 and "pinned together" in refused.stderr + refused.stdout
    settings = copy.deepcopy(frozen["settings"])
    settings.pop("evaluator")
    refused = records.swdb("freeze-protocol", _payload(tmp_path, "unpinned", {
        "message_version": "1.0", "id": "unpinned-policy", "version": 1, "settings": settings}), "--format", "json")
    assert refused.returncode == 1 and "pinned together" in refused.stderr + refused.stdout
    member = {**request["candidate"], "id": "v2.mismatch", "evaluator": "swdb.native.evaluator.v1"}
    result = records.swdb("evaluate", _payload(tmp_path, "mismatch", member), "--runs-dir", runs, "--format", "json")
    assert "differs from the frozen protocol" in json.loads(result.stdout)["outcome"]["reason"]


def test_registration_replaces_zero_out_degree_sources_and_records_it(v2_setup, tmp_path):
    """Ticket 64 (2026-10-04 ET): GAPBS SourcePicker rule, deterministic successor, recorded."""
    graph = {"num_vertices": 7, "directed": False, "edges": [[0, 1], [1, 2], [5, 6], [4, 5]]}
    records = v2_setup[0]
    request = _workload_request(records, tmp_path, graph, name="isolated-source")
    request["sources"] = [3, 4, 0]
    request["source_policy"] = "swdb.sources.next_positive_out_degree.v1"
    workload = _command(records, "register-workload", _payload(tmp_path, "isolated", request))
    definition = workload["definition"]
    assert definition["sources"] == [5, 4, 0]      # 3 is isolated; 4 is already a source, so 5
    assert definition["source_policy"]["requested_sources"] == [3, 4, 0]
    assert definition["source_policy"]["replacements"] == [
        {"requested": 3, "requested_out_degree": 0, "selected": 5, "selected_out_degree": 2}]
    request.update(id="isolated-source-unknown", source_policy="random")
    refused = records.swdb("register-workload", _payload(tmp_path, "unknown", request), "--format", "json")
    assert refused.returncode == 1
    request.pop("source_policy")
    request["id"] = "isolated-source-plain"
    plain = _command(records, "register-workload", _payload(tmp_path, "plain", request))
    assert plain["definition"]["sources"] == [3, 4, 0] and "source_policy" not in plain["definition"]
