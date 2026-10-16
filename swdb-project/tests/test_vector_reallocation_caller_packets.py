"""2026-10-16 ET. Canonical source/contract caller preparation; no verifier."""
from pathlib import Path
import hashlib

from conftest import FIXTURES

SOURCE=FIXTURES/'proof/vector_reallocation_v3.cc'
CONTRACT=[r'requires 0 <= n;',r'assigns \nothing;',r'ensures \result == (n > 0 ? 7 : 0);']


def test_canonical_caller_preparation_binds_existing_contract_without_enabling_proof(tmp_path):
    from swdb import vector_reallocation_caller_packets as packets
    stage=tmp_path/'caller'
    plan=packets.prepare(SOURCE,'vector_realloc_v3_safe',CONTRACT,stage)
    assert plan['proof_admission']=='unsupported: complete caller composition remains pending'
    assert plan['preparation_only'] is True and plan['caller_premises_added']==[]
    assert plan['contract']['clauses']==CONTRACT
    assert plan['contract']['entry_discharge']=='matching prospective nonnegative-count clause; public contract binding pending'
    assert plan['source']['sha256']==hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert (stage/plan['source']['path']).read_bytes()==SOURCE.read_bytes()
    numeric=next(row for row in plan['obligations'] if row['id']=='caller.count.numeric')
    assert (stage/numeric['path']).read_text().count('requires 0 <= count;')==1
    assert all(row['status']=='pending' and row['dependencies']==[] for row in plan['obligations'])
    assert plan['current_proof_records_admitted']==[]
    assert packets.check(SOURCE,'vector_realloc_v3_safe',CONTRACT,stage)==plan


import json
import shutil
import pytest

@pytest.mark.parametrize('contract', [
    CONTRACT[1:],
    [r'requires \true;',*CONTRACT[1:]],
    [r'requires n > 0;',*CONTRACT[1:]],
    [r'requires 0 <= n <= 16;',*CONTRACT[1:]],
    [CONTRACT[0],CONTRACT[0],*CONTRACT[1:]],
    [CONTRACT[0],CONTRACT[2]],
    [*CONTRACT[:2],r'ensures \result == 8;'],
    [*CONTRACT,r'axiom desired: \false;'],
])
def test_caller_contract_is_explicit_and_never_completed_from_source_samples(tmp_path,contract):
    from swdb import vector_reallocation_caller_packets as packets
    stage=tmp_path/'refused'
    with pytest.raises(ValueError,match='no premise is inferred or added'):
        packets.prepare(SOURCE,'vector_realloc_v3_safe',contract,stage)
    assert not stage.exists()


@pytest.fixture(scope='module')
def prepared_caller(tmp_path_factory):
    from swdb import vector_reallocation_caller_packets as packets
    stage=tmp_path_factory.mktemp('caller-packets')/'source'
    plan=packets.prepare(SOURCE,'vector_realloc_v3_safe',CONTRACT,stage)
    assert len(plan['obligations'])==84 # 30ctor +30reserve(with four cell conjuncts) +11dtor +10local +1numeric +2applications
    assert len(plan['required_models'])==5
    assert all(row['proof_record'] is None for row in plan['required_models'])
    return stage


@pytest.mark.parametrize('mutation',['target','body_step','contract','original','extra_import','symlink'])
def test_caller_packet_check_reconstructs_source_and_contract_after_self_consistent_tampering(tmp_path,prepared_caller,mutation):
    from swdb import vector_reallocation_caller_packets as packets
    stage=tmp_path/'changed';shutil.copytree(prepared_caller,stage)
    plan=json.loads((stage/'manifest.json').read_bytes())
    if mutation=='target':
        row=next(r for r in plan['obligations'] if r['id']=='caller.data.read')
        path=stage/row['path'];path.write_text(path.read_text().replace(row['statement'],r'\true'))
        row['statement']=r'\true';row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    elif mutation=='body_step':
        row=next(r for r in plan['obligations'] if r['id']=='body.reserve.grow.copy.step')
        (stage/row['path']).unlink();plan['obligations'].remove(row)
        body=stage/'bodies/reserve/manifest.json';body_plan=json.loads(body.read_bytes())
        body_plan['obligations']=[r for r in body_plan['obligations'] if r['id']!='grow.copy.step']
        body.write_text(json.dumps(body_plan,sort_keys=True,indent=2)+'\n')
    elif mutation=='contract':
        path=stage/'contract.json';contract=json.loads(path.read_bytes())
        contract['clauses'][0]=r'requires \true;'
        path.write_text(json.dumps(contract,sort_keys=True,indent=2)+'\n');plan['contract']=contract
    elif mutation=='original':
        path=stage/'original.cc';path.write_bytes(path.read_bytes()+b'\n// altered original input\n')
        plan['source']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    elif mutation=='extra_import':(stage/'theory/unreviewed.why').write_text('theory Bad axiom desired:false end\n')
    elif mutation=='symlink':
        path=stage/'local/caller-count-numeric.c';data=path.read_bytes()
        other=tmp_path/'same-bytes.c';other.write_bytes(data);path.unlink();path.symlink_to(other)
    (stage/'manifest.json').write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n')
    with pytest.raises(ValueError):packets.check(SOURCE,'vector_realloc_v3_safe',CONTRACT,stage)


def test_caller_contract_does_not_join_malformed_keyword_tokens(tmp_path):
    from swdb import vector_reallocation_caller_packets as packets
    malformed=[r'requires0 <= n;',*CONTRACT[1:]]
    with pytest.raises(ValueError,match='clause tokens'):
        packets.prepare(SOURCE,'vector_realloc_v3_safe',malformed,tmp_path/'invalid')
    assert not(tmp_path/'invalid').exists()


@pytest.mark.parametrize('contract',[
    [r're quires 0 <= n;',*CONTRACT[1:]],
    [r'requires 0 < = n;',*CONTRACT[1:]],
    ['requ','ires 0 <= n;',*CONTRACT[1:]],
    [CONTRACT[0],r'as signs \nothing;',CONTRACT[2]],
    [*CONTRACT[:2],r'ensu res \result == (n > 0 ? 7 : 0);'],
    [*CONTRACT[:2],r'ensures \ result == (n > 0 ? 7 : 0);'],
    [*CONTRACT[:2],r'ensures \result = = (n > 0 ? 7 : 0);'],
    [r'requires 0 <= co unt;',r'assigns \nothing;',r'ensures \result == (co unt > 0 ? 7 : 0);'],
])
def test_whitespace_and_annotation_boundaries_never_create_different_clause_tokens(tmp_path,contract):
    from swdb import vector_reallocation_caller_packets as packets
    with pytest.raises(ValueError,match='clause tokens'):
        packets.prepare(SOURCE,'vector_realloc_v3_safe',contract,tmp_path/'invalid')
    assert not(tmp_path/'invalid').exists()


def test_whole_clauses_may_share_one_actual_annotation_without_splitting_tokens(tmp_path):
    from swdb import vector_reallocation_caller_packets as packets
    clauses=['requires\t0 <= n;\n','assigns \\nothing;\nensures \\result ==\n(n > 0 ? 7 : 0);']
    plan=packets.prepare(SOURCE,'vector_realloc_v3_safe',clauses,tmp_path/'whole')
    assert plan['contract']['clauses']==clauses
    assert plan['contract']['ordinary_contract_identity'].startswith('pending:')
    assert plan['current_proof_records_admitted']==[] and len(plan['obligations'])==84


def test_constructor_entry_application_maps_source_storage_and_existing_count_clause(tmp_path):
    from swdb import vector_reallocation_caller_packets as packets
    plan=packets.prepare(SOURCE,'vector_realloc_v3_safe',CONTRACT,tmp_path/'entry')
    row=next((r for r in plan['obligations'] if r['id']=='apply.ctor.entry'),None)
    assert row is not None, 'the caller needs its constructor precondition application, not only isolated body laws'
    assert row['statement']==(
        r'\forall Heap::heap h; \forall integer a,n; Heap::well_formed(h) && '
        r'Heap::automatic_available(h,24,8,a) && 0 <= n <= 2147483647 ==> '
        r'Heap::typed_writes(Heap::begin_automatic(h,24,a),Heap::fresh_id(h),0,24,8) && '
        r'!Heap::freeable(Heap::begin_automatic(h,24,a),Heap::fresh_id(h),0) && '
        r'0 <= n <= 4611686018427387903')
    application=plan['composition']['constructor_entry']
    assert application['callee']=='std_vector_int_realloc_v3_ctor_count_value'
    assert application['source_parameter']==plan['candidate']['count']
    assert application['source_call']==next(r['source']for r in plan['candidate']['call_obligations']if r['call']=='ctor_count_value')
    assert application['contract_clause']==CONTRACT[0]
    assert application['model_arguments']=={'this':'Heap::fresh_id(h), offset0','n':'source signed int converted to size_t','value':7}
    assert application['automatic_storage_embedding']=='pending source-runtime discharge; not a caller assumption'
    assert application['source_type_range']=='pending signed32 source image; separate numeric kernel asserts actual C ABI'
    assert row['dependencies']==[] and row['status']=='pending'
    assert plan['proof_admission'].startswith('unsupported:') and plan['current_proof_records_admitted']==[]
    assert plan['caller_premises_added']==[] and plan['incoming_pointer_maps_restricted'] is False
    assert packets.check(SOURCE,'vector_realloc_v3_safe',CONTRACT,tmp_path/'entry')==plan


def test_zero_constructor_application_retains_empty_buffer_and_actual_store_path(tmp_path):
    from swdb import vector_reallocation_caller_packets as packets
    plan=packets.prepare(SOURCE,'vector_realloc_v3_safe',CONTRACT,tmp_path/'zero')
    row=next((r for r in plan['obligations']if r['id']=='apply.ctor.zero'),None)
    assert row is not None, 'the source zero branch needs its own constructed state, without an initialized buffer premise'
    entry='Heap::begin_automatic(h,24,a)'
    state='t25_initial('+entry+',Heap::fresh_id(h),0)'
    assert row['statement']==(
        r'\forall Heap::heap h; \forall integer a; Heap::well_formed(h) && '
        r'Heap::automatic_available(h,24,8,a) ==> '
        't25v3_eligible('+state+',Heap::fresh_id(h),0,0,0,0,0) && '
        'Heap::pointer_at('+state+',Heap::fresh_id(h),0,0,0)')
    application=plan['composition']['zero_constructor']
    assert application['source_path_condition']=='source count == 0; the zero branch does not restrict caller entry'
    assert application['state_before']==entry and application['state_after']==state
    body=(tmp_path/'zero/bodies/ctor_count_value/qualified.c').read_bytes()
    for key,expected in [('initial_stores',b'this->data = NULL; this->size = 0; this->capacity = 0;'),
                         ('zero_return',b'if (n == 0) return;')]:
        span=application[key]
        assert body[span['begin']:span['end']]==expected
        assert hashlib.sha256(expected).hexdigest()==span['sha256']
    assert application['buffer_loads']==0 and application['allocation_executed'] is False
    assert plan['caller_premises_added']==[] and plan['current_proof_records_admitted']==[]
    assert plan['proof_admission'].startswith('unsupported:')
    assert packets.check(SOURCE,'vector_realloc_v3_safe',CONTRACT,tmp_path/'zero')==plan
