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
    assert len(plan['obligations'])==78 # 30ctor + 26reserve(with grow) +11dtor +10local +1numeric
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
