"""2026-10-16 ET. Closed no-growth source projection through its public view."""
import copy
from dataclasses import replace

import pytest

from testkit.vector_reallocation import CONTRACT


def test_closed_view_preserves_original_contract_capture_and_explicit_lifetime_duties(lowered_no_growth):
    from swdb import vector_reallocation_closed_view as views
    source, lowering = lowered_no_growth
    view = views.prepare(lowering, source, CONTRACT)
    assert views.check(lowering, source, view, CONTRACT) == view
    assert view.formal_texts == tuple(CONTRACT)
    root = view.text.split('int vector_realloc_v3_no_growth(int n) {', 1)[1]
    assert 'std_vector_int_ctor_count_value(&v, (unsigned long)n, 7);' in root
    assert 'int *saved = v.data;' in root
    assert 'assert swdb_closed_data_requires: std_vector_int_readable(&v);' in root
    assert 'assert swdb_closed_reserve_requires:' in root
    assert 'assert swdb_reserve_no_growth: (unsigned long)n <= v.capacity;' in root
    assert 'std_vector_int_data(&v)' not in root
    assert 'std_vector_int_reserve(&v' not in root
    assert 'std_vector_int_grow(&v' not in root
    assert 'std_vector_int_dtor(&v)' not in root
    assert 'int swdb_return = (n > 0) ? (*saved) : 0;' in root
    assert root.index('int swdb_return') < root.index('checked private terminal cleanup')
    assert root.index('checked private terminal cleanup') < root.index('return swdb_return;')
    assert '+ 0' not in root
    certificate = view.certificate
    assert certificate['original_lowering_inverse_equal'] is True
    assert certificate['caller_premises_added'] == []
    assert certificate['original_assigns'] == r'assigns \nothing;'
    assert certificate['cfg']['fallback_reachable'] is False
    assert certificate['cfg']['reason'] == 'exact canonical compound ends in unconditional scalar return'
    assert certificate['terminal_cleanup']['transition'] == 'Heap.end_automatic(Heap.release(now,buffer),receiver)'
    assert certificate['terminal_cleanup']['freeable_duty']['status'] == 'pending source-allocation/lifetime bridge'
    assert certificate['proof_admission'].startswith('unsupported:')
    assert certificate['source_typed_bridge_established'] is False
    with pytest.raises(views.Refused):
        views.check_launch(lowering, source, view, CONTRACT)


@pytest.mark.parametrize('change', ['text', 'cfg', 'lifetime', 'provenance'])
def test_closed_view_rejects_altered_source_cfg_cleanup_or_allocator_binding(lowered_no_growth, change):
    from swdb import vector_reallocation_closed_view as views
    source, lowering = lowered_no_growth
    view = views.prepare(lowering, source, CONTRACT)
    changed = copy.deepcopy(view)
    if change == 'text':
        changed = replace(changed, text=changed.text.replace('(*saved)', '7'))
    elif change == 'cfg':
        changed.certificate['cfg']['fallback_reachable'] = True
    elif change == 'lifetime':
        changed.certificate['terminal_cleanup']['transition'] = 'now'
    else:
        changed_lowering = copy.copy(lowering)
        provenance = copy.deepcopy(lowering.stdlib_provenance)
        provenance['verdict'] = 'refused'
        object.__setattr__(changed_lowering, 'stdlib_provenance', provenance)
        with pytest.raises(views.Refused):
            views.prepare(changed_lowering, source, CONTRACT)
        return
    with pytest.raises(views.Refused):
        views.check(lowering, source, changed, CONTRACT)
