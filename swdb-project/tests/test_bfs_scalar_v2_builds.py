"""Scalar build orchestration contracts, never empirical evidence. Updated 2026-09-29 ET."""
import copy
from contextlib import nullcontext
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
import xml.etree.ElementTree as XML

import pytest
from scripts import bfs_scalar_v2_builds as build
from swdb import artifacts
from swdb.store import Store


def test_fixed_four_requests_preserve_old_source_and_caps():
    manifest=build.load_manifest(); store=Store(build.RECORDS)
    assert [(x['source'],x['role']) for x in manifest['operations']]==[
        ('dx100','primary'),('dx100','diagnostic'),('upstream','primary'),('upstream','diagnostic')]
    for op in manifest['operations']:
        request=json.loads((build.ROOT/op['request']['path']).read_text())
        prior=store.get(op['historical_v1_build']['id'])['request']
        assert [k for k in request if request[k]!=prior[k]]==['id']
        assert store.get(request['candidate'])['artifact_role']=='source_baseline'
    assert len(build.record_pins(manifest))==8


@pytest.fixture
def clock(monkeypatch):
    value=SimpleNamespace(mono=100.,wall=datetime(2026,9,26,21,tzinfo=build.own.ET))
    monkeypatch.setattr(build.time,'monotonic',lambda:value.mono)
    monkeypatch.setattr(build,'now',lambda:value.wall)
    value.advance=lambda seconds:(setattr(value,'mono',value.mono+seconds),setattr(value,'wall',value.wall+timedelta(seconds=seconds)))
    return value


def make_clock(clock):
    return build.Clock(clock.wall.isoformat(),(clock.wall+timedelta(seconds=1200)).isoformat())


def test_one_clock_preserves_ancillary_budget_across_all_compiles(clock):
    policy=make_clock(clock); clock.advance(100)
    for _ in range(4):
        with policy.compile(): clock.advance(20);policy.check()
    assert policy.compile_seconds==80 and policy.ancillary()==100
    clock.advance(111)
    with pytest.raises(ValueError,match='210-second'):policy.check()
    assert policy.hard==1300 and policy.work==1270


@pytest.mark.parametrize('fault',['future','late','extended','wall','work'])
def test_original_clock_cannot_borrow_startup_or_final_reserve(clock,fault):
    if fault in ('future','late','extended'):
        begin=clock.wall+timedelta(seconds=1 if fault=='future' else -31 if fault=='late' else 0)
        end=begin+timedelta(seconds=1201 if fault=='extended' else 1200)
        with pytest.raises(ValueError,match='original 1200'):build.Clock(begin.isoformat(),end.isoformat())
    else:
        policy=make_clock(clock)
        with policy.compile():
            if fault=='wall':clock.wall += timedelta(seconds=1171)
            else:clock.mono += 1171
            with pytest.raises(ValueError,match='original scalar'):policy.check()


def test_ancillary_failure_still_allows_bounded_failure_finalization(clock):
    policy=make_clock(clock);clock.advance(211);policy.begin_finalization()
    with pytest.raises(ValueError,match='ancillary'):policy.check(True)
    clock.advance(990)
    with pytest.raises(ValueError,match='deadline'):policy.check(True)


@pytest.mark.parametrize('transition',['compile-exit','finalizing'])
def test_monitor_gets_one_coherent_clock_snapshot(clock,transition):
    """Force a transition between the monitor's reads of related fields."""
    read=threading.Event();resume=threading.Event();finished=threading.Event();errors=[];values=[]
    class ScheduledClock(build.Clock):
        def __getattribute__(self,key):
            value=super().__getattribute__(key)
            if key=='compiling' and threading.current_thread().name=='clock-monitor' and not read.is_set():
                read.set()
                if not resume.wait(1):raise RuntimeError('test snapshot did not resume')
            return value
    policy=ScheduledClock(clock.wall.isoformat(),(clock.wall+timedelta(seconds=1200)).isoformat())
    context=policy.compile() if transition=='compile-exit' else nullcontext()
    context.__enter__();clock.advance(20)
    def observe():
        try:values.append(policy.ancillary())
        except BaseException as exc:errors.append(exc)
    def change():
        try:
            if transition=='compile-exit':context.__exit__(None,None,None)
            else:policy.begin_finalization()
        except BaseException as exc:errors.append(exc)
        finally:finished.set()
    monitor=threading.Thread(target=observe,name='clock-monitor');monitor.start();assert read.wait(1)
    writer=threading.Thread(target=change);writer.start()
    try:assert not finished.wait(.02), 'transition must wait for the whole accounting snapshot'
    finally:resume.set();monitor.join(1);writer.join(1)
    assert not errors and not monitor.is_alive() and not writer.is_alive()
    expected=0 if transition=='compile-exit' else 20
    assert values==[expected] and policy.ancillary()==expected
    clock.advance(3)
    assert policy.ancillary()==(3 if transition=='compile-exit' else 20)


def test_controlled_child_environment_removes_loader_and_compiler_overrides(tmp_path,monkeypatch):
    for name in build.REMOVED:monkeypatch.setenv(name,'fixture-override')
    result=build.controlled_environment(tmp_path)
    assert all(name not in result for name in build.REMOVED)
    assert result['PATH']=='/usr/bin:/bin' and result['TMPDIR']==str(tmp_path)
    assert result['PYTHONNOUSERSITE']=='1' and result['PYTHONDONTWRITEBYTECODE']=='1'


@pytest.mark.parametrize('name',['LD_PRELOAD','LD_LIBRARY_PATH'])
def test_supervisor_refuses_loader_override_before_project_imports(name):
    env={**os.environ,name:''}
    result=subprocess.run([sys.executable,'-s',str(Path(build.__file__)),'--help'],env=env,
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=5)
    assert result.returncode!=0 and 'unset loader overrides' in result.stderr


class FixtureOwned:
    """Actual direct subprocess reap only; this is not Linux descendant proof."""
    def __init__(self,budget):self.budget=budget;self.history={};self.children=[]
    def remember(self,row):self.history[row['pid'],row['start_ticks']]=row
    def sample(self):
        row={'pid':os.getpid(),'parent_pid':os.getppid(),'start_ticks':1,'rss_pages':1,'rss_bytes':4096,'state':'R'}
        self.history[row['pid'],row['start_ticks']]=row
        return {'sampled_at':build.now().isoformat(),'processes':[row],'rss_bytes':4096,
                'page_size_bytes':4096,'rss_source':build.own.RSS_SOURCE}
    def finish(self,child=None,direct=None):
        if child is not None:
            self.children.append(child)
            if child.poll() is None:child.terminate()
            child.wait(timeout=1)
        return {'state':'all_owned_descendants_absent','errors':[],'subreaper':True,'observed':list(self.history.values()),
                'direct_reaped':True,'shared_budget':str(self.budget.path),'checked_at':build.now().isoformat()}


@pytest.fixture
def worker(tmp_path,monkeypatch):
    manifest=build.load_manifest(); raw=tmp_path/'raw';Path(str(raw)+'.dispatch').mkdir()
    builds=tmp_path/'builds';builds.mkdir(); records=tmp_path/'records';records.mkdir()
    monkeypatch.setattr(build,'RAW',raw);monkeypatch.setattr(build,'BUILDS',builds);monkeypatch.setattr(build,'RECORDS',records)
    monkeypatch.setattr(build.os,'statvfs',lambda _:SimpleNamespace(f_bavail=100*1024**3,f_frsize=1))
    monkeypatch.setattr(build.own,'identity',lambda pid:{'pid':pid,'start_ticks':1,'parent_pid':os.getpid()})
    monkeypatch.setattr(build.own,'ancestry',lambda ident,pane:[ident,pane])
    monkeypatch.setattr(build.own,'Owned',FixtureOwned)
    begin=build.now();clock=build.Clock(begin.isoformat(),(begin+timedelta(seconds=1200)).isoformat())
    args=SimpleNamespace(pane_pid=999,pane_start_ticks=1,lane=1,expected_commit='a'*40,
                         admission=Path(str(raw)+'.dispatch')/'admission.json',admission_sha256='fixture')
    driver=build.Driver(args,manifest,clock)
    driver.guard=build.own.Monitor(driver.observe,interrupt=False);driver.guard.start()
    yield driver
    if driver.guard.thread.is_alive():driver.guard.stop(time.monotonic()+1)


def tiny_public_root(path):
    package=path/'swdb';package.mkdir()
    (package/'__init__.py').write_text('')
    (package/'__main__.py').write_text('''import sys,json,time
if sys.argv[1]=='slow':time.sleep(.3)
if sys.argv[1]=='bad':sys.exit(7)
print(json.dumps({'argv':sys.argv[1:]}))
''')


@pytest.mark.parametrize('mode',['ok','bad','slow'])
def test_actual_public_child_keeps_external_db_and_shared_cleanup(worker,tmp_path,monkeypatch,mode):
    tiny_public_root(tmp_path);monkeypatch.setattr(build,'ROOT',tmp_path)
    if mode=='ok':
        result=worker.call(['ok'],timeout=1)
        assert result['argv'][-6:]==['--records',str(build.RECORDS),'--db',str(build.RAW/'swdb.sqlite'),'--format','json']
    else:
        with pytest.raises((ValueError,subprocess.TimeoutExpired)):
            worker.call([mode],timeout=.03 if mode=='slow' else 1,compile=True)
    stage=worker.receipt['stages'][0]
    assert stage['returncode']==(0 if mode=='ok' else 7 if mode=='bad' else -15)
    assert stage['cleanup']['direct_reaped'] and all(child.returncode is not None for child in worker.owner.children)
    assert worker.budget.snapshot()['spent_seconds']>0
    assert not worker.budget.snapshot()['reservations']
    if mode=='ok':assert worker.clock.compile_seconds==0
    else:assert 0 < worker.clock.compile_seconds < 2


def test_ancillary_exhaustion_refuses_child_before_spawn(worker,monkeypatch):
    worker.clock.compile_seconds=-211
    with pytest.raises(ValueError,match='ancillary'):worker.call(['ok'])
    assert worker.receipt['stages']==[] and worker.owner.children==[]


@pytest.mark.parametrize('location',['raw','dispatch','build','record','db-sidecar'])
def test_all_new_artifact_locations_are_charged(worker,monkeypatch,location):
    initial=worker.account()['artifact_bytes']; cap=initial+32768
    monkeypatch.setitem(build.BOUNDS,'artifact_bytes',cap)
    op=worker.manifest['operations'][0]
    if location=='raw':path=build.RAW/'retained.log'
    elif location=='dispatch':path=Path(str(build.RAW)+'.dispatch')/'outer.stdout'
    elif location=='build':path=build.BUILDS/op['id']/'bfs'
    elif location=='record':path=build.RECORDS/build.canonical_path('evaluation',op['id'])
    else:path=build.RAW/'swdb.sqlite-wal'
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'x'*65536)
    with pytest.raises(ValueError,match='artifact/build'):worker.account()


def test_build_subset_is_independent_of_total_cap(worker,monkeypatch):
    monkeypatch.setitem(build.BOUNDS,'build_bytes',16384)
    (worker.temporary/'compiler.tmp').write_bytes(b'x'*32768)
    with pytest.raises(ValueError,match='artifact/build'):worker.account()


def test_existing_historical_records_are_not_new_output_charge(worker):
    before=worker.account()['artifact_bytes']
    (build.RECORDS/'old.yaml').write_bytes(b'x'*65536)
    assert worker.account()['artifact_bytes']==before


@pytest.mark.parametrize('fault',['cleanup','guard','final-write'])
def test_failure_is_retained_without_masking_first_error(worker,monkeypatch,fault):
    original=RuntimeError('original public failure');secondary=ValueError('secondary '+fault)
    if fault=='cleanup':monkeypatch.setattr(build.own,'verified_finish',lambda *args:(_ for _ in ()).throw(secondary))
    elif fault=='guard':
        real=worker.guard.stop
        def stop(until):real(until);raise secondary
        monkeypatch.setattr(worker.guard,'stop',stop)
    else:
        real=build.save_receipt;calls=[]
        def save(folder,value):
            calls.append(1)
            if len(calls)==1:raise secondary
            real(folder,value)
        monkeypatch.setattr(build,'save_receipt',save)
    with pytest.raises(RuntimeError) as caught:worker.finalize(original)
    assert caught.value is original
    saved=json.loads((worker.folder/'driver.json').read_text())
    assert saved['state']=='failed' and saved['reason']=='RuntimeError: original public failure'
    assert worker.budget.snapshot()['spent_seconds']<=30
    assert not worker.guard.thread.is_alive()


def test_successful_finalization_retains_samples_and_shared_ledger(worker):
    worker.receipt['state']='complete';worker.finalize(None)
    value=json.loads((worker.folder/'driver.json').read_text())
    assert value['state']=='complete' and value['resource_validation']['samples']>=2
    assert value['cleanup']['direct_reaped'] and value['cleanup_verified'] is False
    assert value['process_observations']['owned_processes']
    assert not worker.budget.snapshot()['reservations']
    assert worker.budget.snapshot()['spent_seconds']<=30


@pytest.fixture
def proof(tmp_path):
    runtime={'commit':'a'*40,'python':{'path':'/fixture/python','sha256':'d'*64},
             'files':{name:artifacts.digest(name) for name in build.PROOF_FILES}}
    def ref(name,value):
        path=tmp_path/name;path.write_text(json.dumps(value));return {'path':str(path),'sha256':artifacts.file_hash(path)}
    xml=XML.Element('testsuite')
    names=['test_linux_owned_stage_reaps_detached_child[False]','test_linux_owned_stage_reaps_detached_child[True]',
        'test_linux_nested_interruption_uses_one_cleanup_budget','test_linux_term_resistant_nested_cleanup_keeps_final_kill_reserve']
    for name in names:XML.SubElement(xml,'testcase',name=name)
    junit=tmp_path/'junit.xml';junit.write_bytes(XML.tostring(xml))
    output=tmp_path/'stdout';output.write_text('contract fixture only')
    tested=copy.deepcopy(runtime);tested['commit']='b'*40
    driver=ref('driver.json',{'state':'complete','kind':'owned_cleanup','code_commit':'b'*40,'returncode':0,'runtime':tested})
    pending=ref('pending.json',{'state':'tests_passed_cleanup_unverified','driver':driver,'code_commit':'b'*40})
    value={'format':'swdb.bfs.linux-fixture.v1','kind':'owned_cleanup','state':'passed','host':'mbit10','platform':'linux',
       'evidence_kind':'contract_fixture','independent_cleanup_verified':True,'returncode':0,'code_commit':'b'*40,
       'runtime_sha256':copy.deepcopy(runtime['files']),'driver':driver,'pending':pending,
       'started':'2026-09-26T10:00:00-04:00','finished':'2026-09-26T10:00:01-04:00','audited_at':'2026-09-26T10:01:00-04:00',
       'junit':{'path':str(junit),'sha256':artifacts.file_hash(junit)},'stdout':{'path':str(output),'sha256':artifacts.file_hash(output)}}
    audit={'state':'passed','code_commit':value['code_commit'],'lease_released':True,
           'driver':value['driver'],'pending':value['pending'],'kind':'owned_cleanup','route':'standard'}
    def seal():value['terminal_audit']=ref('audit.json',audit);return ref('proof.json',value)
    return value,audit,runtime,seal


def storage_proof_fixture(proof):
    """Reseal the exact approved fifth-case shape using synthetic files only."""
    value,audit,runtime,seal=proof
    dependency='scripts/bfs_storage.py';digest=artifacts.digest(dependency)
    runtime['files'][dependency]=digest;value['runtime_sha256'][dependency]=digest
    path=Path(value['driver']['path']);driver=json.loads(path.read_text())
    driver['runtime']['files'][dependency]=digest;path.write_text(json.dumps(driver))
    value['driver']['sha256']=artifacts.file_hash(path);audit['driver']=value['driver']
    path=Path(value['pending']['path']);pending=json.loads(path.read_text());pending['driver']=value['driver']
    path.write_text(json.dumps(pending));value['pending']['sha256']=artifacts.file_hash(path);audit['pending']=value['pending']
    path=Path(value['junit']['path']);xml=XML.fromstring(path.read_bytes())
    XML.SubElement(xml,'testcase',name='test_linux_storage_observation_handles_sqlite_journal_unlink')
    path.write_bytes(XML.tostring(xml));value['junit']['sha256']=artifacts.file_hash(path)
    return proof


@pytest.mark.parametrize('required',[False,True])
def test_exact_five_case_proof_adds_storage_runtime_identity(proof,required):
    value,audit,runtime,seal=storage_proof_fixture(proof)
    result=build.validate_proof(seal(),runtime,build.stamp('2026-09-26T11:00:00-04:00'),
                                require_storage_case=required)
    assert result['identical_tested_files']['scripts/bfs_storage.py']==runtime['files']['scripts/bfs_storage.py']
    assert len(result['identical_tested_files'])==len(build.PROOF_FILES)+1


def test_historical_four_case_proof_cannot_satisfy_required_storage_case(proof):
    value,audit,runtime,seal=proof
    with pytest.raises(ValueError,match='SQLite'):
        build.validate_proof(seal(),runtime,build.stamp('2026-09-26T11:00:00-04:00'),require_storage_case=True)


@pytest.mark.parametrize('fault',['unknown-extra','duplicate','skipped','failed','runtime-missing',
    'runtime-changed','tested-missing','tested-changed','proof-missing','proof-changed','all-null'])
def test_five_case_proof_rejects_extra_cases_or_unbound_storage(proof,fault):
    value,audit,runtime,seal=storage_proof_fixture(proof);key='scripts/bfs_storage.py'
    if fault=='all-null':
        runtime['files'][key]=value['runtime_sha256'][key]=None
        path=Path(value['driver']['path']);driver=json.loads(path.read_text());driver['runtime']['files'][key]=None
        path.write_text(json.dumps(driver));value['driver']['sha256']=artifacts.file_hash(path);audit['driver']=value['driver']
        path=Path(value['pending']['path']);pending=json.loads(path.read_text());pending['driver']=value['driver']
        path.write_text(json.dumps(pending));value['pending']['sha256']=artifacts.file_hash(path);audit['pending']=value['pending']
    elif fault in {'unknown-extra','duplicate','skipped','failed'}:
        path=Path(value['junit']['path']);xml=XML.fromstring(path.read_bytes())
        if fault=='unknown-extra':XML.SubElement(xml,'testcase',name='unapproved')
        elif fault=='duplicate':XML.SubElement(xml,'testcase',name=xml[-1].get('name'))
        else:XML.SubElement(xml[-1],'skipped' if fault=='skipped' else 'failure')
        path.write_bytes(XML.tostring(xml));value['junit']['sha256']=artifacts.file_hash(path)
    elif fault.startswith('runtime'):
        if fault.endswith('missing'):runtime['files'].pop(key)
        else:runtime['files'][key]='e'*64
    elif fault.startswith('proof'):
        if fault.endswith('missing'):value['runtime_sha256'].pop(key)
        else:value['runtime_sha256'][key]='e'*64
    else:
        path=Path(value['driver']['path']);driver=json.loads(path.read_text())
        if fault.endswith('missing'):driver['runtime']['files'].pop(key)
        else:driver['runtime']['files'][key]='e'*64
        path.write_text(json.dumps(driver));value['driver']['sha256']=artifacts.file_hash(path);audit['driver']=value['driver']
        path=Path(value['pending']['path']);pending=json.loads(path.read_text());pending['driver']=value['driver']
        path.write_text(json.dumps(pending));value['pending']['sha256']=artifacts.file_hash(path);audit['pending']=value['pending']
    with pytest.raises(ValueError):
        build.validate_proof(seal(),runtime,build.stamp('2026-09-26T11:00:00-04:00'))


def test_prior_proof_commit_can_differ_only_with_identical_helpers(proof):
    value,audit,runtime,seal=proof
    result=build.validate_proof(seal(),runtime,build.stamp('2026-09-26T11:00:00-04:00'))
    assert result['actual_proof_commit']=='b'*40 and result['driver_commit']=='a'*40


@pytest.mark.parametrize('fault',['helper','python','unsealed','failed-audit','late','fixture-promoted','pending','skipped'])
def test_prior_proof_substitutions_fail(proof,fault):
    value,audit,runtime,seal=proof
    if fault=='helper':runtime['files'][build.PROOF_FILES[0]]='0'*64
    elif fault=='python':runtime['python']['sha256']='0'*64
    elif fault=='unsealed':value['independent_cleanup_verified']=False
    elif fault=='failed-audit':audit['state']='failed'
    elif fault=='late':value['finished']='2026-09-26T10:02:00-04:00'
    elif fault=='fixture-promoted':value['evidence_kind']='execution'
    elif fault=='pending':audit['pending']={'path':'other'}
    else:
        path=Path(value['junit']['path']);root=XML.fromstring(path.read_bytes())
        XML.SubElement(root.find('testcase'),'skipped');path.write_bytes(XML.tostring(root));value['junit']['sha256']=artifacts.file_hash(path)
    with pytest.raises(ValueError):build.validate_proof(seal(),runtime,build.stamp('2026-09-26T11:00:00-04:00'))


@pytest.fixture
def collection(worker,tmp_path,monkeypatch):
    """Synthetic compiler outputs, real retained byte/manifest and request checks."""
    source=tmp_path/'source';source.mkdir();(source/'bfs.cc').write_text('// contract fixture only\n')
    artifact=artifacts.identify(source)
    worker.manifest=copy.deepcopy(worker.manifest)
    operations=worker.manifest['operations'];calls=[];failure={'ordinal':None}
    # The live implementation catalog can evolve after the historical manifest
    # was sealed. Bind this fixture's own input bodies once, before mutations,
    # without changing any production manifest or input verification rule.
    pins=[worker.manifest['model'][key] for key in ('build','target')]
    pins += [op[key] for op in operations for key in ('candidate','source_snapshot','implementation')]
    values={pin['id']:{'id':pin['id'],'kind':pin['kind'],
                     'extensions':{'contract_fixture':True}} for pin in pins}
    for op in operations:
        op['source_artifact']['sha256']=artifact['sha256']
        values[op['source_snapshot']['id']].update(implementation=op['implementation']['id'],artifact=artifact)
        values[op['candidate']['id']].update(implementation=op['implementation']['id'],
            source_snapshot=op['source_snapshot']['id'],artifact_role='source_baseline',artifact=artifact)
    for pin in pins:pin['canonical_sha256']=artifacts.digest(values[pin['id']])
    def call(command,*,timeout=15,compile=False):
        calls.append((command[:],timeout,compile))
        if command[0]=='get':
            rid=command[1]
            if '--chain' in command:
                op=next(x for x in operations if x['id']==rid)
                ids=[rid,op['candidate']['id'],op['source_snapshot']['id']]
                return {'root':rid,'records':{key:values[key] for key in ids}}
            return values[rid]
        request=json.loads(Path(command[1]).read_text())
        op=next(x for x in operations if x['id']==request['id'])
        assert command==['dx100-compile',command[1],'--runs-dir',str(build.RAW),'--lane','1']
        assert compile and timeout==240
        if op['ordinal']==failure['ordinal']:raise RuntimeError('synthetic compiler failure')
        folder=build.BUILDS/op['id'];folder.mkdir()
        binary=folder/'bfs';binary.write_text('contract binary bytes, never executed\n')
        driver=folder/'complete_call.cc';driver.write_text('// fixture driver\n')
        m5ops=tmp_path/'m5op.S';m5ops.write_text('// fixture m5ops\n')
        value={'id':request['id'],'candidate':request['candidate'],'request':request,
            'outcome':{'state':'complete','stage':'candidate_build'},'evidence_kind':'execution',
            'gain_claim':False,'timing':[],'correctness':{'state':'unverified'},
            'context':{'roi':request['roi'],'candidate_sha256':artifact['sha256'],'function':'DOBFS','accelerated_requested':False},
            'build':{'adapter':'dx100.complete_call.v2','compiler':op['historical_compiler']['compiler'],
                'compiler_sha256':op['historical_compiler']['compiler_sha256'],'source_artifact':artifact,
                'flags':['-O3'],'binary':str(binary),'binary_sha256':artifacts.file_hash(binary),
                'driver':build.reference(driver),'m5ops':build.reference(m5ops)}}
        if request['diagnostic_regions']:value['context']['diagnostic']={'fixture':True}
        values[value['id']]=value
        return value
    monkeypatch.setattr(worker,'call',call)
    monkeypatch.setattr(build,'Store',lambda _:SimpleNamespace(get=lambda rid,*args:values.get(rid)))
    return worker,values,calls,failure


def test_four_calls_and_fresh_chains_use_fixed_order_without_provider(collection):
    worker,values,calls,failure=collection;worker.collect()
    assert [x['id'] for x in worker.receipt['builds']]==[x['id'] for x in worker.manifest['operations']]
    assert [cmd[0][0] for cmd in calls]==['get']*8+['dx100-compile','get']*4
    assert all(row[1]==(240 if row[2] else 15) for row in calls)
    assert all('submit' not in row[0] and 'repair' not in row[0] and 'dx100-execute' not in row[0] for row in calls)


@pytest.mark.parametrize('kind',['model','candidate','source_snapshot','implementation'])
def test_retained_input_mutation_fails_before_any_compile(collection,kind):
    worker,values,calls,failure=collection
    pin=worker.manifest['model']['build'] if kind=='model' else worker.manifest['operations'][0][kind]
    values[pin['id']]['extensions']['mutated']=True
    with pytest.raises(ValueError,match='fresh public input differs'):worker.collect()
    assert not worker.receipt['builds']
    assert all(command[0]=='get' for command,timeout,compile in calls)


@pytest.mark.parametrize('ordinal',[1,2,3,4])
def test_first_unsuccessful_compile_stops_sequence_without_retry(collection,ordinal):
    worker,values,calls,failure=collection;failure['ordinal']=ordinal
    with pytest.raises(RuntimeError,match='synthetic compiler failure'):worker.collect()
    compiles=[row for row in calls if row[0][0]=='dx100-compile']
    assert len(compiles)==ordinal
    assert len(worker.receipt['builds'])==ordinal-1
    assert len({json.loads(Path(row[0][1]).read_text())['id'] for row in compiles})==ordinal
    for op in worker.manifest['operations'][ordinal:]:assert not (build.BUILDS/op['id']).exists()


@pytest.mark.parametrize('fault',['v1','candidate','role','binary','compiler','timing','request'])
def test_build_binding_rejects_semantic_and_rehashed_output_mutations(collection,fault):
    worker,values,calls,failure=collection;worker.collect()
    op=worker.manifest['operations'][0];value=values[op['id']]
    request=json.loads((build.ROOT/op['request']['path']).read_text())
    if fault=='v1':value['build']['adapter']='dx100.complete_call.v1'
    elif fault=='candidate':value['candidate']='unrelated.candidate'
    elif fault=='role':value['context']['diagnostic']={'wrong':True}
    elif fault=='binary':Path(value['build']['binary']).write_text('changed')
    elif fault=='compiler':value['build']['compiler_sha256']='f'*64
    elif fault=='timing':value['timing']=[{'duration_s':1}]
    else:value['request']={**value['request'],'accelerated':True}
    with pytest.raises(ValueError):build.verify_build(value,request,op,build.Store(build.RECORDS))
