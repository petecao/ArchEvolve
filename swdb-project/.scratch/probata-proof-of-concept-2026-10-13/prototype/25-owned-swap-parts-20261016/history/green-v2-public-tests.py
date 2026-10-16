"""2026-10-16 ET. Public exact-conclusion decomposition of the swap world duty."""
import json

import pytest


def test_swap_parts_reconstruct_the_original_world_under_its_complete_premise(tmp_path):
    from swdb import vector_owned_swap_parts as packets
    directory = tmp_path/'parts'
    plan = packets.prepare(directory)
    assert packets.check(directory) == plan
    assert plan['checker'] == packets.identity()
    assert plan['logical_target'] == 'swap.owner_correspondence'
    assert len(plan['obligations']) == 13
    assert {row['group'] for row in plan['obligations']} == {
        'heap', 'owners', 'receiver', 'header', 'freeable'}
    assert [len(plan['reconstruction']['groups'][group])
            for group in ('heap', 'owners', 'receiver', 'header', 'freeable')] == [4, 4, 3, 1, 1]
    assert len(plan['unchanged_dependencies']) == 8
    assert plan['source_heap_bridge_established'] is False
    assert plan['source_typed_bridge_established'] is False
    assert plan['current_model_records_admitted'] == []
    assert plan['caller_premises_added'] == []
    assert plan['original_timeout_evidence_preserved'] is True
    assert plan['reconstruction']['added_premises'] == []
    assert plan['reconstruction']['axioms_added'] == []
    assert plan['reconstruction']['equivalence'] == 'exact definition unfolding and conjunction/universal distribution'
    assert plan['original_statement'].endswith(
        'OwnedEffects::world(OwnedEffects::swap(h,l,r,a),Owners::swap(owners,l,r),ready)')
    for row in plan['obligations']:
        assert row['source_antecedent'] == plan['complete_source_antecedent']
        assert row['source_antecedent'] in row['statement']
        assert row['dependencies'] == [] and row['status'] == 'pending'
        assert row['statement'].count('OwnedEffects::world(h,owners,ready)') == 1
        assert 'OwnedEffects::world(OwnedEffects::swap' not in row['statement']
        raw = (directory/row['path']).read_text()
        assert raw.count('check lemma ') == 1 and 'axiom ' not in raw
    assert plan['source_admission'].startswith('unsupported:')
    with pytest.raises(ValueError, match='source|proof'):
        packets.check_launch(directory)


def test_swap_parts_refuse_missing_clause_weaker_premise_or_changed_source(tmp_path):
    from swdb import vector_owned_swap_parts as packets
    for case in ('missing', 'premise', 'conclusion', 'reference', 'definition', 'claim', 'extra', 'redirect'):
        directory = tmp_path/case
        plan = packets.prepare(directory)
        if case == 'missing':
            (directory/plan['obligations'][-1]['path']).unlink()
        elif case in {'premise', 'conclusion'}:
            path = directory/next(row['path'] for row in plan['obligations'] if row['group'] == 'freeable')
            text = path.read_text()
            changed = (text.replace('Heap::automatic_available(h,24,8,a)', '1 == 1') if case == 'premise'
                       else text.replace('Heap::freeable(', 'Heap::forms('))
            assert changed != text
            path.write_text(changed)
        elif case == 'reference':
            path = directory/plan['reference_path']
            path.write_text(path.read_text().replace('Owners::swap(owners,l,r)', 'owners'))
        elif case == 'definition':
            path = directory/'theory/vector_owned_effects.mlw'
            path.write_text(path.read_text().replace('H.freeable h (O.buffer s r) 0', 'H.forms h (O.buffer s r) 0'))
        elif case == 'claim':
            path = directory/'manifest.json'
            value = json.loads(path.read_text())
            value['source_heap_bridge_established'] = True
            value['reconstruction']['added_premises'] = ['the timed-out compound target']
            path.write_text(json.dumps(value))
        elif case == 'extra':
            (directory/'accepted.json').write_text('{}')
        else:
            path = directory/'theory/vector_owned_effects.mlw'
            path.unlink()
            path.symlink_to(directory/'manifest.json')
        with pytest.raises(ValueError):
            packets.check(directory)
