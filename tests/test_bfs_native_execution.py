"""Prospective native execution contracts. Synthetic fixtures, 2026-09-26 ET."""
from contextlib import contextmanager
import copy
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest
from scripts import bfs_native_campaign as campaign, bfs_process
from swdb import artifacts, processes
from test_bfs_campaign_cleanup import driver


def test_public_get_uses_raw_database_and_preserves_runtime(tmp_path, monkeypatch):
    source = Path(campaign.__file__).resolve().parents[1]
    checkout = tmp_path / 'checkout'; checkout.mkdir()
    paths = subprocess.check_output(['git', 'ls-files', '--', 'scripts', 'swdb', 'schemas',
        'vocab', 'tools/bfs_native', 'tests', 'pyproject.toml'], cwd=source, text=True).splitlines()
    for name in paths:
        target = checkout / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
    (checkout / 'records/machines').mkdir(parents=True)
    shutil.copyfile(source / 'records/machines/mbit10.yaml', checkout / 'records/machines/mbit10.yaml')
    subprocess.run(['git', 'init', '-q'], cwd=checkout, check=True)
    subprocess.run(['git', 'add', '.'], cwd=checkout, check=True)
    subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
        'commit', '-qm', 'Disposable runtime fixture'], cwd=checkout, check=True)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, text=True).strip()
    before = campaign.campaign_runtime(commit, root=checkout)
    runs, sources, builds = (tmp_path / name for name in ('raw', 'sources', 'builds'))
    for path in (runs, Path(str(runs)+'.dispatch'), sources, builds): path.mkdir()
    args = SimpleNamespace(id='db-cache-contract', protocol='unused-fixture-protocol',
        lane='fixture-lane', total_seconds=60, runs_dir=runs, source_runs_dir=sources,
        build_root=builds, records=checkout / 'records', repair_config=None)
    monkeypatch.setattr(campaign, 'ROOT', checkout)
    # Host admission alone is synthetic. Public get, SQLite creation, runtime
    # identity and raw storage accounting use their production implementations.
    monkeypatch.setattr(campaign.profile, '_verified_lane', lambda *_: 'fixture-lane')
    monkeypatch.setattr(campaign.os, 'statvfs',
        lambda _: SimpleNamespace(f_bavail=100 * 1024**3, f_frsize=1))
    worker = campaign.Driver(args)
    accounting = campaign.NativeSupervision.__new__(campaign.NativeSupervision)
    accounting.args = args; accounting.remaining = lambda *_: 60
    initial_bytes = accounting.account()['artifact_bytes']
    for _ in range(2):
        assert worker.call('get', 'mbit10', timeout=20)['id'] == 'mbit10'
        assert campaign.campaign_runtime(commit, root=checkout) == before
    database = worker.folder / 'swdb.sqlite'
    assert database.is_file() and not (checkout / 'build').exists()
    saved = json.loads((worker.folder / 'driver.json').read_text())
    assert saved['database'] == str(database)
    assert accounting.account()['artifact_bytes'] - initial_bytes >= database.stat().st_size
    before_wrapper = accounting.account()['artifact_bytes']
    wrapper_log = Path(str(runs)+'.dispatch')/'outer.stdout'
    wrapper_log.write_bytes(b'x'*32768)
    assert accounting.account()['artifact_bytes'] - before_wrapper >= 32768
    assert str(wrapper_log.parent) in accounting.account()['storage_paths']


@pytest.mark.parametrize('route',['campaign','shared'])
def test_signal_failure_still_reaps_and_preserves_timeout(driver,tmp_path,monkeypatch,route):
    worker,_=driver;children=[];popen=subprocess.Popen
    def launch(*args,**kwargs):
        child=popen(*args,**kwargs);children.append(child);return child
    monkeypatch.setattr(subprocess,'Popen',launch)
    def denied(*args):raise PermissionError('fixture denied signal')
    monkeypatch.setattr(processes.os,'killpg',denied)
    command=[sys.executable,'-c','import time;time.sleep(.2);print("{}")']
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            if route=='campaign':worker.execute('probe',command,timeout=.03)
            else:bfs_process.run_stage({'stages':[]},tmp_path,command,timeout=.03,deadline=time.monotonic()+3,cwd=tmp_path)
        assert children[0].returncode==0
        with pytest.raises(ChildProcessError):os.waitpid(children[0].pid,os.WNOHANG)
    finally:
        for child in children:child.wait(timeout=2)


@pytest.mark.parametrize('route',['campaign','shared'])
def test_final_hash_cannot_escape_total_deadline(driver,tmp_path,monkeypatch,route):
    worker,_=driver;clock=time.monotonic;offset=[0];digest=artifacts.file_hash
    def delayed(path):
        result=digest(path);offset[0]=40;return result
    monkeypatch.setattr(campaign.time,'monotonic',lambda:clock()+offset[0])
    if route=='campaign':monkeypatch.setattr(campaign.artifacts,'file_hash',delayed)
    else:monkeypatch.setattr(bfs_process,'file_hash',delayed)
    with pytest.raises(TimeoutError):
        if route=='campaign':worker.execute('last-get',[sys.executable,'-c','print("{}")'],timeout=2)
        else:bfs_process.run_stage({'stages':[]},tmp_path,[sys.executable,'-c','print("{}")'],timeout=2,deadline=clock()+3,cwd=tmp_path)
    path=worker.folder/'driver.json' if route=='campaign' else tmp_path/'driver.json'
    assert json.loads(path.read_text())['stages'][0]['state']=='failed'


def test_reaped_direct_child_never_authorizes_numeric_group_signal(monkeypatch):
    child=subprocess.Popen([sys.executable,'-c','pass'],start_new_session=True)
    child.wait(timeout=2)
    def forbidden(*_):pytest.fail('stale numeric group signal')
    monkeypatch.setattr(bfs_process.os,'killpg',forbidden)
    bfs_process.finish_legacy_group(child,time.monotonic()+1)


def test_original_timeout_survives_final_hash_failure(tmp_path,monkeypatch):
    def broken(_):raise OSError('fixture final hash failure')
    monkeypatch.setattr(bfs_process,'file_hash',broken)
    with pytest.raises(subprocess.TimeoutExpired):
        bfs_process.run_stage({'stages':[]},tmp_path,[sys.executable,'-c','import time;time.sleep(2)'],
            timeout=.03,deadline=time.monotonic()+1,cwd=tmp_path)
    row=json.loads((tmp_path/'driver.json').read_text())['stages'][0]
    assert 'TimeoutExpired' in row['reason'] and 'OSError' in row['finalization_error']


def test_generic_stage_charges_spawn_time_before_any_work_wait(tmp_path,monkeypatch):
    events=[];children=[];popen=subprocess.Popen;killpg=bfs_process.os.killpg
    def launch(*args,**kwargs):
        child=popen(*args,**kwargs);children.append(child);wait=child.wait
        def waiting(*args,**kwargs):events.append('wait');return wait(*args,**kwargs)
        child.wait=waiting;time.sleep(.08);return child
    def signal_group(*args):events.append('signal');return killpg(*args)
    monkeypatch.setattr(subprocess,'Popen',launch);monkeypatch.setattr(bfs_process.os,'killpg',signal_group)
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            bfs_process.run_stage({'stages':[]},tmp_path,[sys.executable,'-c','import time;time.sleep(3)'],
                timeout=.03,deadline=time.monotonic()+2,cwd=tmp_path)
        assert events[0]=='signal', 'startup must not grant another fresh work timeout'
    finally:
        for child in children:child.wait(timeout=2)


def test_successful_early_exit_still_charges_spawn_time(tmp_path,monkeypatch):
    popen=subprocess.Popen;children=[]
    def delayed(*args,**kwargs):
        child=popen(*args,**kwargs);children.append(child);time.sleep(.12);return child
    monkeypatch.setattr(subprocess,'Popen',delayed)
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            bfs_process.run_stage({'stages':[]},tmp_path,[sys.executable,'-c','print("{}")'],
                timeout=.02,deadline=time.monotonic()+2,cwd=tmp_path)
        assert children[0].returncode==0
        row=json.loads((tmp_path/'driver.json').read_text())['stages'][0]
        assert row['state']=='interrupted_or_timeout'
    finally:
        for child in children:child.wait(timeout=2)


def test_initial_receipt_time_cannot_borrow_cleanup_for_child_work(tmp_path,monkeypatch):
    save=bfs_process.save_receipt;popen=subprocess.Popen;children=[];first=True
    def delayed(folder,receipt):
        nonlocal first
        if first:
            first=False;time.sleep(.20)
        save(folder,receipt)
    def launch(*args,**kwargs):
        child=popen(*args,**kwargs);children.append(child);return child
    monkeypatch.setattr(bfs_process,'save_receipt',delayed)
    monkeypatch.setattr(subprocess,'Popen',launch)
    outer=time.monotonic()+2
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            bfs_process.run_stage({'stages':[]},tmp_path,[sys.executable,'-c',
                'import time;time.sleep(.20);print("explicit local clock fixture")'],
                timeout=.30,deadline=outer,cwd=tmp_path)
        assert len(children)==1 and children[0].returncode is not None
        with pytest.raises(ChildProcessError):os.waitpid(children[0].pid,os.WNOHANG)
        row=json.loads((tmp_path/'driver.json').read_text())['stages'][0]
        assert row['state']=='interrupted_or_timeout' and 'TimeoutExpired' in row['reason']
        assert 0 < row['timeout_s'] < .15
        assert row['host_wall_s'] >= .20 and time.monotonic() < outer
    finally:
        for child in children:child.wait(timeout=2)


def test_initial_receipt_exhaustion_rejects_before_spawning(tmp_path,monkeypatch):
    save=bfs_process.save_receipt;first=True
    def delayed(folder,receipt):
        nonlocal first
        if first:
            first=False;time.sleep(.08)
        save(folder,receipt)
    def forbidden(*args,**kwargs):pytest.fail('exhausted stage launched a child')
    monkeypatch.setattr(bfs_process,'save_receipt',delayed)
    monkeypatch.setattr(subprocess,'Popen',forbidden)
    with pytest.raises(TimeoutError,match='time budget exhausted'):
        bfs_process.run_stage({'stages':[]},tmp_path,[sys.executable,'-c','pass'],
            timeout=.02,deadline=time.monotonic()+2,cwd=tmp_path)
    row=json.loads((tmp_path/'driver.json').read_text())['stages'][0]
    assert row['state']=='interrupted_or_timeout' and row['returncode'] is None
    assert row['host_wall_s'] >= .08


class FakeBudget:
    def __init__(self,path,binding,deadline):self.path=Path(path);self.binding=binding;self.deadline=deadline;self.spent=0
    @staticmethod
    def create(path,end,deadline):Path(path).write_text('{}');return 'fixture-budget'
    @contextmanager
    def reservation(self,maximum=5,grace=False):
        start=time.monotonic()
        if start>=self.deadline or self.spent>=30:raise ValueError('fixture cleanup exhausted')
        try:yield min(start+maximum,self.deadline)
        finally:
            self.spent+=time.monotonic()-start
            if self.spent>30 or time.monotonic()>self.deadline:raise ValueError('fixture cleanup exhausted')
    def snapshot(self):return {'spent_seconds':self.spent,'budget_seconds':30,'reservations':{}}


class FakeOwned:
    def __init__(self,budget):self.budget=budget;self.history={}
    def sample(self):
        row={'pid':os.getpid(),'start_ticks':1,'parent_pid':os.getppid(),'rss_bytes':4096,'rss_pages':1}
        self.history[row['pid'],1]=row
        return {'sampled_at':campaign.now().isoformat(),'rss_bytes':4096,'rss_source':'linux_proc_pid_stat_rss_pages.v1',
                'page_size_bytes':4096,'processes':[row]}
    def remember(self,row):self.history[row['pid'],row['start_ticks']]=row
    def finish(self,child=None,direct=None):
        if child is not None:child.wait(timeout=2)
        return {'state':'all_owned_descendants_absent','subreaper':True,'observed':list(self.history.values()),'errors':[]}


@pytest.fixture
def supervised(tmp_path,monkeypatch):
    from scripts.bfs_owned_execution import Monitor
    monkeypatch.setattr(campaign.os,'statvfs',lambda _:SimpleNamespace(f_bavail=100*1024**3,f_frsize=1))
    monkeypatch.setattr(campaign.profile,'_verified_lane',lambda *_:'fixture-lane')
    monkeypatch.setattr(campaign,'Store',lambda _:SimpleNamespace(get=lambda *_:{},by_id={}))
    start=campaign.now()
    args=SimpleNamespace(id='fixture-native',protocol='fixture-protocol',lane='mbit10-evaluation-node1',
        total_seconds=14400,runs_dir=tmp_path/'raw',source_runs_dir=tmp_path/'sources',build_root=tmp_path/'builds',
        records=tmp_path/'records',repair_config=None,provider_config=None,existing_candidate='fixture-candidate',
        outer_started=start.isoformat(),outer_deadline=(start+timedelta(seconds=14400)).isoformat(),
        pane_pid=os.getppid(),pane_start_ticks=1,expected_commit='a'*40,proposal=tmp_path/'proposal.json',
        packages=['one','two'],reassessment=None)
    for path in (args.runs_dir,Path(str(args.runs_dir)+'.dispatch'),args.source_runs_dir,args.build_root,args.records):path.mkdir()
    args.proposal.write_text('{}')
    worker=campaign.Driver(args)
    def identity(pid):return {'pid':pid,'parent_pid':os.getppid() if pid==os.getpid() else os.getpid(),'start_ticks':1}
    lifecycle=SimpleNamespace(SharedCleanup=FakeBudget,Owned=FakeOwned,identity=identity,
        ancestry=lambda ident,pane:[ident,pane],Monitor=lambda callback:Monitor(callback,interrupt=False))
    value=campaign.NativeSupervision(worker,lifecycle=lifecycle);worker.supervision=value
    value.guard.observe()
    return value


@pytest.mark.parametrize('fault',['reset','short','long','total'])
def test_supervised_clock_cannot_reset_or_extend(supervised,fault):
    c=supervised;args=c.args
    if fault=='reset':args.outer_started=(campaign.now()+timedelta(seconds=1)).isoformat()
    elif fault=='short':args.outer_deadline=(timestamp(args.outer_deadline)-timedelta(seconds=1)).isoformat()
    elif fault=='long':args.outer_deadline=(timestamp(args.outer_deadline)+timedelta(seconds=1)).isoformat()
    else:args.total_seconds=21600
    with pytest.raises(ValueError,match='outer clock'):
        campaign.NativeSupervision(c.driver,lifecycle=c.lifecycle)


def timestamp(value):return campaign.timestamp(value)


@pytest.mark.parametrize('fault',['rss','storage','builds','reserve','gap'])
def test_native_resource_bounds_do_not_inherit_simulator_limit(supervised,monkeypatch,fault):
    c=supervised
    if fault=='rss':
        original=c.owner.sample
        def sample():
            row=original();row['rss_bytes']=campaign.NATIVE_BOUNDS['sampled_rss_bytes']+1;return row
        monkeypatch.setattr(c.owner,'sample',sample)
    elif fault in {'storage','builds'}:
        from scripts import bfs_dx100_coverage_execution as coverage
        monkeypatch.setattr(coverage,'artifact_bytes',lambda paths:17*1024**3 if fault=='storage' else (5*1024**3 if len(paths)==1 else 6*1024**3))
    elif fault=='reserve':monkeypatch.setattr(campaign.os,'statvfs',lambda _:SimpleNamespace(f_bavail=0,f_frsize=1))
    else:c.last-=timedelta(seconds=31)
    with pytest.raises(ValueError):c.observe()


@pytest.mark.parametrize('fault',['hash','first-write','second-write','storage'])
def test_final_persistence_cannot_retain_success_after_crossing_bound(supervised,monkeypatch,fault):
    c=supervised;c.driver.receipt['state']='evaluated';c.observe();writes=[0]
    if fault=='hash':
        original=campaign.reference
        def reference(path):
            value=original(path);c.deadline=time.monotonic()-1;return value
        monkeypatch.setattr(campaign,'reference',reference)
    else:
        original=c.driver.save
        def save():
            original();writes[0]+=1
            if writes[0]==(2 if fault=='second-write' else 1):
                if fault=='storage':monkeypatch.setattr(campaign.os,'statvfs',lambda _:SimpleNamespace(f_bavail=0,f_frsize=1))
                else:c.deadline=time.monotonic()-1
        monkeypatch.setattr(c.driver,'save',save)
    with pytest.raises(ValueError):c.finalize()
    assert json.loads((c.driver.folder/'driver.json').read_text())['state']=='failed'


def test_supervised_public_failure_json_and_original_error_are_retained(supervised):
    c=supervised
    result=c.driver.execute('fixture',[sys.executable,'-c','print("{\\"outcome\\":\\"failed\\"}");raise SystemExit(3)'],timeout=2,required=False)
    assert result=={'outcome':'failed'}
    row=c.driver.receipt['stages'][0]
    assert row['returncode']==3 and row['state']=='failed' and row['identity']['pid']
    c.driver.receipt['state']='incomplete';c.finalize()
    assert c.driver.receipt['cleanup_verified'] is False
    assert row['identity'] in c.driver.receipt['process_observations']['owned_processes']


def test_supervised_cleanup_failure_preserves_original_timeout_and_reap(supervised,monkeypatch):
    c=supervised;children=[];popen=subprocess.Popen
    def launch(*args,**kwargs):
        child=popen(*args,**kwargs);children.append(child);return child
    def finish(child=None,direct=None):
        if child is not None:child.wait(timeout=2)
        raise PermissionError('fixture cleanup signal denied after independent wait')
    monkeypatch.setattr(subprocess,'Popen',launch);monkeypatch.setattr(c.owner,'finish',finish)
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        c.driver.execute('fixture',[sys.executable,'-c','import time;time.sleep(.1);print("{}")'],timeout=.02)
    assert isinstance(caught.value.__cause__,PermissionError)
    assert children[0].returncode==0
    with pytest.raises(ChildProcessError):os.waitpid(children[0].pid,os.WNOHANG)
    saved=json.loads((c.driver.folder/'driver.json').read_text())['stages'][0]
    assert 'TimeoutExpired' in saved['reason'] and 'PermissionError' in saved['cleanup_error']


@pytest.mark.parametrize('fault',[None,'packages','proposal','bounds','commit','future'])
def test_admission_is_exact_before_any_public_stage(supervised,monkeypatch,fault):
    c=supervised;runtime={'fixture_only':True};calls=[]
    monkeypatch.setattr(campaign,'campaign_runtime',lambda _:runtime)
    monkeypatch.setattr(campaign,'validate_linux_proof',lambda *args:calls.append('proof'))
    monkeypatch.setattr(c,'capacity',lambda:calls.append('capacity') or {'fixture_only':True})
    value={'format':'swdb.bfs.native-campaign-admission.v1','id':c.args.id,
        'prepared_at':c.begin.isoformat(),'code_commit':c.args.expected_commit,'runtime':runtime,
        'inputs':campaign.campaign_inputs(c.args),'bounds':copy.deepcopy(campaign.NATIVE_BOUNDS),'linux_proof':{}}
    if fault=='packages':value['inputs']['packages']=list(reversed(value['inputs']['packages']))
    elif fault=='proposal':value['inputs']['proposal']['sha256']='f'*64
    elif fault=='bounds':value['bounds']['sampled_rss_bytes']=52*1024**3
    elif fault=='commit':value['code_commit']='b'*40
    elif fault=='future':value['prepared_at']=(c.begin+timedelta(seconds=1)).isoformat()
    path=Path(str(c.args.runs_dir)+'.dispatch')/'admission.json';path.write_text(json.dumps(value))
    c.args.supervision_admission=path;c.args.supervision_sha256=artifacts.file_hash(path)
    try:
        if fault:
            with pytest.raises(ValueError,match='identity differs'):c.admit()
            assert calls==[] and c.driver.receipt['stages']==[]
        else:
            c.admit();assert calls==['proof','capacity'] and c.driver.receipt['runtime']==runtime
    finally:c.guard.stop(c.deadline)


def test_final_cleanup_identities_and_continuous_guard_are_retained(supervised,monkeypatch):
    c=supervised;original=c.owner.finish;identity={'pid':99999,'start_ticks':123}
    def finish(*args):
        assert not c.guard.stop_event.is_set(), 'guard must cover final tree cleanup'
        c.owner.history[99999,123]=identity
        return original(*args)
    monkeypatch.setattr(c.owner,'finish',finish)
    c.driver.receipt['state']='evaluated';c.finalize()
    assert identity in c.driver.receipt['process_observations']['owned_processes']
    assert c.guard.stop_event.is_set()


def test_slow_monitor_stop_is_charged_to_remaining_cleanup(supervised,monkeypatch):
    c=supervised;clock=time.monotonic;offset=[0];c.budget.spent=29
    monkeypatch.setattr(campaign.time,'monotonic',lambda:clock()+offset[0])
    def stop(until):
        assert until<=c.deadline
        offset[0]+=2
    monkeypatch.setattr(c.guard,'stop',stop)
    c.driver.receipt['state']='evaluated'
    with pytest.raises(ValueError,match='cleanup exhausted'):c.finalize()
    assert c.driver.receipt['state']=='failed' and c.budget.spent>=31
    assert 'failure_persistence_error' in c.driver.receipt


def proof_fixture(tmp_path):
    runtime={'python':{'path':str(Path(sys.executable).resolve())},'fixture_only':True}
    admission={'code_commit':'a'*40,'runtime':runtime,'prepared_at':'2026-09-26T16:00:00-04:00'}
    junit=tmp_path/'result.xml';junit.write_text('<testsuite><testcase name="test_linux_campaign_reaps_detached_child[False]"/><testcase name="test_linux_campaign_reaps_detached_child[True]"/></testsuite>')
    stdout=tmp_path/'stdout';stdout.write_text('Synthetic fixture receipt only\n')
    value={'format':'swdb.bfs.linux-fixture.v1','kind':'native_campaign_owned_cleanup','host':'mbit10','platform':'linux',
        'evidence_kind':'contract_fixture','state':'passed','returncode':0,'code_commit':'a'*40,'runtime':runtime,
        'started':'2026-09-26T15:00:00-04:00','finished':'2026-09-26T15:00:01-04:00',
        'command':[sys.executable,'-m','pytest','tests/test_bfs_native_execution.py::test_linux_campaign_reaps_detached_child','--junitxml='+str(junit)],
        'junit':campaign.reference(junit),'stdout':campaign.reference(stdout)}
    return admission,value,junit


@pytest.mark.parametrize('fault',[None,'skip','missing-case','runtime','future','true-return','command','overlong'])
def test_linux_proof_is_exact_and_fixture_only(tmp_path,fault):
    admission,value,junit=proof_fixture(tmp_path)
    if fault=='skip':junit.write_text(junit.read_text().replace('/>','><skipped/></testcase>',1));value['junit']=campaign.reference(junit)
    elif fault=='missing-case':junit.write_text('<testsuite><testcase name="other"/></testsuite>');value['junit']=campaign.reference(junit)
    elif fault=='runtime':value['runtime']={'changed':True}
    elif fault=='future':value['finished']='2026-09-26T17:00:00-04:00'
    elif fault=='true-return':value['returncode']=True
    elif fault=='command':value['command'][3]='other.py'
    elif fault=='overlong':value['finished']='2026-09-26T15:01:31-04:00'
    path=tmp_path/'proof.json';path.write_text(json.dumps(value));ref=campaign.reference(path)
    if fault:
        with pytest.raises(ValueError):campaign.validate_linux_proof(ref,admission)
    else:assert campaign.validate_linux_proof(ref,admission)==ref


@pytest.mark.skipif(sys.platform!='linux',reason='actual Linux subreaper/pidfd proof required')
@pytest.mark.parametrize('failure',[False,True])
def test_linux_campaign_reaps_detached_child(tmp_path,failure):
    # The actual owner lives in a separate fixture process, never in pytest.
    program=r'''
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
import json,os,sys
from scripts import bfs_native_campaign as c
from scripts import bfs_owned_execution as own
root=Path(sys.argv[1]);failure=sys.argv[2]=='True';start=c.now()
c.profile._verified_lane=lambda *_:'fixture-lane'
c.Store=lambda _:SimpleNamespace(get=lambda *_:{})
c.os.statvfs=lambda _:SimpleNamespace(f_bavail=100*1024**3,f_frsize=1)
a=SimpleNamespace(id='linux-fixture',protocol='fixture',lane='mbit10-evaluation-node1',total_seconds=14400,
 runs_dir=root/'raw',source_runs_dir=root/'source',build_root=root/'build',records=root/'records',repair_config=None,
 outer_started=start.isoformat(),outer_deadline=(start+timedelta(seconds=14400)).isoformat(),
 pane_pid=os.getppid(),pane_start_ticks=own.identity(os.getppid())['start_ticks'])
for path in (a.runs_dir,Path(str(a.runs_dir)+'.dispatch'),a.source_runs_dir,a.build_root,a.records):path.mkdir()
w=c.Driver(a);s=c.NativeSupervision(w);w.supervision=s;s.guard.start()
code='import subprocess,sys;subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"],start_new_session=True);print("{}");sys.exit('+str(3 if failure else 0)+')'
result=w.execute('fixture',[sys.executable,'-c',code],timeout=5,required=False)
assert result=={}
row=w.receipt['stages'][0];assert row['returncode']==(3 if failure else 0)
assert row['cleanup']['state']=='all_owned_descendants_absent'
assert not [p for p in s.owner.sample()['processes'] if p['pid']!=os.getpid()]
w.receipt['state']='incomplete' if failure else 'evaluated';s.finalize()
assert (row['identity']['pid'],row['identity']['start_ticks']) in {(p['pid'],p['start_ticks']) for p in w.receipt['process_observations']['owned_processes']}
assert w.receipt['cleanup_accounting']['spent_seconds']<30
print(json.dumps({'fixture_only':True,'state':w.receipt['state']}))
'''
    result=subprocess.run([sys.executable,'-c',program,str(tmp_path),str(failure)],capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['fixture_only'] is True
