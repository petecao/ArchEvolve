"""2026-10-16 ET. Exact allocating typed-vector source artifact boundary."""
import hashlib

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
            assert status['positive_nan_counterexample_to_reflexive_equality'] is True
            assert status['separate_lifting_domain'] == 'every copied/fill payload is not NaN; distinct conditional mathematics only'
        assert row['original_contract_modified'] is False
    theory = (directory/semantics['theory']['path']).read_text()
    assert 'type binary32' in theory and 'type binary64' in theory and 'type int_pointer' in theory
    assert 'Real' not in theory and 'Integer' not in theory
    assert not any(line.lstrip().startswith(('axiom ', 'lemma ')) for line in theory.splitlines())
    assert 'not (is_nan x)' in theory
    assert 'NullIntPointer' in theory and 'EncodedIntPointer' in theory
    assert plan['mathematical_obligations']
    assert all(row['kind'] == 'check_lemma' and row['status'] == 'pending' for row in plan['mathematical_obligations'])
