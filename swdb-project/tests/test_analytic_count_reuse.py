"""Public rate-only reuse keeps immutable native counts and every observation policy. 2026-10-06 ET."""
import copy
import json
import yaml
import pytest
from conftest import run_swdb
from testkit.analytic import characterize_command,freeze_protocol,digest


def fact(value,unit):return {'value':value,'basis':'reported','source':'Hand-computed fixture only.','unit':unit}


def setup(records,tmp_path,llvm22):
    mechanisms=[{'model':'reorder_window_rows','selector':{'domain':'offload'},'parameters':{
        'row_miss_service_s':fact(.1,'seconds/request'),'row_hit_service_s':fact(.01,'seconds/request'),
        'effective_memory_parallelism':fact(None,'requests')}}]
    mechanisms[0]['parameters']['effective_memory_parallelism']['basis']='unknown'
    data,counted_hash=characterize_command(records,tmp_path,llvm22,mechanisms=mechanisms)
    return data,counted_hash,yaml.safe_load((tmp_path/'target.yaml').read_text())


def estimate(records,tmp_path,target):
    path=tmp_path/'requested.yaml';path.write_text(yaml.safe_dump(target,sort_keys=False))
    protocol=freeze_protocol(records.path,tmp_path,path,roi='fixture.command.v1',input_id='tiny-sym')
    return run_swdb('estimate','--records',records.path,'--characterization','fixture.command',
        '--target-description',path,'--protocol',protocol,'--id','fixture.reused','--format','json')


def test_rates_only_reuse_retains_original_counts_and_both_target_identities(records,tmp_path,llvm22):
    data,counted_hash,target=setup(records,tmp_path,llvm22)
    before=(records.path/'workload_characterizations/fixture.command.yaml').read_bytes()
    target['id']='fixture.rate-fill';target['version']='2'
    target['mechanisms'][0]['parameters']['effective_memory_parallelism']=fact(2,'requests')
    result=estimate(records,tmp_path,target)
    assert result.returncode==0,result.stdout+result.stderr
    report=json.loads(result.stdout)
    bounds=[b for r in report['regions'] for b in r['bounds'] if b['model']=='reorder_window_rows']
    assert all(b['seconds'] is not None for b in bounds),bounds
    assert report['count_reuse']['counted_target_description_sha256']==counted_hash
    assert report['count_reuse']['requested_target_description_sha256']==digest(target)
    assert report['count_reuse']['state']=='identical_observation_policy'
    assert (records.path/'workload_characterizations/fixture.command.yaml').read_bytes()==before


@pytest.mark.parametrize('change',['window','layout','command_role','source_hash','request_width','placement','extra_selector','extra_parameter','active_policy','backend_selection'])
def test_observation_policy_changes_require_fresh_counts(records,tmp_path,llvm22,change):
    _,_,target=setup(records,tmp_path,llvm22);target['id']='fixture.policy-change'
    observation=target['functional_observation']
    if change=='window':observation['window']['requests']=3
    elif change=='layout':target['dram_address_layout']['row'][0]['lsb']=8
    elif change=='command_role':observation['commands'][0]['aliases'][0]['role']='backend_alias'
    elif change=='source_hash':observation['commands'][0]['aliases'][0]['source_sha256']='0'*64
    elif change=='request_width':observation['request_policy']['transaction_bytes']=32
    elif change=='placement':observation['placement'].update(policy='unknown',basis='unknown')
    elif change=='active_policy':observation['commands'][0].update(active_elements_policy='observed_target_reads',target_reads_per_active_element=2)
    elif change=='backend_selection':observation['commands'][0]['hardware_operations']=['fixture.changed.backend']
    elif change=='extra_selector':target['mechanisms'][0]['selector']['future_observer_policy']='changed'
    else:target['mechanisms'][0]['parameters']['future_observer_width']=fact(4,'bytes')
    result=estimate(records,tmp_path,target)
    assert result.returncode==1,result.stdout+result.stderr
    assert 'observation policy changed; fresh counts required' in result.stdout+result.stderr
    assert not (records.path/'estimates/fixture.reused.yaml').exists()


def test_retained_policy_reference_pins_resolved_rate_value(records,tmp_path,llvm22):
    mechanisms=[{'model':'reorder_window_rows','selector':{'domain':'offload','future_policy':{'parameter':'row_miss_service_s'}},
        'parameters':{'row_miss_service_s':fact(.1,'seconds/request'),'row_hit_service_s':fact(.01,'seconds/request'),
            'effective_memory_parallelism':fact(2,'requests')}}]
    characterize_command(records,tmp_path,llvm22,mechanisms=mechanisms)
    target=yaml.safe_load((tmp_path/'target.yaml').read_text());target['id']='fixture.reference-change'
    target['mechanisms'][0]['parameters']['row_miss_service_s']['value']=.2
    result=estimate(records,tmp_path,target)
    assert result.returncode==1,result.stdout+result.stderr
    assert 'observation policy changed; fresh counts required' in result.stdout+result.stderr
