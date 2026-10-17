# PROTOTYPE method18 bounded-debt state seam; created 2026-10-15 ET.
# Deterministic candidate assessments only: no provider, Frama-C or verifier.
import json
import pytest
import edit_core as E


def candidate(unit=2, hint=19, tag='incumbent'):
    goals = ([{'goal':f'typed_TDStep_ensures_u{i}','hint_ids':[]} for i in range(unit)] +
             [{'goal':f'typed_TDStep_assert_h{i}','hint_ids':['agent']} for i in range(hint)])
    return {'hints':[{'id':tag}], 'failing_goals':goals, 'n_open':len(goals), 'from':tag}


@pytest.fixture
def state(tmp_path, monkeypatch):
    monkeypatch.setattr(E,'ACCEPT',['total'])
    monkeypatch.setattr(E,'TWO_PHASE',[False])
    E.save_best(tmp_path,candidate())
    return tmp_path


def test_debt_keeps_checked_incumbent_separate_then_promotes_recovered_rule(state):
    original=(state/'best.json').read_bytes()
    result,promoted=E.accept_candidate(state,candidate(),candidate(hint=23,tag='stage'),counted_s=10,remaining_s=600)
    assert result.startswith('staged') and promoted is None
    assert (state/'best.json').read_bytes()==original
    working=E.load_working(state,counted_s=11,remaining_s=599)
    assert working['from']=='stage'
    E.start_repair(state,counted_s=11)
    result,promoted=E.accept_candidate(state,working,candidate(hint=22,tag='repair'),counted_s=20,remaining_s=590)
    assert result.startswith('staged') and promoted is None
    assert (state/'best.json').read_bytes()==original
    working=E.load_working(state,counted_s=21,remaining_s=589)
    E.start_repair(state,counted_s=21)
    result,promoted=E.accept_candidate(state,working,candidate(hint=19,tag='recovered'),counted_s=30,remaining_s=580)
    assert result.startswith('accepted') and promoted['from']=='recovered'
    E.save_best(state,promoted)
    assert E.load_working(state,counted_s=31,remaining_s=579)['from']=='recovered'
    assert not (state/'debt.json').exists()


@pytest.mark.parametrize('unit,hint',[(3,18),(2,24)])
def test_unit_regression_and_fifth_hint_debt_never_enter_stage(state,unit,hint):
    result,promoted=E.accept_candidate(state,candidate(),candidate(unit,hint),counted_s=10,remaining_s=600)
    assert result.startswith('reverted') and promoted is None
    assert not (state/'debt.json').exists() and E.load_best(state)['from']=='incumbent'


def test_stage_may_not_give_back_a_temporary_unit_gain(state):
    _,promoted=E.accept_candidate(state,candidate(),candidate(unit=1,hint=23),counted_s=10,remaining_s=600)
    assert promoted is None
    working=E.load_working(state,counted_s=11,remaining_s=599)
    E.start_repair(state,counted_s=11)
    result,promoted=E.accept_candidate(state,working,candidate(unit=2,hint=19),counted_s=12,remaining_s=598)
    assert result.startswith('reverted') and promoted is None
    assert E.load_working(state,counted_s=13,remaining_s=597)['failing_goals']==working['failing_goals']


def test_fifth_repair_is_impossible_and_fourth_can_recover(state):
    E.accept_candidate(state,candidate(),candidate(hint=23),counted_s=0,remaining_s=600)
    for n in range(1,4):
        E.start_repair(state,counted_s=n)
        working=E.load_working(state,counted_s=n,remaining_s=600)
        E.accept_candidate(state,working,candidate(hint=22),counted_s=n,remaining_s=600)
    E.start_repair(state,counted_s=4)
    result,promoted=E.accept_candidate(state,candidate(hint=22),candidate(hint=18),counted_s=4,remaining_s=600)
    assert result.startswith('accepted') and promoted['n_open']==20
    assert not (state/'debt.json').exists()


@pytest.mark.parametrize('counted_s,remaining_s,repairs',[(300,300,0),(1,0,0),(4,596,4)])
def test_expired_or_exhausted_stage_rolls_back_without_changing_authoritative_best(state,counted_s,remaining_s,repairs):
    original=(state/'best.json').read_bytes()
    E.accept_candidate(state,candidate(),candidate(hint=23),counted_s=0,remaining_s=600)
    for n in range(repairs):E.start_repair(state,counted_s=n)
    working=E.load_working(state,counted_s=counted_s,remaining_s=remaining_s)
    assert working['from']=='incumbent' and (state/'best.json').read_bytes()==original
    assert not (state/'debt.json').exists()
    events=[json.loads(x) for x in (state/'debt-events.jsonl').read_text().splitlines()]
    assert events[-1]['event']=='rollback'


def test_stage_entry_requires_full_five_minutes_before_final_reserve(state):
    result,promoted=E.accept_candidate(state,candidate(),candidate(hint=23),counted_s=0,remaining_s=299)
    assert result.startswith('reverted') and promoted is None and not (state/'debt.json').exists()


def test_completion_after_time_expiry_cannot_promote_even_a_recovered_candidate(state):
    E.accept_candidate(state,candidate(),candidate(hint=23),counted_s=0,remaining_s=600)
    E.start_repair(state,counted_s=1)
    result,promoted=E.accept_candidate(state,candidate(hint=23),candidate(hint=0),counted_s=300,remaining_s=300)
    assert result.startswith('reverted') and promoted is None
    assert E.load_best(state)['from']=='incumbent' and not (state/'debt.json').exists()


def test_failed_edit_checks_also_exhaust_the_four_repair_slots(state,monkeypatch):
    monkeypatch.setattr(E,'DEBT',[True])
    monkeypatch.setattr(E,'COUNTED_S',[lambda:1.0])
    monkeypatch.setattr(E,'SEARCH_REMAINING_S',[lambda:599.0])
    E.accept_candidate(state,candidate(),candidate(hint=23),counted_s=0,remaining_s=600)
    for n in range(4):
        rec,promoted=E.attempt(state,candidate(),[],f'bad{n}','test','round',10,set())
        assert rec['result']=='edit rejected (edit rules)' and promoted is None
    assert not (state/'debt.json').exists() and E.load_best(state)['from']=='incumbent'


def test_precheck_deadline_refuses_without_starting_a_verifier(state,monkeypatch):
    import loop as L
    def forbidden(*args,**kwargs):raise AssertionError('verifier launched after deadline')
    monkeypatch.setattr(L,'verifier',forbidden)
    rec={}
    assert L.precheck(state,'expired',(L.STANDIN_DIR/L.UNIT).read_text(),[],rec,remaining_s=lambda:0) is None
    assert rec['outcome']=='rejected (search deadline)'


def test_deadline_between_parse_and_goal_generation_keeps_final_reserve(state,monkeypatch):
    import loop as L
    left=[2.0];calls=[]
    def parse_only(out,d,mode,**kwargs):
        calls.append((mode,kwargs['timeout']));left[0]=0
        p=d/'parse.log';p.write_text('')
        return p,{'exit_code':0,'wall_s':2.0}
    monkeypatch.setattr(L,'verifier',parse_only)
    rec={}
    assert L.precheck(state,'parse',(L.STANDIN_DIR/L.UNIT).read_text(),[],rec,remaining_s=lambda:left[0]) is None
    assert calls==[('parse',2.0)] and rec['outcome']=='rejected (search deadline)'


@pytest.mark.parametrize("fresh_baseline", [False, True])
@pytest.mark.parametrize("deadline_flag", [False, True])
def test_loop_summary_and_best_hash_never_report_an_unrecovered_working_set(tmp_path,monkeypatch,fresh_baseline,deadline_flag):
    import hashlib
    import sys
    from types import SimpleNamespace
    import edit_loop as EL
    import loop as L
    out=tmp_path/'run'
    clock=[1000.0]
    monkeypatch.setattr(EL.time,'time',lambda:clock[0])
    monkeypatch.setattr(sys,'argv',['edit_loop.py','--out',str(out),'--monotone','--bounded-debt',
                                  '--rounds','1','--final-reserve-min','8'] + ([] if fresh_baseline else ['--dev-skip-round0']) +
                                  (['--budget-deadline'] if deadline_flag else []))
    monkeypatch.setattr(EL.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='stand-in version'))
    monkeypatch.setattr(L,'precheck',lambda out,name,standin,hs,rec,**kw:L.run_dir(out,name,H.merge(standin,hs)))
    def verifier(out,d,*a,**kw):
        log=d/'standin.log';log.write_text('controlled assessment, no verifier')
        return log,{'exit_code':0,'wall_s':0,'peak_rss_mb':1,'log_sha256':'a'*64}
    monkeypatch.setattr(L,'verifier',verifier)
    if fresh_baseline:
        def no_hint_round(out,name,standin,hs,rec,**kw):
            clock[0]+=12
            d=L.run_dir(out,name,standin);(d/'goals.json').write_text('[]')
            rec.update(outcome='controlled baseline',wp={'goals_sha256':L.sha(d/'goals.json')})
        monkeypatch.setattr(L,'wp_round',no_hint_round)
    baseline=candidate()
    for goal in baseline['failing_goals']:
        goal.update(file='tdstep_standin.c',line=1,kind='assert',source='',failure_class='timeout')
    monkeypatch.setattr(L,'assess_round',lambda *a:{'failing_goals':baseline['failing_goals'],'n_goals':100})
    def provider(out,*a,**k):
        stop=k['budget_stop']
        assert callable(stop), 'method18 requires its counted provider deadline even without the legacy flag'
        saved_clock=clock[0]
        clock[0]=1000+52*60-0.1
        assert stop() is False
        clock[0]=1000+52*60
        assert stop() is True, 'provider must stop at52min; no120s grace may consume the8min reserve'
        clock[0]=saved_clock
        assert a[4] <= 52*60-(12 if fresh_baseline else 0)
        clock[0]+=6
        incumbent=E.load_best(out)
        E.accept_candidate(out,incumbent,candidate(hint=23,tag='unrecovered'),counted_s=0,remaining_s=3600)
        return {'exit':0,'wall_s':0,'usage':{},'thread':'stand-in','killed_at_deadline':False,
                'stop_reason':None,'ops':[],'notes':'controlled staging','error':None}
    monkeypatch.setattr(EL,'codex_call',provider)
    # Restore all module globals changed by this public harness invocation.
    for name in ('DEBT','COUNTED_S','SEARCH_REMAINING_S','ACCEPT','CAP','TWO_PHASE'):
        monkeypatch.setattr(E,name,list(getattr(E,name)))
    import hints as H
    EL.main()
    summary=json.loads((out/'summary.json').read_text())
    best=json.loads((out/'best.json').read_text())
    assert json.loads((out/'meta.json').read_text())['frozen_wp_flags']==['-wp-no-filter-init']
    assert summary['best_n_open']==21 and summary['best_unit_hint_open']==[2,19]
    assert summary['best_hints']==len(best['hints'])==0
    assert summary['best_sha256']==hashlib.sha256((out/'best.json').read_bytes()).hexdigest()
    assert summary['final'] is None and summary['proven'] is False
    assert summary['elapsed_min']==(0.3 if fresh_baseline else 0.1)
    assert not (out/'debt.json').exists()
    assert json.loads((out/'debt-events.jsonl').read_text().splitlines()[-1])['event']=='rollback'


@pytest.mark.parametrize('mode',['parse','wp-gen','round','round-s','wp-smoke-s','print','wp','wp-smoke','wp-rte'])
def test_every_frozen_invocation_disables_initialization_filtering_without_running_frama(tmp_path,mode):
    import os
    import subprocess
    import sys
    import loop as L
    binpath=tmp_path/'bin';binpath.mkdir()
    capture=tmp_path/'argv.json'
    opam=binpath/'opam'
    opam.write_text(f'#!{sys.executable}\nimport json,sys\nfrom pathlib import Path\n'
                    f'Path({str(capture)!r}).write_text(json.dumps(sys.argv[1:]))\n')
    opam.chmod(0o755)
    run=tmp_path/'run';run.mkdir()
    done=subprocess.run(['/bin/sh',str(L.HERE/'wp_run.sh'),mode,str(run),L.UNIT,
                         '-wp-fct TDStep' if mode=='print' else str(tmp_path/'cache'),'1'],
                        env={**os.environ,'PATH':str(binpath)+os.pathsep+os.environ['PATH']},capture_output=True,text=True)
    assert done.returncode==0,done.stdout+done.stderr
    argv=json.loads(capture.read_text())
    assert argv.count('-wp-no-filter-init')==1 and '-wp-filter-init' not in argv,argv
    if mode!='parse':assert '-wp' in argv


@pytest.mark.parametrize('remaining_s',[-1.0,0.0])
def test_fresh_improvement_cannot_promote_after_search_deadline(state,remaining_s):
    original=(state/'best.json').read_bytes()
    result,promoted=E.accept_candidate(state,candidate(),candidate(hint=18),counted_s=3121,remaining_s=remaining_s)
    assert result.startswith('reverted') and promoted is None
    assert (state/'best.json').read_bytes()==original and not (state/'debt.json').exists()


@pytest.mark.parametrize("completion_remaining,expected", [(-0.5, False), (0.0, False), (0.5, True)])
def test_final_round_success_requires_positive_total_time_at_completion(state,monkeypatch,completion_remaining,expected):
    import loop as L
    remaining=[1.0]
    d=L.run_dir(state,'late-final',(L.STANDIN_DIR/L.UNIT).read_text())
    def verifier(*args,**kwargs):
        remaining[0]=completion_remaining
        log=d/'wp-smoke.log';log.write_text('controlled all-goal result')
        return log,{'exit_code':0,'wall_s':1.5,'peak_rss_mb':1,'log_sha256':'a'*64}
    monkeypatch.setattr(L,'verifier',verifier)
    monkeypatch.setattr(L,'assess',lambda *args:{'ok':True,'n_goals':1,'failing_goals':[],
                                              'problems':[],'smoke_failures':[]})
    rec={}
    assessed=L.wp_round(state,'late-final',(L.STANDIN_DIR/L.UNIT).read_text(),[],rec,d=d,
                        remaining_s=lambda:remaining[0])
    assert rec['proven'] is expected and assessed['ok'] is expected
    if not expected:assert 'deadline' in rec['outcome']
