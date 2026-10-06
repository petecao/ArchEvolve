"""CPU service coverage through frozen public estimates. Updated: 2026-10-06 ET."""
import json

import pytest
import yaml

from conftest import run_swdb
from testkit.analytic import digest, fixture_characterization, target_description, freeze_protocol


def fact(value):
    return {'value': value, 'basis': 'reported' if value is not None else 'unknown', 'scope': 'per_call'}


def clock_case(records, tmp_path, *, cost=.1, events=4, body_counted=False, extra_selector=None):
    records.add_stub()
    data = fixture_characterization(records.path, subject_id='stub-impl', input_id='tiny-sym')
    data['regions'] = [{'id': 'fixture.region', 'source_location': {'function': 'fixture', 'line': 1},
        'mapped': True, 'kind': 'serial_remainder', 'access_patterns': [],
        'operation_counts': {k: fact(0 if k != 'floating_point' else 32) for k in ('integer','floating_point','branch','atomic')},
        'dynamic_counts': {'loop_iterations': fact(0)}, 'footprint_bytes': {'value': 0, 'basis': 'reported'},
        'active_workers': {'value': 1, 'basis': 'reported'}, 'worker_context': {'team_sizes': [1], 'measurement': 'Hand fixture.'},
        'accelerator_calls': [], 'address_stream_counts': {}}]
    data['unmodeled_calls'] = [{'site': 29, 'region': 'fixture.region', 'name': 'fixture.clock.abi',
        'body_counted': body_counted, 'cost_accounting': 'counted_body' if body_counted else 'opaque_callee',
        'execution_count': fact(events)}]
    data.pop('identity_sha256'); data['identity_sha256'] = digest(data)
    records.write('workload_characterizations/fixture.counts.yaml', data)
    path = target_description(tmp_path)
    target = yaml.safe_load(path.read_text()); target['target'] = 'testhost'; target['mechanisms'] = target['mechanisms'][:1]
    target['mechanisms'].append({'model': 'native_service_costs', 'accounting': 'additive_overhead',
        'selector': {'domain': 'host', 'worker_scope': 'serial_T1', 'calls': [
            {'name': 'fixture.clock.abi', 'parameter': 'clock_s', 'unit': 'seconds/call'}], **(extra_selector or {})},
        'parameters': {'clock_s': {'value': cost, 'basis': 'unknown' if cost is None else 'reported',
            'source': 'Independent hand fixture only.', 'unit': 'seconds/call'}}})
    path.write_text(yaml.safe_dump(target, sort_keys=False))
    protocol = freeze_protocol(records.path, tmp_path, path, roi='fixture.stream.v1', input_id='tiny-sym')
    result = run_swdb('estimate', '--records', records.path, '--characterization', 'fixture.counts',
        '--target-description', path, '--protocol', protocol, '--id', 'fixture.cpu.estimate', '--format', 'json')
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout)


def test_exact_scalar_service_coverage_adds_once_and_clears_its_opaque_call(records, tmp_path):
    data = clock_case(records, tmp_path)
    region = data['regions'][0]
    assert region['overheads'][0]['seconds'] == .4
    assert region['overheads'][0]['inputs']['covered_calls'] == [{'site': 29, 'execution_count': 4}]
    assert region['bounds'][0]['seconds'] == 2 and region['seconds'] == 2.4
    assert data['seconds'] == 2.4 and data['evidence_kind'] == 'contract_fixture'
    checked = records.validate()
    assert checked.returncode == 0, checked.stdout + checked.stderr


@pytest.mark.parametrize('cost, events, body_counted, expected', [
    (None, 4, False, None), (None, 0, False, 2.), (None, 4, True, 2.)])
def test_service_missing_rate_zero_and_counted_body_keep_honest_coverage(records, tmp_path, cost, events, body_counted, expected):
    data = clock_case(records, tmp_path, cost=cost, events=events, body_counted=body_counted)
    assert data['seconds'] == expected
    overhead = data['regions'][0]['overheads'][0]
    if expected is None:
        assert overhead['seconds'] is None and overhead['inputs']['covered_calls'] == []
        assert any(b['model'] == 'unmodeled_calls' for b in data['regions'][0]['bounds'])
    else:
        assert overhead['seconds'] == 0


def test_unsupported_service_selector_never_claims_opaque_body_coverage(records, tmp_path):
    data = clock_case(records, tmp_path, extra_selector={'length_bytes': 16})
    overhead = data['regions'][0]['overheads'][0]
    assert data['seconds'] is None and overhead['inputs']['covered_calls'] == []
    assert 'selector.length_bytes' in overhead['missing']
