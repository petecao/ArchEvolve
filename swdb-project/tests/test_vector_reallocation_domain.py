"""Qualified vector domain preparation through public prove; 2026-10-16 ET.

No formal execution: unsupported preparation receipts must retain explicit
versioning and caller obligations without treating them as assumptions.
"""
from pathlib import Path
import json
import subprocess
import pytest

from test_standard_range_model import _public_seed


def test_public_qualified_grow_records_allocation_identity_domain_without_claiming_proof(tmp_path):
    _library, prove, marker = _public_seed(tmp_path)
    record = prove('--model', 'std_vector_int_realloc_v3_grow')
    assert record['verdict'] == 'not_proven'
    assert record['failure_class'] == 'unsupported_construct'
    assert not marker.exists()
    domain = record['settings']['vector_reallocation_domain']
    assert domain['version'] == 3
    assert domain['original_member'] == 'std_vector_int_grow'
    assert domain['unary_role'] == 'reallocation eligibility; not exclusive ownership'
    assert domain['caller_discharge'] == 'required; not assumed'
    assert domain['original_contract_proved'] is False
    image = domain['typed_source_image']
    assert image['id'] == 'wp-typed-int32-source-image-1'
    assert image['raw_effective_type_safety_proved'] is False
    assert image['caller_discharge'] == 'source-derived typed int objects; opaque raw storage unsupported'
    assert image['runtime_source_binding'] == 'required selected-tool verification before every launch; not assumed'
    assert record['pins']['vector_reallocation_model']['id'] == 'vector-reallocation-domain-3'
    reports = {r['name']: r for r in record['evidence']['reports']}
    source = Path(reports['vector_reallocation_model']['path']).read_text()
    assert r'\base_addr(v) != \base_addr(v->data)' in source
    assert r'\freeable(v->data)' in source
    assert 'requires std_vector_int_reallocatable_v3(this)' in source
    assert 'std_vector_int_realloc_v3_grow' in source
    assert not any('exclusive ownership' in a['sentence'] for a in record['assumptions'])


def test_public_candidate_retains_original_body_and_defined_native_growth_behavior(tmp_path):
    from swdb import c_lowering
    _library, prove, _marker = _public_seed(tmp_path)
    record = prove('--model', 'std_vector_int_realloc_v3_grow')
    reports = {r['name']: r for r in record['evidence']['reports']}
    original = Path(reports['vector_reallocation_original']['path']).read_text()
    candidate = Path(reports['vector_reallocation_model']['path']).read_text()
    outputs = []
    for label, source, function in [('original', original, 'std_vector_int_grow'),
                                    ('qualified', candidate, 'std_vector_int_realloc_v3_grow')]:
        unit = tmp_path / (label + '.c')
        harness = r'''
#include <stdio.h>
int main(void) {
  const size_t capacities[] = {0,1,4,6};
  const size_t sizes[] = {0,1,2,0};
  for (size_t i=0;i<4;i++) {
    size_t cap=capacities[i], n=sizes[i];
    std_vector_int v={cap ? malloc(cap*sizeof(int)) : NULL,n,cap};
    if(cap && !v.data) return 2;
    for(size_t j=0;j<n;j++) v.data[j]=(int)(7+j);
    GROW(&v,cap+2);
    if(v.size!=n || v.capacity!=cap+2) return 3;
    for(size_t j=0;j<n;j++) if(v.data[j]!=(int)(7+j)) return 4;
    printf("%zu:%zu;",v.size,v.capacity);
    free(v.data);
  }
  return 0;
}
'''
        unit.write_text('#include <stdlib.h>\n#include <stdint.h>\n#include <stddef.h>\n#include <stdbool.h>\n'
                        '#include <limits.h>\n' + source + harness.replace('GROW', function))
        command = [*c_lowering.locate().command, '-x', 'c', '-std=c11', str(unit), '-o', str(tmp_path / label)]
        (tmp_path / (label + '.command.json')).write_text(json.dumps(command, indent=2) + '\n')
        built = subprocess.run(command, capture_output=True, text=True, timeout=30)
        (tmp_path / (label + '.compile.stdout')).write_text(built.stdout)
        (tmp_path / (label + '.compile.stderr')).write_text(built.stderr)
        assert built.returncode == 0, built.stdout + built.stderr
        run = subprocess.run([str(tmp_path / label)], capture_output=True, text=True, timeout=10)
        (tmp_path / (label + '.run.stdout')).write_text(run.stdout)
        (tmp_path / (label + '.run.stderr')).write_text(run.stderr)
        assert run.returncode == 0, run.stdout + run.stderr
        outputs.append(run.stdout)
    assert outputs == ['0:2;1:3;2:6;0:8;'] * 2


def test_public_qualified_grow_exposes_typed_snapshot_copy_obligations_before_any_verifier(tmp_path):
    _library, prove, marker = _public_seed(tmp_path)
    record = prove('--model', 'std_vector_int_realloc_v3_grow')
    assert record['failure_class'] == 'unsupported_construct' and not marker.exists()
    reports = {r['name']: r for r in record['evidence']['reports']}
    plan = json.loads(Path(reports['vector_reallocation_obligations']['path']).read_text())
    assert plan['preparation_only'] is True
    assert plan['caller_premises_added'] == []
    assert plan['typed_memory_role'] == 'explicit typed int source-image domain; source-derived caller discharge required'
    rows = {r['id']: r for r in plan['obligations']}
    assert 'control.grow.premises_feasible' in rows
    assert plan['obligations'][0]['id'] == 'control.grow.premises_feasible'
    assert {'grow.copy.establish', 'grow.copy.step', 'grow.copy.exit'} <= rows.keys()
    assert 'Heap::copy_int(h,b,bo+4*k,f,4*k)' in rows['grow.copy.step']['statement']
    assert 't25v3_copy_inv(entry,' in rows['grow.copy.step']['statement']
    projection = rows['grow.entry.int_projection']['statement']
    assert 'Heap::project_int_region' in projection and 'Heap::bounded_int_values' in projection
    assert 't25_repr(h,r,o,b,bo,s,c)' in projection
    assert all(not r['dependencies'] for r in rows.values()), 'no desired helper lemma is silently assumed'
    theory = Path(reports['vector_reallocation_semantics']['path']).read_text()
    assert 'function load_int' in theory and 'predicate int32_at' in theory
    assert 'function begin_automatic' in theory and 'dynamic = set h.dynamic h.next False' in theory
    assert 'predicate copied_prefix' in theory and 'function end_automatic' in theory
    assert not any(line.strip().startswith(('axiom ', 'lemma ')) for line in theory.splitlines())


def test_public_grow_numeric_packet_guards_the_actual_receiver_and_integer_layout(tmp_path):
    from swdb import c_lowering
    _library, prove, _marker = _public_seed(tmp_path)
    record = prove('--model', 'std_vector_int_realloc_v3_grow')
    reports = {r['name']: r for r in record['evidence']['reports']}
    kernel = Path(reports['vector_reallocation_vc_grow.numeric']['path'])
    text = kernel.read_text()
    assert all(label in text for label in ('mapped receiver extent', 'mapped data field',
                                         'mapped capacity field', 'mapped int alignment'))
    command = [*c_lowering.locate().command, '-x', 'c', '-std=c11', '-fsyntax-only', str(kernel)]
    (tmp_path / 'numeric-compile.command.json').write_text(json.dumps(command, indent=2) + '\n')
    done = subprocess.run(command, capture_output=True, text=True, timeout=30)
    (tmp_path / 'numeric-compile.stdout').write_text(done.stdout)
    (tmp_path / 'numeric-compile.stderr').write_text(done.stderr)
    assert done.returncode == 0, done.stdout + done.stderr


def test_public_reserve_inventory_owns_each_source_event_clause_and_trusted_helper(tmp_path):
    _library, prove, marker = _public_seed(tmp_path)
    record = prove('--model', 'std_vector_int_realloc_v3_reserve')
    reports = {r['name']: r for r in record['evidence']['reports']}
    plan = json.loads(Path(reports['vector_reallocation_obligations']['path']).read_text())
    assert record['failure_class'] == 'unsupported_construct' and not marker.exists()
    inventory = plan['source_inventory']
    assert inventory['unmapped_executable_events'] == []
    assert inventory['unmapped_contract_clauses'] == []
    events = {row['id']: row for row in inventory['events']}
    assert {'grow.allocate', 'grow.loop.init', 'grow.loop.test', 'grow.copy',
            'grow.loop.increment', 'grow.release', 'grow.data.store',
            'grow.capacity.store', 'reserve.branch_and_call'} == events.keys()
    ids = {row['id'] for row in plan['obligations']}
    assert all(set(row['obligations']) <= ids and row['obligations'] for row in events.values())
    assert {row['name'] for row in inventory['trusted_helpers']} == {'swdb_alloc_int', 'swdb_free'}
    assert all(row['role'] == 'existing allocator policy; not a proved model body'
               for row in inventory['trusted_helpers'])
    clauses = inventory['clauses']
    assert {'requires', 'ensures', 'assigns', 'allocates', 'frees',
            'loop invariant', 'loop assigns', 'loop variant'} <= {row['kind'] for row in clauses}
    source = Path(reports['vector_reallocation_model']['path']).read_bytes()
    import hashlib
    for row in [*events.values(), *clauses, *inventory['trusted_helpers']]:
        span = row['source']
        assert hashlib.sha256(source[span['begin']:span['end']]).hexdigest() == span['sha256']
    assert plan['coverage_complete'] is False, 'a source inventory cannot stand in for proof/source-image admission'


@pytest.mark.parametrize('member,groups', [
    ('ctor_count_value', {f'C{i}' for i in range(1, 10)} | {'QC1', 'QC2'}),
    ('reserve', {f'G{i}' for i in range(1, 10)} | {'R1', 'R2', 'R3'}),
    ('dtor', {f'D{i}' for i in range(1, 8)}),
])
def test_public_qualified_model_maps_original_source_and_new_contract_duties(tmp_path, member, groups):
    _library, prove, marker = _public_seed(tmp_path)
    record = prove('--model', 'std_vector_int_realloc_v3_' + member)
    assert record['failure_class'] == 'unsupported_construct' and not marker.exists()
    reports = {r['name']: r for r in record['evidence']['reports']}
    plan = json.loads(Path(reports['vector_reallocation_obligations']['path']).read_text())
    assert groups <= {group for row in plan['obligations'] for group in row['source_groups']}
    assert plan['caller_premises_added'] == []
    source = Path(reports['vector_reallocation_model']['path']).read_bytes()
    import hashlib
    for row in plan['obligations']:
        for area in row['source_spans']:
            assert hashlib.sha256(source[area['begin']:area['end']]).hexdigest() == area['sha256']
    if member == 'ctor_count_value':
        assert any('t25v3_ctor_inv' in (row['statement'] or '') for row in plan['obligations'])
        assert any(row['id'] == 'ctor.qualified.zero_post' for row in plan['obligations'])
        assert any(row['id'] == 'ctor.qualified.positive_post' for row in plan['obligations'])


@pytest.mark.parametrize('member', ['ctor_count_value', 'reserve', 'dtor'])
def test_public_minimal_qualified_composition_has_explicit_contracts_and_pending_discharge(tmp_path, member):
    _library, prove, marker = _public_seed(tmp_path)
    record = prove('--model', 'std_vector_int_realloc_v3_' + member)
    assert record['verdict'] == 'not_proven' and record['failure_class'] == 'unsupported_construct'
    assert not marker.exists()
    report = next(r for r in record['evidence']['reports'] if r['name'] == 'vector_reallocation_model')
    text = Path(report['path']).read_text()
    certificate = record['settings']['vector_reallocation_domain']
    assert certificate['caller_discharge'] == 'required; not assumed'
    functions = {row['original_function'] for row in certificate['executable_bodies']}
    required = {'std_vector_int_' + member, 'swdb_free', 'swdb_alloc_int'}
    if member == 'reserve':
        required.add('std_vector_int_grow')
    assert functions == required
    assert all(row['body_sha256'] == row['inverse_qualified_body_sha256']
               for row in certificate['executable_bodies'])
    if member == 'ctor_count_value':
        assert r'requires \valid(this) && n <=' in text
        assert 'ensures std_vector_int_reallocatable_v3(this)' in text
        assert 'ensures this->capacity == n;' in text
    elif member == 'reserve':
        assert text.count('requires std_vector_int_reallocatable_v3(this)') == 2
        assert 'std_vector_int_realloc_v3_grow(this, n)' in text
        assert 'ensures std_vector_int_reallocatable_v3(this)' in text
    else:
        # Destruction needs no receiver survival, so retain its original broad
        # overlap domain instead of silently requiring reallocation eligibility.
        assert 'requires std_vector_int_valid(this)' in text
        assert 'requires std_vector_int_reallocatable_v3(this)' not in text
        assert certificate['typed_source_image']['applicable'] is False
