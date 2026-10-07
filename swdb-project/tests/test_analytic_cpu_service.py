"""CPU service coverage through frozen public estimates. Updated: 2026-10-06 ET."""
import json

import pytest
import yaml

from conftest import run_swdb
from testkit.analytic import digest, fixture_characterization, target_description, freeze_protocol


from testkit.cpu_service import fact, clock_case


def test_exact_scalar_service_coverage_adds_once_and_clears_its_opaque_call(records, tmp_path):
    data = clock_case(records, tmp_path)
    region = data['regions'][0]
    assert region['overheads'][0]['seconds'] == .4
    assert region['overheads'][0]['inputs']['covered_calls'] == [{'site': 29, 'execution_count': 4}]
    assert region['bounds'][0]['seconds'] == 2 and region['seconds'] == 2.4
    assert data['seconds'] == 2.4 and data['evidence_kind'] == 'contract_fixture'
    checked = records.validate()
    assert checked.returncode == 0, checked.stdout + checked.stderr


@pytest.mark.parametrize('cost, events, body_counted, expected', [
    (None, 4, False, None), (None, 0, False, 2.), (None, 4, True, 2.)])
def test_service_missing_rate_zero_and_counted_body_keep_honest_coverage(records, tmp_path, cost, events, body_counted, expected):
    data = clock_case(records, tmp_path, cost=cost, events=events, body_counted=body_counted)
    assert data['seconds'] == expected
    overhead = data['regions'][0]['overheads'][0]
    if expected is None:
        assert overhead['seconds'] is None and overhead['inputs']['covered_calls'] == []
        assert any(b['model'] == 'unmodeled_calls' for b in data['regions'][0]['bounds'])
    else:
        assert overhead['seconds'] == 0


def test_unsupported_service_selector_never_claims_opaque_body_coverage(records, tmp_path):
    data = clock_case(records, tmp_path, extra_selector={'length_bytes': 16})
    overhead = data['regions'][0]['overheads'][0]
    assert data['seconds'] is None and overhead['inputs']['covered_calls'] == []
    assert 'selector.length_bytes' in overhead['missing']



def test_exact_size_service_bins_require_full_site_coverage(records,tmp_path):
    data=clock_case(records,tmp_path,events=3,shaped=True)
    overhead=data['regions'][0]['overheads'][0]
    assert overhead['seconds']==.5 and data['seconds']==2.5
    assert overhead['inputs']['covered_calls']==[{'site':29,'execution_count':3}]
    assert 'inferred' in ' '.join(overhead['notes'])
    assert records.validate().returncode==0


def test_partial_size_bins_never_waive_the_full_opaque_site(records,tmp_path):
    data=clock_case(records,tmp_path,events=4,shaped=True)
    overhead=data['regions'][0]['overheads'][0]
    assert data['seconds'] is None and overhead['seconds'] is None
    assert overhead['inputs']['covered_calls']==[]
    assert 'call_shape.full_site_count._Znam' in overhead['missing']
    assert any(b['model']=='unmodeled_calls' for b in data['regions'][0]['bounds'])


def test_allocator_regime_cannot_waive_a_bulk_copy_call(records, tmp_path):
    data=clock_case(records,tmp_path,events=3,shaped=True,shaped_name='llvm.memcpy.p0.p0.i64')
    overhead=data['regions'][0]['overheads'][0]
    assert data['seconds'] is None and overhead['seconds'] is None
    assert overhead['inputs']['covered_calls']==[]
    assert 'selector.calls.allocator_abi_bin_kind' in overhead['missing']
    assert any(b['model']=='unmodeled_calls' for b in data['regions'][0]['bounds'])


def test_pinned_service_context_cannot_cover_another_characterization(records,tmp_path):
    data=clock_case(records,tmp_path,extra_selector={'characterization_sha256':'f'*64})
    overhead=data['regions'][0]['overheads'][0]
    assert data['seconds'] is None and overhead['inputs']['covered_calls']==[]
    assert 'service_scope.characterization_sha256' in overhead['missing']


def test_exact_characterization_allowlist_admits_only_named_counted_scope(records,tmp_path):
    from conftest import make_records
    clock_case(records,tmp_path)
    char=records.read('workload_characterizations/fixture.counts.yaml')
    allowed=[{'id':'fixture.counts','sha256':digest(char)},{'id':'fixture.outcome.free.holdout','sha256':'f'*64}]
    def isolated(name,selector):
        directory=tmp_path/name;directory.mkdir()
        return clock_case(make_records(directory),directory,extra_selector=selector)
    known=isolated('allowed',{'characterization_allowlist':allowed})
    assert known['seconds']==2.4
    unmatched=isolated('unmatched',{'characterization_allowlist':[{'id':'other','sha256':digest(char)}]})
    assert unmatched['seconds'] is None
    assert 'service_scope.characterization_allowlist' in unmatched['regions'][0]['overheads'][0]['missing']
    ambiguous=isolated('ambiguous',{'characterization_allowlist':allowed,'characterization_sha256':digest(char)})
    assert ambiguous['seconds'] is None
