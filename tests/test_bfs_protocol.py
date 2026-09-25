"""Public graph, freeze, and comparison workflows. Created 2026-09-25.

External compiler and simulator-shaped records are explicit contract fixtures.
Their durations never establish experimental performance.
"""

import copy
import hashlib
import json
import struct
from pathlib import Path

import pytest
import yaml

from conftest import REPO
from test_proposals import proposal_setup
from test_bfs_native import PROGRAM, evaluation_setup


NORMALIZATION = {"remove_self_loops": True, "deduplicate": True, "sort_neighbors": True,
                 "symmetrize_undirected": True}


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _payload(tmp_path, name, value):
    file = tmp_path / f"{name}.yaml"
    file.write_text(yaml.safe_dump(value))
    return file


def _command(records, command, file, succeeds=True):
    result = records.swdb(command, file, "--format", "json")
    assert result.returncode == (0 if succeeds else 1), result.stderr + result.stdout
    return json.loads(result.stdout) if result.stdout else None


def _sg(graph, width):
    n = graph["num_vertices"]
    rows = [set() for _ in range(n)]
    for u, v in graph["edges"]:
        if u != v:
            rows[u].add(v)
            if not graph["directed"]:
                rows[v].add(u)
    rows = [sorted(row) for row in rows]
    m = sum(map(len, rows))
    integer = "i" if width == 4 else "q"
    def csr(adjacency):
        offsets = [0]
        for row in adjacency:
            offsets.append(offsets[-1] + len(row))
        return struct.pack("<" + integer * len(offsets), *offsets) + struct.pack("<" + "i" * m, *(v for row in adjacency for v in row))
    raw = struct.pack("<?" + integer * 2, graph["directed"], m, n) + csr(rows)
    if graph["directed"]:
        reverse = [[] for _ in range(n)]
        for u, row in enumerate(rows):
            for v in row:
                reverse[v].append(u)
        raw += csr(reverse)
    return raw


def _workload_request(records, tmp_path, graph, name="small-graph"):
    records.copy_repo("applications")
    representations = []
    for kind, application in (("json_graph", "gapbs"), ("gapbs_sg32le", "dx100-gapbs"), ("gapbs_sg64le", "gapbs")):
        path = tmp_path / f"{name}.{kind}"
        path.write_bytes(json.dumps(graph).encode() if kind == "json_graph" else _sg(graph, 4 if kind.endswith("32le") else 8))
        representations.append({"id": kind, "format": kind, "application": application,
                                "path": str(path), "sha256": _hash(path)})
    return {"message_version": "1.0", "id": name, "version": 1, "kernel": "gapbs-bfs",
            "family": "contract_fixture", "generator": {"name": "handwritten-correctness-graph", "revision": "fixture-v1", "parameters": {}},
            "normalization": NORMALIZATION, "sources": [0, graph["num_vertices"] - 1], "representations": representations}


def _settings(base, workload):
    build = {**base["build"], "adapter": "gapbs_native", "compiler_version": ["SWDB external compiler contract fixture v1"]}
    instrumentation = {"template_sha256": _hash(REPO / "tools/bfs_native/driver.cc.in"), "treatment": "included"}
    return {"mode": "native", "kernel": "gapbs-bfs", "workloads": [workload["id"]],
            "targets": {role: {"id": base["machine"], "configuration": {}} for role in ("baseline", "candidate")},
            "builds": {role: build for role in ("baseline", "candidate")},
            "instrumentation": {role: instrumentation for role in ("baseline", "candidate")},
            "threads": 1, "roi": "bfs.complete_call.v1",
            "correctness": {"coverage": "every_timed_trial", "verifier": "swdb.bfs.structural.v1", "required_cases": []},
            "sampling": {"repetitions": 5, "warmups": 0, "aggregation": "geomean_source_median_ratio"},
            "profitability": {"minimum_speedup": 1.01, "maximum_relative_spread": 0.2, "confidence": 0.95,
                              "bootstrap_resamples": 2000, "bootstrap_seed": 17},
            "differences": {"software": ["Declared source rewrite under contract fixture"], "accelerator": [], "configuration": []},
            "region_pairs": []}


@pytest.fixture
def protocol_setup(evaluation_setup, tmp_path):
    records, runs, evaluate_request, base = evaluation_setup
    # The external compiler fixture emits the graph's real structural result and
    # an explicitly artificial duration selected by the test client.
    compiler = Path(base["build"]["compiler"])
    program = PROGRAM.replace('"duration_s": 0.025', '"duration_s": float(os.environ.get("SWDB_PROTOCOL_DURATION", "0.025"))')
    compiler.write_text("#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\n"
                        "if '--version' in sys.argv:\n print('SWDB external compiler contract fixture v1'); sys.exit(0)\n"
                        f"p=Path(sys.argv[sys.argv.index('-o')+1]); p.write_text({program!r}); p.chmod(0o755)\n")
    request = _workload_request(records, tmp_path, base["workload"]["graph"])
    workload = _command(records, "register-workload", _payload(tmp_path, "register", request))
    settings = _settings(base, workload)
    protocol_request = {"message_version": "1.0", "id": "fixture-policy", "version": 1, "settings": settings}
    protocol = _command(records, "freeze-protocol", _payload(tmp_path, "freeze", protocol_request))
    evaluations = {}
    for role, duration in (("baseline", "0.05"), ("candidate", "0.025")):
        file = evaluate_request(id=f"eval-{role}", protocol=protocol["id"], protocol_role=role,
                                sources=request["sources"], repetitions=5, workload={"id": workload["id"]})
        result = records.swdb("evaluate", file, "--runs-dir", runs, "--format", "json", env={"SWDB_PROTOCOL_DURATION": duration})
        assert result.returncode == 0, result.stderr + result.stdout
        evaluations[role] = json.loads(result.stdout)
    comparison = {"message_version": "1.0", "id": "compare-fixture", "protocol": protocol["id"],
                  "baseline_evaluation": evaluations["baseline"]["id"], "candidate_evaluation": evaluations["candidate"]["id"],
                  "comparison_baseline": "gapbs-bfs-do"}
    return records, workload, protocol, protocol_request, evaluations, comparison


def test_graph_representations_are_actually_equivalent_and_retrievable(protocol_setup):
    records, workload, *_ = protocol_setup
    definition = workload["definition"]
    assert definition["realized"] == {"num_vertices": 5, "num_directed_edges": 4, "directed": True,
                                       "isolated_vertices": 2, "minimum_out_degree": 0, "maximum_out_degree": 2}
    assert definition["sources"] == [0, 4]
    assert {row["canonical_sha256"] for row in definition["representations"]} == {definition["canonical_sha256"]}
    assert len({row["sha256"] for row in definition["representations"]}) == 3
    later = records.swdb("get", workload["id"], "--format", "json")
    assert json.loads(later.stdout) == workload
    assert records.swdb("build").returncode == 0
    assert json.loads(records.swdb("get", workload["id"], "--format", "json").stdout) == workload


def test_frozen_native_comparison_is_fixture_not_gain(protocol_setup, tmp_path):
    records, workload, protocol, _, evaluations, comparison = protocol_setup
    result = _command(records, "compare-evaluations", _payload(tmp_path, "compare", comparison))
    assert result["decision"]["state"] == "fixture_comparison" and not result["gain_claim"]
    assert result["metrics"]["fixture_ratio"] == pytest.approx(2)
    assert result["metrics"]["confidence_interval"]["lower"] == pytest.approx(2)
    assert result["metrics"]["workload"] == workload["id"]
    assert result["protocol_sha256"] == protocol["identity_sha256"]
    assert result["comparison_baseline"] == "gapbs-bfs-do"
    for evaluation in evaluations.values():
        assert evaluation["context"]["protocol_binding"]["frozen_sha256"] == protocol["identity_sha256"]
        assert evaluation["context"]["workload"]["canonical_sha256"] == workload["definition"]["canonical_sha256"]
    later = records.swdb("get", result["id"], "--chain", "--format", "json")
    assert later.returncode == 0, later.stderr
    assert json.loads(later.stdout)["records"][result["id"]] == result


@pytest.mark.parametrize("fault", ["different-source", "different-roi", "different-target", "different-threads",
                                   "unverified", "missing-timing", "wrong-binary", "different-graph", "pre-freeze",
                                   "host-time", "simulated-time", "missing-binding", "promoted-fixture"])
def test_incompatible_evaluations_retain_explicit_rejection(protocol_setup, tmp_path, fault):
    records, _, _, _, evaluations, comparison = protocol_setup
    candidate = copy.deepcopy(evaluations["candidate"])
    candidate["id"] = "bad-" + fault
    if fault == "different-source": candidate["context"]["sources"] = [1, 4]
    elif fault == "different-roi": candidate["context"]["roi"] = "wrapper-total"
    elif fault == "different-target": candidate["context"]["backend_configuration"] = {"unfrozen": True}
    elif fault == "different-threads": candidate["context"]["threads"] = 2
    elif fault == "unverified": candidate["correctness"]["checks"][0]["passed"] = False
    elif fault == "missing-timing": candidate["timing"].pop()
    elif fault == "wrong-binary": candidate["timing"][0]["binary_sha256"] = "f" * 64
    elif fault == "different-graph": candidate["context"]["workload"]["canonical_sha256"] = "f" * 64
    elif fault == "pre-freeze": candidate["stages"][0]["started"] = "2000-01-01T00:00:00Z"
    elif fault == "host-time": candidate["timing"][0]["roi"] = "simulator-host-cost"
    elif fault == "simulated-time": candidate["timing"][0].update(basis="simulated", quantity="simulated_roi_seconds")
    elif fault == "missing-binding": candidate["context"].pop("protocol_binding")
    else:
        candidate["evidence_kind"] = "execution"
        for timing in candidate["timing"]: timing["evidence_kind"] = "execution"
    added = records.swdb("add", _payload(tmp_path, candidate["id"], candidate))
    assert added.returncode == 0, added.stderr
    comparison.update(id="compare-" + fault, candidate_evaluation=candidate["id"])
    result = _command(records, "compare-evaluations", _payload(tmp_path, "request-" + fault, comparison), succeeds=False)
    assert result["decision"]["state"] == "rejected" and result["decision"]["reasons"]
    assert result["metrics"] == {} and not result["gain_claim"]
    assert json.loads(records.swdb("get", result["id"], "--format", "json").stdout)["decision"] == result["decision"]


def test_new_protocol_version_preserves_comparison_and_marks_rerun(protocol_setup, tmp_path):
    records, _, protocol, request, _, comparison = protocol_setup
    result = _command(records, "compare-evaluations", _payload(tmp_path, "comparison", comparison))
    request.update(version=2, supersedes=protocol["id"])
    request["settings"]["profitability"]["minimum_speedup"] = 1.1
    replacement = _command(records, "freeze-protocol", _payload(tmp_path, "new-freeze", request))
    assert replacement["id"] != protocol["id"] and replacement["supersedes"] == protocol["id"]
    assert result["id"] in replacement["invalidated_comparisons"]
    assert json.loads(records.swdb("get", result["id"], "--format", "json").stdout) == result
    comparison.update(id="compare-stale-policy", protocol=replacement["id"])
    refused = _command(records, "compare-evaluations", _payload(tmp_path, "stale", comparison), succeeds=False)
    assert "binding" in refused["decision"]["reasons"][0]


def test_raw_add_cannot_recompute_content_under_old_frozen_id(protocol_setup, tmp_path):
    records, _, protocol, *_ = protocol_setup
    forged = copy.deepcopy(protocol)
    forged["id"] = "forged-policy"
    forged["settings"]["sampling"]["repetitions"] = 99
    result = records.swdb("add", _payload(tmp_path, "forged", forged))
    assert result.returncode == 1 and "content changed" in result.stderr


@pytest.mark.parametrize("fault", ["wrong-offset-width", "wrong-adjacency", "wrong-inverse", "truncated", "wrong-hash"])
def test_registration_rejects_non_equivalent_or_invalid_files(evaluation_setup, tmp_path, fault):
    records, _, _, base = evaluation_setup
    request = _workload_request(records, tmp_path, base["workload"]["graph"])
    representation = request["representations"][1]
    path = Path(representation["path"])
    if fault == "wrong-offset-width": representation["format"] = "gapbs_sg64le"
    elif fault == "wrong-adjacency":
        graph = copy.deepcopy(base["workload"]["graph"])
        graph["edges"].append([0, 4])
        path.write_bytes(_sg(graph, 4))
        representation["sha256"] = _hash(path)
    elif fault == "wrong-inverse":
        raw = bytearray(path.read_bytes())
        raw[-4:] = struct.pack("<i", 0)
        path.write_bytes(raw)
        representation["sha256"] = _hash(path)
    elif fault == "truncated":
        path.write_bytes(path.read_bytes()[:-4])
        representation["sha256"] = _hash(path)
    else: representation["sha256"] = "f" * 64
    result = records.swdb("register-workload", _payload(tmp_path, "bad-register", request), "--format", "json")
    assert result.returncode == 1 and not result.stdout
    assert not list((records.path / "workloads").glob("*.yaml"))


def test_frozen_dispatch_rejects_wrong_sources_before_build(protocol_setup, evaluation_setup):
    records, workload, protocol, *_ = protocol_setup
    _, runs, request, _ = evaluation_setup
    result = records.swdb("evaluate", request(id="eval-wrong-source", protocol=protocol["id"], protocol_role="candidate",
                          workload={"id": workload["id"]}, sources=[1], repetitions=5), "--runs-dir", runs, "--format", "json")
    assert result.returncode == 1, result.stderr
    data = json.loads(result.stdout)
    assert "source sequence" in data["outcome"]["reason"]
    assert not any(stage["stage"] == "build" for stage in data["stages"])
