"""Immutable service bindings through the separate public module CLI (2026-10-06 ET)."""
import json
import subprocess
import sys

import yaml

from conftest import run_swdb
from test_cpu_service_calibration import fixture_receipt, save_receipt
from testkit.analytic import target_description, fixture_characterization, digest


def bind(records, *args):
    return subprocess.run([sys.executable,'-m','swdb.cpu_service_binding','--records',str(records.path),
        *map(str,args),'--format','json'], capture_output=True,text=True)


def test_binding_pins_typed_receipt_and_preserves_original_target(records,tmp_path):
    records.add_stub()
    original=yaml.safe_load(target_description(tmp_path).read_text())
    original['id']='fixture.cpu.base';original['target']='testhost'
    records.write('target_descriptions/fixture.cpu.base.yaml',original)
    before=(records.path/'target_descriptions/fixture.cpu.base.yaml').read_bytes()
    char=fixture_characterization(records.path,subject_id='stub-impl',input_id='tiny-sym')
    raw=fixture_receipt();raw['machine']='testhost'
    raw['services'][0]['denominator']['proof']={'event_abi':'fixture.clock.abi'}
    result=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',save_receipt(tmp_path,raw),
        '--id','fixture.clock.cost','--fixture','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    outcome=bind(records,'--target-description','fixture.cpu.base','--characterization','fixture.counts',
        '--calibration','fixture.clock.cost','--id','fixture.cpu.services','--fixture')
    assert outcome.returncode==0,outcome.stderr+outcome.stdout
    data=json.loads(outcome.stdout)
    assert data['calibration_sources']==['fixture.clock.cost','fixture.counts']
    model=data['mechanisms'][-1]
    assert model['model']=='native_service_costs' and model['parameters']['service_0']['value']==.1
    assert model['parameters']['service_0']['basis']=='reported'
    assert model['selector']['calls']==[{'name':'fixture.clock.abi','parameter':'service_0','unit':'seconds/call'}]
    snapshot=data['extensions']['cpu_services_binding']
    assert snapshot['characterization']=={'id':'fixture.counts','sha256':digest(char)}
    assert snapshot['calibrations'][0]['id']=='fixture.clock.cost'
    assert (records.path/'target_descriptions/fixture.cpu.base.yaml').read_bytes()==before
    assert records.validate().returncode==0
    refused=bind(records,'--target-description','fixture.cpu.base','--characterization','fixture.counts',
        '--calibration','fixture.clock.cost','--id','fixture.cpu.false.native')
    assert refused.returncode!=0 and 'fixture' in refused.stderr
    assert not (records.path/'target_descriptions/fixture.cpu.false.native.yaml').exists()


def test_native_cost_with_unproven_workload_runtime_stays_unknown(records,tmp_path):
    from conftest import REPO
    records.add_stub()
    original=yaml.safe_load(target_description(tmp_path).read_text());original['id']='fixture.cpu.base'
    records.write('target_descriptions/fixture.cpu.base.yaml',original)
    fixture_characterization(records.path,subject_id='stub-impl',input_id='tiny-sym')
    name='mbit10.cpu.lanl20261006.service.clock.a1'
    actual=yaml.safe_load((REPO/'records/cpu_service_calibrations'/f'{name}.yaml').read_text())
    records.write('cpu_service_calibrations/'+name+'.yaml',actual)
    outcome=bind(records,'--target-description','fixture.cpu.base','--characterization','fixture.counts',
        '--calibration',name,'--id','fixture.cpu.unmatched','--fixture')
    assert outcome.returncode==0,outcome.stderr+outcome.stdout
    data=json.loads(outcome.stdout)
    assert data['mechanisms'][-1]['parameters']['service_0']['value'] is None
    assert data['mechanisms'][-1]['parameters']['service_0']['basis']=='unknown'
    reasons=data['extensions']['cpu_services_binding']['compatibility'][0]['missing']
    assert 'service_compiler_identity' in reasons and 'service_runtime.libc.so' in reasons
    assert 'service_interposer_control_absence_scope' in reasons
    assert actual['services'][0]['parameter']['basis']=='measured'


def test_duplicate_exact_abi_cannot_create_an_ambiguous_cost(records,tmp_path):
    records.add_stub()
    original=yaml.safe_load(target_description(tmp_path).read_text());original['id']='fixture.cpu.base'
    original['target']='testhost';records.write('target_descriptions/fixture.cpu.base.yaml',original)
    fixture_characterization(records.path,subject_id='stub-impl',input_id='tiny-sym')
    raw=fixture_receipt();raw['machine']='testhost'
    raw['services'][0]['denominator']['proof']={'event_abi':'fixture.clock.abi'}
    result=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',save_receipt(tmp_path,raw),
        '--id','fixture.clock.cost','--fixture')
    assert result.returncode==0,result.stderr+result.stdout
    outcome=bind(records,'--target-description','fixture.cpu.base','--characterization','fixture.counts',
        '--calibration','fixture.clock.cost','--calibration','fixture.clock.cost','--id','fixture.cpu.ambiguous','--fixture')
    assert outcome.returncode!=0 and 'ambiguous duplicate' in outcome.stderr
    assert not (records.path/'target_descriptions/fixture.cpu.ambiguous.yaml').exists()


def test_binding_freezes_exact_outcome_free_characterization_allowlist_and_checks_every_member(records,tmp_path):
    import copy
    records.add_stub()
    original=yaml.safe_load(target_description(tmp_path).read_text());original.update(id='fixture.cpu.base',target='testhost')
    records.write('target_descriptions/fixture.cpu.base.yaml',original)
    first=fixture_characterization(records.path,subject_id='stub-impl',input_id='tiny-sym')
    second=copy.deepcopy(first);second['id']='fixture.holdout.counts'
    second.pop('identity_sha256');second['identity_sha256']=digest(second)
    records.write('workload_characterizations/fixture.holdout.counts.yaml',second)
    raw=fixture_receipt();raw['machine']='testhost';raw['services'][0]['denominator']['proof']={'event_abi':'fixture.clock.abi'}
    imported=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',save_receipt(tmp_path,raw),
        '--id','fixture.clock.cost','--fixture')
    assert imported.returncode==0,imported.stderr+imported.stdout
    outcome=bind(records,'--target-description','fixture.cpu.base','--characterization','fixture.counts',
        '--scope-characterization','fixture.holdout.counts','--calibration','fixture.clock.cost',
        '--id','fixture.cpu.allowed','--fixture')
    assert outcome.returncode==0,outcome.stderr+outcome.stdout
    target=json.loads(outcome.stdout);expected=[{'id':c['id'],'sha256':digest(c)} for c in (first,second)]
    assert target['mechanisms'][-1]['selector']['characterization_allowlist']==expected
    assert 'characterization_sha256' not in target['mechanisms'][-1]['selector']
    assert target['extensions']['cpu_services_binding']['characterization_allowlist']==expected
    assert all(c['id'] in target['calibration_sources'] for c in (first,second))
    assert target['mechanisms'][-1]['parameters']['service_0']['basis']=='reported'
    assert records.validate().returncode==0
    third=copy.deepcopy(first);third.update(id='fixture.wrong.thread.counts');third['binding']['threads']=2
    third.pop('identity_sha256');third['identity_sha256']=digest(third)
    records.write('workload_characterizations/fixture.wrong.thread.counts.yaml',third)
    unknown=bind(records,'--target-description','fixture.cpu.base','--characterization','fixture.counts',
        '--scope-characterization','fixture.wrong.thread.counts','--calibration','fixture.clock.cost',
        '--id','fixture.cpu.partly.unmatched','--fixture')
    assert unknown.returncode==0,unknown.stderr+unknown.stdout
    assert json.loads(unknown.stdout)['mechanisms'][-1]['parameters']['service_0']['basis']=='unknown'
