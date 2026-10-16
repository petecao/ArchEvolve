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
