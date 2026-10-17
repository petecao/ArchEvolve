"""2026-10-16 ET. Closed source move/capture/cleanup public seam controls."""
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
