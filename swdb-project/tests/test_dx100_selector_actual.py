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
    ordinary=[g for g in record['goals'] if not g.get('smoke')]
    assert ordinary and any(g.get('smoke') for g in record['goals'])
    if expected==0:
        assert record['verdict']=='proven',record.get('unproven_properties')
    else:
        assert record['verdict']=='not_proven' and record.get('failure_class') not in ('tool_crash','parse_error','unsupported_construct')
        failed=[g for g in ordinary if g.get('status')!='valid']
        assert failed and all('ensures' in str(g.get('goal','')) for g in failed),failed
    for pin in [record['evidence']['adapter_log'], *record['evidence']['reports']]:
        assert hashlib.sha256(Path(pin['path']).read_bytes()).hexdigest()==pin['sha256'],pin
    assert record['pins']['proof_semantics']['sha256']==hashlib.sha256(entry.read_bytes()).hexdigest()
