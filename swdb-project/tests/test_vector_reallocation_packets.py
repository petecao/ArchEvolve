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
    assert len(plan['obligations'])==21
    group=plan['logical_obligations'][0]
    assert group['id']=='grow.entry.int_projection'
    assert group['original_statement']==baseline['original_projection']['statement']
    assert group['parts']==['grow.entry.int_projection.repr','grow.entry.int_projection.cells']
    assert group['fresh_index']=='j' and group['fresh_index_free_in_antecedent'] is False
    assert group['dependencies']==[] and group['premises_added']==[]
    old=baseline['original_projection'];reference=tmp_path/'split'/group['reference']['path']
    assert hashlib.sha256(reference.read_bytes()).hexdigest()==old['sha256']==group['reference']['sha256']
    expected={r['id']:(r['path'],r['sha256'])for r in baseline['targets'] if r['id']!=old['id']}
    observed={r['id']:(r['path'],r['sha256'])for r in plan['obligations'] if r['id'] in expected}
    assert observed==expected and len(observed)==19
    for row in plan['obligations']:
        if row['id'] not in group['parts']:continue
        assert row['dependencies']==[] and row['statement'].startswith(group['quantifiers'])
        assert group['antecedent'] in row['statement']
    assert {r['path'].split('-')[0]for r in plan['obligations'] if r['id']in group['parts']}=={'002a','002b'}
    for row in group['definition_sources']:
        raw=(packets.HERE/row['path']).read_bytes()
        assert hashlib.sha256(raw[row['begin']:row['end']]).hexdigest()==row['sha256']
    assert packets.check('std_vector_int_realloc_v3_grow',tmp_path/'split')==plan


@pytest.mark.parametrize('attack',['none','drop_repr','drop_cells','assume_repr','antecedent','capture','reference','definition'])
def test_projection_group_requires_both_isolated_pieces_and_original_definitions(tmp_path,attack):
    from swdb import vector_reallocation_view
    stage=tmp_path/'split'
    view=vector_reallocation_view.prepare('std_vector_int_realloc_v3_grow',stage)
    plan=json.loads((stage/'manifest.json').read_bytes())
    group=plan['logical_obligations'][0]
    rows={r['id']:r for r in plan['obligations']}
    if attack in {'drop_repr','drop_cells'}:
        ident='grow.entry.int_projection.'+attack.removeprefix('drop_')
        plan['obligations'].remove(rows[ident]);(stage/rows[ident]['path']).unlink()
        group['parts'].remove(ident)
    elif attack=='assume_repr':
        row=rows['grow.entry.int_projection.cells'];row['dependencies']=[group['parts'][0]]
    elif attack in {'antecedent','capture'}:
        row=rows['grow.entry.int_projection.cells'];path=stage/row['path']
        before=row['statement']
        row['statement']=before.replace('Heap::bounded_int_values(values,bo,s)','\\true') if attack=='antecedent' else before.replace('integer j;','integer s;')
        path.write_text(path.read_text().replace(before,row['statement']));row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    elif attack=='reference':
        path=stage/group['reference']['path'];path.write_text('/* false old-target receipt */\n')
        group['reference']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    elif attack=='definition':group['definition_sources'][0]['sha256']='0'*64
    (stage/'manifest.json').write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n')
    if attack=='none':
        checked=vector_reallocation_view.check('std_vector_int_realloc_v3_grow',view,stage)
        assert len(checked.certificate['obligations'])==21
        assert checked.certificate['logical_obligations'][0]['parts']==group['parts']
        assert all(rows[part]['expected']=='proven' and not rows[part]['dependencies'] for part in group['parts'])
    else:
        with pytest.raises(vector_reallocation_view.engine.Refused):
            vector_reallocation_view.check('std_vector_int_realloc_v3_grow',view,stage)
