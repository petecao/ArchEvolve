"""2026-10-16 ET. Root-admitted actual WP gate; no tools probed during collection."""
import hashlib
import json
import os
from pathlib import Path

import pytest
import yaml

from testkit.dx100_selector import prove_selector


@pytest.mark.skipif(os.environ.get('SWDB_DX100_SELECTOR_ACTUAL')!='1', reason='requires coordinated root admission')
@pytest.mark.parametrize('expected', [0, 1], ids=['positive','wrong-enum'])
def test_actual_wp_source_selector_first_gate(tmp_path,expected):
    result,records,entry,marker=prove_selector(tmp_path,expected,actual=True)
    assert result.returncode==0,result.stdout+result.stderr
    record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
    assert not marker.exists(), 'an external stand-in cannot satisfy actual admission'
    assert record['proof_setup_check']['verdict']=='passed'
    assert record['proof_setup_check']['hashes']['dx100_source_selector'] != hashlib.sha256(b'[]').hexdigest()
    settings=record['settings']
    assert settings['verifier_launched'] is True
    flags=settings['flags']
    for flag in ('-wp-rte','-rte-initialized','-wp-no-filter-init','-wp-smoke-tests'):
        assert flag in flags,flags
    assert flags[flags.index('-rte-initialized')+1]=='@all'
    assert flags[flags.index('-wp-cache')+1]=='none'
    assert settings['proof_semantics']['unit_requires']==[] and settings['proof_semantics']['unit_ensures']==[]
    assert_selector_outcome(record,expected)
    for pin in [record['evidence']['adapter_log'], *record['evidence']['reports']]:
        assert hashlib.sha256(Path(pin['path']).read_bytes()).hexdigest()==pin['sha256'],pin
    assert record['pins']['proof_semantics']['sha256']==hashlib.sha256(entry.read_bytes()).hexdigest()


def assert_selector_outcome(record,expected):
    ordinary=[g for g in record['goals'] if not g.get('smoke')]
    smoke=[g for g in record['goals'] if g.get('smoke')]
    assert ordinary and smoke
    assert all(g.get('status')=='valid' for g in smoke),smoke
    assert record.get('failure_class')!='vacuous_pass'
    if expected==0:
        assert record['verdict']=='proven',record.get('unproven_properties')
        assert all(g.get('status')=='valid' for g in ordinary),ordinary
    else:
        assert record['verdict']=='not_proven' and record.get('failure_class') not in ('tool_crash','parse_error','unsupported_construct')
        failed=[g for g in ordinary if g.get('status')!='valid']
        assert failed and all('ensures' in str(g.get('goal','')) for g in failed),failed


@pytest.mark.parametrize('problem', ['vacuous_pass','failed_smoke'])
def test_actual_wrong_enum_acceptance_rejects_vacuity_and_failed_smoke(problem):
    record={'verdict':'not_proven','failure_class':'vacuous_pass' if problem=='vacuous_pass' else 'unknown',
            'goals':[{'goal':'typed_trust_fixture_ensures','status':'unknown','smoke':False},
                     {'goal':'smoke_trust_fixture_entry','status':'unknown' if problem=='failed_smoke' else 'valid','smoke':True}]}
    with pytest.raises(AssertionError):
        assert_selector_outcome(record,1)


@pytest.mark.parametrize('expected',[0,1])
def test_actual_selector_acceptance_keeps_consistent_positive_and_ordinary_wrong_enum_results(expected):
    record={'verdict':'proven' if expected==0 else 'not_proven','failure_class':None if expected==0 else 'unknown',
            'goals':[{'goal':'typed_trust_fixture_ensures','status':'valid' if expected==0 else 'unknown','smoke':False},
                     {'goal':'smoke_trust_fixture_entry','status':'valid','smoke':True}]}
    assert_selector_outcome(record,expected)
