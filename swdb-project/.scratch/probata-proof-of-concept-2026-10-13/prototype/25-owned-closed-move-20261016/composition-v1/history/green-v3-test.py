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


def test_closed_move_composes_fill_transfer_scalar_capture_and_actual_cleanup(tmp_path):
    from swdb import vector_owned_move_composition as composition
    source, lowering = build_move(tmp_path)
    directory = tmp_path/'composition'
    plan = composition.prepare(lowering, source, CONTRACT, directory)
    assert composition.check(lowering, source, CONTRACT, directory) == plan
    positive = plan['cases']['positive']
    assert positive['arithmetic']['buffer_width_bounds'] == [4, 8589934588]
    assert positive['arithmetic']['buffer_end_bounds'] == [60, 8589934644]
    assert positive['arithmetic']['n_to_unsigned64_exact'] is True
    assert positive['fill_induction']['base_empty_prefix'] is True
    assert positive['fill_induction']['step_preserves_every_earlier_element'] is True
    assert positive['fill_induction']['all_0_le_k_lt_n_checked_symbolically'] is True
    assert positive['fill_induction']['remaining_extent_nonnegative_coefficients'] == [0, 4, 0]
    for branch, value in [('zero', 0), ('positive', 7)]:
        case = plan['cases'][branch]
        assert case['capture']['value'] == value
        assert case['capture']['saved_private_key'] == case['entry']['buffer']
        assert case['capture']['before_any_destructor'] is True
        assert case['capture']['saved_alias_registered_as_owner'] is False
        assert case['after_move']['source_header'] == {'buffer': 0, 'count': [0, 0], 'capacity': [0, 0]}
        assert case['after_move']['destination_header']['buffer'] == case['entry']['buffer']
        assert case['after_move']['world']['derived'] is True
        assert [row['owner'] for row in case['cleanup']['steps']] == ['destination', 'source']
        assert case['cleanup']['steps'][1]['released_private_key'] == 0
        assert case['cleanup']['buffer_release_count'] == int(branch == 'positive')
        assert case['cleanup']['registry_retirement_is_Heap_release'] is False
        assert case['after_cleanup']['owners']['active_keys'] == []
        assert all(not row['alive'] for row in case['after_cleanup']['objects'])
        assert case['after_cleanup']['next'] == case['entry']['next']
        assert [row['key'] for row in case['after_cleanup']['objects']] == [row['key'] for row in case['entry']['objects']]
        assert case['incoming_frame']['all_source_effects_checked'] is True
        assert case['incoming_frame']['arbitrary_incoming_type_restriction'] is None
        assert case['incoming_frame']['dead_physical_bytes_preserved'] is False
        assert case['administrative_product']['source_order_checked'] is True
        assert case['administrative_product']['consumes_selected_private_frontier'] is False
    dependencies = plan['scientific_dependencies']
    assert [len(dependencies[name]['targets']) for name in ('constructor', 'destructor', 'private_frame', 'move_source')] == [35, 11, 9, 4]
    assert {row['id'] for row in dependencies['move_source']['targets']} == {
        'move.destination_header', 'move.source_empty', 'move.incoming_frame', 'move.owner_correspondence'}
    assert plan['exact_mathematical_evidence_bound'] is False
    assert plan['normal_public_diagnostic_ledger_bound'] is False
    assert plan['source_model_TCB']['moved_from_empty_is_portable_Cpp17_postcondition'] is False
    assert 'allocation' in plan['source_model_TCB'] and 'release' in plan['source_model_TCB']
    assert (directory/'derivation.md').read_text().startswith('2026-10-16 ET.')


def test_closed_move_has_a_total_private_memory_denotation_and_complete_count_partition(tmp_path):
    from swdb import vector_owned_move_composition as composition
    source, lowering = build_move(tmp_path)
    plan = composition.prepare(lowering, source, CONTRACT, tmp_path/'composition')
    assert plan['input_partition'] == {
        'original_signed32_n_domain': [0, 2147483647], 'zero_domain': [0, 0],
        'positive_domain': [1, 2147483647], 'disjoint_and_complete': True,
        'upper_bound_is_source_type_not_new_requires': True}
    assert plan['private_total_maps']['unlisted_allocated_alive_dynamic_writable'] is False
    assert plan['private_total_maps']['unlisted_extent_address'] == 0
    assert plan['private_total_maps']['unwritten_cell_choice'] == ['Integer', [0, 0]]
    for branch in ('zero', 'positive'):
        case = plan['cases'][branch]
        for obj in case['entry']['objects']:
            assert obj['memory_denotation']['default_unobserved_cell'] == ['Integer', [0, 0]]
            assert obj['initialization_denotation']['default_unobserved_initialized'] is False
        destination = next(obj for obj in case['entry']['objects'] if obj['key'] == case['entry']['destination'])
        assert destination['memory_denotation']['explicit_stores'] == []
        assert destination['initialization_denotation']['explicit_initialized_offsets'] == []
    positive = plan['cases']['positive']
    buffer = next(obj for obj in positive['entry']['objects'] if obj['key'] == 2)
    assert buffer['memory_denotation']['int_prefix'] == {
        'count': [1, 0], 'stride': 4, 'element': ['Integer', [0, 7]],
        'offset_predicate': 'p=4*k for some integer 0<=k<n'}
    assert buffer['initialization_denotation']['initialized_int_prefix'] == {
        'count': [1, 0], 'stride': 4, 'initialized': True,
        'offset_predicate': 'p=4*k for some integer 0<=k<n'}
    assert positive['fill_induction']['prior_cell_separation_coefficients'] == [4, 0]
    assert positive['fill_induction']['counter_decrease'] == 1
    assert plan['source_layout_TCB']['logical_addresses_equal_physical_addresses'] is False
    assert plan['source_layout_TCB']['total_incoming_Typed_encoding_claimed'] is False
