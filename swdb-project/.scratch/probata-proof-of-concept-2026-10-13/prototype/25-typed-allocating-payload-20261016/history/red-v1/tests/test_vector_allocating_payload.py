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
