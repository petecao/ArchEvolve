"""2026-10-16 ET. Original transfer field/lifetime packet public controls."""
import json

import pytest


def test_owned_source_view_retains_original_source_layout_and_phase_duties(tmp_path):
    from swdb import vector_owned_source_view as view
    directory=tmp_path/'source-view'
    plan=view.prepare(directory, elements=('int','float','double','int *'))
    assert view.check(directory, elements=('int','float','double','int *'))==plan
    assert plan['checker']==view.identity()
    assert plan['source_typed_bridge_established'] is False
    assert plan['source_heap_bridge_established'] is False
    assert plan['source_admission'].startswith('unsupported:')
    assert plan['current_model_records_admitted']==[]
    assert plan['caller_premises_added']==[]
    assert plan['phases']['reserved']['physical_field_values_established'] is False
    assert plan['phases']['live']['initialized_header_required'] is True
    assert plan['ownership']['frontier']=='Heap.next; never-issued allocation identity, not live-owner count'
    assert plan['ownership']['complete_source_owner_set_required'] is True
    assert plan['frame']['receiver_padding_unchanged_claimed'] is False
    assert plan['frame']['buffer_payload_interpreted'] is False
    assert plan['cleanup']['retire_replaces_release'] is False
    assert plan['cleanup']['source_cleanup_established'] is False
    assert len(plan['source_members'])==8
    for row in plan['source_members']:
        original=(directory/row['original_path']).read_bytes()
        checked=(directory/row['view_path']).read_bytes()
        assert original==checked[row['original_range'][0]:row['original_range'][1]]
        assert row['source_body_changed'] is False
        assert row['layout_assertions_executed'] is False
        assert row['old_contract_proved'] is False
        assert b'_Static_assert' in checked and b'offsetof' in checked
        assert {event['operation'] for event in row['events']} >= {'header_copy'}
        if row['member']=='move_ctor':
            assert [event['field'] for event in row['events'] if event['operation']=='zero_field']==['data','size','capacity']
        else:
            assert row['self_swap_old_contract_relaxed'] is False
            assert row['events'][0]['operation']=='begin_automatic'
            assert row['events'][-1]['operation']=='end_automatic'
    assert len(plan['obligations'])==9
    assert all(row['dependencies']==[] and row['status']=='pending' for row in plan['obligations'])
    with pytest.raises(ValueError,match='source/Heap'):
        view.check_launch(directory,elements=('int','float','double','int *'))


def test_owned_source_view_refuses_changed_body_theory_phase_or_admission(tmp_path):
    from swdb import vector_owned_source_view as view
    for case in ('body','theory','layout','phase','claim','extra','redirect'):
        directory=tmp_path/case;plan=view.prepare(directory)
        if case in {'body','layout'}:
            row=plan['source_members'][0];path=directory/row['view_path']
            text=path.read_text()
            path.write_text(text.replace('other->data = NULL;', 'other->data = this->data;',1) if case=='body' else text.replace('sizeof(size_t) == 8','sizeof(size_t) == 4',1))
        elif case=='theory':
            path=directory/'theory/vector_owned_effects.mlw';path.write_text(path.read_text().replace('function move','function changed_move',1))
        elif case in {'phase','claim'}:
            path=directory/'manifest.json';changed=json.loads(path.read_bytes())
            if case=='phase':changed['phases']['reserved']['physical_field_values_established']=True
            else:changed['source_heap_bridge_established']=True
            path.write_text(json.dumps(changed))
        elif case=='extra':(directory/'accepted.json').write_text('{}')
        else:
            path=directory/'theory/vector_owned_effects.mlw';path.unlink();path.symlink_to(directory/'manifest.json')
        with pytest.raises(ValueError):view.check(directory)
