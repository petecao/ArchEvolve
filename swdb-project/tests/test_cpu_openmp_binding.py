"""Public site/hash binding, no native evidence invented.2026-10-06 ET."""
import copy,json
import pytest,yaml
from conftest import run_swdb
from testkit.analytic import fixture_characterization,target_description,digest
from testkit.cpu_service import save_receipt,bind,fact
from testkit.cpu_openmp import native_receipt


def setup(records,tmp_path, *, native=False):
    records.add_stub()
    if native:records.copy_repo("machines")
    target=yaml.safe_load(target_description(tmp_path).read_text());target.update(id='fixture.omp.base',target='mbit10' if native else 'testhost')
    records.write('target_descriptions/fixture.omp.base.yaml',target)
    char=fixture_characterization(records.path,subject_id='stub-impl',input_id='tiny-sym')
    char['regions']=[{'id':'fixture.region','source_location':{'function':'fixture','line':1},'mapped':True,'kind':'serial_remainder','access_patterns':[],'accelerator_calls':[],'address_stream_counts':{},'dynamic_counts':{'loop_iterations':fact(0)},'footprint_bytes':{'value':0,'basis':'reported'},'operation_counts':{k:fact(0) for k in ('integer','floating_point','branch','atomic')}}]
    region=char['regions'][0]['id'];char['static_analysis']['source_ir_sha256']='b'*64
    char['unmodeled_calls']=[{'site':29,'region':region,'name':'__kmpc_dispatch_next_4','body_counted':False,
        'cost_accounting':'opaque_callee','execution_count':fact(3)}]
    char.pop('identity_sha256');char['identity_sha256']=digest(char)
    records.write('workload_characterizations/fixture.counts.yaml',char)
    raw=native_receipt();raw.update(evidence_kind='native' if native else 'fixture',machine='mbit10' if native else 'testhost')
    imported=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',save_receipt(tmp_path,raw),
        '--id','fixture.omp.calibration','--fixture','--format','json')
    assert imported.returncode==0,imported.stderr+imported.stdout
    signature=copy.deepcopy(raw['services'][17]['denominator']['proof']['static_projection']['calls'][17])
    signature.update(site=29,region=region,llvm_function='fixture.omp_outlined')
    projection={'format':'swdb.openmp-call-projection.v1','characterization':{'id':char['id'],'sha256':digest(char)},
        'source_ir_sha256':'b'*64,'source_json_sha256':'c'*64,'all_source_json_sites_cross_checked':True,'calls':[signature]}
    path=tmp_path/'projection.json'
    def save():
        projection.pop('identity_sha256',None);projection['identity_sha256']=digest(projection)
        path.write_text(json.dumps(projection))
    save()
    return projection,save,['--target-description','fixture.omp.base','--characterization','fixture.counts',
        '--calibration','fixture.omp.calibration','--fixture','--openmp-projection',str(path),
        '--openmp-next-policy','max_constructed_success_failure_median']


def test_exact_typed_openmp_binding_retains_projection_and_both_return_sources(records,tmp_path):
    projection,save,args=setup(records,tmp_path)
    result=bind(records,*args,'--id','fixture.omp.bound')
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout);model=data['mechanisms'][-1]
    assert model['selector']['openmp_projections']==[projection]
    call=model['selector']['calls'][0];site=call['abi_sites'][0]
    assert site['profile_indexes']==[17,18] and len(site['source_parameters'])==2
    assert model['parameters'][site['parameter']]['basis']=='inferred'
    assert model['parameters'][site['parameter']]['value']==max(model['parameters'][p['parameter']]['value'] for p in site['source_parameters'])
    assert records.validate().returncode==0


@pytest.mark.parametrize('field',['char_hash','ir_hash','missing_site'])
def test_wrong_projection_scope_or_incomplete_executed_union_refuses_binding(records,tmp_path,field):
    projection,save,args=setup(records,tmp_path)
    if field=='char_hash':projection['characterization']['sha256']='f'*64
    elif field=='ir_hash':projection['source_ir_sha256']='f'*64
    else:projection['calls']=[]
    save()
    refused=bind(records,*args,'--id','fixture.omp.invalid')
    assert refused.returncode!=0 and not (records.path/'target_descriptions/fixture.omp.invalid.yaml').exists()


def test_native_openmp_cost_with_unproven_library_and_controls_stays_unknown(records,tmp_path):
    projection,save,args=setup(records,tmp_path,native=True)
    result=bind(records,*args,'--id','fixture.omp.native.unmatched')
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout);model=data['mechanisms'][-1]
    assert all(p['value'] is None for p in model['parameters'].values())
    missing=data['extensions']['cpu_services_binding']['compatibility'][0]['missing']
    assert 'service_runtime.libomp' in missing and 'service_openmp_control_absence_scope' in missing and 'service_openmp_controls' in missing
