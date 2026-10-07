"""Typed conditional memory costs bound through the public module CLI (2026-10-06)."""
import json
import subprocess
import sys

import yaml

from conftest import run_swdb
from testkit.analytic import target_description,fixture_characterization


def run_bind(records,*args):
    return subprocess.run([sys.executable,'-m','swdb.cpu_service_binding','--records',str(records.path),
        *map(str,args),'--format','json'],capture_output=True,text=True)


def setup(records,tmp_path):
    records.add_stub();base=yaml.safe_load(target_description(tmp_path).read_text())
    base.update(id='fixture.memory.base',target='testhost')
    records.write('target_descriptions/fixture.memory.base.yaml',base)
    fixture_characterization(records.path,subject_id='stub-impl',input_id='tiny-sym')
    operations=('read','write','add-update','cas-success','cas-failure')
    kinds=('read','write','add-update','compare-and-swap','compare-and-swap')
    services=[]
    for op,kind in zip(operations,kinds):
        for width in (4,8):
            for footprint in (32768,8388608):
                services.append({'id':f'memory.{op}.{width}.{footprint}','unit':'seconds/request',
                    'event_definition':'Hand fixture only; not native evidence.',
                    'scope':{'operation':op,'update_kind':kind,'element_bytes':width,'footprint_bytes':footprint,
                        'memory_regime':'resident_serial_constructed_requests','transfer_basis':'inferred','worker_scope':'serial'},
                    'denominator':{'level':'source_normalized_work','basis':'reported','proof':'Hand fixture, not native proof.'},
                    'trials':[{'events':10,'gross_seconds':3 if op=='cas-failure' else 2,'driver_seconds':1,
                        'order':'service_first' if i%2==0 else 'driver_first'} for i in range(3)]})
    services.append({'id':'memory.read.1.256','unit':'seconds/request','event_definition':'Hand byte-read fixture.',
        'scope':{'operation':'read','update_kind':'read','element_bytes':1,'footprint_bytes':256,
            'memory_regime':'fixed_small_byte_read_constructed_requests','transfer_basis':'inferred','worker_scope':'serial'},
        'denominator':{'level':'source_normalized_work','basis':'reported','proof':'Hand fixture only.'},
        'trials':[{'events':10,'gross_seconds':2,'driver_seconds':1,'order':'service_first' if i%2==0 else 'driver_first'} for i in range(3)]})
    raw={'format':'swdb.cpu-service-calibration.v1','evidence_kind':'fixture','machine':'testhost','threads':1,
        'context':{'compiler_version':'hand fixture'},'settings':{'repetitions':3},'services':services}
    from swdb.cpu_service_calibration import identity
    raw['identity_sha256']=identity(raw);path=tmp_path/'memory-fixture.json';path.write_text(json.dumps(raw))
    result=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',path,'--id','fixture.memory.costs','--fixture','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    return (records.path/'target_descriptions/fixture.memory.base.yaml').read_bytes()


def test_binding_selects_preregistered_footprint_retains_cas_inputs_and_does_not_reuse_stream_costs(records,tmp_path):
    before=setup(records,tmp_path)
    outcome=run_bind(records,'--target-description','fixture.memory.base','--characterization','fixture.counts',
        '--calibration','fixture.memory.costs','--memory-footprint-bytes','8388608',
        '--memory-cas-policy','max_constructed_success_failure_median','--id','fixture.memory.bound','--fixture')
    assert outcome.returncode==0,outcome.stderr+outcome.stdout
    target=json.loads(outcome.stdout);model=target['mechanisms'][-1]
    assert model['model']=='memory_service_scenario'
    assert all(m['model']!='streaming_bandwidth' for m in target['mechanisms'])
    assert target['extensions']['cpu_services_binding']['memory_selection']['superseded_memory_models']==['streaming_bandwidth']
    rows=model['selector']['requests']
    assert {(r['update_kind'],r['element_bytes']) for r in rows}=={
        ('read',1),('read',4),('read',8),('write',4),('write',8),('add-update',4),('add-update',8),('compare-and-swap',4),('compare-and-swap',8)}
    for row in rows:
        scope=row['construction']
        assert scope['footprint_bytes']==(256 if row['element_bytes']==1 else 8388608)
        parameter=model['parameters'][row['parameter']]
        if row['update_kind']=='compare-and-swap':
            assert parameter['value']==.2 and parameter['basis']=='inferred'
            assert len(scope['source_services'])==2 and scope['outcome_policy']=='max_constructed_success_failure_median'
        else:assert parameter['basis']=='reported'
    assert 'fixture.memory.costs' in target['calibration_sources'] and 'fixture.counts' in target['calibration_sources']
    assert (records.path/'target_descriptions/fixture.memory.base.yaml').read_bytes()==before
    assert records.validate().returncode==0


def test_binding_requires_explicit_memory_footprint_and_cas_policy_before_writing(records,tmp_path):
    setup(records,tmp_path)
    rejected=run_bind(records,'--target-description','fixture.memory.base','--characterization','fixture.counts',
        '--calibration','fixture.memory.costs','--id','fixture.implicit.memory','--fixture')
    assert rejected.returncode!=0 and 'explicit memory footprint' in rejected.stderr
    assert not (records.path/'target_descriptions/fixture.implicit.memory.yaml').exists()
