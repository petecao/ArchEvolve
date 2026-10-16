"""2026-10-16 ET. Source-bound constructor/private-cleanup public packets."""
import json

import pytest

from testkit.vector_reallocation import CONTRACT


def test_closed_lifetime_packet_binds_constructor_frame_and_real_cleanup(lowered_no_growth, tmp_path):
    from swdb import vector_reallocation_closed_lifetime as packets
    source, lowering = lowered_no_growth
    directory = tmp_path/'closed-lifetime'
    plan = packets.prepare(lowering, source, CONTRACT, directory)
    assert packets.check(lowering, source, CONTRACT, directory) == plan
    assert plan['caller_premises_added'] == []
    assert plan['current_proof_records_admitted'] == []
    assert plan['source_typed_bridge_established'] is False
    assert plan['original_contract'] == CONTRACT
    assert plan['constructor_dependency']['original_source_sha256'] == plan['source_view']['constructor']['model_sha256']
    assert len(plan['constructor_dependency']['required_targets']) == 35
    assert len(plan['private_frame_dependency']['required_targets']) == 9
    assert len(plan['destructor_dependency']['required_targets']) == 11
    assert len(plan['obligations']) == 6
    assert {row['id'] for row in plan['obligations']} == {
        'receiver.entry', 'constructor.frame', 'buffer.identity', 'zero.cleanup',
        'positive.exit_image', 'positive.cleanup'}
    for row in plan['obligations']:
        assert row['dependencies'] == [] and row['status'] == 'pending'
        assert row['source_events'] and row['local_antecedent_discharge']
        text = (directory/row['path']).read_text()
        assert text.count('check lemma ') == 1
        assert 'axiom ' not in text
    zero = next(row for row in plan['obligations'] if row['id'] == 'zero.cleanup')
    positive = next(row for row in plan['obligations'] if row['id'] == 'positive.cleanup')
    assert 'Heap::end_automatic(Heap::release(' in zero['statement']
    assert 'Heap::end_automatic(Heap::release(' in positive['statement']
    assert r'\exists Heap::heap final; \exists integer scalar;' in positive['statement']
    assert 't25v3_ctor_inv(loop,r,0,b,n,n,7)' in positive['statement']
    assert 'Heap::fresh_id(before)' in positive['statement']
    assert 'Heap::load_int(t25_closed_positive(loop,r,n),b,0)' in positive['statement']
    identity = next(row for row in plan['obligations'] if row['id'] == 'buffer.identity')
    assert '!Heap::issued(entry,Heap::fresh_id(Heap::begin_automatic(entry,24,a)))' in identity['statement']
    assert 'Heap::fresh_id(t25_initial(Heap::begin_automatic(entry,24,a),Heap::fresh_id(entry),0))' in identity['statement']
    assert plan['explicit_allocator_library_TCB']['future_record_policy'].endswith('allocation success alone is insufficient')
    assert plan['proof_admission'].startswith('unsupported:')
    with pytest.raises(packets.Refused):
        packets.check_launch(lowering, source, CONTRACT, directory)


def test_closed_lifetime_packet_refuses_changed_observer_source_or_dependencies(lowered_no_growth, tmp_path):
    from swdb import vector_reallocation_closed_lifetime as packets
    source, lowering = lowered_no_growth
    for index, change in enumerate(['cleanup', 'incoming_frame', 'dependency', 'extra']):
        directory = tmp_path/str(index)
        plan = packets.prepare(lowering, source, CONTRACT, directory)
        if change == 'extra':
            (directory/'unbound.c').write_text('/* no foreign target admission */')
        elif change == 'dependency':
            manifest = json.loads((directory/'manifest.json').read_text())
            manifest['constructor_dependency']['required_targets'] = []
            (directory/'manifest.json').write_text(json.dumps(manifest))
        else:
            path = directory/plan['obligations'][-1]['path']
            text = path.read_text()
            if change == 'cleanup':
                changed = text.replace('Heap::end_automatic(Heap::release(t25_closed_positive(loop,r,n),b),r)', 't25_closed_positive(loop,r,n)')
            else:
                changed = text.replace('t25_private_frame(entry,final)', '1 == 1')
            assert changed != text
            path.write_text(changed)
        with pytest.raises(packets.Refused):
            packets.check(lowering, source, CONTRACT, directory)
