"""Local context-only continuation contracts, 2026-09-27 ET. No provider call."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import pytest
from swdb import yamlio

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=module('context2_prepare',HERE/'prepare.py')
r=module('context2_recipe',HERE/'bfs-provider-context2-20260927.py')


def test_context_is_additive_and_preserves_exact_strategy_and_headers():
    prior=yamlio.load(ROOT/'records/proposals'/(p.PRIOR_ID+'.yaml'))
    build=yamlio.load(ROOT/p.BUILD_PATH);raw=(ROOT/p.SOURCE_PATH).read_bytes()
    new=p.build_request(prior,raw,build);old=prior['request']
    assert new==json.loads((HERE/'prepared/upstream-annotated-context2.proposal.json').read_text())
    assert {k:v for k,v in old.items() if k not in ('id','parameters')}=={k:v for k,v in new.items() if k not in ('id','parameters')}
    assert old['parameters']['read_only_context']==new['parameters']['read_only_context']
    excerpts=new['parameters']['target_execution_clarification']['reference_source_excerpts']
    assert [x['lines'] for x in excerpts]==[[63,64],[366,403]]
    assert 'tilesi[tid]' in excerpts[1]['text'] and 'regs5[tid]' in excerpts[1]['text']
    assert 'tiles6[tid]' not in excerpts[1]['text']


def test_budget_keeps_both_actual_charges_and_prior_floor():
    b=p.budget();assert b['next_allowance_seconds']==1632 and b['initial_floor_remaining_seconds']==1737
    assert b['cumulative_used_seconds']==166.97339878883213
    assert b['remaining_after_prior_floor_seconds']==1632.4462377745658
    d=r.debit(600);assert d['remaining_provider_seconds']==1032 and d['cumulative_used_seconds']==766.9733987888321
    assert r.CONFIG==p.CONFIG and r.PREVIOUS_SECONDS==b['cumulative_used_seconds']


@pytest.mark.parametrize('bad',[True,None,-1,float('nan'),float('inf'),1632.01])
def test_invalid_budget_cannot_reset_allowance(bad):
    with pytest.raises(ValueError):r.debit(bad)


def test_all_prepared_hashes_and_manifest_are_exact():
    for key,suffix in [('PROMPT','prompt.txt'),('REQUEST','proposal.json'),('CONFIG','provider.json')]:
        assert r.sha(r.PREP/('upstream-annotated-context2.'+suffix))==getattr(r,key+'_SHA')
    assert r.sha(r.PREP/'lineage-and-budget.json')==r.LINEAGE_SHA
    assert r.sha(r.RUNTIME_MANIFEST)==r.RUNTIME_MANIFEST_SHA
    assert len((r.PREP/'upstream-annotated-context2.prompt.txt').read_bytes())==523066
    compile(r.PREFLIGHT,'context2-preflight','exec')


def test_one_submit_only_no_repair_or_evaluation():
    tree=ast.parse((HERE/'bfs-provider-context2-20260927.py').read_text())
    calls=[x for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='public']
    commands=[x.args[1].value for x in calls if len(x.args)>1 and isinstance(x.args[1],ast.Constant)]
    assert commands.count('submit')==1 and not {'evaluate','repair','build'} & set(commands)
    assert r.SUP_COMMIT=='8cbfee600f23416a8e9578fa8d3ce3f0e19fced8'
    assert r.RECORDS_COMMIT=='1b2250670077a2f48c7dd8b28333685c4f757982'
    assert r.ORIGIN_COMMIT=='5f1b8028619976b36df5fa24b8aacb91bf488168'
    wrapper=(HERE/'bfs-provider-context2-launch-20260927.sh').read_text()
    assert 'python3.12 -I -B -c' in wrapper and 'wrapper_entry' in wrapper


def test_node0_preflight_refuses_actual_node1(monkeypatch,tmp_path):
    from swdb import profile
    call=next(x for x in ast.walk(ast.parse(r.PREFLIGHT)) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=='_verified_lane')
    claimed=call.args[1].value
    assert claimed=='mbit10-evaluation-node0'
    wrapper=(HERE/'bfs-provider-context2-launch-20260927.sh').read_text()
    assert 'bash "$HELPER" 0 swdb' in wrapper and 'bash "$HELPER" 1 swdb' not in wrapper
    machine={'id':'mbit10','hostname':'mbit10','numa_nodes':[{'node':1,'cpus':'1'}]}
    monkeypatch.setattr(profile,'lane_required',lambda m:True)
    monkeypatch.setenv('LACT_SOCKET_LANE_PID','123')
    monkeypatch.setenv('LACT_SOCKET_LANE_GENERATION','9')
    monkeypatch.setenv('LACT_LEASE_ROOT',str(tmp_path))
    monkeypatch.setattr(profile.os,'getpid',lambda:123)
    monkeypatch.setattr(profile.os,'sched_getaffinity',lambda pid:{1},raising=False)
    monkeypatch.setattr(profile,'_read_proc',lambda pid,name:'socket_lane.sh' if name=='cmdline' else '0 bind:1')
    monkeypatch.setattr(profile.os,'readlink',lambda p:str(tmp_path/'mbit10-evaluation-node1.lease'))
    (tmp_path/'mbit10-evaluation-node1.meta.json').write_text(json.dumps({'state':'held','lease':{'generation':9,'daemon_pid':123}}))
    with pytest.raises(profile.Failure,match='process is confined'):
        profile._verified_lane(machine,claimed)
