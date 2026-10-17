"""2026-10-16 ET. Exact allocating typed-vector source artifact boundary."""
import hashlib
import shutil

import pytest


def test_typed_allocating_constructors_preserve_all_nine_original_units(tmp_path):
    from swdb import vector_allocating_payload as payload
    from swdb import std_models

    directory = tmp_path/'typed-constructors'
    plan = payload.prepare(directory)
    assert payload.check(directory) == plan
    assert plan['parent_model'] == std_models.identity()
    assert [(row['element'], row['member']) for row in plan['source_members']] == [
        (element, member) for element in ('float', 'double', 'int *')
        for member in ('ctor_count', 'ctor_count_value', 'copy_ctor')]
    for row in plan['source_members']:
        original = (directory/row['original_path']).read_bytes()
        view = (directory/row['view_path']).read_bytes()
        begin, end = row['original_range']
        assert view[begin:end] == original == std_models.model_text(row['function']).encode()
        assert hashlib.sha256(original).hexdigest() == row['original_sha256']
        assert row['original_contract_modified'] is False
        assert row['source_effects_checked'] is True
        assert row['element_access'] == 'typed copy or typed zero store; no arithmetic or pointee access'
        assert row['loop']['unbounded'] is True
        assert row['loop']['stride'] == (4 if row['element'] == 'float' else 8)
        assert row['loop']['variant'] == ('other->size - k' if row['member'] == 'copy_ctor' else 'n - k')
    assert plan['caller_premises_added'] == []
    assert plan['source_admission'] is False
    assert plan['current_model_records_created'] == []
    with pytest.raises(payload.Refused, match='actual mathematical evidence'):
        payload.check_launch(directory)


def test_typed_source_domains_and_canonical_gate_reject_unaccounted_effects(tmp_path):
    from swdb import vector_allocating_payload as payload
    from swdb import std_models

    directory = tmp_path/'original'
    plan = payload.prepare(directory)
    assert payload.check(directory) == plan
    assert plan['typed_payload']['heap_theory']['sha256'] == 'a8f89e41decdbd2890f72e7725590c62134650fde84a18a6ec7fd9d5bd9abbc5'
    for row in plan['source_members']:
        domain = row['numeric_source_domain']
        if row['member'] == 'copy_ctor':
            assert domain['original_readable_to_full_byte_bound_proved'] is False
            assert domain['source_object_extent_and_separation_discharge_required'] is True
        assert domain['target_layout_executed'] is False
    sources = {row['function']: std_models.model_text(row['function']).encode() for row in plan['source_members']}
    selected = 'std_vector_float_ctor_count_value'
    changes = [
        (selected, b'this->data[k] = value;', b'this->data[k] = value; unrelated();'),
        (selected, b'this->data[k] = value;', b'/*@ assume \\false; */ this->data[k] = value;'),
        (selected, b'this->data[k] == value', b'\\true'),
        ('std_vector_int_ptr_ctor_count_value', b'this->data[k] = value;', b'this->data[k] = &value[0];'),
        ('std_vector_double_copy_ctor', b'this->data[k] = other->data[k];', b'this->data[k] = other->data[k+1];')]
    for index, (function, before, after) in enumerate(changes):
        assert before in sources[function]
        changed = dict(sources)
        changed[function] = changed[function].replace(before, after, 1)
        with pytest.raises(payload.Refused, match='complete original'):
            payload.prepare(tmp_path/('foreign-'+str(index)), model_sources=changed)
    for mutation in ('bytes', 'manifest', 'missing', 'extra', 'empty_directory', 'link'):
        target = tmp_path/mutation
        shutil.copytree(directory, target)
        assert payload.check(target) == plan
        theory = target/'theory/vector_typed_payload.mlw'
        if mutation == 'bytes':
            theory.write_bytes(theory.read_bytes()+b'\n')
        elif mutation == 'manifest':
            (target/'manifest.json').write_text('{}')
        elif mutation == 'missing':
            theory.unlink()
        elif mutation == 'extra':
            (target/'accepted.json').write_text('{}')
        elif mutation == 'empty_directory':
            (target/'unbound').mkdir()
        else:
            theory.unlink()
            theory.symlink_to(directory/'theory/vector_typed_payload.mlw')
        with pytest.raises(payload.Refused):
            payload.check(target)
    assert plan['current_model_records_created'] == []
    with pytest.raises(payload.Refused, match='actual mathematical evidence'):
        payload.check_launch(directory)


def test_typed_payload_transport_keeps_bits_categories_and_nan_equality_distinct(tmp_path):
    from swdb import vector_allocating_payload as payload

    directory = tmp_path/'typed-payload'
    plan = payload.prepare(directory)
    assert payload.check(directory) == plan
    semantics = plan['typed_payload']
    assert semantics['floating_representation'] == 'nominal binary32/binary64 sign, exponent and fraction bit fields'
    assert semantics['integer_or_real_surrogate'] is False
    assert semantics['pointer_representation'] == 'opaque typed int-pointer value category and symbolic 64 representation bits'
    assert semantics['arbitrary_pointer_bits_admitted'] is False
    assert semantics['pointee_validity_or_liveness_implied'] is False
    assert semantics['float_store_preserves_physical_nan_bits_proved'] is False
    assert semantics['payload_transport_is_C_equality'] is False
    assert semantics['default_pointer_representation'] == 'symbolic null representation, never assumed all-zero bits'
    examples = {row['id']: row for row in semantics['classification_examples']}
    for name in ('float.nan', 'double.nan'):
        assert examples[name]['is_nan'] is True
        assert examples[name]['self_C_equal'] is False
        assert examples[name]['same_typed_payload'] is True
    assert examples['float.negative_zero']['self_C_equal'] is True
    assert examples['double.positive_infinity']['self_C_equal'] is True
    for row in plan['source_members']:
        status = row['original_equality_contract']
        if row['element'] != 'int *' and row['member'] != 'ctor_count':
            assert status['arbitrary_IEEE_domain_established'] is False
            assert status['plain_ACSL_equality_is_IEEE_comparison'] is False
            assert status['original_ACSL_counterexample_established'] is False
            assert status['nonfinite_source_logical_promotion_characterized'] is False
            assert status['separate_lifting_domain'] == 'every copied/fill payload is not NaN; distinct conditional mathematics only'
            assert status['separate_C_comparison_lifting_proves_original_ACSL_clause'] is False
        assert row['original_contract_modified'] is False
    theory = (directory/semantics['theory']['path']).read_text()
    assert 'type binary32' in theory and 'type binary64' in theory and 'type int_pointer' in theory
    assert 'Real' not in theory and 'Integer' not in theory
    assert not any(line.lstrip().startswith(('axiom ', 'lemma ')) for line in theory.splitlines())
    assert 'not (is_nan x)' in theory
    assert 'NullIntPointer' in theory and 'EncodedIntPointer' in theory
    assert plan['mathematical_obligations']
    assert all(row['kind'] == 'check_lemma' and row['status'] == 'pending' for row in plan['mathematical_obligations'])


def test_typed_constructor_derives_width_safe_unbounded_fill_copy_and_full_incoming_frame(tmp_path):
    from swdb import vector_allocating_payload as payload

    directory = tmp_path/'derivation'
    plan = payload.prepare(directory)
    assert payload.check(directory) == plan
    rules = plan['checked_source_derivation']
    for name, width, bound in [('float', 4, 4611686018427387903),
                               ('double', 8, 2305843009213693951),
                               ('int *', 8, 2305843009213693951)]:
        numeric = rules['elements'][name]
        assert numeric['stride'] == width
        assert numeric['maximum_count'] == bound
        assert numeric['maximum_bytes'] == width*bound
        assert numeric['step_substitution'] == 'n = k + remaining + 1; k = j + distance + 1'
        assert numeric['remaining_after_store_coefficients'] == [0, width, 0]
        assert numeric['earlier_store_distance_coefficients'] == [width, 0, width]
        assert numeric['remaining_after_increment_coefficients'] == [0, 1, 0]
        assert numeric['variant_decrease'] == 1
        assert numeric['all_nonnegative_parameters_checked'] is True
    assert rules['incoming_frame']['observed_allocations'] == 'every issued incoming identity, including dead identities and non-int objects'
    assert rules['incoming_frame']['observed_live_payloads'] == 'all live incoming source bytes/typed values and initialization outside the original assigns *this region'
    assert rules['incoming_frame']['new_identity_not_previously_issued'] is True
    assert rules['incoming_frame']['dead_physical_bytes_preserved'] is False
    assert rules['copy']['source_read_only_preserved_at_every_step'] is True
    assert rules['copy']['source_destination_disjointness'] == 'fresh backing identity differs from every issued incoming source identity'
    assert rules['whole_source_body_rule_checked'] is True
    assert rules['mathematical_solver_acceptance_claimed'] is False
    goals = {row['id']: row for row in plan['mathematical_obligations']}
    for name in ('fill.access', 'fill.step', 'fill.exit', 'copy.empty', 'copy.step', 'copy.exit',
                 'copy.non_nan_equality_lifting', 'store.other_cell_frame', 'allocate.uninitialized'):
        assert name in goals
    assert 'k < n' not in goals['fill.exit']['statement'].split('==>')[0]
    assert 'k == n' in goals['fill.exit']['statement'].split('==>')[0]
    assert 'TypedPayload::source_unchanged' in goals['copy.step']['statement']
    for row in goals.values():
        assert '.shape' not in row['statement']
        assert row['dependencies'] == []
    assert plan['source_Heap_Typed_bridge_established'] is False
    assert plan['allocator_library_TCB']['allocation_success_alone_establishes_frame'] is False
    assert plan['allocator_library_TCB']['physical_representation_transport_proved'] is False


def test_ieee_aware_successor_relation_admits_nan_class_without_assuming_bit_copy(tmp_path):
    from swdb import vector_allocating_payload as payload

    directory = tmp_path/'class-relation'
    plan = payload.prepare(directory)
    assert payload.check(directory) == plan
    semantics = plan['typed_payload']
    assert semantics['proposed_model_successor_relation'] == 'TypedPayload.value_copy'
    assert semantics['original_FP_contract_requires_reviewed_model_successor'] is True
    assert semantics['non_nan_carveout_is_permanent_source_admission_policy'] is False
    examples = {row['id']: row for row in semantics['relation_examples']}
    for name in ('float.nan_payload_change', 'double.nan_payload_change',
                 'pointer.same_value_changed_representation', 'pointer.null_changed_representation'):
        assert examples[name]['value_copy'] is True
        assert examples[name]['exact_payload'] is False
    for name in ('float.nan_to_infinity', 'cross_format.nan', 'pointer.changed_value_same_bits'):
        assert examples[name]['value_copy'] is False
    for name in ('float.nan_payload_change', 'double.nan_payload_change'):
        assert examples[name]['C_equal'] is False
    assert examples['float.signed_zero_change']['C_equal'] is True
    goals = {row['id']: row for row in plan['mathematical_obligations']}
    for name in ('value_copy.reflexive', 'class_fill.step', 'class_fill.exit', 'class_copy.step', 'class_copy.exit'):
        assert name in goals
    assert 'TypedPayload::value_copy(stored,value)' in goals['class_fill.step']['statement']
    assert 'TypedPayload::source_unchanged' in goals['class_copy.step']['statement']
    assert 'exact_payload_bits_required' not in goals['class_copy.step']['statement']
    assert plan['original_contract_proved'] is False
    assert plan['source_admission'] is False
