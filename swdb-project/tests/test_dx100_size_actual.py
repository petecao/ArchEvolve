"""2026-10-16 ET. Coordinator-only conditional boot/size gate; no collection probes."""
import hashlib,json,os
from pathlib import Path

import pytest
import yaml

from testkit.dx100_size import prove_size,BOOT_STATEMENT


@pytest.mark.skipif(os.environ.get('SWDB_DX100_SIZE_ACTUAL')!='1',reason='requires coordinated root admission')
@pytest.mark.parametrize('expected',[0,1],ids=['correct-size','wrong-size'])
def test_actual_wp_source_size_first_gate(tmp_path,expected):
    result,records,entry,marker=prove_size(tmp_path,expected,actual=True)
    assert result.returncode==0,result.stdout+result.stderr
    assert not marker.exists(), 'external stand-ins cannot establish actual admission'
    record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
    assert record['proof_setup_check']['verdict']=='passed'
    assert record['proof_setup_check']['hashes']['dx100_size_source']!=hashlib.sha256(b'[]').hexdigest()
    settings=record['settings'];assert settings['verifier_launched'] is True
    flags=settings['flags']
    assert all(flag in flags for flag in ('-wp-rte','-rte-initialized','-wp-no-filter-init','-wp-smoke-tests'))
    assert flags[flags.index('-rte-initialized')+1]=='@all'
    assert flags[flags.index('-wp-cache')+1]=='none'
    semantics=settings['proof_semantics']
    assert semantics['unit_requires']==[] and semantics['unit_ensures']==[]
    assert semantics['entry_projection']['bytes']==64 and semantics['entry_projection']['statement']==BOOT_STATEMENT
    assert len(semantics['source_definitions'])==1
    assert any(a['sentence']==BOOT_STATEMENT for a in record['assumptions'])
    assert not any(a['kind']=='reduction' or 'as if it finished at issue' in a['sentence'] for a in record['assumptions'])
    assert_size_outcome(record,expected)
    for pin in [record['evidence']['adapter_log'],*record['evidence']['reports']]:
        assert hashlib.sha256(Path(pin['path']).read_bytes()).hexdigest()==pin['sha256'],pin
    assert record['pins']['proof_semantics']['sha256']==hashlib.sha256(entry.read_bytes()).hexdigest()


def assert_size_outcome(record,expected):
    ordinary=[g for g in record['goals'] if not g.get('smoke')]
    smoke=[g for g in record['goals'] if g.get('smoke')]
    assert ordinary and smoke
    assert all(g.get('status')=='valid' for g in smoke),smoke
    assert record.get('failure_class')!='vacuous_pass'
    if expected==0:
        assert record['verdict']=='proven'
        assert all(g.get('status')=='valid' for g in ordinary),ordinary
    else:
        # A healthy ordinary nonproof is distinct from a tool/resource failure.
        # The record's best status alone can hide another prover's Failed result.
        assert record['verdict']=='not_proven' and record.get('failure_class') in ('unknown','timeout')
        failed=[g for g in ordinary if g.get('status')!='valid']
        assert failed and all('ensures' in str(g.get('goal','')) for g in failed),failed
        reports=[p for p in record.get('evidence',{}).get('reports',[]) if p.get('name')=='wp_inventory']
        assert len(reports)==1,'negative acceptance needs the complete pinned native inventory'
        data=Path(reports[0]['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==reports[0]['sha256']
        inventory=json.loads(data)
        assert inventory.get('version')=='1' and inventory.get('complete') is True
        rows=inventory.get('goals')
        assert isinstance(rows,list) and rows and all(isinstance(r,dict) for r in rows)
        generated={r.get('goal'):r for r in rows}
        recorded={g.get('goal'):g for g in record['goals']}
        assert None not in generated and len(generated)==len(rows)
        assert None not in recorded and len(recorded)==len(record['goals'])
        assert set(generated)==set(recorded),'unread or missing native goals'
        healthy={'valid','unknown','timeout','stepout','untried'}
        for name,row in generated.items():
            results=row.get('results')
            assert isinstance(results,list) and all(isinstance(r,str) and r in healthy for r in results),row
            assert type(row.get('passed')) is bool and type(row.get('smoke')) is bool
            assert row['smoke']==bool(recorded[name].get('smoke'))
            assert row['passed']==(recorded[name].get('status')=='valid')
            if not row['passed']:
                assert any(r in ('unknown','timeout','stepout') for r in results),'unattempted ordinary goal'


@pytest.mark.skipif(os.environ.get('SWDB_DX100_SIZE_ACTUAL')!='1',reason='requires coordinated root admission')
def test_actual_missing_fresh_certificate_refuses_before_wp(tmp_path):
    result,records,entry,marker=prove_size(tmp_path,0,certificate=False,actual=True)
    assert result.returncode!=0
    assert 'fresh SPD constructor certificate' in result.stderr+result.stdout
    assert not marker.exists()
    assert not list((tmp_path/'runs').glob('**/wp_input.c'))
    assert not list(records.path.glob('proofs/*.yaml'))


@pytest.mark.parametrize('problem',['vacuous_pass','failed_smoke','failed_rte'])
def test_size_actual_wrong_result_control_refuses_inconsistent_or_unrelated_failures(problem):
    record={'verdict':'not_proven','failure_class':'vacuous_pass' if problem=='vacuous_pass' else 'unknown',
        'goals':[{'goal':'typed_trust_fixture_ensures','status':'unknown','smoke':False},
                 {'goal':'smoke_trust_fixture_entry','status':'unknown' if problem=='failed_smoke' else 'valid','smoke':True}]}
    if problem=='failed_rte':record['goals'].append({'goal':'typed_trust_fixture_rte_bounds','status':'unknown','smoke':False})
    with pytest.raises(AssertionError):assert_size_outcome(record,1)
