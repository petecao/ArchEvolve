"""2026-10-16 ET. Inert root-only original-total counter allocation actual pair."""
import hashlib,json,os
from pathlib import Path
import pytest,yaml
from testkit.dx100_allocation import prove_allocation,STATEMENT
from testkit.dx100_stream_outcomes import assert_stream_outcome

@pytest.mark.skipif(os.environ.get('SWDB_DX100_ALLOCATION_ACTUAL')!='1',reason='requires coordinator admission')
@pytest.mark.parametrize('expected',[102,101],ids=['correct-counter-result','wrong-counter-result'])
def test_actual_original_total_software_allocator_source_pair(tmp_path,expected):
 result,records,entry,marker=prove_allocation(tmp_path,expected,actual=True)
 assert result.returncode==0,result.stdout+result.stderr
 assert not marker.exists()
 record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
 assert record['subject']=={'kind':'library_summary','id':'contract.dx100_software_allocation_fixture.v1'}
 settings=record['settings']['proof_semantics']
 assert settings['correctness_scope']=='original total software-counter unit; no hardware progress premise'
 assert settings['unit_requires']==[]and settings['unit_ensures']==[]
 assert settings['original_assigns_frame']==['REG_count','SPD_count','region_count']
 assert {c['call']for c in settings['source_definitions']}=={'init_MAA','get_new_tile','get_new_reg'}
 assert record['proof_setup_check']['verdict']=='passed'and record['proof_setup_check']['hashes']['dx100_allocation_source']
 assert record['settings']['verifier_launched']is True
 flags=record['settings']['flags']
 assert all(f in flags for f in ['-wp-rte','-rte-initialized','-wp-no-filter-init','-wp-smoke-tests'])
 assert flags[flags.index('-rte-initialized')+1]=='@all'and flags[flags.index('-wp-cache')+1]=='none'
 assert STATEMENT in [a['sentence']for a in record['assumptions']]
 assert not any('as if it finished at issue'in a['sentence']for a in record['assumptions'])
 assert_stream_outcome(record,1 if expected==102 else 0)
 for p in [record['evidence']['adapter_log'],*record['evidence']['reports']]:assert hashlib.sha256(Path(p['path']).read_bytes()).hexdigest()==p['sha256']
 wp=next(p for p in record['evidence']['reports']if p.get('name')=='wp_input')
 assert r'terminates \false'not in Path(wp['path']).read_text()
