"""2026-10-16 ET. Public exact mathematical dependencies of the closed int move."""
import hashlib
import copy
from pathlib import Path
import shutil

import pytest


BASE = Path(__file__).parent/'fixtures/proof/vector_closed_scientific_bundle'
MOVE = Path(__file__).parent/'fixtures/proof/vector_owned_move_scientific_bundle'


def test_closed_move_binds_all59_exact_conditional_targets_without_source_admission():
    from swdb import vector_owned_move_binding as packets

    result, files = packets.mathematical_dependencies(BASE, MOVE)
    assert result['complete_source_target_count'] == 59
    assert result['scientific_dependencies_bound'] is True
    assert [(row['id'], len(row['targets'])) for row in result['components']] == [
        ('constructor', 35), ('destructor', 11), ('private_frame', 9), ('move_source', 4)]
    assert [row['id'] for row in result['components'][-1]['targets']] == [
        'move.destination_header', 'move.source_empty',
        'move.incoming_frame', 'move.owner_correspondence']
    for component in result['components']:
        for target in component['targets']:
            assert any(hashlib.sha256(raw).hexdigest() == target['input_sha256'] for raw in files.values())
    move = result['components'][-1]
    assert move['historical_source_commit'] == '032e1851eec7b195c7a3737997d5f5ea1d1343a5'
    assert move['complete_task_contexts'] == 12
    assert all(row['observation']['normal_verdict'] == 'proven' for row in move['targets'])
    assert move['targets'][-1]['observation']['native_results'] == ['timeout', 'unknown', 'valid']
    assert result['preserved_unaccepted_swap']['normal_verdict'] == 'not_proven'
    assert result['preserved_unaccepted_swap']['native_results'] == ['timeout', 'timeout', 'timeout']
    assert result['source_admission'] is False
    assert result['source_Heap_Typed_bridge_established'] is False
    assert result['caller_acceptance'] is False
    assert result['current_model_records_created'] == []


def test_move_binding_rejects_changed_missing_extra_or_redirected_scientific_evidence(tmp_path):
    from swdb import vector_owned_move_binding as packets

    for mutation in ('changed', 'missing', 'extra', 'redirect'):
        directory = tmp_path/mutation
        shutil.copytree(MOVE, directory)
        path = directory/'bundle.json'
        if mutation == 'changed':
            path.write_bytes(path.read_bytes().replace(b'move.destination_header', b'move.destination_broken', 1))
        elif mutation == 'missing':
            path.unlink()
        elif mutation == 'extra':
            (directory/'accepted.json').write_text('{}')
        else:
            path.unlink()
            path.symlink_to(MOVE/'bundle.json')
        with pytest.raises(packets.Refused):
            packets.mathematical_dependencies(BASE, directory)


def test_move_binding_refuses_foreign_current_public_source_domain_or_inputs(monkeypatch):
    from swdb import vector_owned_move_binding as packets
    from swdb import vector_owned_source_view as current

    original = current.declaration
    for mutation in ('model', 'statement', 'input', 'theory', 'original_source'):
        def foreign(*args, **kwargs):
            plan, files = original(*args, **kwargs)
            plan = copy.deepcopy(plan)
            files = dict(files)
            if mutation == 'model':
                plan['parent_model']['sha256'] = '0'*64
            elif mutation == 'statement':
                plan['obligations'][0]['statement'] = r'\true'
            elif mutation == 'input':
                path = plan['obligations'][0]['path']
                files[path] = files[path].replace(b'OwnedEffects::header', b'OwnedEffects::receiver', 1)
            elif mutation == 'theory':
                path = 'theory/vector_owned_effects.mlw'
                files[path] = files[path].replace(b'ready[r] = True', b'ready[r] = False')
            else:
                path = plan['source_members'][0]['original_path']
                files[path] = files[path].replace(b'NULL', b'other->data', 1)
            return plan, files
        with monkeypatch.context() as local:
            local.setattr(current, 'declaration', foreign)
            with pytest.raises(packets.Refused):
                packets.mathematical_dependencies(BASE, MOVE)
