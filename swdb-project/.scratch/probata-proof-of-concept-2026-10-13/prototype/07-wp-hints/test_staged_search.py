"""Prospective method19 state seam; 2026-10-15 ET. No provider or verifier."""
import json
import pytest
import edit_core as E
from test_debt import candidate


def test_early_inductive_strengthening_can_expose_unit_obligations_without_overwriting_incumbent(tmp_path,monkeypatch):
    E.save_best(tmp_path,candidate())
    original=(tmp_path/'best.json').read_bytes()
    monkeypatch.setattr(E,'ACCEPT',['total'])
    monkeypatch.setattr(E,'TWO_PHASE',[False])
    monkeypatch.setattr(E,'STAGED',[{'start_s':0.0,'stop_s':1800.0}],raising=False)
    result,promoted=E.accept_candidate(tmp_path,candidate(),candidate(unit=4,hint=22,tag='induction'),counted_s=10,remaining_s=1790)
    assert result.startswith('staged') and promoted is None
    assert (tmp_path/'best.json').read_bytes()==original
    assert E.load_working(tmp_path,counted_s=11,remaining_s=1789)['from']=='induction'


@pytest.mark.parametrize('unit,hint,counted,remaining',[
    (10,20,10,1790),  # nine total goals of debt exceeds the fixed eight
    (4,22,1200,600),  # the last search third is recovery-only
    (4,22,10,299),   # no five-minute working lifetime fits before the reserve
])
def test_new_working_candidates_respect_total_cap_and_recovery_window(tmp_path,monkeypatch,unit,hint,counted,remaining):
    E.save_best(tmp_path,candidate())
    original=(tmp_path/'best.json').read_bytes()
    monkeypatch.setattr(E,'ACCEPT',['total'])
    monkeypatch.setattr(E,'TWO_PHASE',[False])
    monkeypatch.setattr(E,'STAGED',[{'start_s':0.0,'stop_s':1800.0}])
    result,promoted=E.accept_candidate(tmp_path,candidate(),candidate(unit,hint),counted_s=counted,remaining_s=remaining)
    assert result.startswith('reverted') and promoted is None
    assert (tmp_path/'best.json').read_bytes()==original and not (tmp_path/'debt.json').exists()


def test_recovery_compares_every_goal_to_the_captured_incumbent_total(tmp_path,monkeypatch):
    E.save_best(tmp_path,candidate())
    monkeypatch.setattr(E,'ACCEPT',['total'])
    monkeypatch.setattr(E,'TWO_PHASE',[False])
    monkeypatch.setattr(E,'STAGED',[{'start_s':0.0,'stop_s':1800.0}])
    E.accept_candidate(tmp_path,candidate(),candidate(unit=4,hint=22),counted_s=10,remaining_s=1790)
    working=E.load_working(tmp_path,counted_s=11,remaining_s=1789)
    E.start_repair(tmp_path,counted_s=11)
    result,promoted=E.accept_candidate(tmp_path,working,candidate(unit=3,hint=18,tag='recovered'),counted_s=12,remaining_s=1788)
    assert result.startswith('accepted') and promoted['n_open']==21
    assert not (tmp_path/'debt.json').exists()
    assert E.load_best(tmp_path)['from']=='incumbent'  # only the caller can commit the returned candidate


def test_method19_clock_does_not_reset_or_move_with_wall_clock_adjustment(monkeypatch):
    import loop as L
    import edit_loop as EL
    import staged_search as S
    monkeypatch.setattr(L,'CLOCK_KIND',['continuous_monotonic'])
    monkeypatch.setattr(S,'clock',lambda:125.0)
    monkeypatch.setattr(L.time,'time',lambda:50000.0)
    monkeypatch.setattr(L,'LOCKWAIT',[5.0])
    assert EL.budget_s(100.0)==20.0


def test_continuous_clock_counts_suspend_jumps_without_decreasing(monkeypatch):
    import staged_search as S
    values=iter([100.0,100.0,1900.0])
    monkeypatch.setattr(S,'_CLOCK',lambda:next(values))
    monkeypatch.setattr(S,'_LAST',None,raising=False)
    assert [S.clock(),S.clock(),S.clock()]==[100.0,100.0,1900.0]


def test_a_backward_clock_read_fails_closed(monkeypatch):
    import staged_search as S
    values=iter([200.0,100.0])
    monkeypatch.setattr(S,'_CLOCK',lambda:next(values))
    monkeypatch.setattr(S,'_LAST',None,raising=False)
    assert S.clock()==200.0
    with pytest.raises(RuntimeError):S.clock()


def test_live_wait_exclusion_requires_the_serialized_clock_kind(tmp_path,monkeypatch):
    import loop as L
    import edit_loop as EL
    monkeypatch.setattr(L,'CLOCK_KIND',['continuous_monotonic'])
    monkeypatch.setattr(L,'clock',lambda:125.0)
    path=tmp_path/'lockwait_live.json'
    path.write_text(json.dumps({'clock':'wall','pending_since':100.0,'settled_s':5.0}))
    assert EL.live_lock_wait(tmp_path)==0.0
    import staged_search as S
    path.write_text(json.dumps({'clock':'continuous_monotonic','clock_info':S.clock_info(),'pending_since':100.0,'settled_s':5.0}))
    assert EL.live_lock_wait(tmp_path)==30.0


def test_driver_counts_the_fresh_baseline_and_keeps_working_hints_out_of_the_summary(tmp_path,monkeypatch):
    import sys
    from types import SimpleNamespace
    import edit_loop as EL
    import loop as L
    import staged_search as S
    clock=[1000.0]
    monkeypatch.setattr(S,'clock',lambda:clock[0])
    monkeypatch.setattr(S,'clock_info',lambda:{'kind':'continuous_monotonic','implementation':'controlled','includes_sleep':True})
    monkeypatch.setattr(L,'CLOCK_KIND',['wall'])
    for name,value in [('STAGED',[None]),('DEBT',[False]),('ACCEPT',['total']),('TWO_PHASE',[False]),('COUNTED_S',[lambda:0]),('SEARCH_REMAINING_S',[lambda:1])]:
        monkeypatch.setattr(E,name,value)
    out=tmp_path/'run'
    monkeypatch.setattr(sys,'argv',['edit_loop.py','--out',str(out),'--monotone','--staged-induction',
        '--seeds','--rounds','1','--final-reserve-min','8'])
    original_run=EL.subprocess.run
    monkeypatch.setattr(EL.subprocess,'run',lambda argv,**kw: SimpleNamespace(stdout='controlled version') if argv[0]==L.CODEX else original_run(argv,**kw))
    def baseline(out,name,standin,hs,rec,**kwargs):
        clock[0]+=12
        d=L.run_dir(out,name,standin);(d/'goals.json').write_text('[]')
        rec.update(outcome='controlled baseline',wp={'goals_sha256':L.sha(d/'goals.json')})
    monkeypatch.setattr(L,'wp_round',baseline)
    def check(out,name,standin,hs,rec,**kwargs):
        clock[0]+=2
        return L.run_dir(out,name,EL.H.merge(standin,hs))
    monkeypatch.setattr(L,'precheck',check)
    def verifier(out,d,*args,**kwargs):
        clock[0]+=3
        p=d/'controlled.log';p.write_text('no verifier launched')
        return p,{'exit_code':0,'wall_s':3,'peak_rss_mb':1,'log_sha256':L.sha(p)}
    monkeypatch.setattr(L,'verifier',verifier)
    failures=candidate()['failing_goals']
    for g in failures:g.update(file=L.UNIT,line=1,kind='assert',source='',failure_class='timeout')
    monkeypatch.setattr(L,'assess_round',lambda *a:{'failing_goals':failures,'n_goals':100})
    def provider(out,r,prompt,resume,state,*args,**kwargs):
        cfg=json.loads((state/'config.json').read_text())
        assert cfg['clock_kind']=='continuous_monotonic' and cfg['t0']==1000.0
        assert cfg['staged_search']['start_s']==17.0
        assert cfg['staged_search']['stop_s']==3120.0
        result,promoted=E.accept_candidate(out,E.load_best(out),candidate(4,22,'working-only'),counted_s=17,remaining_s=3103)
        assert result.startswith('staged') and promoted is None
        clock[0]+=5
        return {'exit':0,'wall_s':5,'usage':{},'error':None,'killed_at_deadline':False,'stop_reason':None,'notes':'controlled','ops':[],'thread':'controlled'}
    monkeypatch.setattr(EL,'codex_call',provider)
    EL.main()
    summary=json.loads((out/'summary.json').read_text())
    meta=json.loads((out/'meta.json').read_text())
    assert summary['elapsed_min']==round(22/60,2) and summary['final'] is None
    assert summary['best_n_open']==21 and not (out/'debt.json').exists()
    assert all(h['id'].startswith('seed') for h in E.load_best(out)['hints'])
    assert meta['method19']['clock']['kind']=='continuous_monotonic'
    assert 'staged_search.py' in meta['harness_sha256'] and 'counted_verifier.py' in meta['harness_sha256']


def test_wait_settlement_requires_exact_clock_and_valid_durations(monkeypatch):
    import staged_search as S
    info={'kind':'continuous_monotonic','implementation':'controlled','includes_sleep':True}
    base={'clock':'continuous_monotonic','clock_info':info,'settled_s':5.0,'pending_since':100.0,'runner_pid':42}
    assert S.wait_seconds(base,info,125.0,runner_pid=42)==30.0
    for changed in ({'clock_info':{**info,'implementation':'other'}},{'clock_info':None},{'clock':'wall'},
                    {'settled_s':float('nan')},{'settled_s':-1},{'pending_since':126.0},{'runner_pid':43}):
        assert S.wait_seconds({**base,**changed},info,125.0,runner_pid=42)==0


def test_changed_stage_context_cannot_reuse_temporary_candidate(tmp_path,monkeypatch):
    E.save_best(tmp_path,candidate())
    monkeypatch.setattr(E,'STAGED',[{'start_s':0.0,'stop_s':1800.0}])
    E.accept_candidate(tmp_path,candidate(),candidate(4,22,'temporary'),counted_s=10,remaining_s=1790)
    E.STAGED[0]={'start_s':1.0,'stop_s':1800.0}
    assert E.load_working(tmp_path,counted_s=11,remaining_s=1789)['from']=='incumbent'
    assert not (tmp_path/'debt.json').exists()


def test_phase_transition_never_resets_working_age_and_late_recovery_cannot_promote(tmp_path,monkeypatch):
    E.save_best(tmp_path,candidate())
    monkeypatch.setattr(E,'STAGED',[{'start_s':0.0,'stop_s':1800.0}])
    E.accept_candidate(tmp_path,candidate(),candidate(4,22,'temporary'),counted_s=1190,remaining_s=610)
    E.start_repair(tmp_path,counted_s=1210)
    E.accept_candidate(tmp_path,candidate(4,22),candidate(4,21,'retained'),counted_s=1211,remaining_s=589)
    assert E.debt_status(tmp_path)['started_s']==1190
    result,promoted=E.accept_candidate(tmp_path,candidate(4,21),candidate(0,0),counted_s=1490,remaining_s=310)
    assert promoted is None and result.startswith('reverted')
    assert E.load_best(tmp_path)['n_open']==21 and not (tmp_path/'debt.json').exists()


@pytest.mark.parametrize('tag', ['missing','wall','wrong_implementation','matched'])
def test_driver_settlement_never_excludes_untagged_or_mixed_clock_waits(tmp_path,monkeypatch,tag):
    import edit_loop as EL
    import loop as L
    import staged_search as S
    monkeypatch.setattr(L,'CLOCK_KIND',['continuous_monotonic'])
    monkeypatch.setattr(L,'LOCKWAIT',[0.0])
    info=S.clock_info()
    rec={'n':1,'tool':'show_best','lockwait_total_s':5.0}
    if tag!='missing':rec.update(clock='wall' if tag=='wall' else 'continuous_monotonic',clock_info=info)
    if tag=='wrong_implementation':rec['clock_info']={**info,'implementation':'other'}
    (tmp_path/'submissions.jsonl').write_text(json.dumps(rec)+'\n')
    EL.read_tool(tmp_path)
    assert L.LOCKWAIT[0]==(5.0 if tag=='matched' else 0.0)


def test_continuous_runner_is_scoped_and_exactly_tagged_before_any_wait_is_excluded(tmp_path,monkeypatch):
    import loop as L
    import staged_search as S
    monkeypatch.setattr(L,'CLOCK_KIND',['continuous_monotonic'])
    monkeypatch.setattr(L,'LOCKWAIT',[0.0])
    monkeypatch.setattr(L,'LIVE_FILE',[str(tmp_path/'live.json')])
    clock=[100.0]
    monkeypatch.setattr(L,'clock',lambda:clock[0])
    launches=[]
    class Runner:
        pid=42
        def __init__(self,argv,**kw):
            launches.append(argv)
            log=tmp_path/'round.log'
            summary={'clock':'continuous_monotonic','clock_info':S.clock_info(),'runner_pid':42,
                'lock_wait_s':5.0,'exit_code':0}
            Path(str(log)+'.summary.json').write_text(json.dumps(summary))
        def poll(self):
            clock[0]=110.0
            return 0
    from pathlib import Path
    monkeypatch.setattr(L.subprocess,'Popen',Runner)
    _,summary=L.verifier(tmp_path,tmp_path,'round')
    assert launches[0][1]==str(L.HERE/'counted_verifier.py')
    assert L.VRUN not in launches[0] and summary['excluded_lock_wait_s']==5.0
    assert L.LOCKWAIT[0]==5.0
    assert json.loads((tmp_path/'live.json').read_text())['pending_since'] is None


def test_method19_pins_the_exact_historical_standin_and_models(tmp_path,monkeypatch):
    import shutil
    import staged_search as S
    import loop as L
    S.check_inputs(L.STANDIN_DIR)
    for path in L.STANDIN_DIR.iterdir():
        if path.is_file():shutil.copy(path,tmp_path/path.name)
    (tmp_path/L.UNIT).write_text((tmp_path/L.UNIT).read_text()+'\n/* changed */\n')
    with pytest.raises(RuntimeError,match='historical'):
        S.check_inputs(tmp_path)


def test_method19_mcp_tool_uses_the_serialized_clock_and_reports_each_phase(tmp_path):
    import subprocess
    import sys
    import loop as L
    import staged_search as S
    info=S.clock_info()
    out=tmp_path/'run';out.mkdir()
    E.save_best(out,{**candidate(0,0),'hints':[]})
    state=tmp_path/'tool';state.mkdir()
    config={'out':str(out),'t0':S.clock()-17,'lockwait_before_s':0,'budget_min':60,'final_reserve_min':8,
        'round_timeout':10,'round':1,'mode':'round','allowed_kinds':['assert'],'show_goal':False,
        'clock_kind':info['kind'],'clock_info':info,'staged_search':{'start_s':17,'stop_s':3120}}
    (state/'config.json').write_text(json.dumps(config))
    message=json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'show_best','arguments':{}}})+'\n'
    process=subprocess.run([sys.executable,str(L.HERE/'edit_tool_mcp.py'),'--state',str(state)],
        input=message,capture_output=True,text=True,timeout=5)
    assert process.returncode==0,process.stderr
    response=json.loads(process.stdout)
    assert response['result']['isError'] is False
    assert 'METHOD19 PHASE 1/3: bridges' in response['result']['content'][0]['text']
    assert not (out/'debt.json').exists()
    config['clock_info']={**info,'implementation':'different'}
    (state/'config.json').write_text(json.dumps(config))
    rejected=subprocess.run([sys.executable,str(L.HERE/'edit_tool_mcp.py'),'--state',str(state)],
        input=message,capture_output=True,text=True,timeout=5)
    assert rejected.returncode!=0 and 'does not match' in rejected.stderr
