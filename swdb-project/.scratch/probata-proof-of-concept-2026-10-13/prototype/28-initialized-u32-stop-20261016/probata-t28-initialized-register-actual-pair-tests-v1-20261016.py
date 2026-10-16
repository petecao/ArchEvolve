"""INERT root-only public initialized-u32 original-partial711/1107 pair.

2026-10-16 ET. This external harness uses existing public fixture builders. It
must never be collected before root source/runtime/guard admission. Test exits
are workflow observations; independent complete cold audit decides acceptance.
"""
import hashlib,json,os
from pathlib import Path
import pytest,yaml
from conftest import fixture_host,checkout_records_unchanged
from testkit.dx100_initialized_register import prove_initialized_register
from test_dx100_initialized_register import assert_original_initialized_register_frame
from swdb.dx100_initialized_register_model import STATEMENT
from swdb.dx100_initialized_register_source import KIND,PARTIAL_CONTRACT,PARTIAL_METHOD,SEMANTICS_ID


@pytest.mark.skipif(os.environ.get('SWDB_DX100_INITIALIZED_REGISTER_ACTUAL')!='1',reason='requires root source/runtime/guard admission')
@pytest.mark.parametrize('expected',[711,1107],ids=['correct-initialized-result','wrong-crossregister-result'])
def test_actual_initialized_u32_original_partial_pair(tmp_path,expected):
 result,records,entry,marker=prove_initialized_register(tmp_path,expected,actual=True)
 assert result.returncode==0,result.stdout+result.stderr
 assert not marker.exists()
 record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
 assert record['subject']=={'kind':'partial_library_summary','id':PARTIAL_CONTRACT}
 assert record['pins']['method_version']['id']==PARTIAL_METHOD
 assert record['pins']['proof_semantics']['id']==SEMANTICS_ID
 settings=record['settings']['proof_semantics']
 assert settings['unit_requires']==[]and settings['unit_ensures']==[]
 assert settings['original_assigns_frame']==['REG_count','SPD_count','region_count','__swdb_dx_reg_words[0..1]']
 assert settings['unit_correctness_policy']=={
  'kind':'partial-normal-return-v1','source_policy':KIND,'semantics':record['pins']['proof_semantics']}
 assert settings['termination_policy']=='conditional normal return; no hardware liveness'
 definitions=settings['source_definitions']
 assert definitions and {c['call']for c in definitions}=={'init_MAA','get_new_reg','get_reg'}
 assert all(c['kind']==KIND for c in definitions)
 assert record['proof_setup_check']['verdict']=='passed'
 assert record['proof_setup_check']['hashes']['dx100_initialized_register_source']
 assert record['settings']['verifier_launched']is True
 flags=record['settings']['flags']
 assert all(f in flags for f in ['-wp-rte','-rte-initialized','-wp-no-filter-init','-wp-smoke-tests'])
 for name,value in [('-rte-initialized','@all'),('-wp-cache','none'),('-wp-par','1'),('-wp-timeout','30')]:
  assert flags.count(name)==1 and flags[flags.index(name)+1]==value
 # Smoke2 is the selected Frama33 source default, independently source/runtime
 # pinned by the entry/root; the public fixture adds no override flag.
 assert '-wp-smoke-timeout'not in flags
 assert set(flags[flags.index('-wp-prover')+1].split(','))=={'z3','cvc5','alt-ergo'}
 sentences=[a['sentence']for a in record['assumptions']]
 assert STATEMENT in sentences
 assert not any('dx_state_initialized'in s or 'as if it finished at issue'in s for s in sentences)
 for evidence in [record['evidence']['adapter_log'],*record['evidence']['reports']]:
  assert hashlib.sha256(Path(evidence['path']).read_bytes()).hexdigest()==evidence['sha256']
 reports={}
 for evidence in record['evidence']['reports']:
  reports.setdefault(evidence.get('name'),[]).append(evidence)
 assert len(reports.get('wp_input',[]))==len(reports.get('wp_inventory',[]))==1
 text=Path(reports['wp_input'][0]['path']).read_text()
 assert_original_initialized_register_frame(text)
 assert r'requires 0 <= REG_count <= 31;'in text
 assert 'get_new_reg_unsigned_int_args1(7'in text and 'get_new_reg_unsigned_int_args1(11'in text
 assert text.count(r'terminates \false;')==3
 inventory=json.loads(Path(reports['wp_inventory'][0]['path']).read_text())
 assert inventory.get('version')=='1'and inventory.get('complete')is True
 rows=inventory.get('goals');goals=record['goals']
 assert isinstance(rows,list)and rows and isinstance(goals,list)and goals
 native={g['goal']:g for g in rows};recorded={g['goal']:g for g in goals}
 assert len(native)==len(rows)and len(recorded)==len(goals)and native.keys()==recorded.keys()
 ordinary=[g for g in goals if not g.get('smoke')];smoke=[g for g in goals if g.get('smoke')]
 assert ordinary and smoke
 for name,row in native.items():
  assert type(row.get('passed'))is bool and type(row.get('smoke'))is bool
  assert row['smoke']==bool(recorded[name].get('smoke'))
  assert row['passed']==(recorded[name].get('status')=='valid')
  results=row.get('results')
  assert isinstance(results,list)and all(r in {'valid','unknown','timeout','stepout','untried','invalid'}for r in results)
  if row['smoke']:
   assert row['passed']and results and all(r in {'unknown','timeout','stepout','invalid'}for r in results)
  elif not row['passed']:
   assert any(r in {'unknown','timeout','stepout'}for r in results)
 if expected==711:
  assert record['verdict']=='proven'and all(g.get('status')=='valid'for g in ordinary)
 else:
  assert record['verdict']=='not_proven'and record.get('failure_class')in {'unknown','timeout'}
  failed=[g for g in ordinary if g.get('status')!='valid']
  assert failed and all('ensures'in g['goal']for g in failed)
 assert record.get('failure_class')!='vacuous_pass'
