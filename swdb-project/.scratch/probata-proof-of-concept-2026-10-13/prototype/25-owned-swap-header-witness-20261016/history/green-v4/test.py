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


def test_public_construction_rejects_ill_sorted_captured_or_unbound_witnesses(tmp_path):
    import importlib.util
    from pathlib import Path
    import shutil

    import pytest
    from swdb import vector_owned_swap_header_witness as packets

    baseline = packets.prepare(tmp_path/'baseline')
    source_root = Path(packets.__file__).parent
    original = Path(packets.__file__).read_text()
    for index, witness in enumerate(('h', 'size', 'capacity', 'new_size',
                                    'OwnedEffects::size(h)', 'OwnedEffects::header(h,l,bl,nl,cl)',
                                    r'(\exists integer shadow; shadow)', 'OwnedEffects::size(h,observed)+1')):
        component = tmp_path/('component-'+str(index)); component.mkdir()
        for name in baseline['physical_context']:
            shutil.copyfile(source_root/name, component/name)
        changed = original.replace("('left', 'nr', 'cr')", "('left', "+repr(witness)+", 'cr')", 1)
        assert changed != original
        path = component/'vector_owned_swap_header_witness.py'; path.write_text(changed)
        spec = importlib.util.spec_from_file_location('witness_variant_'+str(index), path)
        copied = importlib.util.module_from_spec(spec); spec.loader.exec_module(copied)
        with pytest.raises(ValueError, match='sort|integer|bound|capture|term|arity'):
            copied.prepare(tmp_path/('refused-'+str(index)))
        assert not (tmp_path/('refused-'+str(index))).exists()


def test_all_supported_types_reject_packet_tampering_and_unproved_launch(tmp_path):
    import json
    import shutil

    import pytest
    from swdb import vector_owned_swap_header_witness as packets

    elements = ('int', 'float', 'double', 'int *')
    baseline = tmp_path/'all-types'
    plan = packets.prepare(baseline, elements=elements)
    assert packets.check(baseline, elements=elements) == plan
    goal = plan['obligations'][0]['path']
    mutations = (
        (goal, 'OwnedEffects::world(h,owners,ready)', 'true'),
        (goal, 'observed == l', 'observed != l'),
        (goal, 'Owners::active_owner(Owners::swap(owners,l,r),observed)', 'true'),
        (goal, 'OwnedEffects::is_ready(ready,observed)', 'true'),
        (goal, ',nr,cr)', ',nl,cl)'),
        (plan['obligations'][0]['existential_reference']['path'], r'\exists integer size,capacity;', 'true ==>'),
        ('theory/heap_reallocation.mlw', '| Integer v -> v', '| Integer v -> 0'),
    )
    for index, (name, before, after) in enumerate(mutations):
        changed = tmp_path/('changed-'+str(index)); shutil.copytree(baseline, changed)
        path = changed/name; original = path.read_text()
        assert before in original
        path.write_text(original.replace(before, after, 1))
        with pytest.raises(ValueError):
            packets.check(changed, elements=elements)
    for index, field in enumerate(('recovery', 'source-admission')):
        changed = tmp_path/('manifest-'+str(index)); shutil.copytree(baseline, changed)
        path = changed/'manifest.json'; content = json.loads(path.read_text())
        if field == 'recovery':
            content['reconstruction']['all_three_stronger_proofs_required'] = False
        else:
            content['source_heap_bridge_established'] = True
        path.write_text(json.dumps(content))
        with pytest.raises(ValueError):
            packets.check(changed, elements=elements)
    for kind in ('missing', 'extra-file', 'empty-directory', 'symlink'):
        changed = tmp_path/kind; shutil.copytree(baseline, changed)
        if kind == 'missing':
            (changed/goal).unlink()
        elif kind == 'extra-file':
            (changed/'unlisted.txt').write_text('unlisted')
        elif kind == 'empty-directory':
            (changed/'unlisted-empty').mkdir()
        else:
            (changed/goal).unlink()
            (changed/goal).symlink_to(baseline/goal)
        with pytest.raises(ValueError):
            packets.check(changed, elements=elements)
    with pytest.raises(ValueError, match='unsupported|proof'):
        packets.check_launch(baseline, elements=elements)
