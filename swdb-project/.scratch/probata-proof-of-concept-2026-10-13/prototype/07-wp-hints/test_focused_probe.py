"""Method20 diagnostic tool/policy seam, 2026-10-15 ET; no verifier/provider."""
import copy
import json
from pathlib import Path
import pytest
import focused_probe as F
import staged_search as S


def design():
    return {name: {'relation':'fresh author relation', 'scope':'source scope',
                   'witness':'fresh author witness and lifetime', 'invalidated_by':'source mutation'}
            for name in F.OBJECTIVES}


def test_design_is_explicit_and_never_publishes_hints(tmp_path):
    (tmp_path/'best.json').write_text('checked incumbent')
    (tmp_path/'debt.json').write_text('temporary candidate')
    before={p.name:p.read_bytes() for p in tmp_path.iterdir()}
    report=F.record_design(tmp_path, design())
    assert report['authority']=='design_only' and report['promoted'] is False
    assert all((tmp_path/n).read_bytes()==v for n,v in before.items())
    assert F.has_design(tmp_path)


@pytest.mark.parametrize('field',['cas_history','queue_phase','consumed_prefix'])
def test_design_requires_each_semantic_objective(tmp_path, field):
    value=design();del value[field]
    with pytest.raises(ValueError):F.record_design(tmp_path,value)
    assert not F.has_design(tmp_path)


def test_method20_phase_weights_and_debt_clock_are_prospective():
    plan=F.schedule(100,1100)
    assert [S.phase(plan,t)['name'] for t in (100,649,650,999,1000)]==[
        'design_bridges','design_bridges','consumption','consumption','recovery']
    assert S.phase(plan,650)['start_s']==650
    assert S.phase(plan,1000)['end_s']==1100
    assert S.TOTAL_DEBT==8 and S.SECONDS==300 and S.REPAIRS==4


@pytest.mark.parametrize('goal',[
 {'goal':'typed_TDStep_wp_smoke_x','smoke':True,'function':'TDStep'},
 {'goal':'typed_TDStep_wp_smoke_x','smoke':False,'function':'TDStep'},
 {'goal':'typed_lemma_injected','smoke':False,'function':None},
 {'goal':'-wp-skip-fct=TDStep','smoke':False,'function':'TDStep'},
])
def test_smoke_lemma_and_flag_targets_are_refused(goal):
    with pytest.raises(ValueError):F.selection(goal)


def test_selection_comes_from_a_closed_goal_class_not_provider_flags():
    assert F.selection({'goal':'typed_TDStep_assert_cut','function':'TDStep','smoke':False})==(
        '-wp-fct TDStep -wp-prop=@assert')


def test_diagnostic_result_never_scores_even_when_every_selected_goal_is_valid():
    rows=[{'goal':'typed_TDStep_assert_cut','passed':True,'smoke':False}]
    report=F.diagnostic(rows, rows[0]['goal'], ['unchecked_hint'])
    assert report['authority']=='diagnostic_only' and report['promoted'] is False
    assert report['selected'][0]['passed'] is True
    assert report['unselected_obligations']==['unchecked_hint']
    assert not {'proven','n_open_after','score','milestone'} & report.keys()


@pytest.fixture
def probe(tmp_path,monkeypatch):
    import loop as L
    out=tmp_path
    original=(L.STANDIN_DIR/L.UNIT).read_text()
    baseline=L.run_dir(out,'incumbent',original)
    (out/'best.json').write_text('{"n_open":9}')
    (out/'debt.json').write_text('{"started_s":5,"repairs":2}')
    (out/'debt-events.jsonl').write_text('{"event":"enter"}\n')
    best={'hints':[],'dir':str(baseline)}
    target={'goal':'typed_TDStep_assert_local','function':'TDStep','passed':False,'smoke':False,'verdict':'unknown'}
    cut={'goal':'typed_TDStep_loop_invariant_fresh_preserved','function':'TDStep','passed':False,'smoke':False,'verdict':'unknown'}
    elapsed=[0]
    def verifier(out,directory,mode,**kw):
        elapsed[0]+=10
        rows=[target,cut] if mode=='probe-gen' else [{**target,'passed':True,'verdict':'valid'}]
        (directory/'goals.json').write_text(json.dumps(rows))
        if mode=='probe-gen':(directory/'lemmas.json').write_text('[]')
        log=directory/'run.log';log.write_text('test protocol output')
        return log,{'exit_code':0}
    monkeypatch.setattr(L,'verifier',verifier)
    monkeypatch.setattr(S,'check_run',lambda *a,**kw:{'n_goals':2})
    return out,best,target,cut,elapsed


def test_probe_preserves_incumbent_and_debt_while_every_second_counts(probe):
    out,best,target,cut,elapsed=probe
    names=('best.json','debt.json','debt-events.jsonl')
    before={n:(out/n).read_bytes() for n in names}
    report=F.run(out,best,target['goal'],'one',remaining_s=lambda:600-elapsed[0],round_timeout=5)
    assert elapsed[0]==20
    assert {n:(out/n).read_bytes() for n in names}==before
    assert report['authority']=='diagnostic_only' and not report['promoted']
    assert report['unselected_obligations']==[cut['goal']]


def test_absent_fresh_target_stops_before_prover(probe):
    out,best,target,cut,elapsed=probe
    with pytest.raises(ValueError,match='fresh full inventory'):
        F.run(out,best,'typed_TDStep_assert_stale','absent',remaining_s=lambda:600,round_timeout=5)
    assert elapsed[0]==10 and not (out/'probe-absent').exists()


def test_deadline_between_generation_and_prover_never_launches_solver(probe):
    out,best,target,cut,elapsed=probe
    with pytest.raises(ValueError,match='deadline'):
        F.run(out,best,target['goal'],'late',remaining_s=lambda:10-elapsed[0],round_timeout=5)
    assert elapsed[0]==10 and not (out/'probe-late').exists()


def test_tampered_working_source_is_refused_before_verification(probe):
    import loop as L
    out,best,target,cut,elapsed=probe
    (Path(best['dir'])/L.UNIT).write_text('changed source')
    with pytest.raises(ValueError,match='recorded source'):
        F.run(out,best,target['goal'],'changed',remaining_s=lambda:600,round_timeout=5)
    assert elapsed[0]==0


def test_independent_state_mutation_is_detected_before_diagnostic_return(probe,monkeypatch):
    import loop as L
    out,best,target,cut,elapsed=probe
    original=L.verifier
    def corrupt(*args,**kwargs):
        result=original(*args,**kwargs)
        (out/'best.json').write_text('forged promotion')
        return result
    monkeypatch.setattr(L,'verifier',corrupt)
    with pytest.raises(RuntimeError,match='protected'):
        F.run(out,best,target['goal'],'fault',remaining_s=lambda:600,round_timeout=5)


def test_method20_prompt_never_calls_filtered_results_milestones():
    import edit_loop
    prompt=F.rule(edit_loop.STAGED_RULE)
    assert '55%' in prompt and '35%' in prompt and '10%' in prompt
    assert 'third' not in prompt
    assert 'diagnostic only' in prompt and 'cannot score, promote, establish a milestone' in prompt


def test_mcp_requires_fresh_design_before_any_proposal_without_touching_incumbent(tmp_path):
    import subprocess,sys
    import loop as L
    source=L.run_dir(tmp_path,'seed',(L.STANDIN_DIR/L.UNIT).read_text())
    best={'hints':[],'dir':str(source),'n_open':1,'n_goals':1,'failing_goals':[
        {'goal':'typed_TDStep_ensures_queue_kept','function':'TDStep','hint_ids':[], 'file':'tdstep_standin.c','line':1,'kind':'ensures','source':'fixture','failure_class':'unknown'}]}
    (tmp_path/'best.json').write_text(json.dumps(best))
    before=(tmp_path/'best.json').read_bytes()
    state=tmp_path/'tool-r1';state.mkdir()
    config={'out':str(tmp_path),'allowed_kinds':[],'staged_search':F.schedule(0,3120),
            'method20':True,'clock_kind':'continuous_monotonic','clock_info':S.clock_info(),
            't0':S.clock(),'budget_min':60,'final_reserve_min':8,'round':1,'round_timeout':5,
            'mode':'round-s','show_goal':True}
    (state/'config.json').write_text(json.dumps(config))
    requests=[{'jsonrpc':'2.0','id':1,'method':'tools/list'},
        {'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'propose_edit','arguments':{'ops':[]}}},
        {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'record_design','arguments':{'relations':design()}}}]
    process=subprocess.run([sys.executable,str(Path(F.__file__).with_name('edit_tool_mcp.py')),'--state',str(state)],
        input=''.join(json.dumps(r)+'\n' for r in requests),text=True,capture_output=True,timeout=10)
    assert process.returncode==0,process.stderr
    replies=[json.loads(line) for line in process.stdout.splitlines()]
    assert {'record_design','focused_probe'}<={t['name'] for t in replies[0]['result']['tools']}
    assert 'First record' in replies[1]['result']['content'][0]['text']
    assert F.has_design(tmp_path) and (tmp_path/'best.json').read_bytes()==before
    assert not list(tmp_path.glob('attempt-*'))


def test_filtered_results_never_enter_promotion_or_wp_attempt_counts(tmp_path,monkeypatch):
    import edit_loop
    import loop as L
    monkeypatch.setattr(L,'CLOCK_KIND',['wall'])
    monkeypatch.setattr(L,'LOCKWAIT',[0])
    row={'n':1,'tool':'focused_probe','result':'diagnostic only','promoted':False,'lockwait_total_s':0}
    (tmp_path/'submissions.jsonl').write_text(json.dumps(row)+'\n')
    result=edit_loop.read_tool(tmp_path)
    assert result['calls']==1 and result['accepted']==0 and result['staged']==0 and result['propose_calls']==0


def test_single_scheduled_diagnostic_keeps_exact_inventory_completeness(tmp_path):
    from test_staged_search import _completed_reports
    log=_completed_reports(tmp_path)
    log.write_text(log.read_text().replace('1 goals scheduled','1 goal scheduled'))
    assert S.check_run(tmp_path,log,round_mode=False)['n_goals']==1
    log.write_text(log.read_text().replace('1 goal scheduled','2 goals scheduled'))
    with pytest.raises(RuntimeError,match='inventory'):
        S.check_run(tmp_path,log,round_mode=False)


def test_every_proposal_route_requires_design_and_rejected_repair_still_ages(tmp_path,monkeypatch):
    import edit_core as E
    import loop as L
    from test_staged_search import candidate
    incumbent=candidate(2,1)
    E.save_best(tmp_path,incumbent)
    monkeypatch.setattr(E,'DEBT',[True]);monkeypatch.setattr(E,'STAGED',[F.schedule(0,1000)])
    monkeypatch.setattr(E,'COUNTED_S',[lambda:10]);monkeypatch.setattr(E,'SEARCH_REMAINING_S',[lambda:900])
    E.accept_candidate(tmp_path,incumbent,candidate(3,1),counted_s=5,remaining_s=995)
    before=(tmp_path/'best.json').read_bytes()
    monkeypatch.setattr(L,'verifier',lambda *a,**kw:pytest.fail('design-free proposal reached verifier'))
    rec,promoted=E.attempt(tmp_path,incumbent,[],'final','fresh provider final answer','round-s',5,set())
    assert promoted is None and 'design' in rec['result']
    assert (tmp_path/'best.json').read_bytes()==before
    assert E.debt_status(tmp_path)['started_s']==5 and E.debt_status(tmp_path)['repairs']==1


@pytest.mark.parametrize('resume', [None, 'private-existing-read-only-session'])
@pytest.mark.parametrize('method20', [False, True])
def test_cli_approves_only_authorized_method20_tools_without_widening_sandbox(tmp_path,monkeypatch,resume,method20):
    """Observe the actual provider argv at its external CLI boundary; no provider."""
    import sys
    import edit_loop
    import loop as L
    state=tmp_path/'state';state.mkdir();(state/'config.json').write_text(json.dumps({'method20':method20}))
    captured=tmp_path/'argv.json';cli=tmp_path/'neutral-cli'
    cli.write_text('#!'+sys.executable+'\nimport json,sys\nfrom pathlib import Path\n'+
        f'Path({str(captured)!r}).write_text(json.dumps(sys.argv[1:]))\n'+
        'sys.stdin.read()\nPath(sys.argv[sys.argv.index("--output-last-message")+1]).write_text(json.dumps({"ops":[],"notes":"neutral"}))\n'+
        'print(json.dumps({"type":"thread.started","thread_id":"private-neutral-session"}))\n'+
        'print(json.dumps({"type":"turn.completed","usage":{}}))\n');cli.chmod(0o755)
    monkeypatch.setattr(L,'CODEX',str(cli))
    result=edit_loop.codex_call(tmp_path,1,'neutral routing probe',resume,state,2)
    assert result['exit']==0 and result['ops']==[]
    argv=json.loads(captured.read_text());settings=[argv[i+1] for i,x in enumerate(argv[:-1]) if x=='-c']
    approvals={x for x in settings if '.approval_mode=' in x}
    expected={'mcp_servers.probata.tools.record_design.approval_mode="approve"',
              'mcp_servers.probata.tools.focused_probe.approval_mode="approve"'} if method20 else set()
    assert approvals==expected
    assert '--dangerously-bypass-approvals-and-sandbox' not in argv and '--approve-for-me' not in argv
    if resume is None:assert argv[argv.index('-s')+1]=='read-only'
    assert argv[argv.index('--disable')+1]=='shell_tool'
