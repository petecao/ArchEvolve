"""Public cross-domain composition and required source coverage. 2026-10-09 ET."""
import json
import copy
import yaml
import pytest
from conftest import run_swdb
from testkit.analytic import digest,fixture_characterization,target_description,freeze_protocol


def fact(value):return {'value':value,'basis':'reported','scope':'per_call'}
def rate(value,unit):return {'value':value,'basis':'unknown' if value is None else 'reported','source':'Hand-computed fixture only.','unit':unit}


def estimate_domains(records,tmp_path,*,overlap=None,host_work=1,memory=False,memory_model=False,host_rate=1,stage_rate=12,queue=False,stage_basis=None,trial_pairs=None):
    records.add_stub()
    path=target_description(tmp_path)
    target=yaml.safe_load(path.read_text());target['target']='testhost'
    target['mechanisms']=[{'model':'compute_throughput','parameters':{
        kind+'_ops_per_s':rate(host_rate if kind=='integer' else 1,'operations/s') for kind in ('integer','floating_point','branch','atomic')}},
        {'model':'tile_staging','selector':{'domain':'offload'},'parameters':{'staging_bytes_per_s':rate(stage_rate,'bytes/s')}}]
    if stage_basis is not None:target['mechanisms'][1]['parameters']['staging_bytes_per_s']['basis']=stage_basis
    if queue:target['mechanisms'].append({'model':'fetch_queue','selector':{'domain':'offload'},'parameters':{
        'queue_entries':rate(2,'entries'),'fetch_latency_s':rate(.1,'seconds/request'),'admission_requests_per_s':rate(10,'requests/s')}})
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
    if trial_pairs is not None:
        first=copy.deepcopy(data['regions'][0]);second=copy.deepcopy(first)
        first['id']='fixture.a';second['id']='fixture.b'
        for region in (first,second):
            observed=region['address_stream_counts'][pin]
            for field in ('line_requests','row_groups','grouped_row_hits','windows','staged_bytes'):observed[field]=fact(0)
            observed['grouped_row_hit_fraction']={'value':None,'basis':'unknown','scope':'per_call'}
        trials=[]
        for position,(left,right) in enumerate(trial_pairs):
            regions=copy.deepcopy([first,second])
            for region,value in zip(regions,(left,right)):region['operation_counts']['integer']=fact(value)
            trials.append({'position':position,'sources':[],'regions':regions,'unmodeled_calls':[]})
        data['regions']=copy.deepcopy(trials[0]['regions']);data['trials']=trials
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


def test_unknown_parameter_report_keeps_impact_unranked_and_structural_gaps_separate(records,tmp_path):
    result=estimate_domains(records,tmp_path,host_rate=None,memory=True)
    report=result['parameter_report']
    unknown=report['unknowns'][0]
    assert unknown['parameter']=='mechanisms[0].parameters.integer_ops_per_s'
    assert unknown['required_for_total'] is True and unknown['priority_rank']==1
    assert unknown['impact_rank'] is None and unknown['impact_magnitude_seconds'] is None
    assert unknown['sensitivity_state']=='unknown_reference'
    assert {row['missing'] for row in report['structural_missing']} >= {'host_memory_service_model','composition_contract.resource_domain_overlap'}
    assert all(row['parameter_fill_allowed'] is False for row in report['structural_missing'])
    staging=next(row for row in report['sensitivities'] if row['parameter'].endswith('.staging_bytes_per_s'))
    assert staging['whole_call_seconds']=={'half':None,'base':None,'double':None}
    assert staging['component_seconds']['half']['fixture.region.bounds.tile_staging']==4.
    assert staging['component_seconds']['double']['fixture.region.bounds.tile_staging']==1.
    assert staging['impact_rank'] is None
    assert result['seconds'] is None


def test_known_numeric_sensitivity_ranks_full_call_and_lists_frozen_estimated_parameters(records,tmp_path):
    result=estimate_domains(records,tmp_path,overlap='serial',stage_basis='estimated')
    stage=next(row for row in result['parameter_report']['sensitivities'] if row['model']=='tile_staging')
    assert stage['whole_call_seconds']=={'half':5.,'base':3.,'double':2.}
    assert stage['impact_magnitude_seconds']==2. and stage['impact_rank']==1
    assert stage['sensitivity_state']=='whole_call_numeric_scenario'
    assert result['llm_parameters']==[stage]
    checked=records.validate();assert checked.returncode==0,checked.stdout+checked.stderr


def test_observation_affecting_capacity_sensitivity_requires_fresh_counts(records,tmp_path):
    result=estimate_domains(records,tmp_path,overlap='full_overlap',queue=True)
    capacity=next(row for row in result['parameter_report']['sensitivities'] if row['parameter'].endswith('.queue_entries'))
    assert capacity['sensitivity_state']=='requires_fresh_observation'
    assert capacity['whole_call_seconds']=={'half':None,'base':2.,'double':None}
    assert capacity['scenario_values']=={'half':1.,'base':2,'double':4.}
    assert capacity['impact_magnitude_seconds'] is None and capacity['impact_rank'] is None


def test_public_validation_refuses_sensitivity_detached_from_frozen_parameter(records,tmp_path):
    result=estimate_domains(records,tmp_path,overlap='serial')
    result['parameter_report']['sensitivities'][0]['value']=999.
    records.write('estimates/fixture.composed.yaml',result)
    refused=records.validate()
    assert refused.returncode==1 and 'parameter differs from its frozen target fact' in refused.stdout+refused.stderr


def test_sensitivity_recomposes_each_trial_before_whole_call_median(records,tmp_path):
    result=estimate_domains(records,tmp_path,trial_pairs=[(10,0),(0,10),(6,6)])
    assert result['seconds']==10.
    assert sum(region['seconds'] for region in result['regions'])==12.
    integer=next(row for row in result['parameter_report']['sensitivities'] if row['parameter'].endswith('.integer_ops_per_s'))
    assert integer['whole_call_seconds']=={'half':20.,'base':10.,'double':5.}
    assert integer['component_seconds']['half']['fixture.a.bounds.compute_throughput']==12.
    assert integer['component_seconds']['half']['fixture.b.bounds.compute_throughput']==12.


def admit_composed(records, estimate):
    from swdb.analytic_estimate_binding import admit
    from swdb.store import Store
    store=Store(records.path)
    char=store.get(estimate['characterization'],'workload_characterization')
    target=store.get(estimate['protocol'],'protocol')['settings']['target_description']['snapshot']
    return admit(store,estimate,char,target)


@pytest.mark.parametrize('fault',[
    'total','region','bound','model_input','scope','binding','target_snapshot',
    'orphan_trials','legacy_proof','numeric_type',
])
def test_fresh_admission_rejects_saved_derivation_tampering(records,tmp_path,fault):
    result=estimate_domains(records,tmp_path,overlap='serial')
    assert result['seconds']==3. and admit_composed(records,result)['id']==result['protocol']
    forged=copy.deepcopy(result)
    if fault=='total':
        forged['seconds']=6.
        # Synchronize diagnostics so the generic finite/hash checks still pass.
        for row in forged['parameter_report']['sensitivities']:
            row['whole_call_seconds']['base']=6.
    elif fault=='region':forged['regions'][0]['seconds']=6.
    elif fault=='bound':forged['regions'][0]['bounds'][0]['seconds']=7.
    elif fault=='model_input':forged['regions'][0]['bounds'][0]['inputs']['integer']['operations']=99
    elif fault=='scope':forged['scope']['whole_timed_call']=True
    elif fault=='binding':forged['binding']['threads']=2
    elif fault=='target_snapshot':
        forged['target_description_snapshot']['composition_contract']['resource_domain_overlap']='full_overlap'
        forged['target_description_sha256']=digest(forged['target_description_snapshot'])
    elif fault=='orphan_trials':forged.update(trials=[],summary='median_whole_call_seconds')
    elif fault=='legacy_proof':forged['extensions']={'legacy_trial_scope_reconciliations':[{'basis':'inferred'}]}
    elif fault=='numeric_type':forged['regions'][0]['bounds'][0]['seconds']=True
    if fault=='total':
        from swdb.analytic import _payload_problems
        assert not list(_payload_problems(forged))
    from swdb.cli import Failure
    with pytest.raises(Failure,match='count-to-model composition'):
        admit_composed(records,forged)


def test_fresh_admission_uses_median_whole_call_not_sum_of_region_medians(records,tmp_path):
    result=estimate_domains(records,tmp_path,trial_pairs=[(10,0),(0,10),(6,6)])
    assert result['seconds']==10. and sum(r['seconds'] for r in result['regions'])==12.
    assert admit_composed(records,result)['id']==result['protocol']
    from swdb.cli import Failure
    for fault in ('total','source_slot','trial_component'):
        forged=copy.deepcopy(result)
        if fault=='total':forged['seconds']=12.
        elif fault=='source_slot':forged['trials'][0]['sources']=[1]
        else:forged['trials'][0]['regions'][0]['bounds'][0]['seconds']=20.
        with pytest.raises(Failure,match='count-to-model composition'):
            admit_composed(records,forged)


def test_fresh_admission_keeps_required_unknown_and_refuses_old_model_version(records,tmp_path,monkeypatch):
    result=estimate_domains(records,tmp_path,overlap='serial',host_rate=None)
    assert result['seconds'] is None and admit_composed(records,result)['id']==result['protocol']
    forged=copy.deepcopy(result);forged['seconds']=2.
    from swdb.cli import Failure
    with pytest.raises(Failure,match='count-to-model composition'):
        admit_composed(records,forged)
    from swdb import estimate_protocol
    monkeypatch.setattr(estimate_protocol,'estimator_identity',lambda:'0'*64)
    with pytest.raises(Failure,match='estimator implementation changed after freeze'):
        admit_composed(records,result)


@pytest.mark.parametrize('fault',['scenario','components','omitted_rows','llm_parameters'])
def test_fresh_admission_binds_halve_double_sensitivity_and_estimated_parameter_list(records,tmp_path,fault):
    result=estimate_domains(records,tmp_path,overlap='serial',stage_basis='estimated')
    assert admit_composed(records,result)['id']==result['protocol']
    stage=next(row for row in result['parameter_report']['sensitivities'] if row['model']=='tile_staging')
    assert stage['whole_call_seconds']=={'half':5.,'base':3.,'double':2.}
    assert result['llm_parameters']==[stage]
    forged=copy.deepcopy(result)
    if fault=='scenario':
        row=next(row for row in forged['parameter_report']['sensitivities'] if row['model']=='tile_staging')
        row['whole_call_seconds'].update(half=99.,double=99.)
        row.update(impact_magnitude_seconds=96.,impact_rank=1)
        forged['llm_parameters']=[copy.deepcopy(row)]
    elif fault=='components':
        forged['parameter_report']['sensitivities'][0]['component_seconds']['half']={'invented.bounds.compute_throughput':99.}
    elif fault=='omitted_rows':forged['parameter_report']['sensitivities']=[];forged['llm_parameters']=[]
    else:forged['llm_parameters']=[]
    from swdb.analytic import _payload_problems
    assert not list(_payload_problems(forged))
    from swdb.cli import Failure
    with pytest.raises(Failure,match='count-to-model composition'):
        admit_composed(records,forged)
