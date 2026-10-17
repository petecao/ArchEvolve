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


def test_recovery_binds_exact_source_kernel_and_capture_free_integer_witnesses(tmp_path):
    import hashlib
    import importlib.util
    from pathlib import Path
    import shutil

    import pytest
    from swdb import vector_owned_swap_header_witness as packets

    directory = tmp_path/'recovery'
    plan = packets.prepare(directory)
    assert packets.check(directory) == plan
    bindings = plan['kernel_bindings']
    assert {'OwnedEffects.header', 'OwnedEffects.size', 'OwnedEffects.capacity',
            'OwnedEffects.swap', 'Heap.load_int', 'Heap.integer_at',
            'Heap.begin_automatic', 'Heap.end_automatic', 'Owners.swap'} <= set(bindings)
    for row in bindings.values():
        source = (directory/row['path']).read_bytes()
        assert hashlib.sha256(source).hexdigest() == row['container_sha256']
        assert hashlib.sha256(source[row['begin']:row['end']]).hexdigest() == row['sha256']
    expected = {'left': ('nr', 'cr'), 'right': ('nl', 'cl'),
                'other': ('OwnedEffects::size(h,observed)', 'OwnedEffects::capacity(h,observed)')}
    for row in plan['obligations']:
        proof = row['existential_introduction']
        assert proof['rule'] == 'capture-free integer existential introduction'
        assert proof['original_existential'].startswith(r'(\exists integer size,capacity;')
        assert proof['instance'] == row['explicit_header']
        assert [(item['name'], item['type'], item['witness']) for item in proof['binders']] == [
            ('size', 'integer', expected[row['case']][0]),
            ('capacity', 'integer', expected[row['case']][1])]
        assert proof['bound_variable_capture'] is False
        assert not {'size', 'capacity'} & set(proof['witness_free_variables'])
        assert set(proof['witness_free_variables']) <= set(proof['outer_universal_variables'])
        assert proof['instance_to_existential_is_sufficient'] is True
    assert plan['reconstruction']['reverse_implication_claimed'] is False
    assert plan['reconstruction']['self_swap_excluded'] is False
    assert plan['reconstruction']['added_premises'] == []
    assert plan['reconstruction']['all_three_stronger_proofs_required'] is True
    # Load an ordinary copy of the public source component, then change an
    # actual physical kernel input. No internal collaborator is mocked.
    component = tmp_path/'component'; component.mkdir()
    source_root = Path(packets.__file__).parent
    for name in plan['physical_context']:
        shutil.copyfile(source_root/name, component/name)
    shutil.copyfile(source_root/'vector_owned_swap_header_witness.py', component/'vector_owned_swap_header_witness.py')
    spec = importlib.util.spec_from_file_location('copied_header_witness', component/'vector_owned_swap_header_witness.py')
    copied = importlib.util.module_from_spec(spec); spec.loader.exec_module(copied)
    copied.prepare(tmp_path/'copied-baseline')
    kernel = component/'heap_reallocation.mlw'
    original = kernel.read_text(); changed = original.replace('| Integer v -> v', '| Integer v -> 0')
    assert changed != original
    kernel.write_text(changed)
    with pytest.raises(ValueError, match='source|kernel|physical'):
        copied.prepare(tmp_path/'changed-kernel')
    assert not (tmp_path/'changed-kernel').exists()
