"""Immutable source-only views preserve historical intrinsic identities. 2026-10-06 ET."""
import copy
import hashlib
import pytest
from conftest import REPO,run_swdb


def add_view(records):
    records.copy_repo()
    value=records.read('intrinsics/dxc_gather.yaml')
    value['id']='dxc_gather.functional-v1'
    value['source_view']={'format':'swdb.intrinsic-source-view.v1','variant':'functional-v1',
        'source':{'root':'library','path':'dx100/dxc_lowering.hpp',
            'sha256':hashlib.sha256((REPO/'library/dx100/dxc_lowering.hpp').read_bytes()).hexdigest()},
        'backend':'functional_source','compile_defines':['FUNC'],'evidence_scope':'functional_source_semantics'}
    # Intentionally retain the old operation: a source view must not launder its gem5 closure.
    records.write('intrinsics/dxc_gather.functional-v1.yaml',value)
    return value


def test_source_view_accepts_same_c_symbol_with_explicit_immutable_variant(records):
    add_view(records)
    result=records.validate()
    assert result.returncode==0,result.stdout+result.stderr


@pytest.mark.parametrize('field,value', [('variant','different'),('backend','gem5'),
    ('source.path','../swdb/analytic.py'),('source.sha256','0'*64),('compile_defines',['FUNC=0'])])
def test_source_view_refuses_identity_path_hash_or_backend_spoof(records,field,value):
    data=add_view(records)
    if '.' in field:
        name,key=field.split('.');data['source_view'][name][key]=value
    else:data['source_view'][field]=value
    records.write('intrinsics/dxc_gather.functional-v1.yaml',data)
    result=records.validate()
    assert result.returncode==1,result.stdout+result.stderr


def test_absent_source_view_preserves_original_c_name_rule(records):
    data=add_view(records);data.pop('source_view')
    records.write('intrinsics/dxc_gather.functional-v1.yaml',data)
    result=records.validate()
    assert result.returncode==1 and 'its C name without leading underscores' in result.stdout+result.stderr


def production_request(records,tmp_path,*,old_operation=False):
    import yaml
    from testkit.analytic import target_description
    data=add_view(records)
    records.add_stub()
    if not old_operation:
        operation=records.read('operations/dx100.mmio.v1.indirect-load.i32.yaml')
        operation.update(id='fixture.functional.operation',backend='functional-source')
        records.write('operations/fixture.functional.operation.yaml',operation)
        data['hardware_operations']=[operation['id']]
        records.write('intrinsics/dxc_gather.functional-v1.yaml',data)
    source=data['source_view']['source']
    path=target_description(tmp_path);target=yaml.safe_load(path.read_text());target['target']='testhost'
    target['functional_observation']={'format':'swdb.functional-observation.v1','commands':[{
        'event':'fixture.functional.gather','intrinsic':data['id'],'hardware_operations':data['hardware_operations'],
        'aliases':[{'debug_name':'__dxc_gather<int>','source':source,'source_sha256':source['sha256'],
            'memory_base_argument':0,'role':'command'}],
        'target_access_sources':[{'debug_name':'__dxc_gather<int>','source':source,'source_sha256':source['sha256']}],
        'bookkeeping_access_sources':[]}],
        'request_policy':{'transaction_bytes':64,'read_coalescing':'none'},
        'placement':{'policy':'unknown','basis':'unknown','physical_placement_known':False},
        'window':{'policy':'logical_fixed_requests_per_command_worker','requests':None,'basis':'unknown','source':'Fixture scope only.'}}
    path.write_text(yaml.safe_dump(target,sort_keys=False))
    return path


@pytest.mark.parametrize('flags',[[],['-DFUNC=0'],['-DFUNC','-UFUNC']])
def test_actual_count_request_refuses_unmatched_compiled_source_view(records,tmp_path,llvm22,flags):
    path=production_request(records,tmp_path)
    result=run_swdb('characterize','--records',records.path,'--source',REPO/'tests/fixtures/analytic/commands.cpp',
        '--implementation','stub-impl','--input','tiny-sym','--llvm-bin',llvm22,'--id','fixture.functional',
        '--target-description',path,'--output',tmp_path/'counted',*[f'--build-flag={flag}' for flag in flags])
    assert result.returncode==1,result.stdout+result.stderr
    assert 'compiled backend differs from intrinsic source_view define FUNC' in result.stdout+result.stderr
    assert not (tmp_path/'counted').exists()


def test_source_view_keeps_old_gem5_operation_closure_refusal(records,tmp_path):
    import yaml
    path=production_request(records,tmp_path,old_operation=True)
    request=tmp_path/'freeze.yaml';request.write_text(yaml.safe_dump({'message_version':'1.0','id':'fixture.protocol',
        'version':1,'settings':{'mode':'estimated','estimator_version':'swdb.analytic.v1','target_description':str(path),
            'inputs':['tiny-sym'],'roi':'fixture.functional.v1','threads':1}}))
    result=run_swdb('freeze-protocol',request,'--records',records.path)
    assert result.returncode==1
    assert 'ADR 0013' in result.stdout+result.stderr and 'dx100.mmio.v1.indirect-load.i32' in result.stdout+result.stderr
