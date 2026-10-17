"""2026-10-16 ET. Source-derived no-growth diagnostic view; no caller admission."""
import copy

import pytest

from testkit.vector_reallocation import CONTRACT


def test_no_growth_source_view_retains_construction_alias_scalar_and_cleanup(lowered_no_growth):
    from swdb import vector_reallocation_caller_view as views
    source, lowering = lowered_no_growth
    view = views.prepare(lowering, source, CONTRACT)
    assert view.certificate['proof_admission'].startswith('unsupported:')
    assert view.certificate['caller_premises_added'] == []
    assert view.certificate['runtime_bridge_proved'] is False
    assert view.formal_texts == tuple(CONTRACT)
    for text in ['std_vector_int_ctor_count_value(&v, (unsigned long)n, 7);',
                 'int *saved = std_vector_int_data(&v);',
                 'int swdb_return = (n > 0) ? (*saved) : 0;',
                 'std_vector_int_dtor(&v);', 'return swdb_return;']:
        assert view.text.count(text) == lowering.text.count(text)
    assert 'assert swdb_reserve_no_growth: (unsigned long)n <= v.capacity;' in view.text
    assert 'if ((unsigned long)n > v.capacity) std_vector_int_grow(&v, (unsigned long)n);' in view.text
    assert view.certificate['original_reserve_summary_imported'] is False
    assert view.certificate['unreachable_fallthrough_cleanup_retained'] is True
    assert views.check(lowering, source, view, CONTRACT) == view


def test_source_view_checks_typed_cells_and_byte_layout_as_distinct_coordinates(lowered_no_growth):
    from swdb import vector_reallocation_caller_view as views
    source, lowering = lowered_no_growth
    view = views.prepare(lowering, source, CONTRACT)
    layout = view.certificate['address_coordinates']
    assert layout['receiver']['typed_cell_extent'] == 3
    assert layout['receiver']['byte_extent'] == 24
    assert [(row['field'], row['typed_cell_offset'], row['byte_offset'])
            for row in layout['receiver']['fields']] == [('data', 0, 0), ('size', 1, 8), ('capacity', 2, 16)]
    assert layout['buffer'] == {'element': 'int32', 'typed_cell_stride': 1,
                                'byte_stride': 4, 'byte_alignment': 4}
    assert layout['address_identity_mapping'] == 'pending injective source-local identity relation; no address-to-integer observation'
    assert 'offsetof(std_vector_int, capacity) == 16' in view.text
    assert 'sizeof(std_vector_int) == 24' in view.text
    assert view.certificate['selected_runtime_requirements']['variable_model'] == 'Var'
    assert {'MemTyped.ml', 'MemVar.ml', 'MemLoader.ml', 'Ctypes.ml', 'Cint.ml', 'Factory.ml'} <= {
        row['name'] for row in view.certificate['selected_runtime_requirements']['source_pins']}


def test_source_view_refuses_altered_scope_request_source_or_contract(lowered_no_growth, tmp_path):
    from swdb import vector_reallocation_caller_view as views
    source, lowering = lowered_no_growth
    for change in ['request', 'lowering', 'source', 'contract']:
        changed = copy.copy(lowering)
        object.__setattr__(changed, 'vector_reallocation_candidate', copy.deepcopy(lowering.vector_reallocation_candidate))
        current_source, clauses = source, CONTRACT
        if change == 'request':
            changed.vector_reallocation_candidate['reserve_request'] = 'count+1'
        elif change == 'lowering':
            object.__setattr__(changed, 'text', lowering.text.replace('(*saved)', '7'))
        elif change == 'source':
            current_source = tmp_path / 'changed.cc'
            current_source.write_bytes(source.read_bytes() + b'\n// changed original\n')
        else:
            clauses = CONTRACT[:2] + [r'ensures \result == 7;']
        with pytest.raises(views.Refused):
            views.prepare(changed, current_source, clauses)


def test_source_view_never_enables_launch_from_hashes_or_a_forged_bridge_label(lowered_no_growth):
    from swdb import vector_reallocation_caller_view as views
    source, lowering = lowered_no_growth
    view = views.prepare(lowering, source, CONTRACT)
    with pytest.raises(views.Refused, match='actual Typed'):
        views.check_launch(lowering, source, view, CONTRACT)
    changed = copy.deepcopy(view)
    changed.certificate['runtime_bridge_proved'] = True
    with pytest.raises(views.Refused):
        views.check(lowering, source, changed, CONTRACT)


def test_source_view_refuses_a_new_reserve_effect_around_the_familiar_branch(lowered_no_growth, monkeypatch):
    from swdb import vector_reallocation_caller_view as views
    source, lowering = lowered_no_growth
    original = views.std_models.model_text
    branch = 'if (n > this->capacity) std_vector_int_grow(this, n);'

    def changed(name):
        text = original(name)
        return text.replace(branch, branch + '\n  this->size = 0;') if name == 'std_vector_int_reserve' else text

    monkeypatch.setattr(views.std_models, 'model_text', changed)
    with pytest.raises(views.Refused, match='reserve.*body'):
        views.prepare(lowering, source, CONTRACT)
