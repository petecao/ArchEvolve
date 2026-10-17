"""2026-10-16 ET. Checked private closed-move composition public artifacts."""
import json

import pytest

from testkit.vector_owned_move import CONTRACT, build_move


def test_closed_move_constructs_full_private_entry_without_an_incoming_world_premise(tmp_path):
    from swdb import vector_owned_move_composition as composition
    source, lowering = build_move(tmp_path)
    directory = tmp_path/'composition'
    plan = composition.prepare(lowering, source, CONTRACT, directory)
    assert composition.check(lowering, source, CONTRACT, directory) == plan
    assert plan['checker'] == composition.identity()
    assert plan['caller_premises_added'] == []
    assert plan['incoming_component']['restriction'] is None
    assert plan['incoming_component']['empty_incoming_C_heap_assumed'] is False
    assert plan['private_initial_heap']['role'] == 'existential interpretation witness'
    assert plan['private_initial_heap']['incoming_Heap_or_Owners_precondition'] is False
    for name, expected in [('zero', (1, 2, 0, 3)), ('positive', (1, 3, 2, 4))]:
        case = plan['cases'][name]
        entry = case['entry']
        assert tuple(entry[key] for key in ('source', 'destination', 'buffer', 'next')) == expected
        assert entry['owners']['active_keys'] == [expected[0], expected[1]]
        assert entry['owners']['backing'] == {str(expected[0]): expected[2], str(expected[1]): 0}
        assert entry['ready_keys'] == [expected[0]]
        destination = next(obj for obj in entry['objects'] if obj['key'] == expected[1])
        assert destination['initialized_offsets'] == [] and destination['cells'] == []
        assert set(case['full_move_premises']) == {
            'OwnedEffects.world', 'OwnedEffects.reserved', 'Owners.active_owner(source)',
            'OwnedEffects.is_ready(source)', 'destination != source', 'OwnedEffects.header(source,b,n,n)'}
        assert all(row['derived'] for row in case['full_move_premises'].values())
        assert case['full_move_premises']['OwnedEffects.world']['ready_header_witnesses'] == [expected[0]]
        assert case['injection']['injective'] is True
        assert case['injection']['logical_addresses_are_actual_pointer_values'] is False
        assert case['injection']['private_keys_claim_global_Heap_next'] is False
    assert plan['source_rule']['source_sha256'] == 'a0dc043284f96a5b7c052963b51188318ae4abc6a85ee347fea78b6ab392d3a2'
    assert plan['source_rule']['lowering_sha256'] == '5c33a1a1843045d0b9d2ba43eb8d590c9e6106c794982286b28505c64e896e34'
    assert plan['source_Heap_Typed_caller_admission'] is False
    with pytest.raises(composition.Refused, match='complete exact mathematical evidence'):
        composition.check_launch(lowering, source, CONTRACT, directory)
