"""2026-10-16 ET. Public complete-premise cases of the pending swap header duty."""
import json

import pytest


def test_three_owner_cases_reconstruct_the_unchanged_ready_header_duty(tmp_path):
    from swdb import vector_owned_swap_header_cases as packets
    from swdb import vector_owned_swap_parts as previous

    directory = tmp_path/'cases'
    plan = packets.prepare(directory)
    assert packets.check(directory) == plan
    old, old_files = previous.declaration()
    header = next(row for row in old['obligations'] if row['id'] == 'swap.owner_correspondence.header.ready')
    quantifiers, conclusion = header['statement'].split(old['complete_source_antecedent']+' ==> ', 1)
    assert plan['logical_target'] == header['id']
    assert plan['original_statement'] == header['statement']
    assert plan['complete_source_antecedent'] == old['complete_source_antecedent']
    assert [(row['case'], row['condition']) for row in plan['obligations']] == [
        ('left', 'observed == l'), ('right', 'observed == r'),
        ('other', 'observed != l && observed != r')]
    assert len(plan['obligations']) == 3
    for row in plan['obligations']:
        assert row['statement'] == quantifiers+old['complete_source_antecedent']+' ==> ('+row['condition']+' ==> '+conclusion+')'
        assert row['statement'].count(r'\exists integer size,capacity;') == 1
        assert 'Owners::active_owner(Owners::swap(owners,l,r),observed)' in row['statement']
        assert 'OwnedEffects::is_ready(ready,observed)' in row['statement']
        assert row['source_antecedent'] == old['complete_source_antecedent']
        assert row['dependencies'] == [] and row['status'] == 'pending'
        raw = (directory/row['path']).read_text()
        assert raw.count('check lemma ') == 1 and 'axiom ' not in raw
    assert len(plan['unchanged_dependencies']) == 12
    assert all(row['id'] != header['id'] for row in plan['unchanged_dependencies'])
    for row in old['obligations']:
        assert (directory/('reference-parts/'+row['path'])).read_bytes() == old_files[row['path']]
    assert (directory/plan['reference_path']).read_bytes() == old_files[header['path']]
    assert plan['reconstruction']['case_disjunction'] == 'observed == l || observed == r || (observed != l && observed != r)'
    assert plan['reconstruction']['self_swap_excluded'] is False
    assert plan['reconstruction']['added_premises'] == []
    assert plan['reconstruction']['axioms_added'] == []
    assert plan['source_heap_bridge_established'] is False
    assert plan['source_typed_bridge_established'] is False
    assert plan['current_model_records_admitted'] == []
    assert plan['caller_premises_added'] == []
    assert plan['source_admission'].startswith('unsupported:')


def test_header_cases_refuse_changed_premise_partition_conclusion_or_source(tmp_path):
    from swdb import vector_owned_swap_header_cases as packets

    for case in ('missing', 'premise', 'partition', 'active', 'ready', 'witness',
                 'reference', 'definition', 'claim', 'extra', 'redirect'):
        directory = tmp_path/case
        plan = packets.prepare(directory)
        path = directory/plan['obligations'][0]['path']
        if case == 'missing':
            path.unlink()
        elif case in {'premise', 'partition', 'active', 'ready', 'witness'}:
            before = path.read_text()
            old, new = {
                'premise': ('Heap::automatic_available(h,24,8,a)', '1 == 1'),
                'partition': ('observed == l ==> ', 'observed != l ==> '),
                'active': ('Owners::active_owner(Owners::swap(owners,l,r),observed)', '1 == 1'),
                'ready': ('OwnedEffects::is_ready(ready,observed)', '1 == 1'),
                'witness': (r'\exists integer size,capacity;', r'\forall integer size,capacity;'),
            }[case]
            changed = before.replace(old, new)
            assert changed != before
            path.write_text(changed)
        elif case == 'reference':
            path = directory/plan['reference_path']
            path.write_text(path.read_text().replace('Owners::swap(owners,l,r)', 'owners'))
        elif case == 'definition':
            path = directory/'theory/vector_owned_effects.mlw'
            before = path.read_text()
            changed = before.replace('ready[r] = True', 'ready[r] = False')
            assert changed != before
            path.write_text(changed)
        elif case == 'claim':
            path = directory/'manifest.json'
            value = json.loads(path.read_text())
            value['source_heap_bridge_established'] = True
            value['reconstruction']['added_premises'] = ['the twelve successful sibling conclusions']
            path.write_text(json.dumps(value))
        elif case == 'extra':
            (directory/'accepted.json').write_text('{}')
        else:
            path = directory/'theory/vector_owned_effects.mlw'
            path.unlink()
            path.symlink_to(directory/'manifest.json')
        with pytest.raises(ValueError):
            packets.check(directory)
