"""2026-10-16 ET. Complete source conjunctions and explicit cleanup witnesses."""
import json

import pytest

from testkit.vector_reallocation import CONTRACT


def test_closed_parts_cover_both_source_goals_without_sibling_premises(lowered_no_growth, tmp_path):
    from swdb import vector_reallocation_closed_lifetime_parts as packets
    source, lowering = lowered_no_growth
    directory = tmp_path/'parts'
    plan = packets.prepare(lowering, source, CONTRACT, directory)
    assert packets.check(lowering, source, CONTRACT, directory) == plan
    assert plan['caller_premises_added'] == []
    assert plan['source_typed_bridge_established'] is False
    assert plan['current_proof_records_admitted'] == []
    assert len(plan['unchanged_gluing_dependencies']) == 4
    assert {row['id'] for row in plan['unchanged_gluing_dependencies']} == {
        'receiver.entry', 'constructor.frame', 'buffer.identity', 'zero.cleanup'}
    assert len(plan['obligations']) == 23
    assert {row['logical_target'] for row in plan['obligations']} == {
        'positive.exit_image', 'positive.cleanup'}
    for row in plan['obligations']:
        assert row['dependencies'] == [] and row['status'] == 'pending'
        assert 't25v3_ctor_inv(loop,r,0,b,n,n,7)' in row['statement']
        assert row['source_antecedent'] == plan['complete_positive_antecedent']
        assert row['source_antecedent'] in row['statement']
        raw = (directory/row['path']).read_text()
        assert raw.count('check lemma ') == 1 and 'axiom ' not in raw
        assert 'positive_exit_image' not in row['statement']
    cleanup = plan['conjunctions']['positive.cleanup']
    assert cleanup['witnesses'] == {
        'final': 'Heap::end_automatic(Heap::release(t25_closed_positive(loop,r,n),b),r)',
        'scalar': '(n > 0 ? Heap::load_int(t25_closed_positive(loop,r,n),b,0) : 0)'}
    assert cleanup['equality_witnesses_checked'] is True
    assert len(cleanup['parts']) == 9
    assert len(plan['conjunctions']['positive.exit_image']['parts']) == 14
    assert all(row['premises_added'] == [] for row in plan['conjunctions'].values())
    scalar = next(row for row in plan['obligations'] if row['id'] == 'positive.cleanup.scalar')
    assert 'Heap::load_int(t25_closed_positive(loop,r,n),b,0)' in scalar['statement']
    assert 'n > 0 ? 7 : 0' in scalar['statement']
    assert plan['proof_admission'].startswith('unsupported:')
    with pytest.raises(packets.Refused):
        packets.check_launch(lowering, source, CONTRACT, directory)


def test_closed_parts_refuse_missing_conjunct_weaker_premise_or_cleanup_witness(lowered_no_growth, tmp_path):
    from swdb import vector_reallocation_closed_lifetime_parts as packets
    source, lowering = lowered_no_growth
    for index, mutation in enumerate(['missing', 'premise', 'witness', 'reference', 'manifest', 'extra']):
        directory = tmp_path/str(index)
        plan = packets.prepare(lowering, source, CONTRACT, directory)
        if mutation == 'missing':
            (directory/plan['obligations'][-1]['path']).unlink()
        elif mutation == 'manifest':
            manifest = json.loads((directory/'manifest.json').read_text())
            manifest['conjunctions']['positive.cleanup']['parts'] = []
            (directory/'manifest.json').write_text(json.dumps(manifest))
        elif mutation == 'extra':
            (directory/'foreign.c').write_text('/* no foreign target */')
        elif mutation == 'reference':
            path = directory/plan['conjunctions']['positive.cleanup']['reference_path']
            path.write_text(path.read_text().replace('t25_private_frame(entry,final)', '1 == 1'))
        else:
            row = next(row for row in plan['obligations'] if row['id'] == 'positive.cleanup.frame.objects')
            path = directory/row['path']
            original = path.read_text()
            changed = (original.replace('t25_frame(before,loop,r,0)', '1 == 1') if mutation == 'premise'
                       else original.replace('Heap::end_automatic(Heap::release(t25_closed_positive(loop,r,n),b),r)',
                                             't25_closed_positive(loop,r,n)'))
            assert changed != original
            path.write_text(changed)
        with pytest.raises(packets.Refused):
            packets.check(lowering, source, CONTRACT, directory)
