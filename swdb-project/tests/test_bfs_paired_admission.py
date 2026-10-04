"""Paired publication glue with explicit nonempirical seams. Date: 2026-09-26 ET."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import bfs_native_paired_pilot as driver
from scripts import bfs_paired_calibration as admission
from scripts.bfs_freeze_pilot import summary
from swdb import artifacts
from swdb.cli import Failure
from swdb.store import Store
from test_bfs_native_paired_pilot import driver_receipt_fixture


@pytest.fixture
def admission_case(tmp_path, monkeypatch):
    plan, receipt, _ = driver_receipt_fixture(tmp_path, monkeypatch)
    original = Store(driver.ROOT / 'records')
    additions, firsts = {}, []
    for cell, entry, stage in zip(plan['cells'], receipt['cells'], receipt['stages'][5:]):
        first = original.get(cell['first_evaluation'], 'evaluation')
        firsts.append(first)
        pair = json.loads(Path(stage['output']).read_text())
        pair.update(request=json.loads(Path(entry['request']['path']).read_text()),
                    baseline_evaluation=cell['baseline_evaluation'], candidate_evaluation=cell['candidate_evaluation'])
        additions[pair['id']] = pair
        for role in ('baseline', 'candidate'):
            evaluation = {'id': cell[role + '_evaluation'], 'evidence_kind': 'contract_fixture',
                'context': {'fixture': True}, 'build': {'fixture': True},
                'timing': [], 'correctness': {'state': 'fixture'}}
            additions[evaluation['id']] = evaluation
        Path(stage['output']).write_text(json.dumps(pair))
        stage['stdout_sha256'] = artifacts.file_hash(stage['output'])
        entry['pair_sha256'] = artifacts.digest(pair)
    receipt_path = tmp_path / 'fixture-driver.json'
    receipt_path.write_text(json.dumps(receipt))
    selected = {'pairs': [cell['id'] for cell in plan['cells']],
        'historical_packages': ['fixture-history-' + str(index) for index in range(4)],
        'driver_receipt': {'path': str(receipt_path), 'sha256': artifacts.file_hash(receipt_path)}}
    spec = {'maximum_relative_spread': .10, 'paired_calibration': selected}
    store = SimpleNamespace(get=lambda rid, kind=None: additions.get(rid) or original.get(rid, kind))
    packets = [{'evaluation': firsts[index]} for index in (1, 3)]
    samples = {cell['id']: {role: [summary(source, [1 + .001 * repeat for repeat in range(10)])
                for source in driver.SOURCES] for role in ('baseline', 'candidate')} for cell in plan['cells']}
    real_pair_admission = driver.validate_pair_result
    # Only raw pair/graph execution admission is substituted; these fixture
    # bodies must fail that real gate. The real resource/command reader runs.
    monkeypatch.setattr(driver, 'validate_pair_result',
                        lambda _store, _first, pair, _machine, _request: copy.deepcopy(samples[pair['id']]))
    return SimpleNamespace(plan=plan, receipt=receipt, spec=spec, store=store,
        packets=packets, additions=additions, samples=samples, real_pair_admission=real_pair_admission)


def test_qualifier_reopens_driver_public_results_and_all_four_controls(admission_case, monkeypatch):
    case = admission_case
    identities, gates = {}, []
    result, primary = admission.qualify(case.spec, case.packets, case.store, identities, gates)
    assert result['state'] == 'qualified' and not result['gain_claim'] and not gates
    assert len(result['pairs']) == 4 and all(len(pair['directions']) == 2 for pair in result['pairs'])
    assert result['execution_artifact_rechecks']
    assert {cell['id'] for cell in case.plan['cells']} <= set(identities)
    assert [row['id'] for row in primary] == [case.plan['cells'][index]['baseline_evaluation'] for index in (1, 3)]
    monkeypatch.setattr(driver, 'validate_pair_result', case.real_pair_admission)
    with pytest.raises((ValueError, Failure), match='real collection receipt'):
        admission.qualify(case.spec, case.packets, case.store, {}, [])


@pytest.mark.parametrize('fault', ['missing-cell', 'changed-pair', 'changed-result', 'changed-driver', 'relaxed-spread'])
def test_qualifier_cannot_admit_partial_changed_or_relaxed_study(admission_case, fault):
    case = admission_case
    first_id = case.plan['cells'][0]['id']
    if fault == 'missing-cell':
        case.spec['paired_calibration']['pairs'].pop()
    elif fault == 'changed-pair':
        case.additions[first_id]['gain_claim'] = True
    elif fault == 'changed-result':
        Path(case.receipt['stages'][5]['output']).write_text('{}')
    elif fault == 'changed-driver':
        Path(case.spec['paired_calibration']['driver_receipt']['path']).write_text('{}')
    else:
        case.spec['maximum_relative_spread'] = 1
    with pytest.raises((ValueError, Failure)):
        admission.qualify(case.spec, case.packets, case.store, {}, [])


def test_other_implementations_failed_negative_control_blocks_selected_upstream(admission_case):
    case = admission_case
    first_id = case.plan['cells'][0]['id']
    case.samples[first_id]['candidate'] = [summary(source, [.5] * 10) for source in driver.SOURCES]
    gates = []
    result, _ = admission.qualify(case.spec, case.packets, case.store, {}, gates)
    assert result['state'] == 'unqualified' and not result['gain_claim']
    assert any(first_id + ': unchanged-code' in gate for gate in gates)
