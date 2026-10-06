"""Public generic logical request models. Fixture numbers are not hardware evidence.
Created: 2026-10-06 ET.
"""
import json
import yaml
from conftest import run_swdb
from testkit.analytic import digest,fixture_characterization,target_description,freeze_protocol


def fact(value):return {'value':value,'basis':'unknown' if value is None else 'reported','scope':'per_call'}
def parameter(value,unit):return {'value':value,'basis':'reported','source':'Hand-computed fixture only.','unit':unit}


def estimate_fixture(records,tmp_path,model,parameters,*,wrong_hash=False,requests=6,groups=3):
    records.add_stub()
    path=target_description(tmp_path)
    target=yaml.safe_load(path.read_text());target['target']='testhost'
    target['mechanisms']=[{'model':model,'selector':{'domain':'offload'},'parameters':parameters}]
    path.write_text(yaml.safe_dump(target,sort_keys=False))
    target_hash=digest(target)
    data=fixture_characterization(records.path,subject_id='stub-impl',input_id='tiny-sym')
    data['regions']=[{'id':'fixture.region','source_location':{'function':'fixture','line':1},'mapped':True,
        'kind':'serial_remainder','operation_counts':{k:fact(0) for k in ('integer','floating_point','branch','atomic')},
        'dynamic_counts':{'loop_iterations':fact(0)},'footprint_bytes':{'value':0,'basis':'reported'},
        'access_patterns':[],'accelerator_calls':[],
        'address_stream_counts':{('f'*64 if wrong_hash else target_hash):{
            'format':'swdb.logical-address-counts.v1','target_description_sha256':target_hash,
            'level':'derived_logical_transactions','state':'complete','scope':'per_call','missing':[],
            **{key:'0'*64 for key in ('layout_sha256','request_policy_sha256','placement_assumption_sha256','window_policy_sha256')},
            'grouped_row_hits':fact(None if requests is None else requests-groups),
            'grouped_row_hit_fraction':fact(None if not requests else (requests-groups)/requests),'windows':fact(2),
            'line_requests':fact(requests),'row_groups':fact(groups),'staged_bytes':fact(24),
            'notes':['Hand-computed logical contract fixture only; no physical request evidence.']}}}]
    data.pop('identity_sha256');data['identity_sha256']=digest(data)
    records.write('workload_characterizations/fixture.counts.yaml',data)
    protocol=freeze_protocol(records.path,tmp_path,path,roi='fixture.stream.v1',input_id='tiny-sym')
    result=run_swdb('estimate','--records',records.path,'--characterization','fixture.counts',
        '--target-description',path,'--protocol',protocol,'--id','fixture.model.estimate','--format','json')
    assert result.returncode==0,result.stdout+result.stderr
    return json.loads(result.stdout)


def test_row_groups_bound_uses_requested_description_and_ideal_logical_service(records,tmp_path):
    result=estimate_fixture(records,tmp_path,'reorder_window_rows',{
        'row_miss_service_s':parameter(.1,'seconds/request'),
        'row_hit_service_s':parameter(.02,'seconds/request'),
        'effective_memory_parallelism':parameter(2,'requests')})
    assert abs(result['seconds']-.18)<1e-12
    component=result['regions'][0]['bounds'][0]
    assert component['basis']=='estimated'
    assert component['inputs']['line_requests']==6
    assert component['inputs']['row_groups']==3
    assert 'physical' in ' '.join(component['notes']).lower()
    checked=records.validate();assert checked.returncode==0,checked.stdout+checked.stderr


def test_fetch_queue_capacity_and_admission_are_competing_logical_bounds(records,tmp_path):
    result=estimate_fixture(records,tmp_path,'fetch_queue',{
        'queue_entries':parameter(2,'entries'),
        'fetch_latency_s':parameter(.1,'seconds/request'),
        'admission_requests_per_s':parameter(10,'requests/s')})
    assert abs(result['seconds']-.6)<1e-12
    assert result['regions'][0]['bounds'][0]['inputs']['line_requests']==6


def test_tile_staging_uses_dynamic_useful_stage_bytes_not_tile_capacity(records,tmp_path):
    result=estimate_fixture(records,tmp_path,'tile_staging',{
        'staging_bytes_per_s':parameter(12,'bytes/s')})
    assert result['seconds']==2.
    assert result['regions'][0]['bounds'][0]['inputs']['staged_bytes']==24


def test_logical_counts_for_a_different_description_never_reuse_rows(records,tmp_path):
    result=estimate_fixture(records,tmp_path,'reorder_window_rows',{},wrong_hash=True)
    assert result['seconds'] is None
    assert 'address_stream_counts.requested_target_description' in result['regions'][0]['bounds'][0]['missing']


def test_proven_zero_requests_need_no_queue_parameters(records,tmp_path):
    result=estimate_fixture(records,tmp_path,'fetch_queue',{},requests=0,groups=0)
    assert result['seconds']==0.


def test_unknown_requests_keep_total_null_with_known_parameters(records,tmp_path):
    result=estimate_fixture(records,tmp_path,'fetch_queue',{
        'queue_entries':parameter(2,'entries'),'fetch_latency_s':parameter(.1,'seconds/request'),
        'admission_requests_per_s':parameter(10,'requests/s')},requests=None)
    assert result['seconds'] is None
    assert 'address_stream_counts.line_requests' in result['regions'][0]['bounds'][0]['missing']
