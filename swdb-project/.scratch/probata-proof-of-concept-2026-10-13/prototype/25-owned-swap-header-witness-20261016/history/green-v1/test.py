"""2026-10-16 ET. Constructive witnesses for the complete swap header duty."""


def test_explicit_header_witnesses_keep_the_complete_original_cases(tmp_path):
    from swdb import vector_owned_swap_header_witness as packets
    from swdb import vector_owned_swap_header_cases as previous

    directory = tmp_path/'witnesses'
    plan = packets.prepare(directory)
    assert packets.check(directory) == plan
    old, old_files = previous.declaration()
    assert plan['original_statement'] == old['original_statement']
    assert plan['complete_source_antecedent'] == old['complete_source_antecedent']
    assert plan['caller_premises_added'] == []
    assert [(row['case'], row['condition']) for row in plan['obligations']] == [
        ('left', 'observed == l'), ('right', 'observed == r'),
        ('other', 'observed != l && observed != r')]
    header = ('OwnedEffects::header(OwnedEffects::swap(h,l,r,a),observed,'
              'Owners::buffer(Owners::swap(owners,l,r),observed),')
    expected = {
        'left': header+'nr,cr)',
        'right': header+'nl,cl)',
        'other': header+'OwnedEffects::size(h,observed),OwnedEffects::capacity(h,observed))'}
    existential = (r'(\exists integer size,capacity; '+header+'size,capacity))')
    for row, original in zip(plan['obligations'], old['obligations'], strict=True):
        assert row['source_antecedent'] == old['complete_source_antecedent']
        assert row['explicit_header'] == expected[row['case']]
        assert row['statement'].replace(expected[row['case']], existential) == original['statement']
        assert r'\exists' not in row['statement']
        assert row['fresh_universal_indices'] == ['observed']
        assert row['dependencies'] == [] and row['status'] == 'pending'
        assert row['existential_reference']['statement'] == original['statement']
        assert (directory/row['existential_reference']['path']).read_bytes() == old_files[original['path']]
    assert len(plan['unchanged_dependencies']) == 12
    assert plan['source_heap_bridge_established'] is False
    assert plan['source_typed_bridge_established'] is False
    assert plan['source_admission'].startswith('unsupported:')
