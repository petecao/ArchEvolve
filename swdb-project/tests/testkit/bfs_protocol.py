"""Workload, freeze and comparison fixtures and helpers. Created 2026-10-05 ET (code
review T1), from tests/test_bfs_protocol.py. The protocol seed runs the end-to-end
evaluation boundary once per module through the plain builders. Updated
2026-10-08 ET: seed only the real dependencies used by these contract fixtures."""

import copy
import datetime
import hashlib
import json
import shutil
import struct
from pathlib import Path

import pytest
import yaml

from conftest import REPO, make_records
from testkit.bfs_native import PROGRAM, build_evaluation_setup
from testkit.proposals import build_proposal_setup
from testkit.record_subset import copy_record_subset

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
    from swdb.bfs_native import controlled_environment, RUNTIME_INHERITED
    build = {**base["build"], "adapter": "gapbs_native", "compiler_version": ["SWDB external compiler contract fixture v1"]}
    instrumentation = {"template_sha256": _hash(REPO / "tools/bfs_native/driver.cc.in"), "treatment": "included"}
    return {"mode": "native", "kernel": "gapbs-bfs", "workloads": [workload["id"]],
            "targets": {role: {"id": base["machine"], "configuration": {}} for role in ("baseline", "candidate")},
            "builds": {role: build for role in ("baseline", "candidate")},
            "instrumentation": {role: instrumentation for role in ("baseline", "candidate")},
            "threads": 1, "roi": "bfs.complete_call.v1",
            "native_runtime": {"version": 1, "environment": {
                **controlled_environment(1), **dict.fromkeys(RUNTIME_INHERITED)}},
            "correctness": {"coverage": "every_timed_trial", "verifier": "swdb.bfs.structural.v1", "required_cases": []},
            "sampling": {"repetitions": 5, "warmups": 0, "aggregation": "geomean_source_median_ratio"},
            "profitability": {"minimum_speedup": 1.01, "maximum_relative_spread": 0.2, "confidence": 0.95,
                              "bootstrap_resamples": 2000, "bootstrap_seed": 17},
            "differences": {"software": ["Declared source rewrite under contract fixture"], "accelerator": [], "configuration": []},
            "region_pairs": []}


def _seed_protocol(evaluation_setup, tmp_path):
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
    baseline = records.swdb('baseline-candidate', 'test-source', '--id', 'protocol-source-baseline',
                            '--runs-dir', runs, '--format', 'json')
    assert baseline.returncode == 0, baseline.stderr
    baseline_id = json.loads(baseline.stdout)['id']
    evaluations = {}
    for role, duration in (("baseline", "0.05"), ("candidate", "0.025")):
        file = evaluate_request(id=f"eval-{role}", protocol=protocol["id"], protocol_role=role,
                                sources=request["sources"], repetitions=5, workload={"id": workload["id"]},
                                candidate=baseline_id if role == 'baseline' else base['candidate'])
        result = records.swdb("evaluate", file, "--runs-dir", runs, "--format", "json", env={"SWDB_PROTOCOL_DURATION": duration})
        assert result.returncode == 0, result.stderr + result.stdout
        evaluations[role] = json.loads(result.stdout)
    comparison = {"message_version": "1.0", "id": "compare-fixture", "protocol": protocol["id"],
                  "baseline_evaluation": evaluations["baseline"]["id"], "candidate_evaluation": evaluations["candidate"]["id"],
                  "comparison_baseline": "gapbs-bfs-do"}
    return records, workload, protocol, protocol_request, evaluations, comparison


@pytest.fixture(scope="module")
def protocol_seed(tmp_path_factory):
    # Run the expensive end-to-end evaluation boundary once. Each test receives
    # isolated authoritative records and performs fresh public CLI requests.
    path = tmp_path_factory.mktemp("protocol-seed")
    records = make_records(path)
    copy_record_subset(REPO / "records", records.path,
                       ["gapbs-bfs-do", "gapbs", "dx100-gapbs", "mbit10"])
    proposal = build_proposal_setup(records, path, copy_all=False)
    evaluation = build_evaluation_setup(proposal, path)
    return _seed_protocol(evaluation, path)


@pytest.fixture
def protocol_setup(records, protocol_seed):
    seed, *data = protocol_seed
    shutil.copytree(seed.path, records.path, dirs_exist_ok=True)
    return (records, *copy.deepcopy(data))


def _add_record(records, tmp_path, record):
    result = records.swdb("add", _payload(tmp_path, record["id"], record))
    assert result.returncode == 0, result.stderr


def _fixture_rebind(evaluation, protocol, role, name):
    """Explicit metadata fixture for a nonexecuted simulator/region protocol."""
    data = copy.deepcopy(evaluation)
    data["id"] = name
    settings = protocol["settings"]
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    binding = data["context"]["protocol_binding"]
    binding.update(protocol=protocol["id"], frozen_sha256=protocol["identity_sha256"],
                   settings_sha256=hashlib.sha256(json.dumps(settings, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                   frozen_at=protocol["frozen_at"], bound_at=now, role=role)
    data["request"].update(protocol=protocol["id"], protocol_role=role, fixture=True)
    data["context"].update(protocol=protocol["id"], target=settings["targets"][role]["id"],
                           backend_configuration=settings["targets"][role]["configuration"])
    for stage in data["stages"]:
        stage.update(started=now, finished=now)
    if settings["mode"] != "native":
        identity = settings.get("simulation_identity")
        if identity:
            data["build"].update(model_build=identity["model_build"], simulator=identity["simulator"]["path"],
                                 simulator_sha256=identity["simulator"]["sha256"])
        reference = settings.get("reference_artifacts", {}).get(role)
        if reference:
            data.update(candidate=reference["candidate"], source_snapshot=reference["source_snapshot"])
            data["context"]["candidate_sha256"] = reference["source_artifact_sha256"]
            data["build"].update(binary=reference["binary"]["path"], binary_sha256=reference["binary"]["sha256"])
            for row in data["timing"] + data["correctness"]["checks"]:
                row["binary_sha256"] = reference["binary"]["sha256"]
        data["context"]["basis"] = "simulated"
        for timing in data["timing"]:
            timing.update(basis="simulated", quantity="simulated_roi_seconds")
        for check in data['correctness']['checks']:
            if settings['correctness'].get('required_accelerator_cases', {}).get(role):
                check['coverage'] = {'accelerator_executed': True, 'instruction_counters': {'system.maa.numInst': 20},
                    'completed_trace_units': {unit: 2 for unit in ('S', 'I', 'R', 'A')},
                    **{key: {'state': 'observed', 'count': 1} for key in ('full_tiles', 'tail_tiles', 'competing_parent_updates')}}
    data["provenance"].append({"id": "comparison-fixture", "kind": "agent_run",
                               "description": "Explicit simulator/region metadata fixture; this protocol was not executed."})
    return data


def _sim_settings(settings):
    data = copy.deepcopy(settings)
    data.pop("native_runtime", None)
    data["mode"] = "controlled_simulator"
    common = {"cpu": {"model": "fixture-timing-cpu", "cores": 4}, "cache": {"llc_kib": 4096},
              "memory": {"kind": "fixture-ddr", "size_gib": 4}, "clock_hz": 1e9, "model_revision": "fixture-v1"}
    data["targets"] = {role: {"id": "fixture-sim-target", "configuration": {**copy.deepcopy(common), "accelerator": role == "candidate"}}
                       for role in ("baseline", "candidate")}
    data["differences"]["accelerator"] = ["Existing accelerator enabled on candidate target; fixture metadata only."]
    return data


def _model_identity_fixture(records, tmp, settings, evaluations, *, fixed=False):
    """Retained synthetic model identity; never an executed hardware model."""
    from swdb import artifacts, workflow
    simulator = tmp / "explicit-simulator-fixture"
    simulator.write_text("explicit model identity fixture\n")
    reference = {"path": str(simulator), "sha256": _hash(simulator)}
    binaries = [reference] + [{"path": row["build"]["binary"], "sha256": row["build"]["binary_sha256"]}
                              for row in evaluations.values()]
    model = workflow.record("evaluation", "explicit-model-fixture", request={"fixture": True},
        context={}, build={"details": {"revision": settings["targets"]["baseline"]["configuration"]["model_revision"],
                                      "state": "completed", "binaries": binaries}},
        outcome={"state": "complete", "stage": "build", "reason": "Explicit contract fixture"}, stages=[], timing=[],
        correctness={"state": "unverified", "checks": []}, profiling={}, raw_artifacts=[], gain_claim=False, evidence_kind="contract_fixture")
    records.write("evaluations/explicit-model-fixture.yaml", model)
    settings["simulation_identity"] = {"version": "1.0", "model_build": {"evaluation": model["id"], "sha256": artifacts.digest(model)},
                                       "simulator": reference}
    if fixed:
        settings['correctness']['required_accelerator_cases'] = {'baseline': [], 'candidate': ['executed']}
        baseline = evaluations["baseline"]
        candidate = records.read(f"candidates/{baseline['candidate']}.yaml")
        source = records.read(f"source_snapshots/{candidate['source_snapshot']}.yaml")
        item = {"candidate": candidate["id"], "candidate_sha256": artifacts.digest(candidate),
                "source_snapshot": source["id"], "source_snapshot_sha256": artifacts.digest(source),
                "source_artifact_sha256": candidate["artifact"]["sha256"],
                "binary": {"path": baseline["build"]["binary"], "sha256": baseline["build"]["binary_sha256"]}}
        settings["reference_artifacts"] = {role: copy.deepcopy(item) for role in ("baseline", "candidate")}
    return settings["simulation_identity"]
