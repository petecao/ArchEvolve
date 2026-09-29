"""T17 orchestration contracts and tiny process fixtures. Date: 2026-09-26 ET."""
import copy
from datetime import timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from conftest import REPO
from scripts import bfs_t17_build_only as build
from swdb import artifacts
from swdb.cli import Failure
from test_bfs_native_campaign import seal_package


class FakeOwned:
    def __init__(self):
        self.sampler = SimpleNamespace(known={os.getpid(): 1})
        self.allowances = []

    def sample(self):
        return {'sampled_at': build.now().isoformat(), 'rss_bytes': 1024,
                'processes': [{'pid': os.getpid(), 'start_ticks': 1, 'parent_pid': 1, 'rss_bytes': 1024}]}

    def finish(self, seconds):
        self.allowances.append(seconds)
        return {'state': 'all_owned_descendants_absent', 'observed': [], 'subreaper': True}


@pytest.fixture
def attempt(tmp_path, monkeypatch):
    # POSIX subprocess fixtures only. This does not attest Linux pidfd/subreaper.
    monkeypatch.setattr(build.observer, 'identity', lambda pid: {'pid': pid, 'start_ticks': 1})
    monkeypatch.setattr(build.shutil, 'disk_usage', lambda _: SimpleNamespace(free=100*1024**3))
    started = build.now()
    clock = build.Clock(started, started + timedelta(seconds=300))
    worker = build.Attempt(tmp_path/'raw', tmp_path/'binary', clock, FakeOwned(), {'pid': 999, 'start_ticks': 1})
    return worker


def test_fixed_public_interface_and_request_bytes():
    assert build.REQUEST.stat().st_size == 551
    assert artifacts.file_hash(build.REQUEST) == build.REQUEST_SHA
    assert artifacts.file_hash(build.OBSERVATION) == build.OBSERVATION_SHA
    command = build.public_command('dx100-compile', build.REQUEST, '--runs-dir', build.RAW, '--lane', 0)
    assert command[1:4] == ['-s', '-m', 'swdb']
    assert command[-4:] == ['--records', str(build.PUBLIC_ROOT/'records'), '--format', 'json']
    assert json.loads(build.REQUEST.read_text())['budget'] == {
        'total_seconds': 240, 'build_seconds': 180, 'memory_gib': 16, 'storage_gib': 1}


def test_owned_cleanup_uses_the_new_single_record_rss_basis(monkeypatch):
    from scripts import bfs_owned_rss
    owner=FakeOwned(); fresh=SimpleNamespace(known={},rss_source=bfs_owned_rss.RSS_SOURCE)
    calls=[]
    monkeypatch.setattr(build,'OwnedDescendants',lambda:owner)
    monkeypatch.setattr(bfs_owned_rss,'DescendantRSS',lambda pid:calls.append(pid) or fresh)
    assert build.owned_descendants() is owner
    assert owner.sampler is fresh and calls==[os.getpid()]
    assert fresh.rss_source=='linux.proc_pid_stat.field24.v1'


@pytest.mark.parametrize('seconds,elapsed', [(301,0),(300,271),(300,-1)])
def test_original_outer_window_cannot_be_extended_or_started_late(seconds, elapsed):
    current = build.now(); start = current - timedelta(seconds=elapsed)
    with pytest.raises(ValueError, match='original 300-second'):
        build.Clock(start, start+timedelta(seconds=seconds))


@pytest.mark.parametrize('fault', [None,'tracked','shadow','commit'])
def test_runtime_pin_covers_actual_code_and_rejects_changes(tmp_path, fault):
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=tmp_path,stderr=subprocess.DEVNULL,text=True).strip()
    git('init');(tmp_path/'scripts').mkdir();(tmp_path/'scripts/fixed.py').write_text('# fixture\n')
    git('add','scripts/fixed.py')
    git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','fixture')
    commit=git('rev-parse','HEAD')
    if fault=='tracked':(tmp_path/'scripts/fixed.py').write_text('# changed\n')
    elif fault=='shadow':(tmp_path/'scripts/shadow.py').write_text('# changed\n')
    elif fault=='commit':commit='0'*40
    if fault is None:
        result=build.runtime_tree(tmp_path,commit)
        assert result['files']=={'scripts/fixed.py':artifacts.file_hash(tmp_path/'scripts/fixed.py')}
    else:
        with pytest.raises(ValueError,match='runtime'):build.runtime_tree(tmp_path,commit)


def test_tiny_real_stage_retains_exact_output_exit_and_reap(attempt):
    command = [sys.executable, '-c', 'import json; print(json.dumps({"fixture_only":True}))']
    result = attempt.stage('public-fixture', command, 2, REPO)
    assert result == {'fixture_only': True}
    row = attempt.receipt['stages'][0]
    assert row['returncode'] == 0 and row['reaped'] is True
    assert row['command'] == command
    assert artifacts.file_hash(row['stdout']['path']) == row['stdout']['sha256']
    with pytest.raises(ChildProcessError):
        os.waitpid(row['identity']['pid'], os.WNOHANG)
    attempt.receipt['state'] = 'complete'
    assert attempt.finish() == 0
    receipt = json.loads((attempt.folder/'driver.json').read_text())
    assert not receipt['cleanup_verified'] and not receipt['gain_claim']
    assert receipt['descendant_cleanup']['state'] == 'all_owned_descendants_absent'


def test_public_failure_is_retained_and_does_not_retry(attempt):
    with pytest.raises(ValueError, match='unsuccessful exit'):
        attempt.stage('fails', [sys.executable, '-c', 'print("{}"); raise SystemExit(7)'], 2, REPO)
    assert len(attempt.receipt['stages']) == 1
    assert attempt.receipt['stages'][0]['returncode'] == 7
    assert attempt.finish(ValueError('public failure')) == 1


def test_failed_compile_json_can_be_freshly_queried_without_retry(attempt):
    result = attempt.stage('compile', [sys.executable, '-c', 'print("{\\"failed\\":true}"); raise SystemExit(1)'],
                           2, REPO, require_success=False)
    assert result == {'failed': True}
    assert attempt.receipt['stages'][0]['state'] == 'failed'


def test_work_deadline_clips_stage_and_reaps_sleeping_child(attempt):
    attempt.clock.work = time.monotonic() + .15
    attempt.clock.hard = attempt.clock.work + 30
    with pytest.raises(ValueError, match='deadline|timeout'):
        attempt.stage('timeout', [sys.executable, '-c', 'import time; time.sleep(20)'], 240, REPO)
    row = attempt.receipt['stages'][0]
    assert row['timeout_seconds'] <= .15 and row['returncode'] is not None and row['reaped'] is True
    assert attempt.finish(ValueError('timeout')) == 1
    assert len(attempt.receipt['stages']) == 1


def test_reap_still_runs_after_owned_shutdown_error(attempt, monkeypatch):
    monkeypatch.setattr(build,'stop_owned',lambda *args:(_ for _ in ()).throw(ValueError('fixture denied signal')))
    with pytest.raises(ValueError,match='timeout'):
        attempt.stage('timeout',[sys.executable,'-c','import time; time.sleep(.2)'],.01,REPO)
    row=attempt.receipt['stages'][0]
    assert row['reaped'] and row['returncode']==0
    assert 'denied signal' in row['cleanup_error']
    assert attempt.cleanup_spent >= .1


def test_each_stage_cleans_descendants_before_the_next_stage(attempt):
    attempt.stage('first',[sys.executable,'-c','print("{}")'],2,REPO)
    assert len(attempt.owned.allowances)==1
    assert attempt.receipt['stages'][0]['descendant_cleanup']['state']=='all_owned_descendants_absent'
    attempt.stage('second',[sys.executable,'-c','print("{}")'],2,REPO)
    assert len(attempt.owned.allowances)==2


def test_stage_cleanup_spends_one_shared_reserve(attempt, monkeypatch):
    attempt.cleanup_spent=27.5
    attempt.stage('last',[sys.executable,'-c','print("{}")'],2,REPO)
    assert 0 < attempt.owned.allowances[0] <= .5
    attempt.cleanup_spent=29
    with pytest.raises(ValueError,match='shared allowance'):
        attempt.stage('exhausted',[sys.executable,'-c','print("{}")'],2,REPO)
    assert len(attempt.owned.allowances)==1


@pytest.mark.parametrize('part', ['sample','storage','write'])
def test_final_work_crossing_original_deadline_cannot_retain_complete(attempt, monkeypatch, part):
    attempt.receipt['state'] = 'complete'
    expire = lambda: setattr(attempt.clock, 'hard', time.monotonic()-1)
    if part == 'sample':
        original = attempt.owned.sample
        def slow():
            row = original(); expire(); return row
        monkeypatch.setattr(attempt.owned, 'sample', slow)
    elif part == 'storage':
        def slow(_):
            expire(); return 0
        monkeypatch.setattr(build.coverage, 'artifact_bytes', slow)
    else:
        original = attempt.save
        def slow():
            original(); expire()
        monkeypatch.setattr(attempt, 'save', slow)
    assert attempt.finish() == 1
    receipt = json.loads((attempt.folder/'driver.json').read_text())
    assert receipt['state'] == 'failed' and 'finalization_error' in receipt


def test_exhausted_cleanup_never_gets_a_new_five_second_budget(attempt):
    attempt.clock.hard = time.monotonic() + 1
    assert attempt.finish() == 1
    assert attempt.owned.allowances == []
    assert attempt.receipt['known_owned_identities'] == [{'pid': os.getpid(), 'start_ticks': 1}]


def test_failed_descendant_cleanup_keeps_known_identities(attempt, monkeypatch):
    def failed(seconds):
        attempt.owned.sampler.known[12345] = 999
        raise ValueError('owned descendant remains')
    monkeypatch.setattr(attempt.owned, 'finish', failed)
    assert attempt.finish() == 1
    assert {'pid': 12345, 'start_ticks': 999} in attempt.receipt['known_owned_identities']


@pytest.mark.parametrize('fault', ['rss','storage','gap'])
def test_resource_guard_fails_closed(attempt, monkeypatch, fault):
    if fault == 'rss':
        monkeypatch.setattr(attempt.owned, 'sample', lambda: {'rss_bytes': build.BOUNDS['sampled_rss_bytes']+1})
    elif fault == 'storage':
        monkeypatch.setattr(build.coverage, 'artifact_bytes', lambda _: build.BOUNDS['artifact_bytes']+1)
    else:
        attempt.last_sample = time.monotonic()-31
    with pytest.raises(ValueError, match='RSS|storage|gap'):
        attempt.sample(force=True)


@pytest.fixture
def execution_fixture(tmp_path, monkeypatch):
    source=tmp_path/'source'; source.mkdir();(source/'fixture.cc').write_text('int fixture;\n')
    artifact=artifacts.identify(source)
    compiler=tmp_path/'compiler';compiler.write_text('fixture compiler identity; never executed\n')
    model_receipt=tmp_path/'model.json';model_receipt.write_text('{}')
    package=seal_package({'id':'package','kind':'profile_package','completeness':'fixture',
                          'evidence':{'classification':'contract_fixture'}})
    values={'proposal':{'id':'proposal','profile_package':package['id'],'repair_budget':{'total_seconds':1800,'used_seconds':233.21830715797842,'repairs':0,'max_repairs':2}},
            'candidate':{'id':'candidate','proposal':'proposal','source_snapshot':'source','artifact':artifact,'protections':[]},
            'source_snapshot':{'id':'source','artifact':artifact},
            'package':package,'model':{'id':'model'},'target':{'id':'target'}}
    pins={key:{'id':values[key]['id'],'canonical_sha256':artifacts.digest(values[key])}
          for key in ('proposal','candidate','source_snapshot')}
    pins['proposal'].update(profile_package=package['id'],retained_provider_budget=copy.deepcopy(values['proposal']['repair_budget']))
    pins['model']={'build_evaluation':'model','target':'target','build_canonical_sha256':artifacts.digest(values['model']),
                   'target_canonical_sha256':artifacts.digest(values['target']),'receipt':build.ref(model_receipt)}
    pins['compiler']=build.ref(compiler)
    binary=tmp_path/'binary';binary.write_text('fixture binary identity; never executed\n')
    driver=tmp_path/'driver.cc';driver.write_text('fixture driver identity\n')
    result={'id':build.RUN_ID,'candidate':'candidate','outcome':{'state':'complete','stage':'candidate_build'},
            'evidence_kind':'execution','gain_claim':False,'request':json.loads(build.REQUEST.read_text()),
            'correctness':{'state':'unverified'},'profiling':{'state':'incomplete'},'timing':[],
            'build':{'adapter':'dx100.complete_call.v2','compiler_sha256':pins['compiler']['sha256'],
                     'binary':str(binary),'binary_sha256':artifacts.file_hash(binary),'driver':build.ref(driver)}}
    records={row['id']:row for row in values.values()}
    chain={'root':build.RUN_ID,'records':{**copy.deepcopy(records),build.RUN_ID:copy.deepcopy(result)}}
    monkeypatch.setattr(build,'Store',lambda _:SimpleNamespace(get=records.get))
    class PublicFixture:
        def __init__(self):self.receipt={'stages':[]};self.calls=[]
        def sample(self,**_):pass
        def stage(self,name,command,timeout,cwd,**kwargs):
            self.calls.append((name,command,timeout,cwd,kwargs))
            self.receipt['stages'].append({'name':name,'returncode':0})
            if name.startswith('before-'):return copy.deepcopy(values[name[7:]])
            return copy.deepcopy(chain if name=='after-chain' else result)
    return PublicFixture(),pins,values,result,chain,records


def test_fixed_sequence_uses_existing_candidate_without_provider_or_retry(execution_fixture):
    attempt,pins,*_=execution_fixture
    build.execute(attempt,pins,{})
    names=[row[0] for row in attempt.calls]
    assert names==['before-proposal','before-candidate','before-source_snapshot','before-package','before-model',
                   'before-target','compile','after-evaluation','after-chain']
    assert sum('dx100-compile' in row[1] for row in attempt.calls)==1
    assert all(row[3]==build.PUBLIC_ROOT for row in attempt.calls)
    assert not any(any(arg in {'submit','repair','evaluate','dx100-execute'} for arg in row[1]) for row in attempt.calls)
    assert attempt.receipt['provider_budget_unchanged'] is True


@pytest.mark.parametrize('fault',['changed-source','changed-candidate','changed-budget','changed-compiler'])
def test_origin_mismatch_refuses_before_compile(execution_fixture, fault):
    attempt,pins,values,_,_,_=execution_fixture
    if fault=='changed-source':values['source_snapshot']['other']='mutated'
    elif fault=='changed-candidate':values['candidate']['other']='mutated'
    elif fault=='changed-budget':values['proposal']['repair_budget']['used_seconds']=0
    else:Path(pins['compiler']['path']).write_text('different bytes')
    reason={'changed-source':'source_snapshot record changed','changed-candidate':'candidate record changed',
            'changed-budget':'proposal record changed','changed-compiler':'compiler changed'}[fault]
    with pytest.raises(ValueError,match=reason):build.execute(attempt,pins,{})
    assert not any(row[0]=='compile' for row in attempt.calls)


def test_changed_sealed_origin_package_refuses_before_compile(execution_fixture):
    attempt,pins,values,*_=execution_fixture
    values['package']['evidence']['classification']='execution'
    with pytest.raises(Failure,match='content differs from its retained identity'):
        build.execute(attempt,pins,{})
    assert not any(row[0]=='compile' for row in attempt.calls)


@pytest.mark.parametrize('fault',['failure','claim','request','chain','budget-after'])
def test_public_build_result_and_fresh_chain_cannot_overstate_success(execution_fixture, fault):
    attempt,pins,values,result,chain,records=execution_fixture
    if fault=='failure':result['outcome']['state']='failed'
    elif fault=='claim':result['correctness']['state']='passed'
    elif fault=='request':result['request']['budget']['build_seconds']=181
    elif fault=='chain':chain['records'].pop('proposal')
    else:
        original=attempt.stage
        def stage(name,*args,**kwargs):
            row=original(name,*args,**kwargs)
            if name=='compile':records['proposal']=copy.deepcopy(values['proposal']);records['proposal']['repair_budget']['used_seconds']=0
            return row
        attempt.stage=stage
    reason={'failure':'only the requested actual build','claim':'overstates build-only evidence',
            'request':'fixed request','chain':'fresh public chain',
            'budget-after':'retained origin record or provider budget changed'}[fault]
    with pytest.raises(ValueError,match=reason):build.execute(attempt,pins,{})
    assert sum(row[0]=='compile' for row in attempt.calls)==1


@pytest.fixture
def cleanup_fixture(tmp_path):
    serial = 0
    def write(value, raw=False):
        nonlocal serial
        serial += 1
        path = tmp_path/str(serial)
        path.write_text(value if raw else json.dumps(value))
        return build.ref(path)
    pane = {'pid':3053339, 'start_ticks':494729548}
    driver_identity = {'pid':3053340, 'start_ticks':494729550}
    descendant = {'pid':3053341, 'start_ticks':494729551}
    sample_ref = write(json.dumps({'processes':[driver_identity, descendant]})+'\n', True)
    observed = {'state':'failed','sampling_complete':False,'cleanup_verified':False,
        'observer_kind':'in_process_driver','driver_identity':driver_identity,'observer_identity':driver_identity,
        'driver_pid':driver_identity['pid'],'pane_pid':pane['pid'],'launcher_identity':pane,
        'ancestry':[driver_identity,pane],'owned_processes':[driver_identity,descendant],'resource_samples':sample_ref}
    observed_ref = write(observed)
    driver = {'id':build.coverage.RUN_ID,'state':'failed','repository_commit':'a'*40,
        'started':'2026-09-26T13:56:02-04:00','finished':'2026-09-26T14:01:48-04:00',
        'host_wall_s':346,'deadline_et':build.coverage.DEADLINE.isoformat(),'bounds':build.coverage.BOUNDS,
        'lane':'mbit10-evaluation-node0 (verified: affinity, bind:0, lease held, generation 321)',
        'driver_pid':driver_identity['pid'],'rss':{'samples':sample_ref},'process_observations':observed_ref}
    lane = {'host':'mbit10','node':0,'lease_name':'mbit10-evaluation-node0','lease_generation':321,
        'exit_code':1,'started_utc':'2026-09-26T13:56:00-04:00','ended_utc':'2026-09-26T14:01:49-04:00'}
    audit = {'id':build.coverage.RUN_ID,'state':'failed','driver':write(driver),'lane':write({'socket_lane':lane}),
        'outer_exit':write('1\n', True),'process_observations':observed_ref,
        'lease_snapshot':write({'state':'released','lease':{'generation':321,'lease_name':lane['lease_name']},
                               'released_at':'2026-09-26T14:01:50-04:00'}),
        'observed_at':'2026-09-26T14:02:00-04:00','cleanup_state':'terminal_no_live_owned_processes',
        'owned_processes_absent':False,'owned_processes_nonrunning':True,
        'owned_processes':[{**driver_identity,'state':'absent'},{**descendant,'state':'absent'},
                           {**pane,'state':'Z','rss_bytes':0,'role':'tmux_launcher'}]}
    return audit, write, tmp_path/'proc'


def test_failed_coverage_cleanup_never_promotes_its_result(cleanup_fixture):
    audit, write, proc = cleanup_fixture
    result = build.coverage_cleanup(write(audit), 'a'*40, build.observer.stamp('2026-09-26T14:03:00-04:00'), proc)
    assert result['state'] == 'failed'


@pytest.mark.parametrize('fault', ['omitted-child','wrong-pane','future','success-label','missing-samples','held-lease',
                                 'active-child','late-start','elapsed','boolean-elapsed','bounds','driver-lane'])
def test_rehashed_failed_coverage_audit_requires_complete_terminal_ownership(cleanup_fixture, fault):
    audit, write, proc = cleanup_fixture
    if fault == 'omitted-child': audit['owned_processes'].pop(1)
    elif fault == 'wrong-pane': audit['owned_processes'][-1]['pid'] += 100
    elif fault == 'future': audit['observed_at'] = '2026-09-27T14:02:00-04:00'
    elif fault == 'success-label': audit['state'] = 'passed'
    elif fault == 'held-lease':
        lease = json.loads(build.coverage.a3.reference(audit['lease_snapshot']));lease['state']='held'
        audit['lease_snapshot']=write(lease)
    elif fault == 'missing-samples':
        observed=json.loads(build.coverage.a3.reference(audit['process_observations']));observed['resource_samples']=write('', True)
        audit['process_observations']=write(observed)
        driver=json.loads(build.coverage.a3.reference(audit['driver']));driver['process_observations']=audit['process_observations'];driver['rss']['samples']=observed['resource_samples']
        audit['driver']=write(driver)
    elif fault in {'late-start','elapsed','boolean-elapsed','bounds','driver-lane'}:
        driver=json.loads(build.coverage.a3.reference(audit['driver']))
        if fault=='late-start':driver.update(started='2026-09-26T16:00:00-04:00',finished='2026-09-26T16:00:01-04:00',host_wall_s=1)
        elif fault=='elapsed':driver['host_wall_s']=1
        elif fault=='boolean-elapsed':driver['host_wall_s']=True
        elif fault=='bounds':driver['bounds']['outer_seconds']=3601
        else:driver['lane']=driver['lane'].replace('321','322')
        audit['driver']=write(driver)
    else:
        row=audit['owned_processes'][1]; folder=proc/str(row['pid']);folder.mkdir(parents=True)
        fields=['S','1']+['0']*17+[str(row['start_ticks']),'0','1']
        (folder/'stat').write_text(f"{row['pid']} (fixture) "+' '.join(fields))
    with pytest.raises(ValueError):
        build.coverage_cleanup(write(audit), 'a'*40, build.observer.stamp('2026-09-26T14:03:00-04:00'), proc)


@pytest.mark.skipif(sys.platform != 'linux', reason='real Linux prctl/pidfd; no host invocation in local preparation')
@pytest.mark.parametrize('leader_failed', [False, True])
def test_linux_build_supervisor_reaps_detached_grandchild(tmp_path, leader_failed):
    script = r'''
import json, pathlib, sys, time
from datetime import timedelta
from scripts import bfs_t17_build_only as b
folder=pathlib.Path(sys.argv[1]); failed=sys.argv[2]=='True'
start=b.now(); owned=b.owned_descendants()
attempt=b.Attempt(folder/'raw',folder/'binary',b.Clock(start,start+timedelta(seconds=300)),owned,{'pid':1,'start_ticks':1})
# Disk reserve admission is the only simulated host condition in this subprocess fixture.
b.shutil.disk_usage=lambda p:type('Space',(),{'free':100*1024**3})()
inner="import os,pathlib,time; pathlib.Path(%r).write_text(str(os.getpid())); time.sleep(20)" % str(folder/'child.pid')
leader="import pathlib,subprocess,sys,time; subprocess.Popen([sys.executable,'-c',%r],start_new_session=True); p=pathlib.Path(%r); end=time.monotonic()+3\nwhile not p.exists() and time.monotonic()<end: time.sleep(.01)\nprint('{}'); sys.exit(%d)" % (inner,str(folder/'child.pid'),3 if failed else 0)
error=None
try:
    attempt.stage('fixture-build',[sys.executable,'-c',leader],5,pathlib.Path.cwd())
    attempt.receipt['state']='complete'
except ValueError as exc:error=exc
pid=int((folder/'child.pid').read_text())
assert not pathlib.Path('/proc',str(pid)).exists(), 'detached process survived the public stage boundary'
assert any(row['pid']==pid for row in attempt.receipt['stages'][0]['descendant_cleanup']['observed'])
code=attempt.finish(error)
assert bool(code)==failed
assert not pathlib.Path('/proc',str(pid)).exists()
assert len(attempt.receipt['stages'])==1
'''
    result = subprocess.run([sys.executable,'-c',script,str(tmp_path),str(leader_failed)],cwd=REPO,
                            capture_output=True,text=True,timeout=20)
    assert result.returncode == 0, result.stdout+result.stderr
