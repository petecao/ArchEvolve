"""Hand-computed memory bounds through CLI records. Updated: 2026-10-09 ET
(code review F2: stride-0 streams; fixture stores copy only their closure)."""
import json

import pytest
import yaml
from conftest import REPO,run_swdb
from testkit.analytic import target_description,freeze_protocol


def gather_case(records,tmp_path,llvm22,latency=0.5,threads=1):
    records=records.copy_closure('gapbs-bfs-do','kron-g16-k16').path
    result=run_swdb('characterize','--records',records,'--source',REPO/'tests/fixtures/analytic/indirect.cpp',
        '--implementation','gapbs-bfs-do','--input','kron-g16-k16','--function','gather',
        '--roi','fixture.gather.v1','--run-arg','gather','--threads',str(threads),'--fixture','--id','fixture.gather','--llvm-bin',llvm22,
        '--output',tmp_path/'counted','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    target=target_description(tmp_path,bandwidth=16)
    data=yaml.safe_load(target.read_text())
    data['threads']=threads
    def fact(value,unit):return {'value':value,'basis':'reported' if value is not None else 'unknown',
        'source':'Independent hand fixture, not hardware measurement.','unit':unit}
    data['mechanisms'] += [
        {'model':'requests_in_flight_latency','parameters':{'dependent_latency_s':fact(latency,'seconds/load'),
            'effective_requests_per_thread':fact(2,'requests/thread')}},
        {'model':'cache_fit','parameters':{'capacity_bytes':fact(128,'bytes'),
            'bytes_per_s':fact(2,'bytes/s'),'cold_bytes_per_s':fact(7,'bytes/s')}}]
    target.write_text(yaml.safe_dump(data,sort_keys=False))
    estimate=run_swdb('estimate','--records',records,'--characterization','fixture.gather',
        '--target-description',target,'--protocol',freeze_protocol(records,tmp_path,target,roi='fixture.gather.v1',threads=threads,arguments=['gather']),'--id','fixture.memory.estimate','--format','json')
    assert estimate.returncode==0,estimate.stderr+estimate.stdout
    return records,json.loads(estimate.stdout)


def test_memory_bounds_use_distinct_footprint_and_cold_first_touches(records,tmp_path,llvm22):
    records,data=gather_case(records,tmp_path,llvm22)
    row=next(r for r in data['regions'] if 'unmapped' in r['id'])
    bounds={b['model']:b for b in row['bounds']}
    # Four irregular requests * 0.5s / (one active worker * two requests) = 1s.
    assert bounds['requests_in_flight_latency']['seconds']==1
    assert bounds['streaming_bandwidth']['seconds']==1
    # 16 index bytes + 12 distinct target bytes = 28 cold bytes; four reused bytes.
    assert bounds['cache_fit']['seconds']==6 # 28/7 + (32-28)/2
    assert row['limiting_bound']=='cache_fit'
    assert data['seconds']==pytest.approx(6,abs=1e-7)
    checked=run_swdb('validate','--records',records)
    assert checked.returncode==0,checked.stdout+checked.stderr


def test_unknown_latency_preserves_other_known_bounds(records,tmp_path,llvm22):
    _,data=gather_case(records,tmp_path,llvm22,latency=None)
    row=next(r for r in data['regions'] if 'unmapped' in r['id'])
    bounds={b['model']:b for b in row['bounds']}
    assert bounds['requests_in_flight_latency']['seconds'] is None
    assert 'dependent_latency_s' in bounds['requests_in_flight_latency']['missing']
    assert bounds['streaming_bandwidth']['seconds']==1
    assert bounds['cache_fit']['seconds']==6
    assert data['seconds'] is None and data['ratio'] is None


def test_aggregate_rates_require_observed_worker_scope(records,tmp_path,llvm22):
    _,data=gather_case(records,tmp_path,llvm22,threads=4)
    row=next(r for r in data['regions'] if 'unmapped' in r['id'])
    bounds={b['model']:b for b in row['bounds']}
    # OMP_NUM_THREADS=4 does not make this ordinary serial gather use four workers.
    for model in ('compute_throughput','streaming_bandwidth','cache_fit'):
        assert bounds[model]['seconds'] is None
        assert 'aggregate_rate_worker_scope' in bounds[model]['missing']
        assert bounds[model]['inputs']['observed_active_workers']['value']==1
        assert bounds[model]['inputs']['rate_active_workers']==4
    assert bounds['requests_in_flight_latency']['seconds']==1
    assert data['seconds'] is None and data['ratio'] is None


def test_reused_accumulator_is_a_first_touch_stream_not_dependent_latency(records,tmp_path,llvm22):
    """Code review F2 (2026-10-09 ET): `*out += a[i]` rereads one element; it is no DRAM request."""
    from swdb import artifacts
    store=records.copy_closure('gapbs-bfs-do','kron-g16-k16').path
    result=run_swdb('characterize','--records',store,'--source',REPO/'tests/fixtures/analytic/streams.cpp',
        '--implementation','gapbs-bfs-do','--input','kron-g16-k16','--function','accumulate',
        '--roi','fixture.accumulate.v1','--run-arg','accumulate','--fixture','--id','fixture.accumulate',
        '--llvm-bin',llvm22,'--output',tmp_path/'counted','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    target=target_description(tmp_path,bandwidth=16)
    data=yaml.safe_load(target.read_text())
    data['mechanisms'].append({'model':'requests_in_flight_latency','parameters':{
        'dependent_latency_s':{'value':0.5,'basis':'reported','source':'Independent hand fixture, not hardware measurement.','unit':'seconds/load'},
        'effective_requests_per_thread':{'value':2,'basis':'reported','source':'Independent hand fixture, not hardware measurement.','unit':'requests/thread'}}})
    target.write_text(yaml.safe_dump(data,sort_keys=False))
    protocol=freeze_protocol(store,tmp_path,target,roi='fixture.accumulate.v1',arguments=['accumulate'])
    # Legacy records label the same invariant address `constant`; it must estimate identically.
    path=store/'workload_characterizations/fixture.accumulate.yaml'
    legacy=yaml.safe_load(path.read_text())
    for region in legacy['regions']:
        for access in region['access_patterns']:
            if access['stride_bytes']['value']==0:access['address_shape']['value']='constant'
    legacy['id']='fixture.accumulate.legacy';legacy.pop('identity_sha256');legacy['identity_sha256']=artifacts.digest(legacy)
    (store/'workload_characterizations/fixture.accumulate.legacy.yaml').write_text(yaml.safe_dump(legacy,sort_keys=False))
    for characterization in ('fixture.accumulate','fixture.accumulate.legacy'):
        estimate=run_swdb('estimate','--records',store,'--characterization',characterization,'--target-description',target,
            '--protocol',protocol,'--id',characterization+'.estimate','--format','json')
        assert estimate.returncode==0,estimate.stderr+estimate.stdout
        row=next(r for r in json.loads(estimate.stdout)['regions'] if any(b['model']=='streaming_bandwidth' and b['seconds'] for b in r['bounds']))
        bounds={b['model']:b for b in row['bounds']}
        # 8 a[i] reads x 4 B, plus one 8-byte first touch each for the *out read and write: 48 B / 16 B/s.
        assert bounds['streaming_bandwidth']['seconds']==3.0
        # No non-stream request remains; before the fix 16 *out requests x 0.5 s / 2 gave 4 s.
        assert bounds['requests_in_flight_latency']['seconds']==0
        assert row['limiting_bound']=='streaming_bandwidth'
