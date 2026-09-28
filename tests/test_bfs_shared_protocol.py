"""R10 shared-protocol aggregation contracts through fresh CLI calls. Created 2026-09-27 ET.

Contract fixtures only: one set of candidate components retains exact bindings for
two frozen policies whose candidate identities match, so each policy aggregates and
compares the same executions. Nothing here is simulator or performance evidence.
"""
import copy
import datetime

import pytest

from test_bfs_aggregation import _aggregate, _digest, simulation_seed, simulation_setup  # noqa: F401
from test_bfs_protocol import (protocol_seed, protocol_setup, proposal_setup, evaluation_setup,  # noqa: F401
                               _payload, _command, _sim_settings, _model_identity_fixture, _hash)


def test_execution_binds_named_shared_policy_only_when_role_identities_match(protocol_setup, tmp_path):
    from swdb import artifacts, bfs_protocol
    from swdb.store import Store
    from swdb.cli import Failure
    records, workload, _, request, evaluations, _ = protocol_setup
    settings = _sim_settings(request['settings'])
    identity = _model_identity_fixture(records, tmp_path, settings, evaluations)
    runtime = tmp_path / 'libramulator.so'; runtime.write_bytes(b'explicit fixture runtime')
    model = records.read('evaluations/explicit-model-fixture.yaml')
    model['build']['details']['binaries'].append({'path': str(runtime), 'sha256': _hash(runtime)})
    records.write('evaluations/explicit-model-fixture.yaml', model)
    identity['model_build']['sha256'] = artifacts.digest(model)

    def freeze(name, value):
        return _command(records, 'freeze-protocol', _payload(tmp_path, name, dict(message_version='1.0', id=name, settings=value)))
    main = freeze('main-policy', settings)
    disclosed = copy.deepcopy(settings)
    disclosed['differences'] = {**disclosed.get('differences', {}), 'configuration': ['A second disclosed policy.']}
    other = freeze('other-policy', disclosed)
    spread = copy.deepcopy(settings)
    spread['profitability']['maximum_relative_spread'] = 0.2
    loose = freeze('loose-policy', spread)
    changed = copy.deepcopy(settings)
    changed['instrumentation']['baseline']['debug_flags'] = 'OtherFlag'
    mismatch = freeze('mismatch-policy', changed)
    store = Store(records.path); candidate = store.get(evaluations['baseline']['candidate'])
    representation = bfs_protocol.workload_representation(store, workload['id'], 'gapbs')['representation']
    actual = {**evaluations['baseline']['build'], 'adapter': settings['builds']['baseline']['adapter'],
              'simulator': identity['simulator']['path'], 'simulator_sha256': identity['simulator']['sha256'], 'model_build': identity['model_build']}
    payload = dict(fixture=True, protocol=main['id'], protocol_role='baseline', protocol_trial={'source_position': 0, 'repetition': 0},
        workload={'id': workload['id'], 'source': 0, 'representation': {key: representation[key] for key in ('path', 'sha256')}},
        shared_protocols=[other['id'], loose['id']])

    def bind(value=payload):
        return bfs_protocol.validate_protocol_for_simulation(store, value, candidate,
            actual_target=settings['targets']['baseline']['id'], actual_configuration=settings['targets']['baseline']['configuration'],
            actual_build=actual, actual_instrumentation=settings['instrumentation']['baseline'], actual_threads=settings['threads'],
            actual_roi=settings['roi'], actual_verifier=settings['correctness']['verifier'])
    bound = bind()['context']
    assert bound['protocol_binding']['protocol'] == main['id']
    assert set(bound['shared_protocol_bindings']) == {other['id'], loose['id']}
    assert bfs_protocol.protocol_binding(bound, other['id'])['frozen_sha256'] == other['identity_sha256']
    assert bfs_protocol.protocol_binding(bound, mismatch['id']) == {}
    for bad in ([main['id']], [other['id'], other['id']], []):
        with pytest.raises(Failure, match='shared_protocols'):
            bind({**payload, 'shared_protocols': bad})
    with pytest.raises(Failure, match='instrumentation'):
        bind({**payload, 'shared_protocols': [mismatch['id']]})
    unfrozen = {key: value for key, value in payload.items() if key != 'protocol'}
    with pytest.raises(Failure, match='primary frozen protocol'):
        bind(unfrozen)


def _second_policy(records, tmp_path, frozen):
    # A distinct frozen policy with identical role identities; only its
    # disclosures differ, as the T16 artifact/control MAA roles do.
    request = {"message_version": "1.0", "id": "simulated-fixture-control", "version": 1,
               "settings": copy.deepcopy(frozen["settings"])}
    request["settings"]["differences"] = {**request["settings"].get("differences", {}),
                                          "configuration": ["Second disclosed policy for the same candidate role."]}
    return _command(records, "freeze-protocol", _payload(tmp_path, "freeze-control", request))


def _after_freeze(row):
    # Fixture executions are restamped after both freezes, as real ones must be.
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for stage in row["stages"]:
        stage["started"] = now
    row["context"]["protocol_binding"]["bound_at"] = now


def _bind(row, frozen, role):
    binding = copy.deepcopy(row["context"]["protocol_binding"])
    binding.update(protocol=frozen["id"], frozen_sha256=frozen["identity_sha256"],
                   settings_sha256=_digest(frozen["settings"]), role=role, frozen_at=frozen["frozen_at"],
                   bound_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    return binding


def test_one_candidate_execution_set_aggregates_under_both_matching_policies(simulation_setup, tmp_path):
    records, artifact, components = simulation_setup
    control = _second_policy(records, tmp_path, artifact)
    for row in components["candidate"] + components["baseline"]:
        _after_freeze(row)
    for row in components["candidate"]:
        row["context"]["shared_protocol_bindings"] = {control["id"]: _bind(row, control, "candidate")}
        records.write(f"evaluations/{row['id']}.yaml", row)
    control_baseline = []
    for row in components["baseline"]:
        item = copy.deepcopy(row)
        item["id"] = row["id"] + "-control"
        item["request"]["protocol"] = item["context"]["protocol"] = control["id"]
        item["context"]["protocol_binding"] = _bind(row, control, "baseline")
        item["context"]["execution_binding"]["execution"] = item["id"]
        records.write(f"evaluations/{item['id']}.yaml", item)
        control_baseline.append(item)
    shared = {name: _aggregate(records, tmp_path, policy, "candidate", components["candidate"], name=name)
              for name, policy in (("artifact-maa", artifact), ("control-maa", control))}
    for name, policy in (("artifact-maa", artifact), ("control-maa", control)):
        result = shared[name]
        assert result["outcome"]["state"] == "complete", result["outcome"]
        assert result["request"]["protocol"] == result["context"]["protocol"] == policy["id"]
        assert result["context"]["protocol_binding"]["protocol"] == policy["id"]
        assert "shared_protocol_bindings" not in result["context"]
        assert [row["evaluation"] for row in result["component_evaluations"]] == [row["id"] for row in components["candidate"]]
    baseline = _aggregate(records, tmp_path, control, "baseline", control_baseline, name="control-scalar")
    request = {"message_version": "1.0", "id": "control-shared-comparison", "protocol": control["id"],
               "baseline_evaluation": baseline["id"], "candidate_evaluation": shared["control-maa"]["id"],
               "comparison_baseline": "gapbs-bfs-do"}
    compared = _command(records, "compare-evaluations", _payload(tmp_path, request["id"], request))
    assert compared["decision"]["state"] == "fixture_comparison", compared["decision"]
    # The artifact aggregate cannot stand in for the control policy.
    request.update(id="control-wrong-aggregate", candidate_evaluation=shared["artifact-maa"]["id"])
    wrong = _command(records, "compare-evaluations", _payload(tmp_path, request["id"], request), succeeds=False)
    assert wrong["decision"]["state"] == "rejected"


@pytest.mark.parametrize("fault", ["unbound", "wrong-role", "stale-settings"])
def test_missing_or_mismatched_shared_binding_is_retained_as_incompatible(simulation_setup, tmp_path, fault):
    records, artifact, components = simulation_setup
    control = _second_policy(records, tmp_path, artifact)
    for row in components["candidate"]:
        _after_freeze(row)
        binding = _bind(row, control, "candidate")
        if fault == "wrong-role":
            binding["role"] = "baseline"
        elif fault == "stale-settings":
            binding["settings_sha256"] = "0" * 64
        if fault != "unbound":
            row["context"]["shared_protocol_bindings"] = {control["id"]: binding}
        records.write(f"evaluations/{row['id']}.yaml", row)
    result = _aggregate(records, tmp_path, control, "candidate", components["candidate"], name="control-maa", succeeds=False)
    assert result["outcome"]["state"] == "incompatible"
    assert "protocol/workload/role binding" in result["outcome"]["reason"]
