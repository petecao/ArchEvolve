"""Source-backed caller obligations at public lower; created 2026-10-16 ET.

These certificates prepare explicit obligations. They grant no ownership fact,
initialization origin or model proof, and never launch a formal verifier.
"""
import hashlib
from pathlib import Path

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
