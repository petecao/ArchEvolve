"""2026-10-16 ET. Closed source move/capture/cleanup public seam controls."""
import copy
from dataclasses import replace
import json

import pytest

from testkit.vector_owned_move import CONTRACT, build_move


def test_closed_move_derives_source_local_transfer_scalar_and_reverse_cleanup(tmp_path):
    from swdb import vector_owned_move_source as move
    source, lowering = build_move(tmp_path)
    directory = tmp_path/'packet'
    plan = move.prepare(lowering, source, CONTRACT, directory)
    assert move.check(lowering, source, CONTRACT, directory) == plan
    assert plan['checker'] == move.identity()
    assert plan['original_contract'] == CONTRACT
    assert plan['caller_premises_added'] == []
    assert plan['source_grammar']['all_statements_accounted'] is True
    assert plan['cfg']['fallback_reachable'] is False
    assert plan['cfg']['whole_lowering_inverse_equal'] is True
    inverse = (directory/'views/unreachable-fallback-eliminated.c').read_text()
    for edit in reversed(plan['cfg']['edits']):
        begin = edit['begin']
        assert inverse[begin:begin+len(edit['replacement'])] == edit['replacement']
        inverse = inverse[:begin]+edit['old']+inverse[begin+len(edit['replacement']):]
    assert inverse == lowering.text
    assert plan['ownership']['complete_participating_lexical_owners'] == ['source', 'destination']
    assert plan['ownership']['incoming_owners_assumed_valid'] is False
    assert plan['ownership']['raw_saved_pointer_is_owner'] is False
    for branch, expected in [('zero', 0), ('positive', 7)]:
        case = plan['branches'][branch]
        assert case['source_after_move'] == {'data': 'null', 'size': 0, 'capacity': 0}
        assert case['destination_after_move'] == case['source_before_move']
        assert case['scalar'] == expected
        assert case['scalar_captured_before_cleanup'] is True
        assert case['cleanup']['destructor_order'] == ['destination', 'source']
        assert case['cleanup']['buffer_release_count'] == (1 if branch == 'positive' else 0)
        assert case['cleanup']['automatic_ends'] == ['destination', 'source']
        assert case['incoming_frame']['all_steps_checked'] is True
        assert case['returned_pointer'] is False
    assert plan['observation']['incoming_type_restriction'] is None
    assert plan['observation']['dead_physical_bytes_preserved'] is False
    assert plan['source_safety']['null_pointer_arithmetic_evaluated'] is False
    assert plan['source_safety']['original_count_upper_bound'] == 2147483647
    assert plan['source_safety']['source_size_observed_after_move'] is False
    assert plan['source_model_TCB']['moved_from_empty_is_portable_Cpp17_postcondition'] is False
    assert plan['source_admission'] is False
    assert plan['source_typed_bridge_established'] is False
    assert plan['caller_acceptance'] is False
    with pytest.raises(move.Refused, match='complete exact evidence'):
        move.check_launch(lowering, source, CONTRACT, directory)


def test_closed_move_accounts_for_private_administrative_storage_in_source_order(tmp_path):
    from swdb import vector_owned_move_source as move
    source, lowering = build_move(tmp_path)
    plan = move.prepare(lowering, source, CONTRACT, tmp_path/'packet')
    for branch in ('zero', 'positive'):
        administrative = plan['branches'][branch]['administrative_storage']
        assert administrative['incoming_frame']['all_steps_checked'] is True
        assert administrative['caller_n_is_entry_parameter'] is True
        assert administrative['no_admin_identity_consumes_selected_Heap_frontier'] is True
        steps = administrative['incoming_frame']['steps']
        def index(operation, target):
            return next(i for i, row in enumerate(steps) if row['operation'] == operation and row.get('target') == target)
        assert index('begin_automatic', 'caller.saved') < index('end_automatic', 'data.this') < index('store', 'caller.saved')
        assert index('store', 'caller.swdb_return') < index('begin_automatic', 'dtor.destination.this')
        assert index('end_automatic', 'dtor.destination.this') < index('begin_automatic', 'dtor.source.this')
        assert index('end_automatic', 'dtor.source.this') < index('end_automatic', 'caller.swdb_return')
        assert ('ctor.k' in administrative['fresh_private_objects']) is (branch == 'positive')


def test_closed_move_binds_complete_observed_statement_and_dependency_censuses(tmp_path):
    from swdb import vector_owned_move_source as move
    source, lowering = build_move(tmp_path)
    plan = move.prepare(lowering, source, CONTRACT, tmp_path/'packet')
    # Independently retained G641 normalized semicolon-statement content pins.
    assert [row['normalized_sha256'] for row in plan['source_events']['lowered']] == [
        'b0c36d00cc712f694acf7ba1f6dd3bcca527d045b3485370bcd6423b3253fac5',
        'c5f26003e4dfca5daf0588921ed3f48711de5b776061f1a6e38c77273307b6e7',
        'ef91192c35c6c8eb8b7b12ed095ac01d8d006f40f45365d0eec28115c9a8dcd3',
        '614927373dbb92fa841d2728c275eb75c07a44a2cf8af90d652c561000e4cbd4',
        'a0b618aa4689ae2ed5e55e7c924b294284b668c388a64c7ad4eb06c22d99a501',
        '43a9008020b7f36f0aee2503badc1c1bd7319c972ce5bfa492370c3a453ed872',
        '21d7ee777fb0dfa56cb4c7c04932b87d4d6dcd62442efeefd91c2907ec30a52c',
        '5118f04061e893dd4be2d93b886de8ef4848d6575ba1c626bba8df6559360af9',
        '984df4c8af6049800e0f2b4094b53d8fb9eb389d04a6bf7a9eb35a5ee94a74b4',
        'dab360f4b2f0c2f471b36b3f09f585484bd6ae1d38b4c1ba3985c198ea43a8d3',
        'b8a0bae0ae7e84c8d86868f11c82c5c7d4dd7a3840bba606353b881718462b51',
        '984df4c8af6049800e0f2b4094b53d8fb9eb389d04a6bf7a9eb35a5ee94a74b4']
    deps = plan['scientific_dependencies']
    assert [len(deps[name]['targets']) for name in ('constructor', 'destructor', 'private_frame', 'move_source')] == [35, 11, 9, 4]
    assert {row['id'] for row in deps['move_source']['targets']} == {
        'move.destination_header', 'move.source_empty', 'move.incoming_frame', 'move.owner_correspondence'}
    assert deps['move_source']['mathematically_admitted'] is False
    assert deps['move_source']['old_eight_native_Valid_or_registry10_is_admission'] is False
