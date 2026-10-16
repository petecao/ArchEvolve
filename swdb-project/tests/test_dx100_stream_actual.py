"""2026-10-16 ET. Inert coordinator-only partial stream gate; collection probes no tool."""
import hashlib,json,os
from pathlib import Path
import pytest,yaml
from testkit.dx100_stream import prove_stream,BOOT_STATEMENT,NORMAL_RETURN_STATEMENT,COMPRESSION_STATEMENT
from testkit.dx100_stream_outcomes import assert_stream_outcome

@pytest.mark.skipif(os.environ.get('SWDB_DX100_STREAM_ACTUAL')!='1',reason='requires coordinator admission')
@pytest.mark.parametrize('expected',[1,0],ids=['correct-size','wrong-size'])
def test_actual_wp_source_partial_stream_gate(tmp_path,expected):
    result,records,entry,marker=prove_stream(tmp_path,expected,actual=True)
    assert result.returncode==0,result.stdout+result.stderr
    assert not marker.exists()
    record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
    assert record['subject']=={'kind':'partial_library_summary','id':'contract.dx100_stream_partial_fixture.v1'}
    assert record['proof_setup_check']['verdict']=='passed'
    assert record['proof_setup_check']['hashes']['dx100_stream_source']!=hashlib.sha256(b'[]').hexdigest()
    assert record['settings']['verifier_launched'] is True
    flags=record['settings']['flags']
    assert all(f in flags for f in ('-wp-rte','-rte-initialized','-wp-no-filter-init','-wp-smoke-tests'))
    assert flags[flags.index('-rte-initialized')+1]=='@all' and flags[flags.index('-wp-cache')+1]=='none'
    semantics=record['settings']['proof_semantics']
    assert semantics['unit_requires']==[] and semantics['unit_ensures']==[]
    assert semantics['unit_correctness_policy']['semantics']==record['pins']['proof_semantics']
    assert semantics['termination_policy']=='conditional normal return; no hardware liveness'
    assert 'unverified' in semantics['source_refinement']
    assert {c['call'] for c in semantics['source_definitions']}=={'maa_stream_load','wait_ready','get_tile_size'}
    assumptions=[a['sentence'] for a in record['assumptions']]
    assert all(s in assumptions for s in (BOOT_STATEMENT,NORMAL_RETURN_STATEMENT,COMPRESSION_STATEMENT))
    assert not any(a['kind']=='reduction' or 'as if it finished at issue' in a['sentence'] for a in record['assumptions'])
    assert_stream_outcome(record,expected)
    for pin in [record['evidence']['adapter_log'],*record['evidence']['reports']]:
        assert hashlib.sha256(Path(pin['path']).read_bytes()).hexdigest()==pin['sha256']
    assert record['pins']['proof_semantics']['sha256']==hashlib.sha256(entry.read_bytes()).hexdigest()
    wp=next(p for p in record['evidence']['reports'] if p.get('name')=='wp_input')
    assert Path(wp['path']).read_text().count(r'terminates \false;')==4

@pytest.mark.skipif(os.environ.get('SWDB_DX100_STREAM_ACTUAL')!='1',reason='requires coordinator admission')
def test_actual_missing_isolated_stream_certificate_refuses_before_wp(tmp_path):
    result,records,entry,marker=prove_stream(tmp_path,1,certificate=False,actual=True)
    assert result.returncode!=0 and 'explicit isolated stream entry certificate' in result.stdout+result.stderr
    assert not marker.exists() and not list((tmp_path/'runs').glob('**/wp_input.c'))

@pytest.mark.parametrize('problem',['healthy','solver_error','failed_smoke','native_failed','unknown_native','unread_goal','unattempted'])
def test_stream_negative_health_reads_every_native_result_and_refuses_unhealthy_inventory(tmp_path,problem):
    record={'verdict':'not_proven','failure_class':'solver_error' if problem=='solver_error' else 'unknown',
      'goals':[{'goal':'typed_trust_fixture_ensures','status':'unknown','smoke':False},
               {'goal':'smoke_trust_fixture_entry','status':'unknown' if problem=='failed_smoke' else 'valid','smoke':True}]}
    rows=[{'goal':g['goal'],'smoke':g['smoke'],'passed':g['status']=='valid',
           'results':['unknown'] if g['status']=='unknown' else ['valid']} for g in record['goals']]
    if problem=='native_failed':rows[0]['results']+=['failed']
    elif problem=='unknown_native':rows[0]['results']+=['future-status']
    elif problem=='unread_goal':rows.append({'goal':'unread','smoke':False,'passed':True,'results':['valid']})
    elif problem=='unattempted':rows[0]['results']=['untried']
    inventory=tmp_path/'wp_inventory.json';inventory.write_text(json.dumps({'version':'1','complete':True,'goals':rows}))
    record['evidence']={'reports':[{'name':'wp_inventory','path':str(inventory),'sha256':hashlib.sha256(inventory.read_bytes()).hexdigest()}]}
    if problem=='healthy':assert_stream_outcome(record,0)
    else:
        with pytest.raises(AssertionError):assert_stream_outcome(record,0)


def test_prospective_stream_runner_has_shell_syntax_and_names_only_the_closed_partial_gate():
    import subprocess
    from conftest import REPO
    path=REPO/'.scratch/probata-proof-of-concept-2026-10-13/prototype/28-proof-semantics/run_stream_acceptance.sh'
    checked=subprocess.run(['bash','-n',str(path)],capture_output=True,text=True)
    assert checked.returncode==0,checked.stderr
    text=path.read_text()
    assert 'SWDB_DX100_STREAM_ACTUAL=1' in text
    assert 'test_actual_wp_source_partial_stream_gate' in text
    assert 'SWDB_DX100_SIZE_ACTUAL=1' not in text
