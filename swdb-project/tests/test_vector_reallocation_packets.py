"""Canonical qualified preparation API controls; created 2026-10-16 ET.

No compiler or formal executable. A source receipt is not a proof verdict.
"""
import hashlib
import json

import pytest

from swdb import vector_reallocation_vcs as packets


@pytest.mark.parametrize('attack', ['none', 'target', 'drop_step', 'clause', 'original',
                                  'theory', 'extra_import', 'symlink'])
def test_canonical_qualified_packet_check_rejects_self_consistent_tampering(tmp_path, attack):
    member='std_vector_int_realloc_v3_reserve'
    stage=tmp_path/'packets'
    plan=packets.prepare(member,stage)
    if attack=='target':
        row=plan['obligations'][0];path=stage/row['path']
        path.write_text(path.read_text().replace(row['statement'],'\\true'))
        row['statement']=r'\true';row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    elif attack=='drop_step':
        plan['obligations']=[row for row in plan['obligations'] if row['id']!='grow.copy.step']
    elif attack=='clause':plan['source_inventory']['clauses'].pop()
    elif attack=='original':
        path=stage/'qualified.c';path.write_text('/* forged body */\n')
        plan['source_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    elif attack=='theory':
        path=stage/plan['semantics']['path']
        path.write_text(path.read_text().replace('\nend\n','\n axiom desired: false\nend\n'))
        plan['semantics']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    elif attack=='extra_import':(stage/'theory/heap_reallocation.why').write_text('theory Heap axiom bad:false end\n')
    elif attack=='symlink':(stage/'unreviewed.c').symlink_to(stage/plan['obligations'][0]['path'])
    (stage/'manifest.json').write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n')
    if attack=='none':
        checked=packets.check(member,stage)
        assert checked==plan and checked['coverage_complete'] is False
    else:
        with pytest.raises(ValueError):packets.check(member,stage)


def test_projection_conjunction_is_completely_split_without_changing_other_target_bytes(tmp_path):
    from pathlib import Path
    baseline=json.loads((Path(__file__).parent/'fixtures/proof/vector-reallocation-projection-017.json').read_bytes())
    plan=packets.prepare('std_vector_int_realloc_v3_grow',tmp_path/'split')
    assert len(plan['obligations'])==38
    group=plan['logical_obligations'][0]
    assert group['id']=='grow.entry.int_projection'
    assert group['original_statement']==baseline['original_projection']['statement']
    assert group['parts']==['grow.entry.int_projection.repr',*group['component_expansions'][0]['parts']]
    assert group['fresh_index']=='j' and group['fresh_index_free_in_antecedent'] is False
    assert group['dependencies']==[] and group['premises_added']==[]
    old=baseline['original_projection'];reference=tmp_path/'split'/group['reference']['path']
    assert hashlib.sha256(reference.read_bytes()).hexdigest()==old['sha256']==group['reference']['sha256']
    expected={r['id']:(r['path'],r['sha256'])for r in baseline['targets'] if r['id'] not in {old['id'],'grow.copy.establish'}}
    observed={r['id']:(r['path'],r['sha256'])for r in plan['obligations'] if r['id'] in expected}
    assert observed==expected and len(observed)==18
    for row in plan['obligations']:
        if row['id'] not in group['parts']:continue
        assert row['dependencies']==[] and row['statement'].startswith(group['quantifiers'])
        assert group['antecedent'] in row['statement']
    assert {r['path'].split('-')[0]for r in plan['obligations'] if r['id']in group['parts']}=={'002a','002b1','002b2','002b3','002b4'}
    for row in group['definition_sources']:
        raw=(packets.HERE/row['path']).read_bytes()
        assert hashlib.sha256(raw[row['begin']:row['end']]).hexdigest()==row['sha256']
    assert packets.check('std_vector_int_realloc_v3_grow',tmp_path/'split')==plan


@pytest.mark.parametrize('attack',['none','drop_repr','drop_cells','drop_initialization','drop_integer','drop_bounds','assume_repr','assume_sibling','antecedent','capture','reference','definition','cell_reference','cell_definition','cell_substitution','drop_component_group'])
def test_projection_group_requires_both_isolated_pieces_and_original_definitions(tmp_path,attack):
    from swdb import vector_reallocation_view
    stage=tmp_path/'split'
    view=vector_reallocation_view.prepare('std_vector_int_realloc_v3_grow',stage)
    plan=json.loads((stage/'manifest.json').read_bytes())
    group=plan['logical_obligations'][0]
    rows={r['id']:r for r in plan['obligations']}
    if attack.startswith('drop_') and attack!='drop_component_group':
        suffix=attack.removeprefix('drop_')
        ident='grow.entry.int_projection.'+('repr' if suffix=='repr' else 'cells.'+('access' if suffix=='cells' else suffix))
        plan['obligations'].remove(rows[ident]);(stage/rows[ident]['path']).unlink()
        group['parts'].remove(ident)
    elif attack=='assume_repr':
        row=rows['grow.entry.int_projection.cells.integer'];row['dependencies']=[group['parts'][0]]
    elif attack=='assume_sibling':
        rows['grow.entry.int_projection.cells.integer']['dependencies']=['grow.entry.int_projection.cells.initialization']
    elif attack in {'antecedent','capture'}:
        row=rows['grow.entry.int_projection.cells.integer'];path=stage/row['path']
        before=row['statement']
        row['statement']=before.replace('Heap::bounded_int_values(values,bo,s)','\\true') if attack=='antecedent' else before.replace('integer j;','integer s;')
        path.write_text(path.read_text().replace(before,row['statement']));row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    elif attack=='reference':
        path=stage/group['reference']['path'];path.write_text('/* false old-target receipt */\n')
        group['reference']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    elif attack=='definition':group['definition_sources'][0]['sha256']='0'*64
    elif attack=='cell_reference':
        reference=group['component_expansions'][0]['reference'];path=stage/reference['path']
        path.write_text('/* altered original cell obligation */\n');reference['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    elif attack=='cell_definition':group['component_expansions'][0]['definition_source']['sha256']='0'*64
    elif attack=='cell_substitution':group['component_expansions'][0]['definition_substitution']['o']='j'
    elif attack=='drop_component_group':group['component_expansions']=[]
    (stage/'manifest.json').write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n')
    if attack=='none':
        checked=vector_reallocation_view.check('std_vector_int_realloc_v3_grow',view,stage)
        assert len(checked.certificate['obligations'])==38
        assert checked.certificate['logical_obligations'][0]['parts']==group['parts']
        assert all(rows[part]['expected']=='proven' and not rows[part]['dependencies'] for part in group['parts'])
    else:
        with pytest.raises(vector_reallocation_view.engine.Refused):
            vector_reallocation_view.check('std_vector_int_realloc_v3_grow',view,stage)


def test_projected_cells_expand_exact_definition_and_keep_other_twenty_inputs(tmp_path):
    from pathlib import Path
    baseline=json.loads((Path(__file__).parent/'fixtures/proof/vector-reallocation-projection-cells-2e01.json').read_bytes())
    plan=packets.prepare('std_vector_int_realloc_v3_grow',tmp_path/'components')
    assert len(plan['obligations'])==38
    logical=plan['logical_obligations'][0]
    expansion=logical['component_expansions'][0]
    assert expansion['id']=='grow.entry.int_projection.cells'
    assert expansion['original_statement']==baseline['original_cells']['statement']
    assert expansion['parts']==['grow.entry.int_projection.cells.'+p for p in ['access','initialization','integer','bounds']]
    assert expansion['combination']=='AND: all four independent definition conjuncts are required'
    assert expansion['premises_added']==[] and expansion['dependencies']==[]
    assert logical['parts']==['grow.entry.int_projection.repr',*expansion['parts']]
    old=baseline['original_cells'];reference=tmp_path/'components'/expansion['reference']['path']
    assert hashlib.sha256(reference.read_bytes()).hexdigest()==old['sha256']==expansion['reference']['sha256']
    expected={r['id']:(r['path'],r['sha256'])for r in baseline['targets']if r['id'] not in {old['id'],'grow.copy.establish'}}
    actual={r['id']:(r['path'],r['sha256'])for r in plan['obligations']if r['id']in expected}
    assert actual==expected and len(actual)==19
    conjuncts=[
        'Heap::typed_reads(Heap::project_int_region(h,values,b,bo,s),b,bo+4*j,4,4)',
        'Heap::initialized_at(Heap::project_int_region(h,values,b,bo,s),b,bo+4*j)',
        'Heap::integer_at(Heap::project_int_region(h,values,b,bo,s),b,bo+4*j,Heap::load_int(Heap::project_int_region(h,values,b,bo,s),b,bo+4*j))',
        '-2147483648 <= Heap::load_int(Heap::project_int_region(h,values,b,bo,s),b,bo+4*j) <= 2147483647',
    ]
    for ident,conjunct in zip(expansion['parts'],conjuncts,strict=True):
        row=next(r for r in plan['obligations']if r['id']==ident)
        assert row['statement']==expansion['quantifiers']+expansion['antecedent']+' ==> '+conjunct
        assert row['status']=='pending' and row['dependencies']==[]
    definition=expansion['definition_source'];raw=(packets.HERE/definition['path']).read_bytes()
    assert hashlib.sha256(raw[definition['begin']:definition['end']]).hexdigest()==definition['sha256']
    assert b'predicate int32_at' in raw[definition['begin']:definition['end']]
    assert packets.check('std_vector_int_realloc_v3_grow',tmp_path/'components')==plan
