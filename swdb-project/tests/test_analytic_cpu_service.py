"""CPU service coverage through frozen public estimates. Updated: 2026-10-06 ET."""
import json

import pytest
import yaml

from conftest import run_swdb
from testkit.analytic import digest, fixture_characterization, target_description, freeze_protocol


def fact(value):
    return {'value': value, 'basis': 'reported' if value is not None else 'unknown', 'scope': 'per_call'}


def clock_case(records, tmp_path, *, cost=.1, events=4, body_counted=False, extra_selector=None, shaped=False, shaped_name="_Znam"):
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
    if shaped:
        data['unmodeled_calls'][0]['name']=shaped_name
        data['regions'][0]['call_shape_counts']={'format':'swdb.call-shape-counts.v1','scope':'per_run','calls':[{
            'site':29,'name':shaped_name,'event':'allocation','execution_count':fact(events),
            'body_counted':False,'known_length_bins':[{'bytes':8,'execution_count':fact(1)},
                {'bytes':16,'execution_count':fact(2)}], 'allocation_lifetime_size_bins':[],
            'unknown_lengths':fact(0),'unknown_free_lifetimes':fact(0),'scope':'per_run','missing':[]}]}
    if shaped:
        data['unmodeled_calls'][0]['execution_count']['scope']='per_run'
        for call in data['regions'][0]['call_shape_counts']['calls']:
            for field in ('execution_count','unknown_lengths','unknown_free_lifetimes'):
                call[field]['scope']='per_run'
            for field in ('known_length_bins','allocation_lifetime_size_bins'):
                for item in call[field]:item['execution_count']['scope']='per_run'
    data.pop('identity_sha256'); data['identity_sha256'] = digest(data)
    records.write('workload_characterizations/fixture.counts.yaml', data)
    path = target_description(tmp_path)
    target = yaml.safe_load(path.read_text()); target['target'] = 'testhost'; target['mechanisms'] = target['mechanisms'][:1]
    target['mechanisms'].append({'model': 'native_service_costs', 'accounting': 'additive_overhead',
        'selector': {'domain': 'host', 'worker_scope': 'serial_T1', 'calls': [
            {'name': 'fixture.clock.abi', 'parameter': 'clock_s', 'unit': 'seconds/call'}], **(extra_selector or {})},
        'parameters': {'clock_s': {'value': cost, 'basis': 'unknown' if cost is None else 'reported',
            'source': 'Independent hand fixture only.', 'unit': 'seconds/call'}}})
    if shaped:
        service=target['mechanisms'][-1]
        service['selector']['calls']=[{'name':shaped_name,'unit':'seconds/call',
            'bin_kind':'known_length_bins','bins':[{'bytes':8,'parameter':'small_s'}, {'bytes':16,'parameter':'large_s'}],
            'scope_assumption':{'regime':'fresh_process_repeated_allocate_free_batches','transfer_basis':'inferred'}}]
        service['parameters']={'small_s':{'value':.1,'basis':'reported','unit':'seconds/call','source':'Hand fixture8B.'},
            'large_s':{'value':.2,'basis':'reported','unit':'seconds/call','source':'Hand fixture16B.'}}
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



def test_exact_size_service_bins_require_full_site_coverage(records,tmp_path):
    data=clock_case(records,tmp_path,events=3,shaped=True)
    overhead=data['regions'][0]['overheads'][0]
    assert overhead['seconds']==.5 and data['seconds']==2.5
    assert overhead['inputs']['covered_calls']==[{'site':29,'execution_count':3}]
    assert 'inferred' in ' '.join(overhead['notes'])
    assert records.validate().returncode==0


def test_partial_size_bins_never_waive_the_full_opaque_site(records,tmp_path):
    data=clock_case(records,tmp_path,events=4,shaped=True)
    overhead=data['regions'][0]['overheads'][0]
    assert data['seconds'] is None and overhead['seconds'] is None
    assert overhead['inputs']['covered_calls']==[]
    assert 'call_shape.full_site_count._Znam' in overhead['missing']
    assert any(b['model']=='unmodeled_calls' for b in data['regions'][0]['bounds'])


def test_allocator_regime_cannot_waive_a_bulk_copy_call(records, tmp_path):
    data=clock_case(records,tmp_path,events=3,shaped=True,shaped_name='llvm.memcpy.p0.p0.i64')
    overhead=data['regions'][0]['overheads'][0]
    assert data['seconds'] is None and overhead['seconds'] is None
    assert overhead['inputs']['covered_calls']==[]
    assert 'selector.calls.allocator_abi_bin_kind' in overhead['missing']
    assert any(b['model']=='unmodeled_calls' for b in data['regions'][0]['bounds'])
