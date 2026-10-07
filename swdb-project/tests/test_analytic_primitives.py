"""Public exact source memory primitive contract. Updated: 2026-10-06 ET."""
import json
from conftest import REPO, run_swdb
from testkit.analytic import llvm22


def test_normalized_primitives_preserve_type_ordering_strength_and_vector_scope(records,tmp_path,llvm22):
    records.add_stub()
    result=run_swdb('characterize','--records',records.path,
        '--source',REPO/'tests/fixtures/analytic/primitives.cpp','--implementation','stub-impl',
        '--input','tiny-sym','--function','primitives','--roi','fixture.primitives.v1',
        '--id','fixture.primitives','--llvm-bin',llvm22,'--output',tmp_path/'counted',
        '--counting-pipeline','source-normalized-v2','--fixture','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    data=json.loads(result.stdout)
    accesses=[a for region in data['regions'] for a in region['access_patterns'] if a['element_count']['value']]
    assert accesses and all('primitive_semantics' in a for a in accesses)
    facts=[a['primitive_semantics'] for a in accesses]
    assert all(p['format']=='swdb.source-memory-primitive.v1' for p in facts)
    signatures={(p['opcode'],p['value_kind'],p['element_bits'],p['update_opcode'],p['atomic_ordering']) for p in facts}
    assert ('atomicrmw','integer',64,'add','seq_cst') in signatures
    assert ('atomicrmw','integer',64,'sub','monotonic') in signatures
    assert ('atomicrmw','integer',64,'xchg','acq_rel') in signatures
    assert ('atomicrmw','floating',64,'fadd','seq_cst') in signatures
    assert ('atomicrmw','floating',64,'fsub','monotonic') in signatures
    cas=[p for p in facts if p['opcode']=='cmpxchg']
    assert {(p['weak'],p['atomic_ordering'],p['failure_ordering']) for p in cas}=={
        (False,'seq_cst','seq_cst'),(True,'acq_rel','acquire')}
    assert any(p['opcode']=='load' and p['volatile'] and not p['vector'] and p['atomic_ordering']=='not_atomic' for p in facts)
    assert any(p['opcode']=='store' and p['volatile'] and p['update_opcode']=='add' for p in facts)
    pointers=[p for p in facts if p['value_kind']=='pointer']
    assert {p['opcode'] for p in pointers}=={'load','store'}
    assert all(p['element_bits']==64 and not p['vector'] for p in pointers)
    vectors=[p for p in facts if p['vector']]
    assert {p['opcode'] for p in vectors}=={'load','store'}
    assert all(p['element_bits']==64 for p in vectors)
    exchange=next(a for a in accesses if a['primitive_semantics']['update_opcode']=='xchg')
    assert exchange['update_kind']=='write' and exchange['read_write']
    assert all(a['id'].startswith('access.') for a in accesses)
    valid=records.validate()
    assert valid.returncode==0,valid.stdout+valid.stderr
