"""Public CPU error-band admission and honest failure. Created: 2026-10-06 ET."""
import json
import yaml
from conftest import run_swdb
from testkit.analytic import fixture_characterization, target_description, freeze_protocol


def test_unknown_complete_costs_freeze_failed_band_with_region_diagnosis(records, tmp_path):
    records.add_stub()
    counts = fixture_characterization(records.path, subject_id='stub-impl', input_id='tiny-sym')
    counts['regions'] = [{'id':'fixture.unknown', 'source_location':{'function':'fixture','line':1},
        'mapped':True,'kind':'serial_remainder','access_patterns':[],
        'operation_counts':{kind:{'value':1,'basis':'reported','scope':'per_call'} for kind in ('integer','floating_point','branch','atomic')},
        'dynamic_counts':{'loop_iterations':{'value':1,'basis':'reported','scope':'per_call'}},
        'footprint_bytes':{'value':4,'basis':'reported'}, 'address_stream_counts':{}, 'accelerator_calls':[]}]
    from testkit.analytic import digest
    counts.pop('identity_sha256'); counts['identity_sha256']=digest(counts)
    records.write('workload_characterizations/fixture.counts.yaml', counts)
    target=target_description(tmp_path)
    td=yaml.safe_load(target.read_text())
    td['mechanisms'][0]['parameters']['floating_point_ops_per_s'].update(value=None,basis='unknown')
    target.write_text(yaml.safe_dump(td))
    protocol=freeze_protocol(records.path,tmp_path,target,roi='fixture.stream.v1',input_id='tiny-sym')
    result=run_swdb('estimate','--records',records.path,'--characterization','fixture.counts',
        '--target-description',target,'--protocol',protocol,'--id','fixture.unknown.estimate','--format','json')
    assert result.returncode==0,result.stdout+result.stderr
    estimated=json.loads(result.stdout); assert estimated['seconds'] is None
    # Explicit absence of a matched native validation remains failure, never zero timing.
    result=run_swdb('freeze-cpu-error-band','--records',records.path,'--estimate','fixture.unknown.estimate',
        '--id','fixture.failed.band','--fixture','--format','json')
    assert result.returncode==0,result.stdout+result.stderr
    band=json.loads(result.stdout)
    assert band['state']=='failed' and band['width_log'] is None
    assert band['pairs'][0]['native_seconds'] is None
    assert 'matched_native_validation' in band['pairs'][0]['missing']
    region=band['pairs'][0]['regions'][0]
    assert region['id']=='fixture.unknown' and region['seconds'] is None
    assert any('floating_point_ops_per_s' in b['missing'] for b in region['bounds'])
    assert records.validate().returncode==0
