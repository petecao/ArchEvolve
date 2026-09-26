"""Actual execution-grid aggregation contract through fresh CLI calls. Date 2026-09-25.

All timings and simulator-shaped records here are explicitly contract fixtures.
"""
import copy
import datetime
import hashlib
import json
import shutil

import pytest

from conftest import records as records_fixture
from test_bfs_protocol import protocol_seed, _payload, _command, _model_identity_fixture


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


@pytest.fixture(scope="module")
def simulation_seed(protocol_seed, tmp_path_factory):
    original, workload, _, request, evaluations, _ = protocol_seed
    tmp = tmp_path_factory.mktemp("simulation-grid")
    records = records_fixture.__wrapped__(tmp)
    shutil.copytree(original.path, records.path, dirs_exist_ok=True)
    request = copy.deepcopy(request)
    request["id"] = "simulated-fixture-policy"
    settings = request["settings"]
    settings["mode"] = "controlled_simulator"
    settings["sampling"]["repetitions"] = 2
    configuration = {"cpu": "fixture_cpu", "cache": "fixture_cache", "memory": "fixture_memory",
                     "clock_hz": 1000000000, "model_revision": "fixture_revision"}
    settings["targets"] = {role: {"id": "fixture_dx100", "configuration": configuration} for role in ("baseline", "candidate")}
    identity = _model_identity_fixture(records, tmp, settings, evaluations)
    frozen = _command(records, "freeze-protocol", _payload(tmp, "freeze-simulated", request))
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    components = {}
    for role in ("baseline", "candidate"):
        components[role] = []
        base = evaluations[role]
        for position, source in enumerate(workload["definition"]["sources"]):
            for repetition in range(2):
                item = copy.deepcopy(base)
                item["id"] = f"sim-{role}-{position}-{repetition}"
                item["request"].update(fixture=True, protocol=frozen["id"], protocol_role=role,
                                       protocol_trial={"source_position": position, "repetition": repetition})
                item["build"].update(model_build=identity["model_build"], simulator=identity["simulator"]["path"],
                                     simulator_sha256=identity["simulator"]["sha256"])
                context = item["context"]
                context.update(protocol=frozen["id"], protocol_trial=item["request"]["protocol_trial"],
                               sources=[source], repetitions=1, target="fixture_dx100",
                               backend_configuration=configuration, basis="simulated")
                context["workload"]["sources"] = [source]
                context["protocol_binding"] = {"protocol": frozen["id"], "frozen_sha256": frozen["identity_sha256"],
                    "settings_sha256": _digest(frozen["settings"]), "workload_id": workload["id"],
                    "workload_sha256": workload["identity_sha256"], "role": role,
                    "frozen_at": frozen["frozen_at"], "bound_at": now}
                context["execution_binding"] = {"execution": item["id"], "binary_sha256": item["build"]["binary_sha256"]}
                row = next(copy.deepcopy(row) for row in base["timing"]
                           if row["source_position"] == position and row["repetition"] == repetition)
                row.update(basis="simulated", quantity="simulated_roi_seconds")
                item["timing"] = [row]
                check = next(copy.deepcopy(row) for row in base["correctness"]["checks"]
                             if row["source_position"] == position and row["repetition"] == repetition)
                item["correctness"]["checks"] = [check]
                item["stages"] = [{"stage": "fixture_simulator", "state": "complete", "started": now}]
                result = records.swdb("add", _payload(tmp, item["id"], item))
                assert result.returncode == 0, result.stderr
                components[role].append(item)
    return records, frozen, components


@pytest.fixture
def simulation_setup(records, simulation_seed):
    original, frozen, components = simulation_seed
    shutil.copytree(original.path, records.path, dirs_exist_ok=True)
    return records, copy.deepcopy(frozen), copy.deepcopy(components)


def _aggregate(records, tmp, frozen, role, components, name=None, succeeds=True):
    request = {"message_version": "1.0", "id": name or f"aggregate-{role}", "protocol": frozen["id"],
               "protocol_role": role, "evaluations": [row["id"] for row in components]}
    return _command(records, "aggregate-evaluations", _payload(tmp, request["id"], request), succeeds=succeeds)


def test_complete_actual_grid_retains_components_and_compares_as_fixture(simulation_setup, tmp_path):
    records, frozen, components = simulation_setup
    aggregated = {role: _aggregate(records, tmp_path, frozen, role, rows) for role, rows in components.items()}
    for role, result in aggregated.items():
        assert result["outcome"]["state"] == "complete"
        assert result["evidence_kind"] == "contract_fixture" and result["gain_claim"] is False
        assert result["component_evaluations"] == [{"evaluation": row["id"], "sha256": _digest(row)} for row in components[role]]
        assert len(result["timing"]) == 4 and len(result["correctness"]["checks"]) == 4
        assert result["context"]["sources"] == [0, 4] and result["context"]["repetitions"] == 2
    request = {"message_version": "1.0", "id": "simulated-fixture-comparison", "protocol": frozen["id"],
               "baseline_evaluation": aggregated["baseline"]["id"], "candidate_evaluation": aggregated["candidate"]["id"],
               "comparison_baseline": "gapbs-bfs-do"}
    compared = _command(records, "compare-evaluations", _payload(tmp_path, request["id"], request))
    assert compared["decision"]["state"] == "fixture_comparison" and compared["metrics"]["fixture_ratio"] == 2
    later = records.swdb("get", aggregated["candidate"]["id"], "--chain", "--format", "json")
    assert later.returncode == 0, later.stderr
    assert all(row["id"] in json.loads(later.stdout)["records"] for row in components["candidate"])


@pytest.mark.parametrize("fault", ["missing", "duplicate-id", "duplicate-cell", "binary", "configuration", "failed", "prefreeze", "multi-trial", "promoted-fixture"])
def test_incomplete_or_mismatched_components_are_retained(simulation_setup, tmp_path, fault):
    records, frozen, components = simulation_setup
    rows = components["candidate"]
    if fault == "missing": rows.pop()
    elif fault == "duplicate-id": rows.append(rows[0])
    else:
        row = rows[-1]
        if fault == "duplicate-cell": row["context"]["protocol_trial"]["repetition"] = 0
        elif fault == "binary": row["build"]["binary_sha256"] = "f" * 64
        elif fault == "configuration": row["context"]["backend_configuration"]["cache"] = "other"
        elif fault == "failed": row["outcome"]["state"] = "failed"
        elif fault == "prefreeze": row["context"]["protocol_binding"]["bound_at"] = "2000-01-01T00:00:00Z"
        elif fault == "multi-trial": row["timing"].append(copy.deepcopy(row["timing"][0]))
        elif fault == "promoted-fixture": row["evidence_kind"] = "execution"
        records.write(f"evaluations/{row['id']}.yaml", row)
    result = _aggregate(records, tmp_path, frozen, "candidate", rows, succeeds=False)
    assert result["outcome"]["state"] == "incompatible" and result["outcome"]["reason"]
    assert not result["gain_claim"] and result["correctness"]["state"] == "unverified"
    saved = records.swdb("get", result["id"], "--format", "json")
    assert saved.returncode == 0 and json.loads(saved.stdout)["request"]["evaluations"] == [row["id"] for row in rows]


def test_changed_component_invalidates_later_comparison(simulation_setup, tmp_path):
    records, frozen, components = simulation_setup
    baseline = _aggregate(records, tmp_path, frozen, "baseline", components["baseline"])
    candidate = _aggregate(records, tmp_path, frozen, "candidate", components["candidate"])
    row = components["candidate"][0]
    row["timing"][0]["duration_s"] *= 100
    records.write(f"evaluations/{row['id']}.yaml", row)
    request = {"message_version": "1.0", "id": "changed-component-comparison", "protocol": frozen["id"],
               "baseline_evaluation": baseline["id"], "candidate_evaluation": candidate["id"], "comparison_baseline": "gapbs-bfs-do"}
    result = _command(records, "compare-evaluations", _payload(tmp_path, request["id"], request), succeeds=False)
    assert result["decision"]["state"] == "rejected"
    assert "component evidence changed" in str(result["decision"]["reasons"])


def test_aggregate_cannot_relabel_component_provenance(simulation_setup, tmp_path):
    records, frozen, components = simulation_setup
    baseline = _aggregate(records, tmp_path, frozen, "baseline", components["baseline"])
    candidate = _aggregate(records, tmp_path, frozen, "candidate", components["candidate"])
    # Keep the sealed policy, timing rows, and all component hashes intact while
    # inventing a different compiler command around the same purported binary.
    candidate["build"]["command"] = ["different-build-provenance"]
    records.write(f"evaluations/{candidate['id']}.yaml", candidate)
    request = {"message_version": "1.0", "id": "relabeled-aggregate-comparison", "protocol": frozen["id"],
               "baseline_evaluation": baseline["id"], "candidate_evaluation": candidate["id"], "comparison_baseline": "gapbs-bfs-do"}
    result = _command(records, "compare-evaluations", _payload(tmp_path, request["id"], request), succeeds=False)
    assert "source/binary identity differs" in str(result["decision"]["reasons"])
