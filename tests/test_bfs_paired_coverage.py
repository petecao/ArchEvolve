"""Paired public coverage and retained-receipt guards. Updated: 2026-09-26 ET.

All executions use the existing external compiler contract fixture. These
observations establish message/evidence behavior, never empirical performance.
"""
import copy

import pytest

from test_bfs_native_pair import paired_seed, paired_setup
from test_bfs_protocol import _command, _payload
from swdb import artifacts, bfs_coverage
from swdb.store import Store


def report(records, tmp_path, frozen):
    return _command(records, 'bfs-coverage', _payload(tmp_path, 'coverage', {
        'message_version': '1.0', 'id': 'paired-coverage', 'candidate_protocols': [frozen['id']]}))


def test_paired_public_coverage_preserves_frozen_block_analysis_without_promoting_fixture(paired_setup, tmp_path):
    records, _, _, _, frozen, request, _ = paired_setup
    comparison = _command(records, 'compare-evaluations', _payload(tmp_path, 'comparison', request))
    result = report(records, tmp_path, frozen)
    assessment = next(row for row in result['comparison_assessments'] if row['id'] == comparison['id'])
    interval = comparison['metrics']['confidence_interval']
    assert interval['method'] == 'paired_repetition_block_bootstrap.v1'
    assert interval['lower'] == interval['upper'] == 1
    assert assessment['metrics']['confidence_interval'] == interval
    assert not any('confidence_interval differs' in reason for reason in assessment['reasons'])
    assert not assessment['qualified'] and not assessment['gain']
    assert result['acceptance'] == 'incomplete' and not result['gain_claim']
    assert bfs_coverage._fixture_comparison(Store(records.path), comparison)['confidence_interval'] == interval
    assert not result['criteria']['AC09']['evidence']['regression']
    assert not result['qualifying_candidate_gains']


@pytest.mark.parametrize('fault', ['failed-pair', 'missing-pair', 'member-identity', 'recorded-identity'])
def test_coverage_reopens_paired_record_and_member_identities(paired_setup, tmp_path, fault):
    records, _, _, pair, frozen, request, _ = paired_setup
    comparison = _command(records, 'compare-evaluations', _payload(tmp_path, 'comparison', request))
    pair = copy.deepcopy(pair)
    if fault == 'failed-pair':
        pair['outcome']['state'] = 'failed'
    elif fault == 'member-identity':
        member = records.read('evaluations/' + pair['candidate_evaluation'] + '.yaml')
        member['context']['pairing']['role'] = 'baseline'
        records.write('evaluations/' + member['id'] + '.yaml', member)
        # Update every advertised content digest; only revalidation of the
        # role/request/schedule relation can catch this consistent substitution.
        pair['evaluation_identities'][member['id']] = artifacts.digest(member)
        comparison['evaluation_identities'][member['id']] = artifacts.digest(member)
    pair['receipt_sha256'] = artifacts.digest({k: v for k, v in pair.items() if k != 'receipt_sha256'})
    comparison['metrics']['paired_collection']['receipt_sha256'] = pair['receipt_sha256']
    records.write('evaluation_pairs/' + pair['id'] + '.yaml', pair)
    if fault == 'missing-pair':
        (records.path / 'evaluation_pairs' / (pair['id'] + '.yaml')).unlink()
    elif fault == 'recorded-identity':
        comparison['metrics']['paired_collection']['schedule_sha256'] = 'f' * 64
    records.write('comparison_results/' + comparison['id'] + '.yaml', comparison)
    assert bfs_coverage._fixture_comparison(Store(records.path), comparison) is None
    result = report(records, tmp_path, frozen)
    assessment = next(row for row in result['comparison_assessments'] if row['id'] == comparison['id'])
    expected = {'failed-pair': 'incomplete paired receipt', 'missing-pair': 'incomplete paired receipt',
                'member-identity': 'mismatched, changed, or from another pair',
                'recorded-identity': 'paired collection identity differs'}[fault]
    assert any(expected in reason for reason in assessment['reasons'])
    assert not assessment['qualified'] and not assessment['gain'] and not result['gain_claim']
