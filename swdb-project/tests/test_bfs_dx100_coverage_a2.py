"""Corrective a2 contract tests; fixtures are not coverage. Date: 2026-09-26 ET."""
import copy
from datetime import timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from scripts import bfs_dx100_coverage_a2 as case
from swdb import artifacts
from test_bfs_dx100_coverage_execution import compiled_fixture, coverage_fixture, write_ref
from testkit.native_pilot import build_reader_fixture


def plan():
    return json.loads(case.PLAN.read_text())


def test_fixed_plan_and_a1_default_helpers_are_unchanged(tmp_path):
    value = case.validate_plan(plan())
    graph = case.original.graph_case.generate(tmp_path/'graph')
    case.graph_identity(graph,value)
    assert value['bounds']['outer_seconds']==3600 and value['bounds']['work_seconds']==3570
    assert value['window']['latest_start']=='2026-09-26T21:00:00-04:00'
    old = case.original.compile_request(); new=case.original.compile_request(run_id=case.RUN_ID)
    assert old['id']==case.original.RUN_ID+'.compile'
    assert {k:v for k,v in old.items() if k!='id'}=={k:v for k,v in new.items() if k!='id'}
    compiled=compiled_fixture();compiled.update(id=case.RUN_ID+'.compile',request=new)
    workload={'id':'fixture.workload','requested_id':case.RUN_ID+'.workload',
              'definition':{'canonical_sha256':graph['canonical_sha256'],'sources':[0]}}
    request=case.original.execution_request(compiled,workload,graph,run_id=case.RUN_ID)
    assert request['id']==case.RUN_ID+'.execute' and request['verification']['coverage'] is True
    assert request['configuration']=={'mode':'MAA','l3_size_mb':8,'l3_assoc':16,'tile_elements':16384}
    assert request['budget']=={'total_seconds':3100,'memory_gib':48,'storage_gib':4,'checkpoint_seconds':300,'run_seconds':2700}
    with pytest.raises(ValueError,match='fresh exact author'):
        case.original.execution_request(compiled,workload,graph)


@pytest.mark.parametrize('fault',['window','graph','rss','budget','candidate','native_commit','native_outcome'])
def test_resealed_prospective_scope_cannot_change(fault):
    value=plan()
    if fault=='window':value['window']['absolute_end']='2026-09-27T00:00:00-04:00'
    elif fault=='graph':value['graph']['vertices']-=1
    elif fault=='rss':value['rss_source']='VmRSS'
    elif fault=='budget':value['bounds']['outer_seconds']+=1
    elif fault=='candidate':value['compile_request']['candidate']='rewritten'
    elif fault=='native_commit':value['native']['commit']='0'*40
    else:value['native']['outcomes']=['complete']
    with pytest.raises(ValueError,match='prospective'):case.validate_plan(value)


def test_optional_case_identity_retains_real_trace_and_verifier_checks(tmp_path,monkeypatch):
    data,request,graph,log=coverage_fixture(tmp_path)
    data['id']=request['id']=case.RUN_ID+'.execute'
    monkeypatch.setattr(case.original.dx100_witness,'validate_completed_witness',lambda *a,**kw:None)
    assert case.original.validate_coverage(data,request,graph,run_id=case.RUN_ID)['full_tiles']['count']==1
    text=log.read_text();log.write_text('\n'.join(line for line in text.splitlines() if 'tile size: 16384' not in line)+'\n')
    check=data['correctness']['checks'][0];check['output']=case.ref(log)
    observed=case.original.dx100_coverage.observe(log,{'simTicks':'100','finalTick':'200'},16384)
    check['coverage']={**observed,'accelerator_executed':True}
    with pytest.raises(ValueError,match='coverage is incomplete'):
        case.original.validate_coverage(data,request,graph,run_id=case.RUN_ID)


@pytest.mark.parametrize('fault',['late','early','reset','short','long','delayed_helper'])
def test_original_outer_clock_must_fit_the_fixed_window(monkeypatch,fault):
    value=plan(); start=case.stamp(value['window']['not_before']);current=start
    seconds=3600
    if fault=='late':start=case.stamp(value['window']['latest_start'])+timedelta(microseconds=1);current=start
    elif fault=='early':start-=timedelta(seconds=1);current=start
    elif fault=='reset':current=start-timedelta(seconds=1)
    elif fault=='short':seconds=3599
    elif fault=='long':seconds=3601
    else:current=start+timedelta(seconds=6)
    monkeypatch.setattr(case,'now',lambda:current)
    with pytest.raises(ValueError,match='original complete 3600'):
        case.Clock(value,start.isoformat(),(start+timedelta(seconds=seconds)).isoformat())


def native_fixture(tmp_path,monkeypatch):
    receipt,native_plan,store,reference=build_reader_fixture(tmp_path,monkeypatch)
    fixed=plan()['native']; begin=case.stamp(receipt['started']);end=case.stamp(receipt['finished'])
    runtime={'root':str(tmp_path),'repository_commit':fixed['commit'],'files':{'fixture_only':True},
             'python':write_ref(tmp_path/'python','fixture Python identity')}
    receipt.update(repository_commit=fixed['commit'],runtime=runtime,phase='primary',
        lane={'verified_lane':'mbit10-evaluation-node1 (verified: affinity, bind:1, lease held, generation 500)'})
    admission={'code_commit':fixed['commit'],'plan_sha256':fixed['plan_sha256'],'prepared_at':begin.isoformat(),
               'proofs':native_plan['fixed_prerequisites'],'coverage_commit':native_plan['coverage_commit']}
    receipt['admission']=write_ref(tmp_path/'admission',admission)
    monkeypatch.setattr(case.native,'runtime_identity',lambda *a,**kw:copy.deepcopy(runtime))
    monkeypatch.setattr(case.native,'validate_driver_receipt',lambda *a,**kw:pytest.fail('cleanup must not qualify the study'))
    ids=receipt['process_observations']['ancestry']+receipt['process_observations']['owned_processes']
    ids={(row['pid'],row['start_ticks']):{'pid':row['pid'],'start_ticks':row['start_ticks'],'state':'absent'} for row in ids}
    lane={'host':'mbit10','node':1,'lease_name':'mbit10-evaluation-node1','lease_generation':500,
          'exit_code':0,'started_utc':begin.isoformat(),'ended_utc':end.isoformat()}
    lease={'state':'released','lease':{'generation':500,'lease_name':lane['lease_name']},'released_at':end.isoformat()}
    audit={'id':fixed['id'],'state':'terminal_and_reaped','owned_processes_absent':True,
        'observed_at':(end+timedelta(seconds=1)).isoformat(),'driver':reference(),
        'lane':write_ref(tmp_path/'lane',{'socket_lane':lane}), 'lease_snapshot':write_ref(tmp_path/'lease',lease),
        'outer_exit':write_ref(tmp_path/'exit','0'),'owned_processes':list(ids.values())}
    def seal():
        audit['driver']=reference();audit['lane']=write_ref(tmp_path/'lane',{'socket_lane':lane})
        return write_ref(tmp_path/'audit',audit)
    return receipt,audit,lane,store,seal,end+timedelta(seconds=2)


@pytest.mark.parametrize('state',['complete','primary_unqualified','failed'])
def test_whole_native_terminal_is_outcome_independent_cleanup_only(tmp_path,monkeypatch,state):
    receipt,audit,lane,store,seal,current=native_fixture(tmp_path,monkeypatch)
    receipt['state']=state
    if state=='failed':lane['exit_code']=1;audit['outer_exit']=write_ref(tmp_path/'exit','1')
    result=case.native_terminal(seal(),plan(),store,current,tmp_path/'proc')
    assert result['native_state']==state and result['qualification_used'] is False and result['cleanup_verified'] is True


@pytest.mark.parametrize('fault',['active','future','expired','reset_budget','native_commit','missing_stage_owner',
    'missing_sample_owner','missing_adopted_owner','live_owner','lease','stage_running','zero_exit_failure'])
def test_native_terminal_rejects_resealed_budget_or_ownership_gaps(tmp_path,monkeypatch,fault):
    receipt,audit,lane,store,seal,current=native_fixture(tmp_path,monkeypatch)
    if fault=='active':receipt['state']='running'
    elif fault=='future':audit['observed_at']=(current+timedelta(seconds=1)).isoformat()
    elif fault=='expired':receipt['finished']='2026-09-26T23:00:00-04:00'
    elif fault=='reset_budget':receipt['bounds']['shared_seconds']+=1
    elif fault=='native_commit':receipt['repository_commit']='0'*40
    elif fault=='missing_stage_owner':audit['owned_processes']=[p for p in audit['owned_processes'] if p['pid']!=207]
    elif fault=='missing_sample_owner':audit['owned_processes']=[p for p in audit['owned_processes'] if p['pid']!=123]
    elif fault=='missing_adopted_owner':receipt['stages'][0]['cleanup']['observed']=[{'pid':999,'start_ticks':44}]
    elif fault=='live_owner':
        folder=tmp_path/'proc'/'207';folder.mkdir(parents=True)
        fields=['S','123']+['0']*17+['1007','0','1'];(folder/'stat').write_text('207 (fixture) '+' '.join(fields))
    elif fault=='lease':lane['lease_generation']+=1
    elif fault=='stage_running':receipt['stages'][0]['state']='running'
    else:receipt['state']='failed'
    with pytest.raises(ValueError):case.native_terminal(seal(),plan(),store,current,tmp_path/'proc')


def linux_proof(tmp_path,kind):
    names=['test_linux_a2_reaps_detached_child[False]','test_linux_a2_reaps_detached_child[True]'] if kind=='owned_cleanup' else [
        'test_public_interruption_is_durable_before_postmortem[raises]','test_public_interruption_is_durable_before_postmortem[stalls]']
    xml='<testsuites><testsuite>'+''.join('<testcase name="'+name+'" />' for name in names)+'</testsuite></testsuites>'
    junit=write_ref(tmp_path/'junit.xml',xml);log=write_ref(tmp_path/'pytest.log','2 passed')
    runtime={'python':{'path':str(Path(sys.executable).resolve())},'fixture_only':True}
    proof={'format':'swdb.bfs.linux-fixture.v1','kind':kind,'host':'mbit10','platform':'linux','code_commit':'a'*40,
        'evidence_kind':'contract_fixture',
        'state':'passed','returncode':0,'started':'2026-09-26T15:00:00-04:00','finished':'2026-09-26T15:01:00-04:00',
        'runtime':runtime,'command':[runtime['python']['path'],'-m','pytest',
          'tests/test_bfs_dx100_coverage_a2.py::test_linux_a2_reaps_detached_child' if kind=='owned_cleanup' else
          'tests/test_dx100_interruption.py::test_public_interruption_is_durable_before_postmortem','--junitxml='+junit['path']],
        'stdout':log,'junit':junit}
    return proof,runtime


@pytest.mark.parametrize('kind',['owned_cleanup','dx100_interruption'])
def test_linux_admission_requires_actual_bound_unskipped_test_receipts(tmp_path,kind):
    proof,runtime=linux_proof(tmp_path,kind);ref=write_ref(tmp_path/'proof',proof)
    assert case.validate_linux_proof(ref,kind,'a'*40,case.stamp('2026-09-26T16:00:00-04:00'),runtime)['cases']==2
    proof['junit']=write_ref(tmp_path/'junit.xml','<testsuites><testsuite><testcase name="fixture"><skipped /></testcase></testsuite></testsuites>')
    with pytest.raises(ValueError,match='unsuccessful/skipped'):
        case.validate_linux_proof(write_ref(tmp_path/'proof',proof),kind,'a'*40,case.stamp('2026-09-26T16:00:00-04:00'),runtime)


class FakeOwned:
    def __init__(self):self.known={os.getpid():1};self.allowances=[]
    def remember(self,row):self.known[row['pid']]=row['start_ticks']
    def retained_identities(self):return sorted(self.known.items())
    def sample(self):
        return {'sampled_at':case.now().isoformat(),'rss_bytes':4096,'rss_source':case.RSS_SOURCE,'page_size_bytes':4096,
            'processes':[{'pid':os.getpid(),'start_ticks':1,'parent_pid':99,'state':'S','rss_bytes':4096,'rss_pages':1}]}
    def finish(self,seconds):
        self.allowances.append(seconds);return {'state':'all_owned_descendants_absent','observed':[],'subreaper':True}


@pytest.fixture
def driver(tmp_path,monkeypatch):
    start=case.stamp(plan()['window']['not_before']);anchor=time.monotonic()
    monkeypatch.setattr(case,'now',lambda:start+timedelta(seconds=time.monotonic()-anchor))
    monkeypatch.setattr(case.observer,'identity',lambda pid:{'pid':pid,'start_ticks':1,'parent_pid':os.getpid()})
    monkeypatch.setattr(case.observer,'ancestry',lambda identity,pane:[identity,pane])
    monkeypatch.setattr(case.shutil,'disk_usage',lambda _:SimpleNamespace(free=100*1024**3))
    value=plan();clock=case.Clock(value,start.isoformat(),(start+timedelta(seconds=3600)).isoformat())
    records=tmp_path/'records';records.mkdir()
    worker=case.Driver(value,clock,tmp_path/'raw',tmp_path/'build',records,FakeOwned(),{'pid':99,'start_ticks':1})
    worker.receipt['lane']='fixture-only';return worker


def test_real_tiny_process_retains_identity_output_and_reap(driver):
    result=driver.stage('tiny',[sys.executable,'-c','import json;print(json.dumps(dict(fixture_only=True)))'],2)
    assert result=={'fixture_only':True}
    row=driver.receipt['stages'][0]
    assert row['reaped'] is True and row['returncode']==0 and row['cleanup']['state']=='all_owned_descendants_absent'
    with pytest.raises(ChildProcessError):os.waitpid(row['identity']['pid'],os.WNOHANG)
    assert (row['identity']['pid'],1) in driver.owned.retained_identities()
    driver.receipt['state']='complete';assert driver.finalize()==0
    assert driver.receipt['cleanup_verified'] is False


def test_failed_stage_retains_one_attempt_and_no_retry(driver):
    with pytest.raises(ValueError,match='public stage failed'):
        driver.stage('failure',[sys.executable,'-c','print("{}");raise SystemExit(7)'],2)
    assert len(driver.receipt['stages'])==1 and driver.receipt['stages'][0]['returncode']==7
    assert driver.finalize(ValueError('fixture failure'))==1


def test_denied_shutdown_still_waits_and_reaps_direct_child(driver,monkeypatch):
    spawned=[];popen=case.subprocess.Popen
    def launch(*args,**kwargs):
        child=popen(*args,**kwargs);spawned.append(child);return child
    monkeypatch.setattr(case.subprocess,'Popen',launch)
    def denied(*args):
        raise PermissionError('synthetic denied signal; must still reap direct child')
    monkeypatch.setattr(case,'stop_owned',denied)
    try:
        with pytest.raises(ValueError,match='stage timeout'):
            driver.stage('denied',[sys.executable,'-c','import time;time.sleep(.2);print("{}")'],.03)
        row=driver.receipt['stages'][0]
        assert row['state']=='failed' and 'PermissionError' in row['cleanup_error']
        assert row['reaped'] is True and row['returncode']==0
        with pytest.raises(ChildProcessError):os.waitpid(row['identity']['pid'],os.WNOHANG)
        assert 0<driver.cleanup_spent<30 and len(driver.receipt['stages'])==1
    finally:
        for child in spawned:child.wait(timeout=2)


def test_failed_public_json_remains_retrievable_without_retry(driver):
    value=driver.stage('failure',[sys.executable,'-c','import json;print(json.dumps(dict(state="interrupted")));raise SystemExit(1)'],2,require_success=False)
    assert value=={'state':'interrupted'} and driver.receipt['stages'][0]['state']=='failed'
    assert driver.finalize(ValueError('failed public result'))==1


def test_shared_cleanup_reserve_cannot_reset_between_stages(driver):
    driver.cleanup_spent=29
    with pytest.raises(ValueError,match='remaining cleanup reserve'):
        driver.stage('blocked',[sys.executable,'-c','print("{}")'],1)
    assert driver.receipt['stages']==[]


def test_final_runtime_rehash_cannot_borrow_cleanup_time(driver,monkeypatch):
    driver.receipt['runtime']={'fixture_only':True}
    def slow_rehash(commit):
        # Rehash finishes with outer time left, but less than its cleanup reserve.
        driver.clock.hard=time.monotonic()+29
        return copy.deepcopy(driver.receipt['runtime'])
    monkeypatch.setattr(case,'runtime_identity',slow_rehash)
    with pytest.raises(ValueError,match='original shared deadline'):
        case.finish_work(driver,'a'*40)
    assert driver.clock.remaining(cleanup=True)>0 and driver.clock.remaining()<0


@pytest.mark.parametrize('fault',['time','storage','late_second_write','hash'])
def test_final_hashes_and_each_persistence_are_inside_original_bounds(driver,monkeypatch,fault):
    driver.receipt['state']='complete';driver.observe()
    original=driver.save;calls=0;crossed=False
    def save():
        nonlocal calls,crossed
        original();calls+=1
        if calls==(2 if fault=='late_second_write' else 1):crossed=True
    monkeypatch.setattr(driver,'save',save)
    if fault=='storage':
        actual=case.original.artifact_bytes
        monkeypatch.setattr(case.original,'artifact_bytes',lambda paths:5*1024**3 if crossed else actual(paths))
    elif fault=='hash':
        original_ref=case.ref
        def reference(path):
            nonlocal crossed
            result=original_ref(path)
            if str(path).endswith('process-observations.json'):crossed=True
            return result
        monkeypatch.setattr(case,'ref',reference)
    actual=driver.clock.check
    if fault!='storage':
        def check(cleanup=False):
            if crossed:raise ValueError('fixture original shared deadline exhausted')
            return actual(cleanup)
        monkeypatch.setattr(driver.clock,'check',check)
    assert driver.finalize()==1
    retained=json.loads((driver.folder/'driver.json').read_text())
    assert retained['state']=='failed' and 'finalization_error' in retained
    assert case.read(retained['process_observations'])['sampling_complete'] is False


def test_shutdown_monitor_error_remains_failure_and_attempts_cleanup(driver):
    def fail():raise ValueError('fixture unavailable RSS')
    driver.monitor=SimpleNamespace(signal_lock=threading.Lock(),done=threading.Event(),thread=None,check=fail)
    driver.receipt['state']='complete';assert driver.finalize()==1
    assert driver.owned.allowances and 'unavailable RSS' in driver.receipt['cleanup_error']


def test_monitor_join_spends_the_same_cleanup_reserve_after_prior_stages(driver,monkeypatch):
    tick=[time.monotonic()];limits=[]
    monkeypatch.setattr(case.time,'monotonic',lambda:tick[0])
    class Slow:
        def join(self,timeout):limits.append(timeout);tick[0]+=10
        def is_alive(self):return False
    driver.monitor=SimpleNamespace(signal_lock=threading.Lock(),done=threading.Event(),thread=Slow(),check=lambda:None)
    driver.cleanup_spent=25;driver.receipt['state']='complete'
    assert driver.finalize()==1
    assert limits and 0 < limits[0] <= 3
    assert driver.receipt['cleanup_seconds_used']>=35 and driver.receipt['state']=='failed'


def completed_fixture(tmp_path,monkeypatch):
    """Real files/trace/graph/terminal reader; prerequisite/witness fixtures only."""
    value=plan();value['run_root']=str(tmp_path/'raw');value['build_root']=str(tmp_path/'build')
    folder=Path(value['run_root'])/case.RUN_ID;folder.mkdir(parents=True)
    root=tmp_path/'checkout';root.mkdir();(root/'records').mkdir()
    data,_,graph,_=coverage_fixture(folder)
    template=case.yamlio.load(case.original.a3.REQUEST);template['simulator']=case.ref(folder/'simulator')
    monkeypatch.setattr(case.original.a3,'REQUEST',Path(write_ref(tmp_path/'template',template)['path']))
    compiled=compiled_fixture();compiled.update(id=case.RUN_ID+'.compile',request=case.original.compile_request(run_id=case.RUN_ID))
    compiled['build'].update(binary=str(folder/'binary'),binary_sha256=artifacts.file_hash(folder/'binary'))
    workload={'id':'fixture.registered','requested_id':case.RUN_ID+'.workload',
              'definition':{'canonical_sha256':graph['canonical_sha256'],'sources':[0]}}
    request=case.original.execution_request(compiled,workload,graph,run_id=case.RUN_ID)
    data.update(id=case.RUN_ID+'.execute',request=request)
    begin=case.stamp(value['window']['not_before']);end=begin+timedelta(seconds=10)
    # The wrapper begins at :00, helper at :01, and actual driver at :02.
    # All work remains charged from :00, not from the later driver entry.
    stamp=lambda s:(begin+timedelta(seconds=s+2)).isoformat()
    python={'path':str(Path(sys.executable).absolute()),'resolved':str(Path(sys.executable).resolve()),
            'sha256':artifacts.file_hash(Path(sys.executable).resolve()),'version':sys.version}
    runtime={'root':str(root),'python':{'path':python['resolved'],'sha256':python['sha256']},'fixture_only':True}
    admissions={'admission':write_ref(folder/'admission',{'fixture_only':True}),'runtime':runtime,
                'linux_proofs':{'fixture_only':True},'prerequisites':{'fixture_only':True}}
    monkeypatch.setattr(case,'validate_admission',lambda *a,**kw:copy.deepcopy(admissions))
    monkeypatch.setattr(case,'validate_plan',lambda value:value)
    monkeypatch.setattr(case.original,'validate_source',lambda *a:None)
    monkeypatch.setattr(case.original.dx100_witness,'validate_completed_witness',lambda *a,**kw:None)
    identity={'pid':1000,'start_ticks':30,'parent_pid':999};pane={'pid':999,'start_ticks':29,'parent_pid':1}
    lane='mbit10-evaluation-node0 (verified: affinity, bind:0, lease held, generation 600)'
    processes=[{**identity,'rss_bytes':4096,'rss_pages':1,'state':'S'}]
    rows=[{'sampled_at':stamp(s),'guard_started':stamp(s),'guard_finished':stamp(s),'guard_seconds':0,
        'rss_bytes':4096,'rss_source':case.RSS_SOURCE,'page_size_bytes':4096,'artifact_bytes':1000,
        'raw_free_bytes':40*1024**3,'build_free_bytes':20*1024**3,'lane':lane,'processes':processes} for s in (0,5,10)]
    sample_ref=write_ref(folder/'rss-samples.jsonl','\n'.join(map(json.dumps,rows))+'\n')
    raw={'node':'\n'.join(f'Node 0 {k}: {v} kB' for k,v in {'MemFree':60*1024**2,'Active(file)':0,'Inactive(file)':0,
        'Dirty':0,'Writeback':0,'SReclaimable':0}.items()),'zones':'Node 0, zone Normal\n low 0\n high 0\n managed 20000000\n protection: (0)\n',
        'global':f'MemAvailable: {80*1024**2} kB\n'}
    estimate=case.original.dx100_capacity.capacity(raw['node'],raw['zones'],raw['global'],0,4096)
    capacity_ref=write_ref(folder/'capacity.json',{'inputs':raw,'result':estimate,'observed':stamp(.01)})
    requests={'register-workload':case.original.registration_request(graph,run_id=case.RUN_ID),
              'dx100-compile':value['compile_request'],'dx100-execute':request}
    refs={key:write_ref(folder/(key+'.request.json'),req) for key,req in requests.items()}
    outputs={'capacity':capacity_ref,'generate':graph,'register-workload':workload,'dx100-compile':compiled,
             'dx100-execute':data,'fresh-get':data}
    stages=[];owners=[identity,pane]
    for index,(name,result) in enumerate(outputs.items()):
        child={'pid':1100+index,'start_ticks':40+index,'parent_pid':1000};owners.append(child)
        if name=='capacity':argv=[python['path'],str(root/'scripts/dx100_capacity.py'),'--node','0','--output',str(folder/'capacity.json')]
        elif name=='generate':argv=[python['path'],str(root/'scripts/bfs_dx100_coverage_graph.py'),'--output-directory',str(folder/'graph'),'--records',str(root/'records'),'--lane',case.LANE]
        elif name=='fresh-get':argv=[python['path'],'-s','-m','swdb','get',data['id'],'--records',str(root/'records'),'--format','json']
        else:
            argv=[python['path'],'-s','-m','swdb',name,refs[name]['path'],'--records',str(root/'records')]
            if name.startswith('dx100-'):argv+=['--runs-dir',str(folder),'--lane','0']
            argv+=['--format','json']
        stages.append({'name':name,'command':argv,'cwd':str(root),'state':'complete','returncode':0,'reaped':True,
            'started':stamp(index+.1),'work_finished':stamp(index+.15),'finished':stamp(index+.2),'work_wall_s':.05,
            'host_wall_s':.1,'timeout_seconds':1,'identity':child,'cleanup':{'state':'all_owned_descendants_absent','observed':[]},
            'stdout':write_ref(folder/(name+'.stdout'),result),'stderr':write_ref(folder/(name+'.stderr'),'')})
    observations={'driver_pid':1000,'pane_pid':999,'driver_identity':identity,'observer_identity':identity,'observer_kind':'in_process_driver',
        'launcher_identity':pane,'ancestry':[identity,pane],'owned_processes':owners,'state':'driver_sampling_finished','sampling_complete':True,
        'cleanup_verified':False,'resource_samples':sample_ref}
    obs=write_ref(folder/'process-observations.json',observations)
    driver={'id':case.RUN_ID,'state':'complete','repository_commit':'a'*40,'plan_sha256':case.PLAN_SHA,'plan':write_ref(folder/'plan',value),
        'bounds':value['bounds'],'started':stamp(0),'finished':stamp(10),'outer_started':begin.isoformat(),
        'outer_deadline':(begin+timedelta(seconds=3600)).isoformat(),'host_wall_s':10,'outer_wall_s':12,'cleanup_seconds_used':.1,
        'gain_claim':False,'profiling':False,'automatic_retry_allowed':False,'provider_calls':False,'driver_pid':1000,'lane':lane,
        'runtime':runtime,'python':python,'environment':{**dict.fromkeys(case.REMOVED_ENV),**case.FIXED_ENV},'records':str(root/'records'),
        'rss':{'source':case.RSS_SOURCE,'samples':sample_ref,'sampled_peak_bytes':4096},'artifact_peak_bytes':1000,'process_observations':obs,
        'cleanup':{'state':'all_owned_descendants_absent','subreaper':True,'observed':[]},
        'final_accounting':{'observed_at':stamp(10),'artifact_bytes':1000000,'raw_free_bytes':40*1024**3,'build_free_bytes':20*1024**3},
        'stages':stages,'requests':refs,'pre_execute_capacity':{'observed_at':stamp(4),'inputs':raw,'estimate':estimate},
        'graph':graph,'evaluation':data['id'],'evaluation_sha256':artifacts.digest(data),
        'coverage':case.original.dx100_coverage.observe(folder/'coverage.log',{'simTicks':'100','finalTick':'200'},16384),**admissions}
    audit={'id':case.RUN_ID,'state':'passed','observed_at':stamp(13),'driver':write_ref(folder/'driver.json',driver),
        'process_observations':obs,'evaluation':write_ref(folder/'evaluation',data),'evaluation_sha256':artifacts.digest(data),
        'outer_exit':write_ref(folder/'outer.exit','0'),'cleanup_state':'terminal_and_reaped','owned_processes_absent':True,
        'owned_processes':[{**row,'state':'absent'} for row in owners],
        'lane':write_ref(folder/'lane',{'socket_lane':{'host':'mbit10','node':0,'lease_name':case.LANE,'lease_generation':600,'exit_code':0,
            'started_utc':(begin+timedelta(seconds=1)).isoformat(),'ended_utc':stamp(11)}}),
        'lease_snapshot':write_ref(folder/'lease',{'state':'released','lease':{'generation':600,'lease_name':case.LANE},'released_at':stamp(12)})}
    store=SimpleNamespace(get=lambda rid,*kind:{v['id']:v for v in (data,compiled,workload)}[rid])
    def seal():
        audit['driver']=write_ref(folder/'driver.json',driver);return write_ref(folder/'audit',audit)
    return driver,audit,store,seal,begin+timedelta(seconds=16),tmp_path/'proc'


def test_completed_a2_reader_reopens_real_fixture_files_graph_trace_and_terminal_union(tmp_path,monkeypatch):
    driver,audit,store,seal,current,proc=completed_fixture(tmp_path,monkeypatch)
    result=case.validate_completed(seal(),store,current,'a'*40,proc)
    lane=case.read(audit['lane'])['socket_lane']
    assert case.stamp(driver['outer_started']) < case.stamp(lane['started_utc']) < case.stamp(driver['started'])
    assert driver['outer_wall_s']==driver['host_wall_s']+2
    assert result['coverage']['full_tiles']['count']==result['coverage']['tail_tiles']['count']==1
    assert result['gain_claim'] is False


@pytest.mark.parametrize('fault',['foreign_commit','late','stage_gap','stage_duration','stage_identity','stage_command','output',
    'rss_basis','omitted_owner','reserve','record','request','binary','coverage','final_cleanup_union','outer_clock_reset'])
def test_completed_a2_reader_rejects_consistently_resealed_invalid_evidence(tmp_path,monkeypatch,fault):
    driver,audit,store,seal,current,proc=completed_fixture(tmp_path,monkeypatch)
    if fault=='foreign_commit':driver['repository_commit']='b'*40
    elif fault=='late':driver['started']='2026-09-26T21:00:01-04:00'
    elif fault=='stage_gap':driver['stages'][3]['started']='2026-09-26T16:00:02-04:00'
    elif fault=='stage_duration':driver['stages'][0]['work_wall_s']=True
    elif fault=='stage_identity':driver['stages'][3]['identity']['parent_pid']=1
    elif fault=='stage_command':driver['stages'][4]['command'][5]='different.request'
    elif fault=='output':Path(driver['stages'][4]['stdout']['path']).write_text('{}')
    elif fault=='rss_basis':driver['rss']['source']='VmRSS'
    elif fault=='omitted_owner':audit['owned_processes'].pop()
    elif fault=='reserve':driver['final_accounting']['build_free_bytes']=0
    elif fault=='record':store.get=lambda *a:{'changed':True}
    elif fault=='request':
        request=case.read(driver['requests']['dx100-execute']);request['verification']['coverage']=False
        driver['requests']['dx100-execute']=write_ref(Path(driver['requests']['dx100-execute']['path']),request)
    elif fault=='binary':Path(case.read(driver['stages'][3]['stdout'])['build']['binary']).write_text('changed')
    elif fault=='final_cleanup_union':driver['cleanup']['observed']=[{'pid':1888,'start_ticks':44}]
    elif fault=='outer_clock_reset':driver['outer_started']=driver['started']
    else:driver['coverage']['tail_tiles']['count']=0
    with pytest.raises(ValueError):case.validate_completed(seal(),store,current,'a'*40,proc)


@pytest.mark.skipif(sys.platform!='linux',reason='actual Linux subreaper/pidfd fixture required before admission')
@pytest.mark.parametrize('failure',[False,True])
def test_linux_a2_reaps_detached_child(tmp_path,failure):
    script=r'''
import json,os,pathlib,resource,sys,time
from datetime import timedelta
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
from scripts import bfs_dx100_coverage_a2 as c
folder=pathlib.Path(sys.argv[1]);failure=sys.argv[2]=='True';p=json.loads(c.PLAN.read_text())
start=c.now();p['window']={'not_before':(start-timedelta(seconds=1)).isoformat(),'latest_start':(start+timedelta(seconds=1)).isoformat(),'absolute_end':(start+timedelta(seconds=3601)).isoformat()}
clock=c.Clock(p,start.isoformat(),(start+timedelta(seconds=3600)).isoformat())
c.observer.ancestry=lambda identity,pane:[identity,pane]
c.shutil.disk_usage=lambda _:type('Space',(),{'free':100*1024**3})()
(folder/'records').mkdir();worker=c.Driver(p,clock,folder/'raw',folder/'build',folder/'records',c.native.LockedOwned(),{'pid':os.getppid(),'start_ticks':1})
worker.receipt['lane']='fixture-only'
inner="import os,pathlib,time; pathlib.Path(%r).write_text(str(os.getpid())); time.sleep(30)"%str(folder/'grandchild')
leader="import pathlib,subprocess,sys,time;subprocess.Popen([sys.executable,'-c',%r],start_new_session=True);p=pathlib.Path(%r);end=time.monotonic()+3\nwhile not p.exists() and time.monotonic()<end:time.sleep(.01)\nprint('{}');sys.exit(%d)"%(inner,str(folder/'grandchild'),7 if failure else 0)
error=None
try:worker.stage('detached',[sys.executable,'-c',leader],5)
except ValueError as exc:error=exc
assert bool(error)==failure
assert not pathlib.Path('/proc',(folder/'grandchild').read_text()).exists()
assert worker.receipt['stages'][0]['cleanup']['state']=='all_owned_descendants_absent'
worker.receipt['state']='complete' if not failure else 'failed';worker.finalize(error)
(folder/'fixture-result.json').write_text(json.dumps({'fixture_only':True,'platform':sys.platform,'state':'passed','failure_case':failure,'cleanup':worker.receipt['cleanup']}))
'''
    result=subprocess.run([sys.executable,'-c',script,str(tmp_path),str(failure)],cwd=case.ROOT,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
    assert json.loads((tmp_path/'fixture-result.json').read_text())['state']=='passed'
