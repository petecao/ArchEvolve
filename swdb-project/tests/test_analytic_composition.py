"""Public cross-domain composition and required source coverage. 2026-10-06 ET."""
import json
import yaml
import pytest
from conftest import run_swdb
from testkit.analytic import digest,fixture_characterization,target_description,freeze_protocol


def fact(value):return {'value':value,'basis':'reported','scope':'per_call'}
def rate(value,unit):return {'value':value,'basis':'reported','source':'Hand-computed fixture only.','unit':unit}


def estimate_domains(records,tmp_path,*,overlap=None,host_work=1,memory=False,memory_model=False):
    records.add_stub()
    path=target_description(tmp_path)
    target=yaml.safe_load(path.read_text());target['target']='testhost'
    target['mechanisms']=[{'model':'compute_throughput','parameters':{
        kind+'_ops_per_s':rate(1,'operations/s') for kind in ('integer','floating_point','branch','atomic')}},
        {'model':'tile_staging','selector':{'domain':'offload'},'parameters':{'staging_bytes_per_s':rate(12,'bytes/s')}}]
    if memory_model:target['mechanisms'].append({'model':'streaming_bandwidth','parameters':{'bytes_per_s':rate(16,'bytes/s')}})
    if overlap is not None:target['composition_contract']={'format':'swdb.composition-contract.v1',
        'resource_domain_overlap':overlap,'basis':'inferred','source':'Declared hand-computed serial/overlap fixture premise.'}
    path.write_text(yaml.safe_dump(target,sort_keys=False));pin=digest(target)
    data=fixture_characterization(records.path,subject_id='stub-impl',input_id='tiny-sym')
    accesses=[]
    if memory:accesses=[{'id':'access.0','source_location':{'function':'fixture','line':1},
        'address_shape':{'value':'stream','basis':'reported'},'stride_bytes':{'value':4,'basis':'reported'},
        'element_bytes':4,'update_kind':'read','element_count':fact(2),'bytes_accessed':fact(8),
        'observed_address_span_bytes':{'value':8,'basis':'reported'},'address_expression':'fixture','ir_lanes':1}]
    data['regions']=[{'id':'fixture.region','source_location':{'function':'fixture','line':1},'mapped':True,
        'kind':'serial_remainder','operation_counts':{k:fact(host_work if k=='integer' else 0) for k in ('integer','floating_point','branch','atomic')},
        'dynamic_counts':{'loop_iterations':fact(0)},'footprint_bytes':{'value':8 if memory else 0,'basis':'reported'},
        'access_patterns':accesses,'accelerator_calls':[],'address_stream_counts':{pin:{
            'format':'swdb.logical-address-counts.v1','target_description_sha256':pin,'level':'derived_logical_transactions',
            'state':'complete','scope':'per_call','missing':[],
            **{name:'0'*64 for name in ('layout_sha256','request_policy_sha256','placement_assumption_sha256','window_policy_sha256')},
            'line_requests':fact(6),'row_groups':fact(3),'grouped_row_hits':fact(3),'grouped_row_hit_fraction':fact(.5),
            'windows':fact(2),'staged_bytes':fact(24),'notes':['Logical hand-counted fixture; no hardware evidence.']}}}]
    data.pop('identity_sha256');data['identity_sha256']=digest(data)
    records.write('workload_characterizations/fixture.counts.yaml',data)
    protocol=freeze_protocol(records.path,tmp_path,path,roi='fixture.stream.v1',input_id='tiny-sym')
    result=run_swdb('estimate','--records',records.path,'--characterization','fixture.counts',
        '--target-description',path,'--protocol',protocol,'--id','fixture.composed','--format','json')
    assert result.returncode==0,result.stdout+result.stderr
    return json.loads(result.stdout)


def test_missing_cross_domain_policy_keeps_known_components_and_total_unknown(records,tmp_path):
    result=estimate_domains(records,tmp_path)
    assert result['seconds'] is None
    bounds=result['regions'][0]['bounds']
    assert [(b['model'],b['seconds']) for b in bounds[:2]]==[('compute_throughput',1.),('tile_staging',2.)]
    composed=next(b for b in bounds if b['model']=='domain_composition')
    assert 'composition_contract.resource_domain_overlap' in composed['missing']


def test_executed_host_memory_requires_a_declared_applicable_model(records,tmp_path):
    result=estimate_domains(records,tmp_path,overlap='serial',memory=True)
    assert result['seconds'] is None
    memory=next(b for b in result['regions'][0]['bounds'] if b['model']=='host_memory_coverage')
    assert memory['missing']==['host_memory_service_model']
    assert memory['inputs']['uncovered_source_accesses']==['access.0']


@pytest.mark.parametrize('overlap,expected',[('serial',3.),('full_overlap',2.)])
def test_declared_cross_domain_scenarios_keep_memory_competing_with_host_compute(records,tmp_path,overlap,expected):
    result=estimate_domains(records,tmp_path,overlap=overlap,memory=True,memory_model=True)
    assert result['seconds']==expected
    bounds=result['regions'][0]['bounds']
    assert next(b for b in bounds if b['model']=='streaming_bandwidth')['seconds']==.5
    assert next(b for b in bounds if b['model']=='domain_composition')['inputs']['domain_maxima']=={'host':1.,'offload':2.}
    checked=records.validate();assert checked.returncode==0,checked.stdout+checked.stderr


def test_proven_zero_host_work_requires_no_cross_domain_policy(records,tmp_path):
    result=estimate_domains(records,tmp_path,host_work=0)
    assert result['seconds']==2.
    assert all(b['model']!='domain_composition' for b in result['regions'][0]['bounds'])
