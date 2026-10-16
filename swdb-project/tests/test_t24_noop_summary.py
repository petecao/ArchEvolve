"""No solver: exact no-op exception remains pending an actual unchanged caller."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest
import yaml
from conftest import REPO
from swdb import artifacts
from test_wp_subset import IMPLS, SUMMARIES, _entry, summary_id
from t24_noop_summary import audit_noop


def runner():
    spec = importlib.util.spec_from_file_location('strict_t24_matrix', REPO/'.scratch/probata-proof-of-concept-2026-10-13/prototype/t24-original-matrix.py')
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def fixture(tmp_path):
    name = 'maa_const'; function, clauses, arrays = SUMMARIES[name]
    contract = _entry(summary_id(name), function, 'summaries/summary_impls.cc', IMPLS, clauses, arrays, {'once':'self'})
    goals = [dict(goal='typed_real_'+function+'_'+kind,property=function+'_'+kind,
                  function=function,status='valid',smoke=False) for kind in ('terminates','exits','assigns')]
    inventory = dict(complete=True,goals=[dict(g,passed=True) for g in goals],properties=[
        dict(property=function+'_'+kind,function=function,description=text) for kind,text in
        [('assigns','assigns \\nothing;'),('exits','exits\n\\false'),('terminates','terminates\n\\true')]])
    reports = []
    for name,text in [('wp_goals','{}'),('wp_properties','{}'),('wp_inventory',json.dumps(inventory)),
                      ('wp_normalized','void maa_const_i32(int value, int reg)\n{\n return;\n}\n')]:
        path=tmp_path/name; path.write_text(text)
        import hashlib
        reports.append(dict(name=name,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    pin=dict(id=contract['id'],sha256=artifacts.digest(contract))
    record=dict(id='proof.const',subject=dict(kind='library_summary',id=contract['id']),verdict='proven',
        goals=goals,pins=dict(code=pin,contract=pin),proof_setup_check=dict(verdict='passed'),
        settings=dict(verifier_launched=True,flags=['-wp-fct=maa_const_i32','-wp-rte','-wp-no-filter-init',
          '-wp-smoke-tests','-rte-initialized','@all','-wp-cache','none','-machdep','x86_64']),
        evidence=dict(reports=reports))
    return record,contract,IMPLS


def test_exact_noop_is_provisional_and_old_strict_rejection_is_preserved(tmp_path):
    record,contract,source=fixture(tmp_path)
    case=yaml.safe_load((REPO/'tests/fixtures/proof/regression_corpus/fixture-noop-summary-has-no-generated-smoke.yaml').read_text())['input']
    import hashlib
    assert hashlib.sha256(source.encode()).hexdigest()==case['source_sha256']
    assert artifacts.digest(contract)==case['contract_sha256']
    assert len(record['goals'])==case['ordinary_valid']==3 and case['generated_smoke']==0
    strict=runner().audit
    assert strict(record,'proven')['errors']  # real original policy RED remains reproducible
    checked=audit_noop(record,contract,source,strict)
    assert checked['errors']==[]
    assert checked['generated_smoke']=='not_applicable_exact_noop'
    assert checked['acceptance']=='pending_unchanged_caller_witness'


@pytest.mark.parametrize('change',['requires','body','subject','open_goal','missing_goal','flags','pin','other_function'])
def test_noop_policy_refuses_every_widening(tmp_path,change):
    record,contract,source=fixture(tmp_path)
    if change=='requires':contract['clauses'].append(dict(acsl=dict(text='requires \\false;')))
    elif change=='body':source=source.replace('(void)value;', '*(int*)0 = value;')
    elif change=='subject':record['subject']['id']='contract.unrelated'
    elif change=='open_goal':record['goals'][0]['status']='unknown'
    elif change=='missing_goal':record['goals'].pop()
    elif change=='flags':record['settings']['flags'].remove('-wp-rte')
    elif change=='pin':record['pins']['code']['sha256']='wrong'
    elif change=='other_function':record['settings']['flags'][0]='-wp-fct=other'
    assert audit_noop(record,contract,source,runner().audit)['errors']


def witness_fixture(tmp_path):
    from t24_noop_summary import caller_witness
    record,contract,source=fixture(tmp_path)
    summaries={contract['id']:record, 'contract.fixture_wp24_summary_maa_indirect_load':dict(
        id='proof.indirect',pins=dict(code=dict(sha256='indirect')))}
    record=copy.deepcopy(record);record['id']='proof.caller';record['subject']=dict(kind='candidate_proof_unit',candidate='original-safe',function='swdb_maa_unit')
    record['pins']['code']=dict(id='original-safe',sha256='safe-code')
    record['pins']['contract']=dict(id='contract.fixture_wp24_maa_summary',sha256='59bc854bb0ad4c12b13eaf84dbb3c99dfc3a9aa7f923ce59fdbdf754812c6c22')
    record['pins']['summaries']=[dict(id=cid,proof_record=r['id'],sha256=r['pins']['code']['sha256']) for cid,r in summaries.items()]
    record['goals']=[dict(goal='typed_real_swdb_maa_unit_assigns',property='assigns',function='swdb_maa_unit',status='valid',smoke=False)]
    for name in ('swdb_maa_unit_wp_smoke_default_requires','maa_const_i32_wp_smoke_dead_call_s4','maa_indirect_load_i32_wp_smoke_dead_call_s5'):
        record['goals'].append(dict(goal='typed_real_'+name,property=name,function='swdb_maa_unit',status='valid',smoke=True))
    path=Path(next(r['path'] for r in record['evidence']['reports'] if r['name']=='wp_inventory'))
    path.write_text(json.dumps(dict(complete=True,goals=[dict(g,passed=True) for g in record['goals']])))
    import hashlib
    next(r for r in record['evidence']['reports'] if r['name']=='wp_inventory')['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    def bound(record,summaries,strict):
        return caller_witness(record,summaries,strict,expected_candidate='original-safe',expected_code=dict(id='original-safe',sha256='safe-code'))
    return record,summaries,bound


def test_noop_acceptance_requires_each_actual_original_caller_smoke(tmp_path):
    record,summaries,check=witness_fixture(tmp_path)
    assert check(record,summaries,runner().audit)['errors']==[]


@pytest.mark.parametrize('change',['const_call','indirect_call','precondition_smoke','smoke_open','dependency','contract','contract_hash','candidate','code','inventory'])
def test_caller_witness_fails_closed(tmp_path,change):
    record,summaries,check=witness_fixture(tmp_path)
    if change in ('const_call','indirect_call','precondition_smoke'):
        token={'const_call':'maa_const_i32','indirect_call':'maa_indirect_load_i32','precondition_smoke':'default_requires'}[change]
        record['goals']=[g for g in record['goals'] if token not in g['goal']]
    elif change=='smoke_open':record['goals'][-1]['status']='unknown'
    elif change=='dependency':record['pins']['summaries'][0]['proof_record']='other'
    elif change=='contract':record['pins']['contract']['id']='other'
    elif change=='contract_hash':record['pins']['contract']['sha256']='other'
    elif change=='candidate':record['subject']['candidate']='other'
    elif change=='code':record['pins']['code']['sha256']='other'
    elif change=='inventory':Path(next(r['path'] for r in record['evidence']['reports'] if r['name']=='wp_inventory')).write_text('{}')
    assert check(record,summaries,runner().audit)['errors']


def test_continuation_rejects_output_alias_before_any_tool_or_input_read(tmp_path,monkeypatch):
    import sys
    path=REPO/'.scratch/probata-proof-of-concept-2026-10-13/prototype/t24-remaining-continuation.py'
    spec=importlib.util.spec_from_file_location('noop_continuation',path)
    continuation=importlib.util.module_from_spec(spec);spec.loader.exec_module(continuation)
    monkeypatch.setattr(continuation.matrix,'git',lambda *args:pytest.fail('output alias must refuse before git/tool/source reads'))
    for destination in (REPO/'should-not-create',tmp_path/'old/matrix',tmp_path/'old'):
        monkeypatch.setattr(sys,'argv',[str(path),'--expected-commit','frozen',
            '--from-seed',str(tmp_path/'old/matrix/seed'),'--output',str(destination)])
        with pytest.raises(SystemExit) as error:continuation.main()
        assert error.value.code==2
        assert not destination.exists()
