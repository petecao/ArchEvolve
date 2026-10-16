"""Source-backed caller obligations at public lower; created 2026-10-16 ET.

These certificates prepare explicit obligations. They grant no ownership fact,
initialization origin or model proof, and never launch a formal verifier.
"""
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from conftest import FIXTURES
from test_c_lowering import lower


SOURCE = FIXTURES / 'proof/vector_reallocation_v3.cc'


def test_public_reserve_caller_records_source_obligations_without_assuming_the_domain(tmp_path):
    result = lower(SOURCE, 'vector_realloc_v3_safe', tmp_path)
    candidate = result['vector_reallocation_candidate']
    assert candidate['verdict'] == 'pending'
    assert candidate['candidate_only'] is True
    assert candidate['source_sha256'] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert candidate['original_caller_premises_added'] == []
    assert candidate['receiver']['name'] == 'v' and candidate['receiver']['storage'] == 'automatic local object'
    assert candidate['alias']['name'] == 'saved'
    assert candidate['reserve_request'] == 'count+1'
    assert candidate['observation'] == 'current buffer'
    assert candidate['guard'] == 'count>0'
    assert {r['call'] for r in candidate['call_obligations']} == {'ctor_count_value', 'data', 'reserve', 'operator_index', 'dtor'}
    assert all(r['status'] == 'pending' for r in candidate['call_obligations'])
    assert candidate['caller_domain'] == 'obligations to prove; not assumptions'
    assert candidate['scalar_read_obligation']['status'] == 'pending'
    assert candidate['scalar_read_obligation']['path'] == 'count>0'
    text = Path(result['c_lowering']['path']).read_text()
    assert candidate['lowered_sha256'] == hashlib.sha256(text.encode()).hexdigest()
    assert 'std_vector_int_reallocatable_v3' not in text, 'the candidate must not silently rewrite original calls'


@pytest.mark.parametrize('function,reserve_request', [
    ('vector_realloc_v3_stale', 'count+1'),
    ('vector_realloc_v3_no_growth', 'count'),
])
def test_public_alias_controls_keep_the_observed_alias_and_growth_request_explicit(tmp_path, function, reserve_request):
    candidate = lower(SOURCE, function, tmp_path)['vector_reallocation_candidate']
    assert candidate['verdict'] == 'pending'
    assert candidate['observation'] == 'captured alias'
    assert candidate['reserve_request'] == reserve_request
    assert candidate['known_origins_granted'] == []
    assert {r['call'] for r in candidate['call_obligations']} == {'ctor_count_value', 'data', 'reserve', 'dtor'}
    assert candidate['scalar_read_obligation']['observed'] == 'captured alias'


def test_public_caller_refuses_signed_count_increment_before_size_conversion(tmp_path):
    source = tmp_path / 'signed.cc'
    source.write_text(SOURCE.read_text().replace('v.reserve((std::size_t)n + 1);', 'v.reserve(n + 1);'))
    candidate = lower(source, 'vector_realloc_v3_safe', tmp_path / 'lower')['vector_reallocation_candidate']
    assert candidate['verdict'] == 'refused'
    assert 'widened count+1' in candidate['reason']


def test_public_caller_source_spans_pin_physical_utf8_bytes(tmp_path):
    source = tmp_path / 'utf8.cc'
    source.write_text('// π is a source comment, not an extra caller premise.\n' + SOURCE.read_text())
    candidate = lower(source, 'vector_realloc_v3_safe', tmp_path / 'lower')['vector_reallocation_candidate']
    assert candidate['verdict'] == 'pending'
    raw = source.read_bytes()
    for row in candidate['call_obligations']:
        area = row['source']
        assert area['sha256'] == hashlib.sha256(raw[area['begin']:area['end']]).hexdigest()


def test_public_caller_retains_crlf_source_identity_and_spans(tmp_path):
    source = tmp_path / 'crlf.cc'
    source.write_bytes(SOURCE.read_bytes().replace(b'\n', b'\r\n'))
    candidate = lower(source, 'vector_realloc_v3_safe', tmp_path / 'lower')['vector_reallocation_candidate']
    assert candidate['verdict'] == 'pending'
    raw = source.read_bytes()
    assert candidate['source_sha256'] == hashlib.sha256(raw).hexdigest()
    for row in candidate['call_obligations']:
        area = row['source']
        assert area['sha256'] == hashlib.sha256(raw[area['begin']:area['end']]).hexdigest()


def test_public_caller_lifetime_plan_derives_local_history_without_global_pointer_premises(tmp_path):
    candidate = lower(SOURCE, 'vector_realloc_v3_safe', tmp_path)['vector_reallocation_candidate']
    plan = candidate['heap_lifetime_plan']
    assert plan['preparation_only'] is True and plan['caller_premises_added'] == []
    assert plan['incoming_pointer_maps_restricted'] is False
    rows = {row['id']: row for row in plan['obligations']}
    assert {'local.begin.feasible', 'local.begin.storage', 'local.begin.history', 'local.end.aliases', 'local.end.frame',
            'caller.data.read', 'caller.guard.empty'} <= rows.keys()
    assert 'Heap::begin_automatic' in rows['local.begin.storage']['statement']
    assert '!Heap::freeable' in rows['local.begin.storage']['statement']
    assert 'Heap::issued(h,b)' in rows['local.begin.history']['statement']
    assert 'Heap::end_automatic' in rows['local.end.aliases']['statement']
    assert all(row['status'] == 'pending' and not row['dependencies'] for row in rows.values())


def test_public_lower_binds_scalar_capture_cleanup_and_unreachable_fallthrough(tmp_path):
    result=lower(SOURCE,'vector_realloc_v3_safe',tmp_path)
    candidate=result['vector_reallocation_candidate']
    lifecycle=candidate['lowered_lifetime']
    assert lifecycle['verdict']=='checked source order; semantic proof pending'
    assert lifecycle['normal_return_cleanup_count']==1
    assert lifecycle['unreachable_fallthrough_cleanup_count']==1
    assert lifecycle['order']==['automatic declaration','constructor','data capture','reserve',
                                'guarded scalar capture','destructor','return scalar','automatic lifetime end']
    assert lifecycle['return_scalar_before_destruction'] is True
    assert lifecycle['raw_alias_rewritten'] is False
    raw=Path(result['c_lowering']['path']).read_bytes()
    for event in lifecycle['events']:
        span=event['lowered_source']
        assert hashlib.sha256(raw[span['begin']:span['end']]).hexdigest()==span['sha256']
    assert candidate['known_origins_granted']==[]


def test_public_caller_lifetime_duties_bind_the_actual_lowered_scope_events(tmp_path):
    result=lower(SOURCE,'vector_realloc_v3_no_growth',tmp_path)
    candidate=result['vector_reallocation_candidate']
    duties={row['id']:row for row in candidate['heap_lifetime_plan']['obligations']}
    assert [event['event'] for event in duties['local.begin.storage']['lowered_events']]==['automatic declaration']
    assert [event['event'] for event in duties['local.end.aliases']['lowered_events']]==[
        'destructor','return scalar','automatic lifetime end']
    assert [event['event'] for event in duties['caller.guard.nonempty']['lowered_events']]==['guarded scalar capture']
    assert all(row['status']=='pending' and not row['dependencies'] for row in duties.values())
    assert candidate['heap_lifetime_plan']['incoming_pointer_maps_restricted'] is False


def test_public_caller_exact_capacity_is_qualified_by_the_actual_cpp17_headers(tmp_path):
    result=lower(SOURCE,'vector_realloc_v3_safe',tmp_path)
    bound=result['vector_reallocation_candidate']['capacity_qualification']
    assert bound['language']=='C++17' and bound['library']=='libc++-22.1.8'
    assert bound['scope']=='implementation-specific count/value capacity; not a universal vector standard theorem'
    assert bound['caller_premises_added']==[]
    assert {row['header_suffix'] for row in bound['sources']}=={
        '__vector/vector.h','__memory/allocate_at_least.h'}
    assert bound['model_postcondition_to_prove']=='capacity == count'
    for row in bound['sources']:
        assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256']


@pytest.mark.parametrize('function', ['vector_realloc_v3_safe', 'vector_realloc_v3_no_growth'])
def test_defined_native_caller_observations_match_original_cpp_after_public_lower(tmp_path, function):
    """Finite source controls only; the stale branch is never executed."""
    from swdb import c_lowering
    result = lower(SOURCE, function, tmp_path / 'lower')
    outputs = []
    for label, standard, path in [('c', 'c11', Path(result['c_lowering']['path'])),
                                   ('cpp', 'c++17', SOURCE)]:
        unit = tmp_path / (label + '.cc')
        unit.write_text('#include <stdlib.h>\n#include <stdio.h>\n' + f'#include "{path}"\n' +
                        'int main(void) { for(int n=0;n<=16;n++) printf("%d\\n",' + function + '(n)); return 0; }\n')
        executable = tmp_path / label
        command = [*c_lowering.locate().command, '-x', 'c' if label == 'c' else 'c++',
                   '-std=' + standard, str(unit), '-o', str(executable)]
        (tmp_path / (label + '.compile.command.json')).write_text(json.dumps(command, indent=2) + '\n')
        built = subprocess.run(command, capture_output=True, text=True, timeout=30)
        (tmp_path / (label + '.compile.stdout')).write_text(built.stdout)
        (tmp_path / (label + '.compile.stderr')).write_text(built.stderr)
        assert built.returncode == 0, built.stdout + built.stderr
        (tmp_path / (label + '.run.command.json')).write_text(json.dumps([str(executable)]) + '\n')
        run = subprocess.run([str(executable)], capture_output=True, text=True, timeout=10)
        (tmp_path / (label + '.run.stdout')).write_text(run.stdout)
        (tmp_path / (label + '.run.stderr')).write_text(run.stderr)
        assert run.returncode == 0, run.stdout + run.stderr
        outputs.append(run.stdout)
    assert outputs[0] == outputs[1] == '0\n' + '7\n' * 16


def test_public_capacity_qualification_refuses_changed_language_macros_or_header_evidence(tmp_path):
    """Public compiler receipt feeds the qualification API; no provenance stand-in."""
    import copy
    from swdb import vector_reallocation_capacity
    result=lower(SOURCE,'vector_realloc_v3_safe',tmp_path/'lower')
    provenance=json.loads(Path(result['anchors']['path']).read_text())['stdlib_provenance']
    assert vector_reallocation_capacity.bind(provenance)['model_postcondition_to_prove']=='capacity == count'
    changes=[]
    wrong_language=copy.deepcopy(provenance)
    wrong_language['context']['command']=[x.replace('-std=c++17','-std=c++23') for x in wrong_language['context']['command']]
    changes.append(wrong_language)
    macro=copy.deepcopy(provenance);macro['context']['command'].append('-D_LIBCPP_STD_VER=23');changes.append(macro)
    omitted=copy.deepcopy(provenance)
    omitted['headers']=[x for x in omitted['headers'] if not x['path'].endswith('/__memory/allocate_at_least.h')]
    changes.append(omitted)
    renamed=copy.deepcopy(provenance)
    row=next(x for x in renamed['headers'] if x['path'].endswith('/__vector/vector.h'))
    row['sha256']='0'*64;changes.append(renamed)
    physical=copy.deepcopy(provenance)
    row=next(x for x in physical['headers'] if x['path'].endswith('/__vector/vector.h'))
    substitute=tmp_path/'changed/__vector/vector.h';substitute.parent.mkdir(parents=True)
    substitute.write_bytes(Path(row['path']).read_bytes()+b'\n// changed header input\n');row['path']=str(substitute)
    changes.append(physical)
    for changed in changes:
        with pytest.raises(ValueError):vector_reallocation_capacity.bind(changed)
