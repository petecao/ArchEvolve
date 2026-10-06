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
