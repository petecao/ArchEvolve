"""Source-bound conjunction preparation controls; created 2026-10-16 ET.

These compiler-free packet checks neither execute nor accept formal proofs.
"""
import hashlib
import json
from pathlib import Path

import pytest

from swdb import vector_reallocation_vcs as packets


def test_empty_copy_prefix_requires_all_fifteen_original_definition_conjuncts(tmp_path):
    baseline=json.loads((Path(__file__).parent/'fixtures/proof/vector-reallocation-copy-establish-046f.json').read_bytes())
    plan=packets.prepare('std_vector_int_realloc_v3_grow',tmp_path/'copy')
    assert len(plan['obligations'])==52
    group=next(g for g in plan['logical_obligations']if g['id']=='grow.copy.establish')
    assert group['original_statement']==baseline['original_establish']['statement']
    assert len(group['parts'])==15 and len(set(group['parts']))==15
    assert group['dependencies']==[] and group['premises_added']==[]
    original=tmp_path/'copy'/group['reference']['path']
    assert hashlib.sha256(original.read_bytes()).hexdigest()==baseline['original_establish']['sha256']
    old={r['id']:(r['path'],r['sha256'])for r in baseline['targets']if r['id']not in {'grow.copy.establish','grow.copy.step'}}
    assert {r['id']:(r['path'],r['sha256'])for r in plan['obligations']if r['id']in old}==old
    assert plan['semantics']==baseline['theory'] and plan['sources']==baseline['sources']
    definition=group['definition_source'];raw=(packets.HERE/definition['path']).read_bytes()
    exact=raw[definition['begin']:definition['end']]
    assert hashlib.sha256(exact).hexdigest()==definition['sha256']
    body=exact.decode().split('=',1)[1].strip().removesuffix(';')
    assert ''.join('&&'.join(group['definition_conjuncts']).split())==''.join(body.split())
    assert group['nested_bound_variables']==['j'] and group['capture_avoiding'] is True
    rows={r['id']:r for r in plan['obligations']}
    for ident,conjunct in zip(group['parts'],group['substituted_conjuncts'],strict=True):
        row=rows[ident]
        assert row['statement']==group['quantifiers']+group['antecedent']+' ==> '+conjunct
        assert row['dependencies']==[] and row['status']=='pending'
    loop=next(e for e in plan['source_inventory']['events']if e['id']=='grow.loop.init')
    assert loop['obligations']==[*group['parts'],'grow.numeric']
    assert packets.check('std_vector_int_realloc_v3_grow',tmp_path/'copy')==plan


def test_definition_expansion_rejects_an_unbound_symbol_instead_of_copying_it():
    with pytest.raises(ValueError,match='unbound'):
        packets.predicate_conjuncts('predicate p(integer x) = x < rogue && x == 0;', ['0'])


def test_definition_expansion_keeps_nested_binder_scope_local():
    with pytest.raises(ValueError,match='unbound'):
        packets.predicate_conjuncts(
            r'predicate p(integer x) = (\forall integer j; x < j) && j == 0;', ['0'])


def test_conjunction_substitution_is_simultaneous_and_preserves_scoped_and_nested_and():
    parts,receipt=packets.predicate_conjuncts(
        r'predicate p(integer x, integer y) = x < y && (\forall integer j; y < j && x < j);',
        ['y','0'])
    assert parts==['y < 0',r'(\forall integer j; 0 < j && y < j)']
    assert receipt['nested_bound_variables']==['j'] and receipt['capture_avoiding'] is True
    assert receipt['definition_substitution']=={'x':'y','y':'0'}
    qualified,_receipt=packets.predicate_conjuncts(
        'predicate p(Heap::heap h) = Heap::h(h) && Heap::well_formed(h);', ['Heap::allocate(entry,cap,a)'])
    assert qualified==['Heap::h(Heap::allocate(entry,cap,a))','Heap::well_formed(Heap::allocate(entry,cap,a))']


def test_closed_conjunction_grammar_refuses_unsupported_or_capturing_shapes():
    attacks=[
        ('predicate p(integer integer) = integer == 0 && integer < 1;', ['0']),
        ('predicate p(integer x, integer x) = x == 0 && x < 1;', ['0','0']),
        ('predicate p(integer x) = x == 0 && x < 1;', []),
        ('predicate p(integer x) = x == 0 && x < 1;', ['0(1)']),
        ('predicate p(integer x) = x == 0 && x < 1;', ['y/0']),
        ('predicate p(integer x) = x == 0 && x < 1;', ['y && 0']),
        ('predicate p(integer x) = x == 0 &&;', ['0']),
        ('predicate p(integer x) = x == 0 || x == 1 && x < 2;', ['0']),
        ('predicate p(integer x) = x == 0 && x < 2 ==> x < 3;', ['0']),
        ('predicate p(integer x) = (x == 0 && x < 2;', ['0']),
        ('predicate p(integer x) = x(0) && x == 0;', ['0']),
        (r'predicate p(integer x) = (\forall integer x; x < 2) && x < 3;', ['0']),
        (r'predicate p(integer x) = (\forall integer j; x < j) && x < 3;', ['Heap::f(j)']),
        (r'predicate p(integer x) = \forall integer j; x < j && x < 3;', ['0']),
        (r'predicate p(integer x) = (\forall integer j,j; x < j) && x < 3;', ['0']),
        (r'predicate p(integer x) = (\forall integer j,; x < j) && x < 3;', ['0']),
        (r'predicate p(integer x) = (\exists integer j; x < j) && x < 3;', ['0']),
        ('predicate p(integer x) = (x < 1; x < 2) && x < 3;', ['0']),
    ]
    for definition,args in attacks:
        with pytest.raises(ValueError):packets.predicate_conjuncts(definition,args)


def test_complete_establishment_and_reference_cannot_be_laundered_by_manifest_rehash(tmp_path):
    for attack in ['drop','sibling','premise','reference','substitution','binder','definition']:
        stage=tmp_path/attack
        plan=packets.prepare('std_vector_int_realloc_v3_grow',stage)
        group=next(g for g in plan['logical_obligations']if g['id']=='grow.copy.establish')
        row=next(r for r in plan['obligations']if r['id']==group['parts'][-1])
        if attack=='drop':
            plan['obligations'].remove(row);(stage/row['path']).unlink();group['parts'].remove(row['id'])
        elif attack=='sibling':row['dependencies']=[group['parts'][0]]
        elif attack in {'premise','binder'}:
            before=row['statement']
            row['statement']=before.replace('Heap::available(entry,cap,a)','\\true') if attack=='premise' else before.replace('integer j;','integer cap;')
            path=stage/row['path'];path.write_text(path.read_text().replace(before,row['statement']))
            row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        elif attack=='reference':
            path=stage/group['reference']['path'];path.write_text('/* forged former target */\n')
            group['reference']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        elif attack=='substitution':group['definition_substitution']['k']='1'
        elif attack=='definition':group['definition_source']['sha256']='0'*64
        (stage/'manifest.json').write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n')
        with pytest.raises(ValueError):packets.check('std_vector_int_realloc_v3_grow',stage)


def test_each_full_premise_implication_jointly_equals_the_original_and():
    # Exhaust the abstract propositional law independently of source parsing.
    for mask in range(1 << 15):
        conjuncts=[bool(mask & (1 << index))for index in range(15)]
        for premise in [False,True]:
            assert (not premise or all(conjuncts))==all(not premise or value for value in conjuncts)
