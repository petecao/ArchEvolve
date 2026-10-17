"""Public graph, freeze, and comparison workflows. Updated: 2026-10-05 ET (shared tests/testkit); 2026-09-26.

External compiler and simulator-shaped records are explicit contract fixtures.
Their durations never establish experimental performance.
"""

import copy
import json
import struct
from pathlib import Path

import pytest

from testkit.bfs_protocol import _add_record, _command, _fixture_rebind, _hash, _model_identity_fixture, _payload, _sg, _sim_settings, _workload_request


def test_graph_representations_are_actually_equivalent_and_retrievable(protocol_setup):
    records, workload, *_ = protocol_setup
    definition = workload["definition"]
    assert definition["realized"] == {"num_vertices": 5, "num_directed_edges": 4, "directed": True,
                                       "isolated_vertices": 1, "minimum_out_degree": 0, "maximum_out_degree": 2}
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


@pytest.mark.parametrize('rematerialize', [False, True])
def test_rewritten_candidate_cannot_impersonate_selected_starting_baseline(protocol_setup, tmp_path, rematerialize):
    records, _, protocol, _, evaluations, comparison = protocol_setup
    changed = records.read('candidates/test-proposal.candidate-1.yaml')
    original = records.read('source_snapshots/test-source.yaml')
    assert changed['artifact']['sha256'] != original['artifact']['sha256']
    if rematerialize:
        source = {**copy.deepcopy(original), 'id': 'rewritten-source', 'artifact': copy.deepcopy(changed['artifact']),
                  'context': copy.deepcopy(changed['context'])}
        _add_record(records, tmp_path, source)
        result = records.swdb('baseline-candidate', source['id'], '--id', 'rematerialized-rewrite',
                              '--runs-dir', tmp_path / 'rematerialized', '--format', 'json')
        assert result.returncode == 0, result.stderr
        changed = json.loads(result.stdout)
        assert changed['artifact_role'] == 'source_baseline'
    baseline = _fixture_rebind(evaluations['baseline'], protocol, 'baseline', 'rewritten-as-baseline')
    baseline.update(candidate=changed['id'], source_snapshot=changed['source_snapshot'])
    if changed.get('proposal'):
        baseline['proposal'] = changed['proposal']
    baseline['context']['candidate_sha256'] = changed['artifact']['sha256']
    _add_record(records, tmp_path, baseline)
    comparison.update(id='reject-rewritten-baseline', baseline_evaluation=baseline['id'])
    result = _command(records, 'compare-evaluations', _payload(tmp_path, 'rewritten-baseline', comparison), succeeds=False)
    assert result['decision']['state'] == 'rejected'
    assert 'selected implementation source' in str(result['decision']['reasons'])
    assert result['metrics'] == {} and not result['gain_claim']
    later = records.swdb('get', result['id'], '--format', 'json')
    assert json.loads(later.stdout)['decision'] == result['decision']


def test_frozen_baseline_dispatch_rejects_a_rewritten_source_before_build(protocol_setup, tmp_path):
    records, _, _, _, evaluations, _ = protocol_setup
    request = copy.deepcopy(evaluations['candidate']['request'])
    request.update(id='dispatch-rewritten-baseline', protocol_role='baseline')
    result = records.swdb('evaluate', _payload(tmp_path, 'bad-baseline-dispatch', request),
                          '--runs-dir', tmp_path / 'dispatch', '--format', 'json')
    assert result.returncode == 1, result.stderr
    retained = json.loads(result.stdout)
    assert 'selected implementation source' in retained['outcome']['reason']
    assert retained['timing'] == [] and all(row['stage'] != 'build' for row in retained['stages'])
    assert records.swdb('get', retained['id'], '--format', 'json').returncode == 0


@pytest.mark.parametrize("fault", ["different-source", "different-roi", "different-target", "different-threads",
                                   "unverified", "missing-timing", "wrong-binary", "different-graph", "pre-freeze",
                                   "host-time", "simulated-time", "missing-binding", "promoted-fixture",
                                   "wrong-checker", "missing-checker", "contradictory-checker"])
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
    elif fault == "wrong-checker": candidate["correctness"]["checks"][0]["verifier"] = "another.verifier"
    elif fault == "missing-checker": candidate["correctness"]["checks"][0].pop("verifier")
    elif fault == "contradictory-checker": candidate["correctness"]["checks"][0]["checker"] = "another.verifier"
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


def test_fresh_result_chain_retains_registered_workload_identity(protocol_setup):
    records, workload, frozen, _, evaluations, _ = protocol_setup
    for root in (evaluations['baseline']['id'], evaluations['candidate']['id'], frozen['id']):
        result = records.swdb('get', root, '--chain', '--format', 'json')
        assert result.returncode == 0, result.stderr
        chain = json.loads(result.stdout)
        assert chain['root'] == root
        assert chain['records'].get(workload['id']) == workload
        assert chain['records'].get(frozen['id']) == frozen
        if root != frozen['id']:
            evaluation = next(row for row in evaluations.values() if row['id'] == root)
            for field in ('implementation', 'machine'):
                assert evaluation[field] in chain['records']


def test_public_protocol_rejects_different_contents_under_same_logical_version(protocol_setup, tmp_path):
    records, _, original, request, _, _ = protocol_setup
    request.update(version=2, supersedes=original['id'])
    first = _command(records, 'freeze-protocol', _payload(tmp_path, 'first-version', request))
    before = set(records.path.glob('protocols/*.yaml'))
    request['settings']['profitability']['minimum_speedup'] = 1.5
    rejected = records.swdb('freeze-protocol', _payload(tmp_path, 'duplicate-version', request), '--format', 'json')
    assert rejected.returncode == 1 and 'logical name/version' in rejected.stderr
    assert set(records.path.glob('protocols/*.yaml')) == before
    saved = records.swdb('get', first['id'], '--format', 'json')
    assert saved.returncode == 0 and json.loads(saved.stdout) == first


def test_raw_add_cannot_recompute_content_under_old_frozen_id(protocol_setup, tmp_path):
    records, _, protocol, *_ = protocol_setup
    forged = copy.deepcopy(protocol)
    forged["id"] = "forged-policy"
    forged["settings"]["sampling"]["repetitions"] = 99
    result = records.swdb("add", _payload(tmp_path, "forged", forged))
    assert result.returncode == 1 and "register-workload/freeze-protocol" in result.stderr


@pytest.mark.parametrize('fault', [None, 'bare-lane', 'wrong-bind', 'different-lane'])
def test_frozen_native_lane_uses_exact_recorded_verifier_receipt(protocol_setup, tmp_path, fault):
    from swdb import artifacts, bfs_protocol
    from swdb.cli import Failure
    from swdb.store import Store
    records, workload, _, request, evaluations, comparison = protocol_setup
    target_id = request['settings']['targets']['baseline']['id']
    machine = records.read(f'machines/{target_id}.yaml')
    machine.update(id='lane-fixture-machine', hostname='mbit10', lane_required=True)
    _add_record(records, tmp_path, machine)
    request['id'] = 'lane-policy'
    for target in request['settings']['targets'].values():
        target['id'] = machine['id']
        target['configuration'] = {'lane': 'mbit10-evaluation-node1'}
    protocol = _command(records, 'freeze-protocol', _payload(tmp_path, 'lane-freeze', request))
    receipt = 'mbit10-evaluation-node1 (verified: affinity, bind:1, lease held, generation 375)'
    if fault == 'bare-lane': receipt = 'mbit10-evaluation-node1'
    elif fault == 'wrong-bind': receipt = receipt.replace('bind:1', 'bind:0')
    elif fault == 'different-lane': receipt = receipt.replace('node1', 'node0').replace('bind:1', 'bind:0')
    for role in ('baseline', 'candidate'):
        data = _fixture_rebind(evaluations[role], protocol, role, f'lane-{role}')
        data['machine'] = machine['id']
        data['context'].update(lane=receipt, machine_sha256=artifacts.digest(machine))
        data['request'].update(machine=machine['id'], target_configuration={'lane': 'mbit10-evaluation-node1'})
        _add_record(records, tmp_path, data)
        comparison[role + '_evaluation'] = data['id']
    # The execution preflight and later public comparator must interpret the
    # identical historical receipt. This test never acquires a real host lane.
    candidate = Store(records.path).get(data['candidate'], 'candidate')
    bound_request = {**data['request'], 'workload': {'id': workload['id']}}
    if fault:
        with pytest.raises(Failure, match='socket lane'):
            bfs_protocol.validate_protocol_for_evaluation(Store(records.path), bound_request, candidate, actual_lane=receipt)
    else:
        binding = bfs_protocol.validate_protocol_for_evaluation(Store(records.path), bound_request, candidate, actual_lane=receipt)
        assert binding['frozen_sha256'] == protocol['identity_sha256']
    comparison.update(id='compare-lane', protocol=protocol['id'])
    result = _command(records, 'compare-evaluations', _payload(tmp_path, 'lane-compare', comparison), succeeds=fault is None)
    assert result['decision']['state'] == ('rejected' if fault else 'fixture_comparison')
    if fault:
        assert 'socket lane' in str(result['decision']['reasons'])
    assert not result['gain_claim']


def test_comparator_differs_from_candidate_source_ancestor(protocol_setup, tmp_path):
    records, _, _, _, evaluations, comparison = protocol_setup
    # A second catalog identity of the same source is sufficient to check the
    # explicit comparison relationship; these remain metadata contract fixtures.
    implementation = records.read("implementations/gapbs-bfs-do.yaml")
    implementation.update(id="fixture-reference", name="Fixture comparison reference")
    implementation["origin"] = {"kind": "collaborator", "derived_from": None, "description": "Explicit identity fixture."}
    _add_record(records, tmp_path, implementation)
    snapshot = records.read("source_snapshots/test-source.yaml")
    snapshot.update(id="fixture-reference-source", implementation=implementation["id"])
    _add_record(records, tmp_path, snapshot)
    baseline_candidate = records.read("candidates/protocol-source-baseline.yaml")
    baseline_candidate.update(id="fixture-reference-candidate", implementation=implementation["id"], source_snapshot=snapshot["id"])
    _add_record(records, tmp_path, baseline_candidate)
    baseline = copy.deepcopy(evaluations["baseline"])
    baseline.update(id="eval-reference", implementation=implementation["id"], candidate=baseline_candidate["id"], source_snapshot=snapshot["id"])
    _add_record(records, tmp_path, baseline)
    candidate = copy.deepcopy(evaluations["candidate"])
    candidate.update(id="eval-selected-reference", comparison_baseline=implementation["id"])
    _add_record(records, tmp_path, candidate)
    comparison.update(baseline_evaluation=baseline["id"], candidate_evaluation=candidate["id"], comparison_baseline=implementation["id"])
    result = _command(records, "compare-evaluations", _payload(tmp_path, "explicit-reference", comparison))
    assert result["source_ancestor"] == "gapbs-bfs-do"
    assert result["comparison_baseline"] == "fixture-reference"
    assert result["metrics"]["fixture_ratio"] == pytest.approx(2) and not result["gain_claim"]


@pytest.mark.parametrize("fault", ["missing", "changed-model", "wrong-simulator", "missing-reference", "rewritten-reference"])
def test_simulated_freeze_requires_model_and_fixed_reference_identities(protocol_setup, tmp_path, fault):
    records, _, _, request, evaluations, _ = protocol_setup
    settings = _sim_settings(request["settings"])
    _model_identity_fixture(records, tmp_path, settings, evaluations, fixed=True)
    if fault == "missing": settings.pop("simulation_identity")
    elif fault == "changed-model": settings["simulation_identity"]["model_build"]["sha256"] = "0" * 64
    elif fault == "wrong-simulator": settings["simulation_identity"]["simulator"]["sha256"] = "0" * 64
    else:
        settings["mode"] = "artifact_reference"
        if fault == "missing-reference": settings.pop("reference_artifacts")
        else:
            from swdb import artifacts
            changed = records.read(f"candidates/{evaluations['candidate']['candidate']}.yaml")
            item = settings["reference_artifacts"]["candidate"]
            item.update(candidate=changed["id"], candidate_sha256=artifacts.digest(changed),
                        source_artifact_sha256=changed["artifact"]["sha256"])
    request.update(id="bad-identity-" + fault, settings=settings)
    result = records.swdb("freeze-protocol", _payload(tmp_path, request["id"], request), "--format", "json")
    assert result.returncode == 1, result.stdout
    assert any(word in result.stderr for word in ("simulation_identity", "model build", "simulator", "reference")), result.stderr


@pytest.mark.parametrize("fault", ["simulator", "model-build", "fixed-binary"])
def test_simulated_comparison_rejects_unfrozen_build_identity(protocol_setup, tmp_path, fault):
    records, _, _, request, evaluations, comparison = protocol_setup
    settings = _sim_settings(request["settings"])
    _model_identity_fixture(records, tmp_path, settings, evaluations, fixed=fault == "fixed-binary")
    request.update(id="identity-policy-" + fault, settings=settings)
    protocol = _command(records, "freeze-protocol", _payload(tmp_path, request["id"], request))
    for role in ("baseline", "candidate"):
        item = _fixture_rebind(evaluations[role], protocol, role, "identity-evaluation-" + role)
        if role == "candidate":
            if fault == "simulator": item["build"]["simulator_sha256"] = "0" * 64
            elif fault == "model-build": item["build"]["model_build"]["sha256"] = "0" * 64
            else: item["build"]["binary_sha256"] = "0" * 64
        _add_record(records, tmp_path, item)
        comparison[role + "_evaluation"] = item["id"]
    comparison.update(id="identity-comparison-" + fault, protocol=protocol["id"])
    result = _command(records, "compare-evaluations", _payload(tmp_path, comparison["id"], comparison), succeeds=False)
    assert not result["gain_claim"] and any("frozen" in reason for reason in result["decision"]["reasons"])


@pytest.mark.parametrize("fault", [None, "simulator", "runtime"])
def test_simulator_binding_rechecks_frozen_model_files(protocol_setup, tmp_path, fault):
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
    frozen = _command(records, 'freeze-protocol', _payload(tmp_path, 'file-freeze', dict(message_version='1.0', id='file-policy', settings=settings)))
    store = Store(records.path); candidate = store.get(evaluations['baseline']['candidate'])
    representation = bfs_protocol.workload_representation(store, workload['id'], 'gapbs')['representation']
    actual = {**evaluations['baseline']['build'], 'adapter': settings['builds']['baseline']['adapter'],
              'simulator': identity['simulator']['path'], 'simulator_sha256': identity['simulator']['sha256'], 'model_build': identity['model_build']}
    payload = dict(fixture=True, protocol=frozen['id'], protocol_role='baseline', protocol_trial={'source_position': 0, 'repetition': 0},
        workload={'id': workload['id'], 'source': 0, 'representation': {key: representation[key] for key in ('path', 'sha256')}})
    if fault == 'simulator': actual['simulator_sha256'] = '0'*64
    if fault == 'runtime': runtime.write_bytes(b'changed runtime while simulator remains identical')
    def bind():
        return bfs_protocol.validate_protocol_for_simulation(store, payload, candidate,
            actual_target=settings['targets']['baseline']['id'], actual_configuration=settings['targets']['baseline']['configuration'],
            actual_build=actual, actual_instrumentation=settings['instrumentation']['baseline'], actual_threads=settings['threads'],
            actual_roi=settings['roi'], actual_verifier=settings['correctness']['verifier'])
    if fault:
        with pytest.raises(Failure, match='frozen'): bind()
    else:
        assert bind()['context']['protocol_binding']['frozen_sha256'] == frozen['identity_sha256']


@pytest.mark.parametrize('fault', [None, 'missing', 'scalar-fallback', 'incomplete-trace', 'label-only', 'one-unobserved-cell'])
def test_comparison_requires_typed_acceleration_for_every_requested_replay(protocol_setup, tmp_path, fault):
    records, _, _, request, evaluations, comparison = protocol_setup
    settings = _sim_settings(request['settings'])
    _model_identity_fixture(records, tmp_path, settings, evaluations)
    cases = ['executed', 'full_tiles', 'tail_tiles', 'competing_parent_updates']
    settings['correctness']['required_accelerator_cases'] = {'baseline': [], 'candidate': cases}
    request.update(id='typed-acceleration-policy', settings=settings)
    frozen = _command(records, 'freeze-protocol', _payload(tmp_path, 'typed-freeze', request))
    for role in ('baseline', 'candidate'):
        item = _fixture_rebind(evaluations[role], frozen, role, 'typed-evaluation-' + role)
        if role == 'candidate' and fault:
            check = item['correctness']['checks'][-1]; coverage = check['coverage']
            if fault == 'missing': check.pop('coverage')
            elif fault == 'scalar-fallback': coverage['instruction_counters']['system.maa.numInst'] = 0
            elif fault == 'incomplete-trace': coverage['completed_trace_units']['I'] = 0
            elif fault == 'label-only':
                check['coverage'] = {'label': 'td_maa', 'full_tiles': 'observed'}
                item['context']['correctness_cases'] = cases
            else: coverage['tail_tiles'] = {'state': 'unobserved', 'count': 0}
        _add_record(records, tmp_path, item)
        comparison[role + '_evaluation'] = item['id']
    comparison.update(id='typed-acceleration-comparison', protocol=frozen['id'])
    result = _command(records, 'compare-evaluations', _payload(tmp_path, 'typed-compare', comparison), succeeds=fault is None)
    assert not result['gain_claim']
    if fault: assert 'typed accelerator coverage' in str(result['decision']['reasons'])
    else: assert result['decision']['state'] == 'fixture_comparison'


def test_legacy_unbound_simulator_protocol_is_readable_but_cannot_compare(protocol_setup, tmp_path):
    from swdb import artifacts, bfs_protocol
    records, _, original, _, evaluations, comparison = protocol_setup
    legacy = copy.deepcopy(original)
    legacy.update(requested_id='legacy-simulator-fixture', settings=_sim_settings(original['settings']))
    legacy['identity_sha256'] = artifacts.digest(bfs_protocol._identity_payload(legacy))
    legacy['id'] = legacy['requested_id'] + '.' + legacy['identity_sha256'][:16]
    # Import an explicitly synthetic historical record; public add still cannot create protocols.
    records.write(f"protocols/{legacy['id']}.yaml", legacy)
    retrieved = records.swdb('get', legacy['id'], '--format', 'json')
    assert retrieved.returncode == 0 and json.loads(retrieved.stdout) == legacy
    for role in ('baseline', 'candidate'):
        item = _fixture_rebind(evaluations[role], legacy, role, 'legacy-evaluation-' + role)
        _add_record(records, tmp_path, item); comparison[role + '_evaluation'] = item['id']
    comparison.update(id='legacy-rejected-comparison', protocol=legacy['id'])
    rejected = _command(records, 'compare-evaluations', _payload(tmp_path, 'legacy-comparison', comparison), succeeds=False)
    assert 'superseding protocol' in str(rejected['decision']['reasons']) and not rejected['gain_claim']


def test_controlled_and_artifact_simulator_protocols_keep_distinct_attribution(protocol_setup, tmp_path):
    records, _, _, request, evaluations, comparison = protocol_setup
    controlled = _sim_settings(request["settings"])
    _model_identity_fixture(records, tmp_path, controlled, evaluations, fixed=True)
    mismatch = copy.deepcopy(controlled)
    mismatch["targets"]["candidate"]["configuration"]["cache"]["llc_kib"] = 16384
    request.update(id="incompatible-control", settings=mismatch)
    result = records.swdb("freeze-protocol", _payload(tmp_path, "bad-control", request), "--format", "json")
    assert result.returncode == 1 and "CPU/cache/memory" in result.stderr
    for mode, settings in (("controlled_simulator", controlled), ("artifact_reference", mismatch)):
        settings["mode"] = mode
        if mode == "artifact_reference":
            settings["differences"]["configuration"] = ["Authors' baseline LLC is 4 MiB; accelerated LLC is 16 MiB."]
        request.update(id="policy-" + mode, settings=settings)
        protocol = _command(records, "freeze-protocol", _payload(tmp_path, "freeze-" + mode, request))
        for role in ("baseline", "candidate"):
            data = _fixture_rebind(evaluations[role], protocol, role, "eval-" + mode + "-" + role)
            _add_record(records, tmp_path, data)
            comparison[role + "_evaluation"] = data["id"]
        comparison.update(id="compare-" + mode, protocol=protocol["id"])
        result = _command(records, "compare-evaluations", _payload(tmp_path, "compare-" + mode, comparison))
        assert result["decision"]["state"] == "fixture_comparison" and not result["gain_claim"]
        assert result["metrics"]["attribution"] == ("joint_hardware_software" if mode == "controlled_simulator" else "artifact_configuration_pair")
        chain = records.swdb('get', result['id'], '--chain', '--format', 'json')
        assert chain.returncode == 0, chain.stderr
        ids = json.loads(chain.stdout)['records']
        assert 'explicit-model-fixture' in ids
        for item in settings['reference_artifacts'].values():
            assert item['candidate'] in ids and item['source_snapshot'] in ids


def test_corresponding_region_ratio_is_separate_from_bfs_roi(protocol_setup, tmp_path):
    records, workload, _, request, evaluations, comparison = protocol_setup
    request.update(id="region-policy")
    request["settings"]["region_pairs"] = [{"semantic_region": "edge-expansion", "baseline": "before-loop", "candidate": "after-helper",
                                             "scope": "accumulated", "attribution": "exclusive"}]
    protocol = _command(records, "freeze-protocol", _payload(tmp_path, "region-freeze", request))
    for role, region, duration in (("baseline", "before-loop", 0.5), ("candidate", "after-helper", 0.1)):
        data = _fixture_rebind(evaluations[role], protocol, role, "region-eval-" + role)
        data["profiling"]["regions"] = [{"id": region, "semantic_region": "edge-expansion", "scope": "accumulated",
                                          "attribution": "exclusive", "roi": protocol["settings"]["roi"],
                                          "binary_sha256": data["build"]["binary_sha256"],
                                          "workload_sha256": workload["definition"]["canonical_sha256"],
                                          "basis": "measured", "invocations": 10, "duration_s": duration}]
        _add_record(records, tmp_path, data)
        comparison[role + "_evaluation"] = data["id"]
    comparison.update(id="region-compare", protocol=protocol["id"])
    result = _command(records, "compare-evaluations", _payload(tmp_path, "region-compare", comparison))
    assert result["metrics"]["fixture_ratio"] == pytest.approx(2)
    assert result["region_comparisons"][0]["duration_ratio"] == pytest.approx(5)
    assert result["region_comparisons"][0]["primary_bfs_roi"] is False
    bad = records.read("evaluations/region-eval-candidate.yaml")
    bad["id"] = "region-wrong-scope"
    bad["profiling"]["regions"][0]["attribution"] = "inclusive"
    _add_record(records, tmp_path, bad)
    comparison.update(id="region-scope-rejected", candidate_evaluation=bad["id"])
    result = _command(records, "compare-evaluations", _payload(tmp_path, "region-scope-rejected", comparison), succeeds=False)
    assert "attribution scopes" in result["decision"]["reasons"][0]


def test_new_workload_version_marks_comparison_for_fresh_evidence(protocol_setup, tmp_path):
    records, workload, _, _, _, comparison = protocol_setup
    old = _command(records, "compare-evaluations", _payload(tmp_path, "old-comparison", comparison))
    request = _workload_request(records, tmp_path, {"num_vertices": 5, "directed": True, "edges": [[0,1], [0,4]]}, name="graph-v2")
    request.update(id=workload["requested_id"], version=2, supersedes=workload["id"])
    updated = _command(records, "register-workload", _payload(tmp_path, "workload-v2", request))
    assert updated["definition"]["canonical_sha256"] != workload["definition"]["canonical_sha256"]
    assert updated["invalidated_comparisons"] == [old["id"]]
    assert json.loads(records.swdb("get", old["id"], "--format", "json").stdout) == old


@pytest.mark.parametrize("fault", ["wrong-offset-width", "wrong-adjacency", "wrong-inverse", "truncated", "wrong-hash"])
def test_registration_rejects_non_equivalent_or_invalid_files(records, tmp_path, fault):
    records.copy_repo()
    before = {path.name: path.read_bytes() for path in (records.path / "workloads").glob("*.yaml")}
    base = {"workload": {"graph": {"num_vertices": 5, "directed": True, "edges": [[0,1], [0,2], [1,3], [2,3]]}}}
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
    assert {path.name: path.read_bytes() for path in (records.path / "workloads").glob("*.yaml")} == before


def test_frozen_dispatch_rejects_wrong_sources_before_build(protocol_setup, tmp_path):
    records, workload, protocol, _, evaluations, _ = protocol_setup
    request = copy.deepcopy(evaluations["candidate"]["request"])
    request.update(id="eval-wrong-source", protocol=protocol["id"], protocol_role="candidate",
                   workload={"id": workload["id"]}, sources=[1], repetitions=5)
    result = records.swdb("evaluate", _payload(tmp_path, "wrong-source", request), "--runs-dir", tmp_path / "runs", "--format", "json")
    assert result.returncode == 1, result.stderr
    data = json.loads(result.stdout)
    assert "source sequence" in data["outcome"]["reason"]
    assert not any(stage["stage"] == "build" for stage in data["stages"])
