"""Public gross allocator derivation; archived paired rates remain unchanged. 2026-10-06 ET."""
import json
import subprocess
import sys
import pytest
from conftest import run_swdb
from testkit.cpu_service import fixture_receipt, save_receipt


def source_case(records, tmp_path):
    records.add_stub(); raw=fixture_receipt();raw['machine']='testhost'
    raw['settings'].update(group='allocator_v1',sizes=[16384],cells=[{'operation':'new_array','size_bytes':16384}],min_trial_s=.05)
    cell=raw['services'][0];cell.update(id='allocator.new_array.16384',event_definition='Hand fixture exact new[] event.')
    cell['scope']={'worker_scope':'serial','operation':'new_array','event_abi':'_Znam','size_bytes':16384,
        'allocator_regime':'fresh_process_repeated_allocate_free_batches','transfer_basis':'inferred','payload_touch':False}
    for trial in cell['trials']:trial['driver_seconds']=.00001
    result=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',save_receipt(tmp_path,raw),
        '--id','fixture.allocator.source','--fixture','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    return json.loads(result.stdout)


def derive(records, *extra):
    return subprocess.run([sys.executable,'-m','swdb.cpu_allocator_resource','--records',str(records.path),
        '--source-calibration','fixture.allocator.source','--id','fixture.allocator.resource',*extra,'--format','json'],
        capture_output=True,text=True)


def test_gross_allocator_recipe_retains_unadmitted_short_driver_and_source(records,tmp_path):
    source=source_case(records,tmp_path);path=records.path/'cpu_service_calibrations/fixture.allocator.source.yaml'
    before=path.read_bytes();result=derive(records,'--fixture')
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout);cell=data['services'][0]
    assert data['kind']=='cpu_allocator_resource_calibration'
    assert data['recipe']['id']=='gross_allocator_loop_resource_v1'
    assert data['recipe']['freeze_scope']=='after_independent_service_collection_before_application_timing'
    assert data['recipe']['includes_loop_control'] is True and data['recipe']['physical_instruction_latency'] is False
    assert cell['parameter']['value']==pytest.approx(.2) and cell['parameter']['basis']=='reported'
    assert cell['paired_residual']['parameter']==source['services'][0]['parameter']
    assert cell['paired_admission']=={'admitted':False,'minimum_window_s':.05,'missing':['paired_driver_window_resolution']}
    assert cell['driver_seconds_per_event']['median']==pytest.approx(.000001)
    assert cell['trials']==source['services'][0]['trials'] and data['calibration_sources']==[source['id']]
    assert path.read_bytes()==before and records.validate().returncode==0


def test_gross_allocator_resource_composes_as_maximum_with_compute(records,tmp_path):
    import yaml
    from testkit.cpu_service import clock_case, bind, fact
    from testkit.analytic import freeze_protocol
    source_case(records,tmp_path);derived=derive(records,'--fixture')
    assert derived.returncode==0,derived.stderr+derived.stdout
    def setup(char,target):
        target['mechanisms']=target['mechanisms'][:1]
        char['unmodeled_calls'][0]['execution_count'].update(value=1,scope='per_run')
        row=char['regions'][0]['call_shape_counts']['calls'][0]
        row['execution_count'].update(value=1,scope='per_run')
        row['known_length_bins']=[{'bytes':16384,'execution_count':{**fact(1),'scope':'per_run'}}]
    initial=clock_case(records,tmp_path,shaped=True,setup=setup)
    assert initial['seconds'] is None
    target=yaml.safe_load((tmp_path/'target.yaml').read_text());target['id']='fixture.allocator.base'
    records.write('target_descriptions/fixture.allocator.base.yaml',target)
    outcome=bind(records,'--target-description',target['id'],'--characterization','fixture.counts',
        '--calibration','fixture.allocator.resource','--id','fixture.allocator.bound','--fixture')
    assert outcome.returncode==0,outcome.stderr+outcome.stdout
    bound=json.loads(outcome.stdout);mechanism=bound['mechanisms'][-1]
    assert mechanism['accounting']=='resource_bound'
    assert mechanism['selector']['resource_recipe']=='gross_allocator_loop_resource_v1'
    request=tmp_path/'allocator-freeze.yaml'
    request.write_text(yaml.safe_dump({'message_version':'1.0','id':'fixture.allocator.protocol','version':1,
        'settings':{'mode':'estimated','estimator_version':'swdb.analytic.v1','target_description':bound['id'],
                    'inputs':['tiny-sym'],'roi':'fixture.stream.v1','threads':1}}))
    frozen=run_swdb('freeze-protocol',request,'--records',records.path,'--format','json')
    assert frozen.returncode==0,frozen.stderr+frozen.stdout
    protocol=json.loads(frozen.stdout)['id']
    result=run_swdb('estimate','--records',records.path,'--characterization','fixture.counts',
        '--target-description',bound['id'],'--protocol',protocol,'--id','fixture.allocator.max.estimate','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    estimate=json.loads(result.stdout)
    assert estimate['seconds']==2.0  # 32 FP operations at16/s dominate one0.2s allocator event.
    assert estimate['regions'][0]['overheads']==[]
    assert records.validate().returncode==0


def test_gross_allocator_derivation_refuses_an_abi_that_disagrees_with_operation(records,tmp_path):
    from testkit.analytic import digest
    source=source_case(records,tmp_path);source['services'][0]['scope']['event_abi']='_Znwm'
    source.pop('identity_sha256');source['identity_sha256']=digest(source)
    records.write('cpu_service_calibrations/fixture.allocator.source.yaml',source)
    result=derive(records,'--fixture')
    assert result.returncode!=0 and 'exact allocator ABI/size' in result.stderr
    assert not (records.path/'cpu_allocator_resource_calibrations/fixture.allocator.resource.yaml').exists()


def test_native_allocator_resource_refuses_unrecognized_shared_work_source(records,tmp_path):
    import copy
    from conftest import REPO
    from swdb import access
    records.copy_repo('machines')
    source=access.read_record(REPO/'records/cpu_service_calibrations/mbit10.cpu.lanl20261006.service.allocator-extra.a1.yaml')
    raw={'format':'swdb.cpu-service-calibration.v1','evidence_kind':'native','machine':'mbit10','threads':1,
        'context':copy.deepcopy(source['context']),'settings':copy.deepcopy(source['settings']),
        'services':[{k:copy.deepcopy(v) for k,v in s.items() if k not in {'parameter','seconds_per_event','missing'}} for s in source['services']]}
    raw['context']['source_sha256']['CpuAllocatorWork.h']='0'*64
    for cell in raw['services']:cell['denominator']['proof']['source_sha256']='0'*64
    accepted=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',save_receipt(tmp_path,raw),
        '--id','fixture.allocator.source','--format','json')
    assert accepted.returncode==0,accepted.stderr+accepted.stdout
    result=derive(records)
    assert result.returncode!=0 and 'frozen allocator source identity' in result.stderr
    assert not (records.path/'cpu_allocator_resource_calibrations/fixture.allocator.resource.yaml').exists()


def test_resource_validation_refuses_a_freeze_before_its_native_service_collection(records,tmp_path):
    from conftest import REPO
    from swdb import access
    from testkit.analytic import digest
    records.copy_repo('machines')
    path='cpu_service_calibrations/mbit10.cpu.lanl20261006.service.allocator-extra.a1.yaml'
    source=access.read_record(REPO/'records'/path);records.write(path,source)
    result=derive(records,'--source-calibration',source['id'])
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout);data['frozen_ns']=source['context']['end_state']['time_ns']-1
    data.pop('identity_sha256');data['identity_sha256']=digest(data)
    records.write('cpu_allocator_resource_calibrations/fixture.allocator.resource.yaml',data)
    refused=records.validate()
    assert refused.returncode!=0 and 'after source service collection' in refused.stdout+refused.stderr
