"""2026-10-16 ET. Inert root-only original-partial u32 register actual pair."""
import hashlib,json,os
from pathlib import Path
import pytest,yaml
from testkit.dx100_register import prove_register,STATEMENT
from testkit.dx100_stream_outcomes import assert_stream_outcome

@pytest.mark.skipif(os.environ.get('SWDB_DX100_REGISTER_ACTUAL')!='1',reason='requires coordinator admission')
@pytest.mark.parametrize('expected',[711,1107],ids=['correct-register-result','wrong-crossregister-result'])
def test_actual_wp_original_partial_register_source_pair(tmp_path,expected):
 result,records,entry,marker=prove_register(tmp_path,expected,actual=True)
 assert result.returncode==0,result.stdout+result.stderr
 assert not marker.exists()
 record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
 assert record['subject']=={'kind':'partial_library_summary','id':'contract.dx100_register_partial_fixture.v1'}
 settings=record['settings']['proof_semantics']
 assert settings['unit_requires']==[]and settings['unit_ensures']==[]
 assert settings['original_assigns_frame']==['__swdb_dx_reg_words[0..1]']
 assert settings['unit_correctness_policy']['semantics']==record['pins']['proof_semantics']
 assert settings['termination_policy']=='conditional normal return; no hardware liveness'
 assert {c['call']for c in settings['source_definitions']}=={'get_reg','set_reg'}
 assert record['proof_setup_check']['verdict']=='passed'and record['proof_setup_check']['hashes']['dx100_register_source']
 assert record['settings']['verifier_launched']is True
 flags=record['settings']['flags']
 assert all(f in flags for f in ['-wp-rte','-rte-initialized','-wp-no-filter-init','-wp-smoke-tests'])
 assert flags[flags.index('-rte-initialized')+1]=='@all'and flags[flags.index('-wp-cache')+1]=='none'
 assert STATEMENT in [a['sentence']for a in record['assumptions']]
 assert not any('as if it finished at issue'in a['sentence']for a in record['assumptions'])
 assert_stream_outcome(record,1 if expected==711 else 0)
 for pin in [record['evidence']['adapter_log'],*record['evidence']['reports']]:assert hashlib.sha256(Path(pin['path']).read_bytes()).hexdigest()==pin['sha256']
 wp=next(p for p in record['evidence']['reports']if p.get('name')=='wp_input')
 text=Path(wp['path']).read_text()
 assert text.count(r'terminates \false;')==3
