"""Public frozen parameter-fill behavior. Created: 2026-10-06 ET.
Updated: 2026-10-09 ET (code review: provider pin/guard refusals on resealed receipts)."""
import json
import sys
import yaml
import pytest
from conftest import run_swdb
from testkit.analytic import fixture_characterization, target_description


def setup_role(records, tmp_path, answers=None):
    records.add_stub()
    char = fixture_characterization(records.path, 'stub-impl', 'tiny-sym')
    target = target_description(tmp_path, bandwidth=None)
    data = yaml.safe_load(target.read_text()); data['target'] = 'testhost'
    target.write_text(yaml.safe_dump(data, sort_keys=False))
    profile = tmp_path / 'profile.yaml'
    profile.write_text(yaml.safe_dump({'kind':'profile_package','schema_version':'0.4',
        'id':'fixture.profile','status':'draft','created':'2026-10-06','updated':'2026-10-06',
        'provenance':[{'id':'fixture','kind':'source_code','description':'Contract fixture only.'}], 'message_version':'1.0',
        'producer':{'name':'fixture','role':'operator','test_client':True},
        'implementation':'stub-impl','source_snapshot':'fixture.source','context':{},
        'completeness':'fixture','regions':[],'dynamic_memory':[],'constraints':{},
        'evidence':{},'reasons':[]}))
    response = {'parameters': answers if answers is not None else [{'parameter':
        'mechanisms[1].parameters.bytes_per_s','value':32.0,'unit':'bytes/s',
        'basis':'estimated','reason':'Hand-worked contract response, not measured performance.'}]}
    program=tmp_path/'provider.py'
    program.write_text('import json\nprint('+repr(json.dumps(response))+')\n')
    config=tmp_path/'provider.yaml'
    config.write_text(yaml.safe_dump({'kind':'external_fixture','command':[sys.executable,str(program)],
        'timeout_s':5,'total_seconds':5}))
    return char, target, profile, config


def fill(records, tmp_path, target, profile, config, *, output='role', rid='fixture.filled'):
    return run_swdb('fill-target-parameters','--records',records.path,
        '--characterization','fixture.counts','--profile',profile,'--target-description',target,
        '--provider-config',config,'--output',tmp_path/output,'--id',rid,'--format','json')


def test_public_stub_freezes_new_description_and_preserves_base(records,tmp_path):
    _,target,profile,config=setup_role(records,tmp_path)
    original=target.read_bytes()
    result=fill(records,tmp_path,target,profile,config)
    assert result.returncode==0,result.stdout+result.stderr
    new=json.loads(result.stdout)
    assert new['id']=='fixture.filled' and new['version']!= '1'
    fact=new['mechanisms'][1]['parameters']['bytes_per_s']
    assert fact['value']==32.0 and fact['basis']=='estimated'
    assert 'Hand-worked' in fact['source']
    assert new['mechanisms'][0]==yaml.safe_load(original)['mechanisms'][0]
    assert target.read_bytes()==original
    receipt=new['parameter_estimation']
    assert receipt['output']['parameters'][0]['reason'].startswith('Hand-worked')
    assert receipt['provider']['classification']=='contract_fixture'
    assert receipt['provider']['audit_passed'] is True
    assert records.validate().returncode==0


def test_public_validation_refuses_tampered_frozen_value(records,tmp_path):
    _,target,profile,config=setup_role(records,tmp_path)
    result=fill(records,tmp_path,target,profile,config)
    assert result.returncode==0,result.stdout+result.stderr
    new=json.loads(result.stdout)
    new['mechanisms'][1]['parameters']['bytes_per_s']['value']=64.0
    records.write('target_descriptions/fixture.filled.yaml',new)
    validation=records.validate()
    assert validation.returncode!=0
    assert 'parameter_estimation' in validation.stdout+validation.stderr


def test_known_numeric_context_requires_model_parameter_semantics(records,tmp_path):
    _,target,profile,config=setup_role(records,tmp_path)
    data=yaml.safe_load(target.read_text())
    data['mechanisms'][0]['parameters']['hidden_timing']={
        'value':987654.0,'unit':'seconds/call','basis':'reported','source':'Nested outcome should never become context.'}
    target.write_text(yaml.safe_dump(data,sort_keys=False))
    result=fill(records,tmp_path,target,profile,config)
    assert result.returncode!=0
    assert 'unsupported parameter contract' in result.stderr
    assert not (tmp_path/'role').exists()


def test_public_workspace_is_semantic_allowlist_and_keeps_omission_hashes(records,tmp_path):
    char,target,profile,config=setup_role(records,tmp_path)
    marker='PRIVATE_TIMING_EVALUATOR_OTHER_CANDIDATE'
    char['source']['path']=marker+'.cpp';char['counting']['output_directory']=marker
    from testkit.analytic import digest
    char['identity_sha256']=digest({k:v for k,v in char.items() if k!='identity_sha256'})
    records.write('workload_characterizations/fixture.counts.yaml',char)
    data=yaml.safe_load(profile.read_text())
    data['regions']=[{'id':marker,'kind':'loop','text':marker,
        'metrics':{'pmu':{'cycles':1234567,'ipc':3.25},'nested':[{'wall_seconds':7654321}]}}]
    data['evidence']={'evaluator':marker,'other_candidates':[marker],
        'timing':{'label':marker,'value':1234567},'hidden':[{'derived_rate':7654321}]}
    profile.write_text(yaml.safe_dump(data,sort_keys=False))
    program=tmp_path/'provider.py'
    program.write_text('from pathlib import Path\nimport json\n'
        'files=[p for p in Path.cwd().iterdir() if p.is_file()]\n'
        'assert sorted(p.name for p in files)==["characterization.json","parameters.json","profile.json"]\n'
        'text="".join(p.read_text() for p in files)\n'
        'assert '+repr(marker)+' not in text\n'
        'assert "1234567" not in text and "7654321" not in text\n'
        'print('+repr(json.dumps({'parameters':[{'parameter':'mechanisms[1].parameters.bytes_per_s',
            'value':32.0,'unit':'bytes/s','basis':'estimated','reason':'Allowlist fixture.'}]}))+')\n')
    result=fill(records,tmp_path,target,profile,config)
    assert result.returncode==0,result.stdout+result.stderr
    new=json.loads(result.stdout);receipt=new['parameter_estimation']
    omissions=receipt['projection']['omitted_raw_fields']
    assert any(row['input']=='profile' and row['field']=='evidence' for row in omissions)
    assert all(len(row['sha256'])==64 for row in omissions)
    workspace=json.loads((tmp_path/'role/workspace.json').read_text())
    assert workspace['source_files']==[] and workspace['read_only'] is True


def test_public_known_parameter_override_is_rejected(records,tmp_path):
    answers=[{'parameter':'mechanisms[0].parameters.integer_ops_per_s','value':123,
        'unit':'operations/s','basis':'estimated','reason':'Invalid override fixture.'}]
    _,target,profile,config=setup_role(records,tmp_path,answers)
    before=target.read_bytes()
    result=fill(records,tmp_path,target,profile,config)
    assert result.returncode!=0 and 'already known' in result.stderr
    assert target.read_bytes()==before
    assert not list((records.path/'target_descriptions').glob('*.yaml'))


def test_public_same_version_cannot_refill_after_cosmetic_base_edit(records,tmp_path):
    _,target,profile,config=setup_role(records,tmp_path)
    first=fill(records,tmp_path,target,profile,config)
    assert first.returncode==0,first.stdout+first.stderr
    data=yaml.safe_load(target.read_text())
    data['mechanisms'][1]['parameters']['bytes_per_s']['source']='A revised note cannot reopen this version.'
    target.write_text(yaml.safe_dump(data,sort_keys=False))
    again=fill(records,tmp_path,target,profile,config,output='second-role',rid='fixture.second')
    assert again.returncode!=0 and 'already has frozen' in again.stderr
    assert not (tmp_path/'second-role').exists()


def stream_region(useful_bytes):
    fact=lambda value,basis='measured':{'value':value,'basis':'unknown' if value is None else basis}
    counted=lambda value:{**fact(value),'scope':'per_trial','formula':None}
    return {'id':'fixture.stream','source_location':{'function':'fixture','line':1},
        'kind':'loop','mapped':False,'operation_counts':{name:counted(0) for name in
            ('integer','floating_point','branch','atomic')},
        'dynamic_counts':{'loop_iterations':counted(useful_bytes//8)},
        'footprint_bytes':fact(useful_bytes),'active_workers':fact(1),
        'access_patterns':[{'id':'access.0','source_location':{'function':'fixture','line':2},
            'address_shape':fact('stream','code_reading'),'stride_bytes':fact(8,'code_reading'),
            'element_bytes':8,'update_kind':'read','element_count':counted(useful_bytes//8),
            'bytes_accessed':counted(useful_bytes),'observed_address_span_bytes':fact(useful_bytes),
            'address_expression':'Hand-worked fixture, not real IR.','ir_lanes':1}],
        'accelerator_calls':[],'address_stream_counts':{}}


def test_public_filled_parameter_drives_full_trial_sensitivity(records,tmp_path):
    char,target,profile,config=setup_role(records,tmp_path)
    char['regions']=[stream_region(96)]
    char['trials']=[{'position':i,'sources':[], 'regions':[stream_region(value)],'unmodeled_calls':[]}
        for i,value in enumerate((96,160,128))]
    from testkit.analytic import digest,freeze_protocol
    char['identity_sha256']=digest({k:v for k,v in char.items() if k!='identity_sha256'})
    records.write('workload_characterizations/fixture.counts.yaml',char)
    result=fill(records,tmp_path,target,profile,config)
    assert result.returncode==0,result.stdout+result.stderr
    new=json.loads(result.stdout)
    protocol=freeze_protocol(records.path,tmp_path,new['id'],roi='fixture.stream.v1',input_id='tiny-sym')
    estimated=run_swdb('estimate','--records',records.path,'--characterization','fixture.counts',
        '--target-description',new['id'],'--protocol',protocol,'--id','fixture.estimate','--format','json')
    assert estimated.returncode==0,estimated.stdout+estimated.stderr
    report=json.loads(estimated.stdout)
    assert report['seconds']==4.0
    assert [t['seconds'] for t in report['trials']]==[3.0,5.0,4.0]
    filled=report['llm_parameters']
    assert len(filled)==1 and filled[0]['value']==32.0 and filled[0]['basis']=='estimated'
    assert filled[0]['whole_call_seconds']=={'half':8.0,'base':4.0,'double':2.0}
    assert filled[0]['scenario_values']=={'half':16.0,'base':32.0,'double':64.0}
    assert filled[0]['source']==new['mechanisms'][1]['parameters']['bytes_per_s']['source']


def test_public_structural_gap_stays_unknown_after_numeric_fill(records,tmp_path):
    char,target,profile,config=setup_role(records,tmp_path)
    char['regions']=[stream_region(128)]
    from testkit.analytic import digest,freeze_protocol
    char['identity_sha256']=digest({k:v for k,v in char.items() if k!='identity_sha256'})
    records.write('workload_characterizations/fixture.counts.yaml',char)
    data=yaml.safe_load(target.read_text())
    data['mechanisms'].append({'model':'unresolved_runtime','parameters':{}})
    target.write_text(yaml.safe_dump(data,sort_keys=False))
    result=fill(records,tmp_path,target,profile,config)
    assert result.returncode==0,result.stdout+result.stderr
    new=json.loads(result.stdout)
    protocol=freeze_protocol(records.path,tmp_path,new['id'],roi='fixture.stream.v1',input_id='tiny-sym')
    estimated=run_swdb('estimate','--records',records.path,'--characterization','fixture.counts',
        '--target-description',new['id'],'--protocol',protocol,'--id','fixture.unknown','--format','json')
    assert estimated.returncode==0,estimated.stdout+estimated.stderr
    report=json.loads(estimated.stdout)
    assert report['seconds'] is None and report['ratio'] is None
    filled=report['llm_parameters'][0]
    assert filled['whole_call_seconds']=={'half':None,'base':None,'double':None}
    assert filled['impact_rank'] is None and filled['sensitivity_state']=='local_components_only'
    assert report['parameter_report']['structural_missing'][0]['parameter_fill_allowed'] is False


@pytest.mark.parametrize('change',[
    {'unit':'GB/s'},{'value':True},{'value':0},{'value':-1},{'value':float('inf')},
    {'basis':'measured'},{'value':None,'basis':'estimated'},{'extra':'unapproved'},
])
def test_public_invalid_provider_values_write_no_description(records,tmp_path,change):
    answer={'parameter':'mechanisms[1].parameters.bytes_per_s','value':32.0,
        'unit':'bytes/s','basis':'estimated','reason':'Invalid output fixture.',**change}
    _,target,profile,config=setup_role(records,tmp_path,[answer])
    result=fill(records,tmp_path,target,profile,config)
    assert result.returncode!=0
    assert not list((records.path/'target_descriptions').glob('*.yaml'))


def test_public_null_output_is_frozen_unknown_without_guess(records,tmp_path):
    answer={'parameter':'mechanisms[1].parameters.bytes_per_s','value':None,
        'unit':'bytes/s','basis':'unknown','reason':'Insufficient service evidence.'}
    _,target,profile,config=setup_role(records,tmp_path,[answer])
    result=fill(records,tmp_path,target,profile,config)
    assert result.returncode==0,result.stdout+result.stderr
    new=json.loads(result.stdout)
    assert new['mechanisms'][1]['parameters']['bytes_per_s']['value'] is None
    assert new['parameter_estimation']['output']['parameters'][0]['reason']=='Insufficient service evidence.'
    again=fill(records,tmp_path,new['id'],profile,config,output='refill',rid='refilled')
    assert again.returncode!=0 and not (tmp_path/'refill').exists()


def test_public_prepare_only_exports_bounded_inputs_without_launch(records,tmp_path):
    _,target,profile,config=setup_role(records,tmp_path)
    config.unlink()
    result=run_swdb('fill-target-parameters','--records',records.path,
        '--characterization','fixture.counts','--profile',profile,'--target-description',target,
        '--prepare-only','--output',tmp_path/'prepared','--id','future.filled','--format','json')
    assert result.returncode==0,result.stdout+result.stderr
    plan=json.loads(result.stdout)
    assert plan['state']=='prepared' and plan['provider_launched'] is False
    assert plan['total_input_bytes']<10*1024**2
    assert sorted(p.name for p in (tmp_path/'prepared/inputs').iterdir())==[
        'characterization.json','parameters.json','profile.json']
    assert not (tmp_path/'prepared/provider-home').exists()
    assert not list((records.path/'target_descriptions').glob('*.yaml'))


def test_public_resealed_projection_must_match_canonical_count_facts(records,tmp_path):
    char,target,profile,config=setup_role(records,tmp_path)
    char['regions']=[stream_region(128)]
    from testkit.analytic import digest
    char['identity_sha256']=digest({k:v for k,v in char.items() if k!='identity_sha256'})
    records.write('workload_characterizations/fixture.counts.yaml',char)
    result=fill(records,tmp_path,target,profile,config)
    assert result.returncode==0,result.stdout+result.stderr
    new=json.loads(result.stdout);receipt=new['parameter_estimation']
    snapshot=receipt['input_snapshots']['characterization.json']
    snapshot['trials'][0]['regions'][0]['access_groups'][0]['elements']=123
    receipt['input_sha256s']['characterization.json']=digest(snapshot)
    row=next(row for row in receipt['projection']['files'] if row['name']=='characterization.json')
    row['sha256']=digest(snapshot)
    row['bytes']=len(json.dumps(snapshot,sort_keys=True,separators=(',',':')).encode())
    receipt['identity_sha256']=digest({k:v for k,v in receipt.items() if k!='identity_sha256'})
    records.write('target_descriptions/fixture.filled.yaml',new)
    validation=records.validate()
    assert validation.returncode!=0
    assert 'projection differs from canonical characterization' in validation.stdout+validation.stderr


def test_public_huge_numeric_output_is_domain_refusal(records,tmp_path):
    answer={'parameter':'mechanisms[1].parameters.bytes_per_s','value':10**400,
        'unit':'bytes/s','basis':'estimated','reason':'Invalid nonrepresentable rate.'}
    _,target,profile,config=setup_role(records,tmp_path,[answer])
    result=fill(records,tmp_path,target,profile,config)
    assert result.returncode!=0 and 'declared domain' in result.stderr
    assert 'Traceback' not in result.stderr


def test_public_role_launcher_enforces_input_contract_before_workspace(records,tmp_path):
    _,target,profile,config=setup_role(records,tmp_path)
    seed=run_swdb('fill-target-parameters','--records',records.path,
        '--characterization','fixture.counts','--profile',profile,'--target-description',target,
        '--prepare-only','--output',tmp_path/'seed','--id','future.filled','--format','json')
    assert seed.returncode==0,seed.stdout+seed.stderr
    files={p.name:p.read_text() for p in (tmp_path/'seed/inputs').iterdir()}
    data=json.loads(files['profile.json']);data['wall_seconds']=987654
    files['profile.json']=json.dumps(data)
    from swdb import provider_roles,rewrite
    from swdb.cli import Failure
    with pytest.raises(Failure,match='invalid estimation input'):
        provider_roles.run('estimation',files,'Ignored fixture prompt',rewrite.configuration(config),tmp_path/'blocked')
    assert not (tmp_path/'blocked').exists()


def test_public_verified_label_alone_cannot_prepare_inputs(records,tmp_path):
    char,target,profile,_=setup_role(records,tmp_path)
    char['binding']['state']='verified'
    from testkit.analytic import digest
    char['identity_sha256']=digest({k:v for k,v in char.items() if k!='identity_sha256'})
    records.write('workload_characterizations/fixture.counts.yaml',char)
    result=run_swdb('fill-target-parameters','--records',records.path,
        '--characterization','fixture.counts','--profile',profile,'--target-description',target,
        '--prepare-only','--output',tmp_path/'blocked','--id','future.filled','--format','json')
    assert result.returncode!=0 and 'counted execution receipt' in result.stderr
    assert not (tmp_path/'blocked').exists()


@pytest.mark.parametrize('answers',[
    [],[{'parameter':'mechanisms[1].parameters.bytes_per_s','value':32.0,'unit':'bytes/s',
        'basis':'estimated','reason':'Fixture duplicate.'}]*2,
])
def test_public_output_requires_one_answer_per_unknown(records,tmp_path,answers):
    _,target,profile,config=setup_role(records,tmp_path,answers)
    result=fill(records,tmp_path,target,profile,config)
    assert result.returncode!=0
    assert 'every declared unknown' in result.stderr or 'duplicate parameter' in result.stderr
    assert not list((records.path/'target_descriptions').glob('*.yaml'))


def test_public_failed_service_compatibility_refuses_before_provider(records,tmp_path):
    _,target,profile,config=setup_role(records,tmp_path)
    data=yaml.safe_load(target.read_text())
    data['extensions']={'cpu_services_binding':{
        'format':'swdb.cpu-services-binding.v1',
        'models':['streaming_bandwidth'],
        'compatibility':[{'calibration':'fixture.service','service':'fixture.read',
            'parameter':'bytes_per_s','missing':['service_compiler_identity'],
            'scopes':[{'characterization':'fixture.counts','missing':['service_compiler_identity']}]}]}}
    target.write_text(yaml.safe_dump(data,sort_keys=False))
    before=target.read_bytes()
    result=fill(records,tmp_path,target,profile,config)
    assert result.returncode!=0
    assert 'structural service compatibility gap' in result.stderr
    assert not (tmp_path/'role').exists()
    assert target.read_bytes()==before
    assert not list((records.path/'target_descriptions').glob('*.yaml'))


@pytest.mark.parametrize('missing,scope_missing',[
    ([],[]),([],['service_serial_T1']),
])
def test_public_service_compatibility_keeps_scoped_premises(records,tmp_path,missing,scope_missing):
    _,target,profile,config=setup_role(records,tmp_path)
    data=yaml.safe_load(target.read_text())
    data['extensions']={'cpu_services_binding':{
        'format':'swdb.cpu-services-binding.v1',
        'models':['streaming_bandwidth'],
        'compatibility':[{'calibration':'fixture.service','service':'fixture.read',
            'parameter':'bytes_per_s','missing':missing,
            'scopes':[{'characterization':'fixture.counts','missing':scope_missing}]}]}}
    target.write_text(yaml.safe_dump(data,sort_keys=False))
    result=fill(records,tmp_path,target,profile,config)
    if scope_missing:
        assert result.returncode!=0 and 'structural service compatibility gap' in result.stderr
        assert not (tmp_path/'role').exists()
    else:
        assert result.returncode==0,result.stdout+result.stderr
        new=json.loads(result.stdout)
        assert new['mechanisms'][1]['parameters']['bytes_per_s']['value']==32.0
        assert new['extensions']==data['extensions']
        assert records.validate().returncode==0


@pytest.mark.parametrize('fault',['wrong-model','guard-not-enforced','fixture-as-actual'])
def test_public_validation_holds_actual_estimation_receipts_to_shared_provider_pins(records,tmp_path,fault):
    # 2026-10-09 ET (code review): the role must use the same pins and guard as
    # the other agent roles; a resealed receipt cannot relax them.
    _,target,profile,config=setup_role(records,tmp_path)
    result=fill(records,tmp_path,target,profile,config)
    assert result.returncode==0,result.stdout+result.stderr
    new=json.loads(result.stdout);receipt=new['parameter_estimation'];provider=receipt['provider']
    from swdb.provider_adapters import PINS
    from testkit.analytic import digest
    if fault=='fixture-as-actual':
        provider['classification']='rewrite_provider'
        expected='fixture provider cannot establish actual evidence'
    else:
        provider.update(kind='codex',classification='rewrite_provider',guard_enforced=True,guard_passed=True,**PINS['codex'])
        if fault=='wrong-model':provider['model']='unpinned-model';expected='actual provider pins or classification differ'
        else:provider['guard_enforced']=False;expected='actual estimation requires a passing enforced provider guard'
    receipt['identity_sha256']=digest({k:v for k,v in receipt.items() if k!='identity_sha256'})
    records.write('target_descriptions/fixture.filled.yaml',new)
    validation=records.validate()
    assert validation.returncode!=0 and expected in validation.stdout+validation.stderr
