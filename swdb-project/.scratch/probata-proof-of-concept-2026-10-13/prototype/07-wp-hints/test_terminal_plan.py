"""Method22 public MCP/CLI controls; external executables are controlled fixtures.

Created: 2026-10-15 ET. No real provider or theorem result is produced here.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

HERE = Path(__file__).resolve().parent


def test_scoped_goal_paging_exposes_omitted_premises_without_regeneration(tmp_path):
    import loop as L
    import staged_search as S
    source = L.run_dir(tmp_path, 'initial', (L.STANDIN_DIR / L.UNIT).read_text())
    goal = 'typed_TDStep_ensures_visited_iff_reachable'
    best = {'hints': [], 'dir': str(source), 'n_open': 1, 'n_goals': 1,
            'failing_goals': [{'goal': goal, 'function': 'TDStep', 'kind': 'ensures', 'line': 1}]}
    (tmp_path / 'best.json').write_text(json.dumps(best))
    task = "Goal Post-condition 'visited_iff_reachable' in 'TDStep':\nEARLY PREMISE\n" + 'P' * 18000 + '\nProve: END.'
    task_sha = hashlib.sha256(task.encode()).hexdigest()
    tools = tmp_path / 'tools'; tools.mkdir()
    capture = tmp_path / 'opam-calls'
    opam = tools / 'opam'
    opam.write_text('#!' + sys.executable + '\nfrom pathlib import Path\n' +
                    f"p=Path({str(capture)!r});p.write_text(p.read_text()+'call\\n' if p.exists() else 'call\\n')\n" +
                    f'print({task!r})\n')
    opam.chmod(0o755)
    state = tmp_path / 'tool-r1'; state.mkdir()
    config = {'out': str(tmp_path), 'allowed_kinds': ['loop_assigns'], 'staged_search': None,
              'clock_kind': 'continuous_monotonic', 'clock_info': S.clock_info(), 'method22': True,
              't0': S.clock(), 'budget_min': 60, 'final_reserve_min': 20, 'round': 1,
              'round_timeout': 10, 'mode': 'round-s', 'show_goal': True}
    (state / 'config.json').write_text(json.dumps(config))
    requests = [{'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}]
    for n, args in enumerate([{'goal': goal, 'offset': 0},
                              {'goal': goal, 'offset': 14000, 'task_sha256': task_sha},
                              {'goal': goal, 'offset': 0, 'task_sha256': '0' * 64},
                              {'goal': goal, 'offset': 14000}], 2):
        requests.append({'jsonrpc': '2.0', 'id': n, 'method': 'tools/call',
                         'params': {'name': 'show_goal', 'arguments': args}})
    env = {**os.environ, 'PATH': str(tools) + os.pathsep + os.environ['PATH'], 'PYTHONDONTWRITEBYTECODE': '1'}
    result = subprocess.run([sys.executable, str(HERE / 'edit_tool_mcp.py'), '--state', str(state)],
                            input=''.join(json.dumps(r)+'\n' for r in requests), env=env,
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    replies = [json.loads(line)['result'] for line in result.stdout.splitlines()]
    schema = next(t for t in replies[0]['tools'] if t['name'] == 'show_goal')['inputSchema']
    assert 'offset' in schema['properties'] and 'task_sha256' in schema['properties']
    first, second, rejected = [r['content'][0]['text'] for r in replies[1:4]]
    assert 'refused' in replies[4]['content'][0]['text'].lower()
    assert 'EARLY PREMISE' in first and 'Prove: END.' not in first
    assert 'Prove: END.' in second and 'EARLY PREMISE' not in second
    assert task_sha in first and task_sha in second and 'total_chars' in first
    assert 'refused' in rejected.lower() and 'task' in rejected.lower()
    assert capture.read_text().splitlines() == ['call']
    records = [json.loads(line) for line in (state / 'submissions.jsonl').read_text().splitlines()]
    assert records[0]['source_sha256'] == records[1]['source_sha256']
    assert records[0]['full_task_sha256'] == task_sha
    assert records[0]['offset'] == 0 and records[1]['offset'] == 14000
    assert records[0]['truncated'] is True and records[1]['truncated'] is False


@pytest.mark.parametrize("corroborated,negative_complete,trace_fault", [(None,True,None),(True,True,None),(False,True,None),(True,False,None),(True,True,"drop-attempt")])
def test_terminal_plan_starts_empty_and_checks_full_replay_with_open_diagnostics(tmp_path, corroborated, negative_complete, trace_fault):
    """A complete provider receipt admits one terminal replay despite open10s goals."""
    home = tmp_path / 'home'; tools = tmp_path / 'tools'; tools.mkdir()
    cli = home / '.local/bin/codex'; cli.parent.mkdir(parents=True)
    cli.write_text('#!' + sys.executable + '\n' + '''import json,sys
if '--version' in sys.argv:print('controlled CLI');sys.exit(0)
p=sys.argv[sys.argv.index('--output-last-message')+1]
open(p,'w').write(json.dumps({'ops':[],'notes':'controlled provider'}))
print(json.dumps({'type':'thread.started','thread_id':'fresh22'}))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':7,'output_tokens':3}}))
'''); cli.chmod(0o755)
    if corroborated is not None:
        from test_focused_probe import design
        ops=[{'op':'add','goal':'typed_TDStep_check_hazard_hints_read','id':'',
              'anchor':'loop:k_loop','kind':'loop_assigns','text':'loop assigns k;'}]
        actions=[('record_design',{'relations':design()}),('propose_edit',{'ops':ops})]
        script='#!'+sys.executable+'\nimport json,sys,subprocess\n'
        script+="if '--version' in sys.argv:print('controlled CLI');sys.exit(0)\n"
        script+=f'actions={actions!r}\n'
        script+="setting=next(a for a in sys.argv if a.startswith('mcp_servers.probata.args='))\n"
        script+="args=json.loads(setting.split('=',1)[1])\n"
        script+="requests=[{'jsonrpc':'2.0','id':i,'method':'tools/call','params':{'name':name,'arguments':arguments}} for i,(name,arguments) in enumerate(actions,1)]\n"
        script+="p=subprocess.run([sys.executable,*args],input=''.join(json.dumps(r)+'\\n' for r in requests),text=True,capture_output=True);assert p.returncode==0,p.stderr\n"
        if trace_fault == 'drop-attempt':
            script+="from pathlib import Path\ntrace=Path(json.loads((Path(args[-1])/'config.json').read_text())['out'])/'provider-origin.jsonl'\n"
            script+="trace.write_text(''.join(line+'\\n' for line in trace.read_text().splitlines() if json.loads(line)['event']!='attempt'))\n"
        script+="print(json.dumps({'type':'thread.started','thread_id':'fresh22'}))\n"
        script+="for i,(name,arguments) in enumerate(actions):\n"
        script+=f" if {corroborated!r} or name=='record_design':print(json.dumps({{'type':'item.completed','item':{{'id':str(i),'type':'mcp_tool_call','server':'probata','tool':name,'arguments':arguments,'status':'completed'}}}}))\n"
        script+="open(sys.argv[sys.argv.index('--output-last-message')+1],'w').write(json.dumps({'ops':[],'notes':'controlled provider'}))\n"
        script+="print(json.dumps({'type':'turn.completed','usage':{'input_tokens':7,'output_tokens':3}}))\n"
        cli.write_text(script)
    capture = tmp_path / 'calls.jsonl'; opam = tools / 'opam'
    opam.write_text('#!' + sys.executable + '\n' + f'''import json,pathlib,sys
args=sys.argv[1:];directory=pathlib.Path.cwd()
with open({str(capture)!r},'a') as s:s.write(json.dumps({{'directory':directory.name,'args':args}})+'\\n')
if '-wp' not in args or '-wp-report-json' not in args:sys.exit(0)
positive=directory.name.startswith('final-');negative=directory.name.startswith('negative-')
goals=[{{'goal':'typed_TDStep_check_hazard_hints_read','property':'TDStep_check_hazard_hints_read','function':'TDStep','smoke':False,'passed':positive,'verdict':'valid' if positive else 'unknown'}}]
if '-wp-smoke-tests' in args:goals.append({{'goal':'typed_TDStep_wp_smoke','function':'TDStep','smoke':True,'passed':True,'verdict':'unknown'}})
pathlib.Path('goals.json').write_text(json.dumps(goals))
if '-wp-fct' in args:pathlib.Path('lemmas.json').write_text('[]')
print(f'[wp] {{len(goals)}} goals scheduled')
if negative and not {negative_complete!r}:sys.exit(0)
status='Valid' if positive else 'Unknown'
print("[report] Computing properties status...\\n--- Properties of Function 'TDStep'\\n[ "+status+" ] Assertion 'hazard_hints_read'\\n--- Status Report Summary\\n    1 Total\\n------------------------")
'''); opam.chmod(0o755)
    out = tmp_path / 'run'
    result = subprocess.run([sys.executable, str(HERE / 'edit_loop.py'), '--out', str(out),
                             '--monotone', '--staged-induction', '--design-probes',
                             '--diagnostic-baseline10', '--terminal-full30', '--strategies',
                             '--rounds', '1', '--final-reserve-min', '24'],
                            env={**os.environ, 'HOME': str(home), 'PATH': str(tools)+os.pathsep+os.environ['PATH'],
                                 'PYTHONDONTWRITEBYTECODE':'1'}, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    meta=json.loads((out/'meta.json').read_text());summary=json.loads((out/'summary.json').read_text())
    assert meta['method22']['mechanical_seeds'] is False
    assert meta['method22']['proof_search_stop_min'] == 33
    assert meta['method22']['provider_hard_stop_min'] == 36
    assert meta['method22']['negative_reserve_min'] == 8
    assert 'loop_assigns' in meta['allowed_kinds']
    history=json.loads((out/'history.json').read_text())
    assert history[1]['hints'] == []
    prompt=(out/'codex-r1/workspace/PROMPT.txt').read_text()
    assert 'mechanically generated frame seeds' not in prompt and 'fixed frame seeds' not in prompt
    assert 'merged with the seed' not in prompt
    assert 'independently author loop_assigns' in prompt
    calls=[json.loads(line) for line in capture.read_text().splitlines()]
    finals=[c for c in calls if c['directory'].startswith('final-') and '-wp-report-json' in c['args']]
    assert summary['best_n_open']==1
    if corroborated is False or trace_fault:
        assert len(finals)==0 and summary['provider_origin']['complete'] is False
        assert summary['negative'] is None and not summary['proven']
        return
    assert len(finals)==1 and summary['provider_origin']['complete']
    if corroborated:
        best=json.loads((out/'best.json').read_text())
        assert len(best['hints'])==1 and best['hints'][0]['kind']=='loop_assigns'
        assert best['hints'][0]['provider_origin']['parent_record_sha256'] is None
    assert summary['final']['proven'] is True
    assert summary['provider_usage']['status']=='complete'
    assert summary['negative']['negative_control_passed'] is negative_complete
    assert summary['proven'] is negative_complete and summary['within_budget'] is negative_complete
    assert summary['elapsed_min'] < 60
    assert finals[0]['args'][finals[0]['args'].index('-wp-timeout')+1]=='30'


def test_mcp_records_provider_frame_operations_before_any_candidate_check(tmp_path):
    """No design means no WP, but the actual supplied operation still needs a trace."""
    import loop as L
    import staged_search as S
    import focused_probe as F
    source=L.run_dir(tmp_path,'initial',(L.STANDIN_DIR/L.UNIT).read_text())
    best={'hints':[],'dir':str(source),'n_open':1,'n_goals':1,'failing_goals':[
        {'goal':'typed_TDStep_ensures_queue_kept','function':'TDStep','hint_ids':[],'file':L.UNIT,'line':1,'kind':'ensures','source':'fixture','failure_class':'unknown'}]}
    (tmp_path/'best.json').write_text(json.dumps(best));state=tmp_path/'tool-r1';state.mkdir()
    config={'out':str(tmp_path),'allowed_kinds':['loop_assigns'],'staged_search':F.schedule(0,1980),
            'method20':True,'method22':True,'clock_kind':'continuous_monotonic','clock_info':S.clock_info(),
            't0':S.clock(),'budget_min':60,'final_reserve_min':24,'proof_search_stop_min':33,
            'round':1,'round_timeout':10,'mode':'round-s','show_goal':True}
    (state/'config.json').write_text(json.dumps(config))
    operation={'op':'add','goal':'typed_TDStep_ensures_queue_kept','id':'','anchor':'loop:k_loop',
               'kind':'loop_assigns','text':'loop assigns k;'}
    request={'jsonrpc':'2.0','id':7,'method':'tools/call','params':{'name':'propose_edit','arguments':{'ops':[operation]}}}
    result=subprocess.run([sys.executable,str(HERE/'edit_tool_mcp.py'),'--state',str(state)],
                          input=json.dumps(request)+'\n',capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stderr
    assert 'First record' in json.loads(result.stdout)['result']['content'][0]['text']
    trace=tmp_path/'provider-origin.jsonl'
    assert trace.exists(), 'raw scoped operation must survive an ordinary parser/design refusal'
    rows=[json.loads(line) for line in trace.read_text().splitlines()]
    assert rows[0]['ops']==[operation] and rows[0]['context']['kind']=='mcp'
    assert rows[0]['context']['round']==1 and rows[0]['base_records']==[]
    assert rows[0]['ops_sha256']==hashlib.sha256(json.dumps([operation],sort_keys=True).encode()).hexdigest()
    assert (tmp_path/'best.json').read_text()==json.dumps(best)
    assert not list(tmp_path.glob('attempt-*'))


@pytest.mark.parametrize("restart", [False, True])
def test_provider_frames_and_edits_keep_exact_raw_content_and_parent_lineage(tmp_path, restart):
    import loop as L
    import staged_search as S
    import focused_probe as F
    from test_focused_probe import design
    source=L.run_dir(tmp_path,'initial',(L.STANDIN_DIR/L.UNIT).read_text())
    goal='typed_TDStep_ensures_queue_kept'
    best={'hints':[],'dir':str(source),'n_open':1,'n_goals':1,'failing_goals':[
        {'goal':goal,'function':'TDStep','hint_ids':[],'file':L.UNIT,'line':1,'kind':'ensures','source':'fixture','failure_class':'unknown'}]}
    (tmp_path/'best.json').write_text(json.dumps(best));state=tmp_path/'tool-r1';state.mkdir()
    (state/'config.json').write_text(json.dumps({'out':str(tmp_path),'allowed_kinds':['loop_assigns','assert'],
        'staged_search':F.schedule(0,1980),'method20':True,'method22':True,
        'clock_kind':'continuous_monotonic','clock_info':S.clock_info(),'t0':S.clock(),
        'budget_min':60,'final_reserve_min':24,'proof_search_stop_min':33,'round':1,'round_timeout':10,'mode':'round-s'}))
    frame={'op':'add','goal':goal,'id':'','anchor':'loop:k_loop','kind':'loop_assigns','text':'loop assigns k;'}
    assertion={'op':'add','goal':goal,'id':'','anchor':'stmt:entry','kind':'assert','text':'assert \\true;'}
    edit={'op':'edit','goal':goal,'id':'r1c2h1','anchor':'','kind':'','text':'loop assigns k;'}
    requests=[('record_design',{'relations':design()}),('propose_edit',{'ops':[frame]}),
              ('propose_edit',{'ops':[assertion,edit]})]
    tools=tmp_path/'tools';tools.mkdir();opam=tools/'opam'
    opam.write_text('#!'+sys.executable+'\n'+'''import pathlib,json,sys
args=sys.argv
if '-wp-report-json' not in args:sys.exit(0)
goals=[{'goal':'typed_TDStep_ensures_queue_kept','function':'TDStep','smoke':False,'passed':False,'verdict':'unknown'}]
pathlib.Path('goals.json').write_text(json.dumps(goals))
if '-wp-fct' in args:pathlib.Path('lemmas.json').write_text('[]')
print("[wp] 1 goal scheduled\\n[report] Computing properties status...\\n--- Properties of Function 'TDStep'\\n[ Unknown ] Post-condition 'queue_kept'\\n--- Status Report Summary\\n    1 Total\\n------------------------")
''');opam.chmod(0o755)
    groups=[[request] for request in enumerate(requests,1)] if restart else [list(enumerate(requests,1))]
    replies=[]
    for group in groups:
        result=subprocess.run([sys.executable,str(HERE/'edit_tool_mcp.py'),'--state',str(state)],
            input=''.join(json.dumps({'jsonrpc':'2.0','id':i,'method':'tools/call','params':{'name':name,'arguments':args}})+'\n'
                          for i,(name,args) in group),env={**os.environ,'PATH':str(tools)+os.pathsep+os.environ['PATH']},
            capture_output=True,text=True,timeout=20)
        assert result.returncode==0,result.stderr
        replies.extend(json.loads(line)['result'] for line in result.stdout.splitlines())
        assert not any(r.get('isError') for r in replies),result.stdout
    after=json.loads((tmp_path/'best.json').read_text());assert len(after['hints'])==2
    bykind={h['kind']:h for h in after['hints']}
    assert bykind['loop_assigns']['text']==frame['text']
    assert bykind['assert']['text']==assertion['text']
    assert bykind['loop_assigns']['provider_origin']['operation_index']==1
    assert bykind['loop_assigns']['provider_origin']['parent_record_sha256']
    assert bykind['assert']['provider_origin']['parent_record_sha256'] is None
    assert not any(h['id'].startswith('seed') for h in after['hints'])
    trace=[json.loads(line) for line in (tmp_path/'provider-origin.jsonl').read_text().splitlines()]
    assert [r['ops'] for r in trace if r['event']=='attempt']==[[frame],[assertion,edit]]


import pytest


@pytest.mark.parametrize('receipt,exit_code,deadline,status', [
    ({'input_tokens':7,'output_tokens':3},0,False,'complete'),
    ({'input_tokens':None,'output_tokens':3},0,False,'unavailable'),
    ({'input_tokens':7},0,False,'unavailable'),
    ({'input_tokens':True,'output_tokens':3},0,False,'unavailable'),
    (None,0,False,'unavailable'),
    ({'input_tokens':7,'output_tokens':3},1,False,'partial'),
    ({'input_tokens':7,'output_tokens':3},0,True,'complete'),
])
def test_external_cli_receipts_never_impute_null_or_missing_usage(tmp_path, monkeypatch, receipt, exit_code, deadline, status):
    import edit_loop as D
    import loop as L
    state=tmp_path/'tool';state.mkdir();(state/'config.json').write_text('{"method22":true}')
    cli=tmp_path/'cli'
    event={'type':'turn.completed','usage':receipt} if receipt is not None else {'type':'turn.failed'}
    cli.write_text('#!'+sys.executable+'\nimport sys,json\n'+
        "open(sys.argv[sys.argv.index('--output-last-message')+1],'w').write('{\"ops\":[],\"notes\":\"fixture\"}')\n"+
        f'print(json.dumps({event!r}))\nsys.exit({exit_code})\n')
    cli.chmod(0o755);monkeypatch.setattr(L,'CODEX',str(cli))
    result=D.codex_call(tmp_path,1,'neutral accounting fixture',None,state,10,budget_stop=lambda:deadline)
    assert result['usage_status']==status
    assert result['completion_deadline_met'] is (not deadline)
    if status=='unavailable':assert result['usage']=={}


@pytest.mark.parametrize('forbidden', ['--seeds','--frame-filter','--examples','--round0-from'])
def test_terminal_plan_refuses_seed_or_historical_inputs_before_work(tmp_path, forbidden):
    args=[sys.executable,str(HERE/'edit_loop.py'),'--out',str(tmp_path/'run'),'--monotone',
          '--staged-induction','--design-probes','--diagnostic-baseline10','--terminal-full30',
          '--final-reserve-min','24',forbidden]
    if forbidden=='--round0-from':args.append(str(tmp_path/'old'))
    result=subprocess.run(args,capture_output=True,text=True,timeout=5)
    assert result.returncode==2 and not (tmp_path/'run').exists()
    assert 'error' in result.stderr
