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
