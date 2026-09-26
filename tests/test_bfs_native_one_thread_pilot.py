"""Prospective client contracts; synthetic fixtures are not calibration. Date: 2026-09-26 ET."""
import copy
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from scripts import bfs_native_one_thread_pilot as client
from swdb import artifacts, bfs_native, bfs_protocol, yamlio
from swdb.store import Store
from test_profile_packages import package_seed, package_setup, _assemble


def plan():
    return yamlio.load(client.PLAN)


@pytest.fixture
def clock(monkeypatch):
    state = SimpleNamespace(mono=100.0, wall=datetime(2026, 9, 26, 14, tzinfo=client.ET))
    monkeypatch.setattr(client.time, 'monotonic', lambda: state.mono)
    monkeypatch.setattr(client, 'now', lambda: state.wall)
    return state


def timer(state, value=None):
    value = value or plan()
    return client.Clock(value, state.mono, state.wall, state.wall.isoformat(),
                        (state.wall+timedelta(seconds=18240)).isoformat())


def test_fixed_new_scope_preserves_old_failed_records_and_thread_only_requests():
    value = plan(); client.validate_plan(value)
    store = Store(client.ROOT/'records'); machine = store.get('mbit10', 'machine')
    old_plan = (client.ROOT/value['historical_plan']['path']).read_bytes()
    assert client.history(value, store) == value['historical_records']
    assert len(value['historical_records']) == 12
    for cell in value['cells']:
        first = store.get(cell['first_evaluation'], 'evaluation'); before = copy.deepcopy(first)
        request = client.pair_request(first, cell, machine, value)
        assert request['collection'] == {'method': 'native_paired.v1', 'order_seed': 20260926}
        for role in ('baseline', 'candidate'):
            new = request[role]
            assert new['threads'] == 1 and new['repetitions'] == 10
            assert new['candidate'] == first['candidate'] and new.get('protocol') is None
            assert new['sources'] == [0, 1234, 7777] and new['roi'] == 'bfs.complete_call.v1'
            assert new['build'] == {key: first['build'][key] for key in ('compiler', 'flags')}
            assert new['budget'] == {'build_seconds': 180, 'run_seconds': 60, 'total_seconds': 2400}
        assert first == before
    assert (client.ROOT/value['historical_plan']['path']).read_bytes() == old_plan
    assert value['profitability'] == {'minimum_speedup': 1.05, 'confidence': .95,
        'bootstrap_resamples': 2000, 'bootstrap_seed': 20260925, 'maximum_relative_spread': .1}


@pytest.mark.parametrize('fault', ['threads', 'active', 'threshold', 'order', 'retry', 'history', 'clock', 'bool'])
def test_any_prospective_scope_change_rejects(fault):
    value = plan()
    if fault == 'threads': value['threads'] = 2
    elif fault == 'active': value['native_runtime']['environment']['OMP_WAIT_POLICY'] = 'ACTIVE'
    elif fault == 'threshold': value['profitability']['maximum_relative_spread'] = .2
    elif fault == 'order': value['cells'].reverse()
    elif fault == 'retry': value['retries'] = 1
    elif fault == 'history': value['historical_records'].pop(next(iter(value['historical_records'])))
    elif fault == 'clock': value['window']['absolute_end'] = '2026-09-27T22:00:00-04:00'
    else: value['native_runtime']['version'] = True
    with pytest.raises(ValueError, match='prospective scope'): client.validate_plan(value)


def test_runtime_environment_removes_observed_unsets_and_preserves_parent():
    original = {'OMP_THREAD_LIMIT': '4', 'OMP_WAIT_POLICY': 'ACTIVE', 'GOMP_SPINCOUNT': '30000',
                'GOMP_CPU_AFFINITY': '999', 'OMP_NUM_THREADS': '4', 'PATH': '/bin'}
    before = dict(original)
    env, policy = bfs_native.runtime_environment(1, plan()['native_runtime'], environ=original)
    assert policy == plan()['native_runtime'] and env['OMP_NUM_THREADS'] == '1'
    assert not any(name in env for name in bfs_native.RUNTIME_INHERITED)
    assert original == before


def test_phase_switch_cannot_mix_a_sample_with_a_new_storage_baseline(tmp_path, monkeypatch, clock):
    driver = client.Driver.__new__(client.Driver)
    driver.clock = timer(clock); driver.plan = plan(); driver.runs = tmp_path
    driver.phase_start_bytes = 0; driver.receipt = {'phases': []}
    driver.accounting_lock = threading.RLock()
    monkeypatch.setattr(client, 'BUILDS', tmp_path/'absent-builds')
    monkeypatch.setattr(client.os, 'statvfs', lambda _: SimpleNamespace(f_bavail=100*1024**3, f_frsize=1))
    reading, release, transitioning = threading.Event(), threading.Event(), threading.Event()
    samples, errors = [], []

    def storage():
        if threading.current_thread() is reader:
            reading.set()
            assert release.wait(2), 'test must release the in-flight observation'
            return 100  # Captured before the main thread observes 150 bytes.
        return 150

    driver.storage = storage
    def sample():
        try: samples.append(driver.accounting(cleanup=True))
        except BaseException as exc: errors.append(str(exc))
    def transition():
        transitioning.set()
        try: driver.start_diagnostics()
        except BaseException as exc: errors.append(str(exc))
    reader = threading.Thread(target=sample)
    switch = threading.Thread(target=transition)
    reader.start()
    try:
        assert reading.wait(1)
        switch.start(); assert transitioning.wait(1)
        switch.join(.1)
    finally:
        release.set(); reader.join(2)
        if switch.ident is not None: switch.join(2)
    assert not reader.is_alive() and not switch.is_alive()
    assert errors == []
    assert samples[0]['phase'] == 'primary' and samples[0]['phase_raw_bytes'] == 100
    assert driver.phase_start_bytes == 150 and driver.clock.phase == 'diagnostic'


def test_shared_window_and_phase_caps_do_not_reset_or_borrow(clock):
    ledger = timer(clock)
    assert ledger.remaining() == 10800
    clock.mono += 7825; clock.wall += timedelta(seconds=7825)
    ledger.diagnostics()
    assert ledger.remaining() == 7200
    assert ledger.shared_end == 18340
    clock.mono += 7200; clock.wall += timedelta(seconds=7200)
    with pytest.raises(ValueError, match='deadline'): ledger.check()
    assert ledger.remaining(cleanup=True) == 120
    with pytest.raises(ValueError, match='restarted'): ledger.diagnostics()


def test_primary_cannot_start_last_cell_without_full_cli_allowance(clock):
    ledger = timer(clock)
    clock.mono += 8341
    with pytest.raises(ValueError, match='full next stage'): ledger.reserve(2460)


@pytest.mark.parametrize('fault', ['late', 'early', 'extended', 'startup', 'wall', 'mono'])
def test_all_clock_boundaries_fail_closed(clock, fault):
    if fault in {'wall', 'mono'}:
        ledger = timer(clock)
        if fault == 'wall': clock.wall += timedelta(seconds=18241)
        else: clock.mono += 10921
        with pytest.raises(ValueError, match='deadline'): ledger.check(cleanup=True)
        return
    start = clock.wall
    if fault == 'late': start = start.replace(hour=16, minute=56, microsecond=1)
    elif fault == 'early': start -= timedelta(seconds=1)
    entry = start+timedelta(seconds=6 if fault == 'startup' else 0)
    end = start+timedelta(seconds=18241 if fault == 'extended' else 18240)
    with pytest.raises(ValueError, match='outer clock'):
        client.Clock(plan(), clock.mono, entry, start.isoformat(), end.isoformat())


def test_bootstrap_admission_checks_both_directions_and_spread_without_trimming():
    value = plan(); sampling = {'collection': value['collection'], 'analysis': value['analysis'], 'repetitions': 10}
    baseline = [{'source':source,'samples_seconds':[1.0]*10,'relative_spread':0} for source in value['sources']]
    candidate = [{'source':source,'samples_seconds':[1.2]*10,'relative_spread':0} for source in value['sources']]
    result = client.negative_control({'baseline': baseline, 'candidate': candidate}, value['profitability'], sampling)
    assert len(result['directions']) == 2 and result['unmet_gates']
    assert result['directions'][0]['numerical_gain_leg'] is False
    assert result['directions'][1]['numerical_gain_leg'] is True
    assert result['gain_claim'] is False


def test_fresh_diagnostics_have_explicit_separate_grid_and_finite_commands():
    value = plan()
    for cell in value['cells']:
        request = client.profile_request(cell)
        assert request['evaluation'] == cell['baseline_evaluation']
        assert request['repetitions'] == 1 and request['memory'] is True
        assert request['budget'] == {'discovery_seconds':120,'build_seconds':180,'run_seconds':600,'total_seconds':1200}
        assert request['id'].startswith(client.RUN_ID)
    assert 4*(1260+180+180) == 6480 < 7200
    assert 10920+7320 == value['bounds']['shared_seconds']


def test_public_immutable_package_shape_is_reopened_without_promoting_fixture(package_setup, tmp_path):
    records, request, evaluation, profile, candidate = package_setup
    package = _assemble(records, tmp_path, request)
    assert package['id'] != request['id']
    bound = client.package_binding(Store(records.path), package['id'], request['id'], evaluation['id'], profile['id'], candidate['id'])
    assert bound['evidence']['classification'] == 'contract_fixture'
    cell = {'package_requested_id':request['id'], 'baseline_evaluation':evaluation['id'],
            'profile':profile['id'], 'candidate':candidate['id']}
    with pytest.raises(ValueError, match='real independently checked'):
        client.validate_package(Store(records.path), cell, package['id'], plan())


def write_ref(path, value):
    path.write_text(value if isinstance(value, str) else json.dumps(value))
    return client.ref(path)


def terminal_fixture(tmp_path):
    # Explicit fabricated terminal data exercises cleanup admission, never coverage.
    start = datetime(2026,9,26,14,tzinfo=client.ET); end = start+timedelta(seconds=30)
    identities = [{'pid':100,'start_ticks':10,'state':'absent','rss_bytes':0},
                  {'pid':3053339,'start_ticks':494729548,'state':'Z','rss_bytes':0,'role':'tmux_launcher'}]
    sample = write_ref(tmp_path/'samples', json.dumps({'processes':identities})+'\n')
    observations = {'state':'failed','sampling_complete':False,'cleanup_verified':False,'observer_kind':'in_process_driver','driver_pid':100,
        'driver_identity':identities[0],'observer_identity':identities[0], 'pane_pid':3053339,
        'launcher_identity':identities[1], 'ancestry':identities, 'owned_processes':identities, 'resource_samples':sample}
    obs = write_ref(tmp_path/'observations', observations)
    driver = {'id':client.coverage.RUN_ID,'state':'failed','repository_commit':'a'*40,
        'deadline_et':client.coverage.DEADLINE.isoformat(),'bounds':client.coverage.BOUNDS,
        'started':start.isoformat(),'finished':end.isoformat(),'host_wall_s':30,'driver_pid':100,
        'lane':'mbit10-evaluation-node0 (verified: affinity, bind:0, lease held, generation 321)',
        'process_observations':obs,'rss':{'samples':sample}}
    driver_ref = write_ref(tmp_path/'driver',driver)
    lane = {'host':'mbit10','node':0,'lease_name':'mbit10-evaluation-node0','lease_generation':321,'exit_code':1,
        'started_utc':start.isoformat(),'ended_utc':end.isoformat()}
    lease = {'state':'released','lease':{'generation':321,'lease_name':lane['lease_name']},'released_at':end.isoformat()}
    audit = {'id':client.coverage.RUN_ID,'state':'failed','driver':driver_ref,'observed_at':end.isoformat(),
        'lane':write_ref(tmp_path/'lane',{'socket_lane':lane}),'lease_snapshot':write_ref(tmp_path/'lease',lease),
        'outer_exit':write_ref(tmp_path/'exit','1'),'process_observations':obs,'owned_processes':identities,
        'cleanup_state':'terminal_no_live_owned_processes','owned_processes_absent':False,'owned_processes_nonrunning':True}
    return audit, end, observations, driver


def test_failed_coverage_can_be_terminal_without_becoming_success(tmp_path):
    audit,current,_,_ = terminal_fixture(tmp_path)
    result = client.coverage_terminal(write_ref(tmp_path/'audit',audit),current,'a'*40,tmp_path/'proc')
    assert result['work_outcome'] == 'failed' and result['outer_exit'] == 1
    assert result['coverage_pass_asserted'] is False and result['cleanup_verified'] is True


@pytest.mark.parametrize('fault', ['missing_owned', 'lease', 'exit', 'code', 'clock', 'wrong_launcher'])
def test_terminal_cleanup_rejects_ambiguous_or_omitted_ownership(tmp_path, fault):
    audit,current,obs,driver = terminal_fixture(tmp_path)
    if fault == 'missing_owned': audit['owned_processes'] = audit['owned_processes'][:1]
    elif fault == 'lease':
        lease = client.read(audit['lease_snapshot']); lease['state']='held'; audit['lease_snapshot']=write_ref(tmp_path/'lease',lease)
    elif fault == 'exit': audit['outer_exit'] = write_ref(tmp_path/'exit','0')
    elif fault == 'code': driver['repository_commit']='b'*40; audit['driver']=write_ref(tmp_path/'driver',driver)
    elif fault == 'clock': driver['finished']=client.coverage.DEADLINE.replace(hour=23).isoformat(); audit['driver']=write_ref(tmp_path/'driver',driver)
    else:
        obs['launcher_identity']={'pid':1,'start_ticks':1}; audit['process_observations']=write_ref(tmp_path/'observations',obs)
        driver['process_observations']=audit['process_observations']; audit['driver']=write_ref(tmp_path/'driver',driver)
    with pytest.raises(ValueError): client.coverage_terminal(write_ref(tmp_path/'audit',audit),current,'a'*40,tmp_path/'proc')


class FakeOwned:
    def finish(self, seconds=5):
        assert seconds >= 0
        return {'state':'all_owned_descendants_absent','subreaper':True}


@pytest.mark.parametrize('exitcode',[0,3])
def test_actual_owned_direct_child_is_reaped_on_success_and_failure(tmp_path, monkeypatch, exitcode):
    current = client.now(); ledger = SimpleNamespace(phase='primary',work_end=client.time.monotonic()+8,
        phase_hard=client.time.monotonic()+10,end=current+timedelta(seconds=10),reserve=lambda _:None,check=lambda:None)
    monkeypatch.setattr(client.observer,'identity',lambda pid:{'pid':pid,'start_ticks':1})
    # Short fixture lowers the reserve locally, not production policy or command.
    clock_mono = client.time.monotonic
    receipt={'stages':[]}
    # ceiling35 ensures the production30-second cleanup reservation leaves5swork.
    ledger.work_end=clock_mono()+35; ledger.phase_hard=clock_mono()+36; ledger.end=current+timedelta(seconds=36)
    command=[sys.executable,'-c',f'import sys; sys.exit({exitcode})']
    if exitcode:
        with pytest.raises(ValueError,match='public stage failed'):
            client.bounded_stage(receipt,tmp_path,command,35,ledger,FakeOwned(),lambda:None)
    else: client.bounded_stage(receipt,tmp_path,command,35,ledger,FakeOwned(),lambda:None)
    row=receipt['stages'][0]
    assert row['returncode']==exitcode and row['cleanup']['state']=='all_owned_descendants_absent'
    with pytest.raises(ChildProcessError): os.waitpid(row['pid'],os.WNOHANG)


@pytest.mark.parametrize('fault',['slow_hash','last_write_time','last_write_storage'])
def test_final_hash_and_second_write_cannot_hide_failed_accounting(tmp_path, monkeypatch, clock, fault):
    driver=client.Driver.__new__(client.Driver); driver.clock=timer(clock); driver.folder=tmp_path
    driver.monitor=None; driver.owned=None; driver.last_sample=clock.wall
    driver.receipt={'state':'complete','rss':{}}
    (tmp_path/'rss-samples.jsonl').write_text('{}\n')
    calls=[]; overflow=[False]
    def account(**kwargs):
        driver.clock.check(**kwargs)
        if overflow[0]: raise ValueError('storage ceiling')
        return {'elapsed_seconds':clock.mono-driver.clock.started}
    driver.accounting=account
    save=client.save_receipt; original_ref=client.ref
    def persist(folder,value):
        save(folder,value); calls.append(value['state'])
        if len(calls)==2:
            if fault=='last_write_time': clock.mono+=10921
            if fault=='last_write_storage': overflow[0]=True
    def slow(path):
        result=original_ref(path)
        if fault=='slow_hash': clock.mono+=10921
        return result
    monkeypatch.setattr(client,'save_receipt',persist); monkeypatch.setattr(client,'ref',slow)
    with pytest.raises(ValueError): driver.finalize()
    assert json.loads((tmp_path/'driver.json').read_text())['state']=='failed'


def test_monitor_failure_during_shutdown_is_not_lost_and_cleanup_still_runs(tmp_path, clock):
    driver=client.Driver.__new__(client.Driver); driver.clock=timer(clock); driver.folder=tmp_path
    driver.last_sample=clock.wall; driver.receipt={'state':'complete','rss':{}}
    class Monitor:
        error=None
        def stop(self): self.error=ValueError('in-flight guard failed after shutdown began')
        def check(self): raise self.error
    class Owned(FakeOwned):
        sampler=SimpleNamespace(known={123:456})
        cleaned=False
        def finish(self,seconds=5):
            self.cleaned=True
            return super().finish(seconds)
    driver.monitor=Monitor(); driver.owned=Owned(); driver.observe=lambda:None
    driver.accounting=lambda **_:{}
    with pytest.raises(ValueError,match='in-flight guard'): driver.finalize()
    result=json.loads((tmp_path/'driver.json').read_text())
    assert result['state']=='failed' and driver.owned.cleaned
    assert result['process_observations']['owned_processes']==[{'pid':123,'start_ticks':456}]


def test_actual_resource_monitor_inflight_shutdown_failure_cannot_publish_success(tmp_path,monkeypatch):
    entered=threading.Event(); release=threading.Event(); calls=[0]; signals=[]
    def sample():
        calls[0]+=1
        if calls[0]>1:
            entered.set(); assert release.wait(3)
            raise ValueError('actual in-flight sampling failure')
    monitor=client.previous.ResourceMonitor(sample)
    monkeypatch.setattr(client.previous.os,'kill',lambda *args:signals.append(args))
    monitor.start(); assert entered.wait(7)
    def releasing():
        deadline=time.monotonic()+3
        while not monitor.done.is_set() and time.monotonic()<deadline: time.sleep(.001)
        release.set()
    helper=threading.Thread(target=releasing);helper.start()
    driver=client.Driver.__new__(client.Driver);driver.folder=tmp_path;driver.monitor=monitor;driver.owned=None
    driver.clock=SimpleNamespace(started=time.monotonic());driver.receipt={'state':'complete','rss':{}}
    driver.last_sample=client.now();driver.accounting=lambda **_:{}
    with pytest.raises(ValueError,match='actual in-flight'):driver.finalize()
    helper.join(timeout=3)
    assert not signals and json.loads((tmp_path/'driver.json').read_text())['state']=='failed'


def test_owned_wrapper_serializes_real_concurrent_sample_and_cleanup(monkeypatch):
    monkeypatch.setattr(client.OwnedDescendants,'__init__',lambda _:None)
    owned=client.LockedOwned(); entered=threading.Event(); release=threading.Event(); cleanup=threading.Event()
    calls=[]; errors=[]; allowances=[]
    def sample(self):
        calls.append(threading.current_thread().name)
        if len(calls)==1:
            entered.set(); assert release.wait(2)
        return {'processes':[{'pid':123,'start_ticks':len(calls)}]}
    def finish(self,seconds):
        cleanup.set(); allowances.append(seconds)
        self.sample()  # The real superclass cleanup recursively samples under the same lock.
        return {'state':'all_owned_descendants_absent'}
    monkeypatch.setattr(client.OwnedDescendants,'sample',sample)
    monkeypatch.setattr(client.OwnedDescendants,'finish',finish)
    def run(call):
        try: call()
        except BaseException as exc: errors.append(exc)
    observer=threading.Thread(target=lambda:run(owned.sample),name='observer')
    stopper=threading.Thread(target=lambda:run(lambda:owned.finish(seconds=1)),name='cleanup')
    observer.start(); assert entered.wait(1); stopper.start()
    assert not cleanup.wait(.05)
    release.set(); observer.join(2); stopper.join(2)
    assert not observer.is_alive() and not stopper.is_alive() and not errors
    assert calls==['observer','cleanup'] and 0 < allowances[0] < .99
    # PID reuse does not erase the earlier observed PID/start identity.
    assert owned.retained_identities()==[(123,1),(123,2)]


def test_owned_wrapper_lock_wait_spends_cleanup_allowance(monkeypatch):
    monkeypatch.setattr(client.OwnedDescendants,'__init__',lambda _:None)
    owned=client.LockedOwned(); called=[]; errors=[]
    monkeypatch.setattr(client.OwnedDescendants,'finish',lambda *args,**kwargs:called.append(True))
    def finish():
        try: owned.finish(seconds=.05)
        except ValueError as exc: errors.append(str(exc))
    with owned.lock:
        worker=threading.Thread(target=finish);worker.start();worker.join(1)
        assert not worker.is_alive()
    assert errors and 'bounded allowance' in errors[0] and not called


@pytest.fixture
def reader_fixture(tmp_path,monkeypatch):
    # The orchestrator reader is tested independently from raw BFS correctness;
    # pair validation is replaced with an explicitly synthetic failing A/A grid.
    value=plan(); real=Store(client.ROOT/'records'); records={}; checks={}
    class Records:
        def get(self,rid,*args): return records[rid] if rid in records else real.get(rid,*args)
    store=Records(); began=datetime(2026,9,26,14,tzinfo=client.ET); ended=began+timedelta(seconds=10)
    runtime={'python':{'path':sys.executable},'fixture_only':True}
    monkeypatch.setattr(client,'runtime_identity',lambda _:runtime)
    monkeypatch.setattr(client,'prerequisites',lambda *args:{'fixture_only':True})
    monkeypatch.setattr(client,'validate_pair_result',lambda store,first,pair,*args:copy.deepcopy(checks[pair['id']]))
    stages=[]; cells=[]; capacities=[]; machine=store.get('mbit10','machine')
    from test_dx100_capacity import node, zone
    raw_capacity={'node':node(30*1024**2),'zones':zone(),'global':f'MemAvailable: {40*1024**2} kB','pressure':'fixture'}
    estimate=client.dx100_capacity.capacity(raw_capacity['node'],raw_capacity['zones'],raw_capacity['global'],1,4096)
    for i,cell in enumerate(value['cells']):
        first=store.get(cell['first_evaluation'],'evaluation')
        req=client.pair_request(first,cell,machine,value)
        pair={'id':cell['id'],'request':req,'fixture_only':True,
            'started':(began+timedelta(seconds=2*i+1.02)).isoformat(),
            'prepared_at':(began+timedelta(seconds=2*i+1.04)).isoformat(),
            'finished':(began+timedelta(seconds=2*i+1.08)).isoformat()}; records[pair['id']]=pair
        checks[pair['id']]={'samples':{'fixture_only':True},'control':{'unmet_gates':['synthetic spread failure'],
            'gain_claim':False},'members':{'fixture_only':True}}
        resolved=Path(first['build']['compiler']).resolve(strict=True)
        cells.append({'id':pair['id'],'pair_sha256':artifacts.digest(pair),**checks[pair['id']],
                      'compiler':{'compiler_resolved':str(resolved),'compiler_sha256':artifacts.file_hash(resolved)}})
        request=write_ref(tmp_path/f'request{i}',req); output=write_ref(tmp_path/f'out{i}',pair)
        error=write_ref(tmp_path/f'err{i}','')
        compiler=write_ref(tmp_path/f'compiler{i}','\n'.join(first['build']['compiler_version'])+'\n')
        stages.append({'command':[first['build']['compiler'],'--version'],'output':compiler['path'],
            'stdout_sha256':compiler['sha256'],'stderr':error['path'],'stderr_sha256':error['sha256'],
            'state':'complete','returncode':0,'cleanup':{'state':'all_owned_descendants_absent'},
            'host_wall_s':.1,'ceiling_seconds':60,'phase':'primary',
            'started':(began+timedelta(seconds=2*i+.1)).isoformat(),
            'finished':(began+timedelta(seconds=2*i+.2)).isoformat()})
        stages.append({'command':[sys.executable,'-m','swdb','evaluate-pair',request['path'],'--runs-dir',str(tmp_path),
            '--records',str(client.ROOT/'records'),'--format','json'],'request':request,'output':output['path'],
            'stdout_sha256':output['sha256'],'stderr':error['path'],'stderr_sha256':error['sha256'],
            'state':'complete','returncode':0,'cleanup':{'state':'all_owned_descendants_absent'},
            'host_wall_s':.1,'ceiling_seconds':2460,'phase':'primary',
            'started':(began+timedelta(seconds=2*i+1)).isoformat(),
            'finished':(began+timedelta(seconds=2*i+1.1)).isoformat()})
        capacities.append({'inputs':raw_capacity,'estimate':estimate,'native_eligible':True,
            'required_bytes':{'node':20*1024**3,'global':24*1024**3},'command':stages[-1]['command'],
            'observed_at':(began+timedelta(seconds=2*i+.9)).isoformat()})
    for index,stage in enumerate(stages):
        stage.update(pid=200+index,identity={'pid':200+index,'start_ticks':1000+index,'parent_pid':123})
    row={'sampled_at':(began+timedelta(seconds=1)).isoformat(),'rss_bytes':4096,
        'rss_source':value['rss_source'],'page_size_bytes':4096,'guard_seconds':.001,
        'processes':[{'pid':123,'start_ticks':100,'parent_pid':99,'state':'S','rss_bytes':4096,'rss_pages':1}],
        'total_raw_bytes':100,'phase_raw_bytes':100,'build_bytes':10,'raw_free_bytes':40*1024**3,'build_free_bytes':15*1024**3,
        'lane':{'verified_lane':'mbit10-evaluation-node1 (verified: affinity, bind:1, lease held, generation 1)'}}
    rows=[copy.deepcopy(row),copy.deepcopy(row)]
    rows[-1]['sampled_at']=(ended-timedelta(seconds=1)).isoformat()
    for sample in rows:
        stamp=client.witness.stamp(sample['sampled_at'])
        sample.update(guard_started=stamp.isoformat(),guard_finished=(stamp+timedelta(seconds=.001)).isoformat())
    samples=write_ref(tmp_path/'samples','\n'.join(map(json.dumps,rows))+'\n')
    admission=write_ref(tmp_path/'admission',{'code_commit':'a'*40,'plan_sha256':client.PLAN_SHA,'prepared_at':began.isoformat()})
    receipt={'id':client.RUN_ID,'state':'primary_unqualified','repository_commit':'a'*40,
        'plan_canonical_sha256':client.PLAN_SHA,'bounds':value['bounds'],'native_runtime':value['native_runtime'],
        'python_environment':client.PYTHON_INPUTS,
        'gain_claim':False,'protocol_freeze':False,'provider_calls':False,'runtime':runtime,
        'plan':write_ref(tmp_path/'plan',value),'started':began.isoformat(),'finished':ended.isoformat(),
        'outer_start':began.isoformat(),'outer_end':(began+timedelta(seconds=18240)).isoformat(),'host_wall_s':10,
        'cleanup':{'state':'all_owned_descendants_absent','subreaper':True},'final_accounting':{**row,'observed_at':ended.isoformat()},
        'admission':admission,'rss':{'source':value['rss_source'],'samples':samples,'peak_bytes':4096},
        'driver_pid':123,'stages':stages,'capacity':capacities,'cells':cells,'primary_qualified':False,
        'process_observations':{'driver_identity':{'pid':123,'start_ticks':100,'parent_pid':99},
            'pane_identity':{'pid':99,'start_ticks':90},'ancestry':[{'pid':123,'start_ticks':100,'parent_pid':99},
                {'pid':99,'start_ticks':90,'parent_pid':1}],
            'owned_processes':[{'pid':123,'start_ticks':100}]+[stage['identity'] for stage in stages]},
        'runs_dir':str(tmp_path),'records':str(client.ROOT/'records'),
        'diagnostics':[{'id':c['profile'],'state':'not_dispatched_primary_unqualified'} for c in value['cells']]}
    return receipt,value,store,lambda:write_ref(tmp_path/'receipt',receipt)


def test_completed_reader_retains_synthetic_unqualified_grid_without_diagnostics(reader_fixture):
    receipt,value,store,reference=reader_fixture
    observed=client.validate_driver_receipt(reference(),value,store,'a'*40)
    assert observed['state']=='primary_unqualified' and observed['qualified'] is False
    assert len(observed['controls'])==4 and observed['gain_claim'] is False


def test_completed_reader_requires_all_four_fresh_diagnostic_packets(reader_fixture,tmp_path,monkeypatch):
    receipt,value,store,reference=reader_fixture
    began=client.witness.stamp(receipt['started']);end=began+timedelta(seconds=30)
    receipt.update(state='complete',primary_qualified=True,diagnostic_started=(began+timedelta(seconds=10)).isoformat(),
                   finished=end.isoformat(),host_wall_s=30,diagnostics=[])
    receipt['final_accounting']['observed_at']=end.isoformat()
    rows=[json.loads(line) for line in client.witness.reference(receipt['rss']['samples']).splitlines()]
    rows[-1]['sampled_at']=(end-timedelta(seconds=1)).isoformat()
    rows[-1]['guard_started']=rows[-1]['sampled_at']
    rows[-1]['guard_finished']=(end-timedelta(seconds=.999)).isoformat()
    receipt['rss']['samples']=write_ref(tmp_path/'samples','\n'.join(map(json.dumps,rows))+'\n')
    for row in receipt['cells']: row['control']['unmet_gates'].clear()
    added={}; original_get=store.get
    store.get=lambda rid,*args: added[rid] if rid in added else original_get(rid,*args)
    checked={}
    monkeypatch.setattr(client,'validate_package',lambda store,cell,rid,plan:checked[rid])
    for i,cell in enumerate(value['cells']):
        first=copy.deepcopy(store.get(cell['first_evaluation']))
        first['id']=cell['baseline_evaluation'];first['context']['threads']=1
        added[first['id']]=first
        package_id=cell['package_requested_id']+'.v1.'+'a'*16
        package={'id':package_id,'fixture_only':True};added[package_id]=package
        checked[package_id]={'id':package_id,'sha256':artifacts.digest(package),
                             'records':{package_id:artifacts.digest(package)}}
        for j,(command,request,result,ceiling) in enumerate([
            ('bfs-profile',client.profile_request(cell),{'id':cell['profile'],'fixture_only':True},1260),
            ('profile-package',client.package_request(cell,first),package,180),
            ('get',None,{'root':package_id,'records':{package_id:package}},180)]):
            added[result.get('id','not-a-record')]=result
            out=write_ref(tmp_path/f'diag-{i}-{j}',result);err=write_ref(tmp_path/f'diag-{i}-{j}-err','')
            start=began+timedelta(seconds=11+3*i+j)
            stage={'phase':'diagnostic','state':'complete','returncode':0,'host_wall_s':.1,'ceiling_seconds':ceiling,
                'started':start.isoformat(),'finished':(start+timedelta(seconds=.1)).isoformat(),
                'cleanup':{'state':'all_owned_descendants_absent'},'output':out['path'],'stdout_sha256':out['sha256'],
                'stderr':err['path'],'stderr_sha256':err['sha256']}
            stage.update(pid=300+3*i+j,identity={'pid':300+3*i+j,'start_ticks':2000+3*i+j,'parent_pid':123})
            receipt['process_observations']['owned_processes'].append(stage['identity'])
            if request:
                requested=write_ref(tmp_path/f'diag-{i}-{j}-request',request);stage['request']=requested
                argv=[sys.executable,'-m','swdb',command,requested['path']]
                if command=='bfs-profile':argv+=['--runs-dir',receipt['runs_dir']]
            else:argv=[sys.executable,'-m','swdb','get',package_id,'--chain']
            stage['command']=argv+['--records',receipt['records'],'--format','json'];receipt['stages'].append(stage)
            if command=='bfs-profile':
                cap=copy.deepcopy(receipt['capacity'][0]);cap.update(command=stage['command'],observed_at=start.isoformat())
                receipt['capacity'].append(cap)
        receipt['diagnostics'].append({**checked[package_id],'profile':cell['profile'],'state':'complete','public_get':out})
    result=client.validate_driver_receipt(reference(),value,store,'a'*40)
    assert result['qualified'] is True and result['state']=='complete' and result['gain_claim'] is False
    receipt['diagnostics'].pop()
    with pytest.raises(ValueError,match='diagnostic phase/grid'):
        client.validate_driver_receipt(reference(),value,store,'a'*40)


@pytest.mark.parametrize('fault',['missing_cell','source_request','command','order','rss_basis','sample_gap',
    'cleanup','phase_cap','clock','false_qualification','changed_output','changed_history'])
def test_completed_reader_cannot_reseal_incompatible_driver_metadata(reader_fixture,fault,tmp_path):
    receipt,value,store,reference=reader_fixture
    if fault=='missing_cell': receipt['cells'].pop()
    elif fault=='source_request':
        request=client.read(receipt['stages'][1]['request']);request['baseline']['threads']=4
        receipt['stages'][1]['request']=write_ref(tmp_path/'badrequest',request)
        receipt['stages'][1]['command'][4]=receipt['stages'][1]['request']['path']
    elif fault=='command': receipt['stages'][1]['command'][0]='/different/python'
    elif fault=='order': receipt['stages'].reverse()
    elif fault=='rss_basis': receipt['rss']['source']='invented'
    elif fault=='sample_gap': receipt['started']='2026-09-26T13:58:00-04:00'
    elif fault=='cleanup': receipt['cleanup']['state']='leader_exited_only'
    elif fault=='phase_cap': receipt['stages'][1]['ceiling_seconds']=2461
    elif fault=='clock': receipt['outer_end']='2026-09-26T23:00:00-04:00'
    elif fault=='false_qualification': receipt['primary_qualified']=True
    elif fault=='changed_output': Path(receipt['stages'][0]['output']).write_text('{}')
    else:
        old=store.get(next(iter(value['historical_records'])));old['gain_claim']=True
        get=store.get
        store.get=lambda rid,*args:old if rid==old['id'] else get(rid,*args)
    with pytest.raises((ValueError,client.bfs_native.Failure)):
        client.validate_driver_receipt(reference(),value,store,'a'*40)


@pytest.mark.parametrize('fault',['missing','wrong_resolved','wrong_hash'])
def test_completed_reader_binds_each_resolved_compiler_to_declared_path(reader_fixture,fault):
    receipt,value,store,reference=reader_fixture
    compiler=receipt['cells'][2]['compiler']
    if fault=='missing':receipt['cells'][2].pop('compiler')
    elif fault=='wrong_resolved':
        compiler.update(compiler_resolved=str(Path(sys.executable).resolve()),
                        compiler_sha256=artifacts.file_hash(Path(sys.executable).resolve()))
    else:compiler['compiler_sha256']='0'*64
    with pytest.raises(ValueError,match='compiler executable'):
        client.validate_driver_receipt(reference(),value,store,'a'*40)


@pytest.mark.parametrize('fault',['missing_observations','changed_driver_start','omitted_union','duplicate_identity',
    'unowned_process','parent_cycle','wrong_stage_parent','guard_duration','guard_overlap','outside_guard'])
def test_completed_reader_rejects_resealed_ownership_and_guard_mismatch(reader_fixture,tmp_path,fault):
    receipt,value,store,reference=reader_fixture
    rows=[json.loads(line) for line in client.witness.reference(receipt['rss']['samples']).splitlines()]
    if fault=='missing_observations':receipt.pop('process_observations')
    elif fault=='changed_driver_start':rows[-1]['processes'][0]['start_ticks']+=1
    elif fault=='omitted_union':receipt['process_observations']['owned_processes'].pop()
    elif fault=='duplicate_identity':receipt['process_observations']['owned_processes'].append(
        receipt['process_observations']['owned_processes'][0])
    elif fault=='unowned_process':
        rows[-1]['processes'].append({'pid':999,'start_ticks':5,'parent_pid':1,'rss_bytes':0,'rss_pages':0})
    elif fault=='parent_cycle':rows[-1]['processes'][0]['parent_pid']=123
    elif fault=='wrong_stage_parent':receipt['stages'][-1]['identity']['parent_pid']=1
    elif fault=='guard_duration':rows[-1]['guard_seconds']=2
    elif fault=='guard_overlap':rows[-1]['guard_started']=rows[0]['guard_started']
    else:rows[-1]['guard_finished']=rows[0]['guard_finished']
    receipt['rss']['samples']=write_ref(tmp_path/'resealed-samples','\n'.join(map(json.dumps,rows))+'\n')
    with pytest.raises(ValueError):client.validate_driver_receipt(reference(),value,store,'a'*40)


@pytest.mark.parametrize('fault',['over_ceiling','wall_mismatch','boolean_wall'])
def test_completed_reader_checks_actual_stage_elapsed_against_allowance(reader_fixture,fault):
    receipt,value,store,reference=reader_fixture;stage=receipt['stages'][0]
    if fault=='over_ceiling':
        stage['finished']=(client.witness.stamp(stage['started'])+timedelta(seconds=61.1)).isoformat()
    elif fault=='wall_mismatch':stage['host_wall_s']=2
    else:stage['host_wall_s']=True
    with pytest.raises(ValueError,match='stage is incomplete or exceeds'):
        client.validate_driver_receipt(reference(),value,store,'a'*40)


def test_runtime_inventory_rejects_ignored_shadow_and_changed_pinned_bytes(tmp_path):
    def git(*args):return subprocess.check_output(['git',*args],cwd=tmp_path,text=True).strip()
    for directory in client.RUNTIME_DIRS:
        path=tmp_path/directory/'fixture.txt';path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture')
    (tmp_path/'.gitignore').write_text('scripts/shadow.py\n')
    target=tmp_path/client.PLAN.relative_to(client.ROOT);target.parent.mkdir(parents=True);target.write_bytes(client.PLAN.read_bytes())
    git('init','-q');git('add','.')
    git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','-c','core.hooksPath=/dev/null','commit','-qm','fixture only')
    runtime=client.runtime_identity(git('rev-parse','HEAD'),root=tmp_path)
    client.recheck_runtime(runtime)
    (tmp_path/'scripts/shadow.py').write_text('fixture = True\n')
    with pytest.raises(ValueError,match='untracked runtime'):client.runtime_identity(git('rev-parse','HEAD'),root=tmp_path)
    with pytest.raises(ValueError,match='runtime changed'):client.recheck_runtime(runtime)
    (tmp_path/'scripts/shadow.py').unlink();(tmp_path/'scripts/fixture.txt').write_text('changed')
    with pytest.raises(ValueError,match='runtime changed'):client.recheck_runtime(runtime)


@pytest.mark.skipif(sys.platform!='linux',reason='actual Linux subreaper/pidfd test; Mac fixture is not admission')
@pytest.mark.parametrize('failure',[False,True])
def test_linux_one_thread_stage_reaps_detached_grandchild(tmp_path,failure):
    script = r'''
import json,os,pathlib,resource,subprocess,sys,time
from datetime import timedelta
from types import SimpleNamespace
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
from scripts import bfs_native_one_thread_pilot as c
folder=pathlib.Path(sys.argv[1]); failure=sys.argv[2]=='True'; started=time.monotonic()
owned=c.LockedOwned()
inner="import os,pathlib,time; pathlib.Path(%r).write_text(str(os.getpid())); time.sleep(15)" % str(folder/'grandchild')
leader="import pathlib,subprocess,sys,time; subprocess.Popen([sys.executable,'-c',%r],start_new_session=True); p=pathlib.Path(%r); end=time.monotonic()+3\nwhile not p.exists() and time.monotonic()<end: time.sleep(.01)\nsys.exit(%d)" % (inner,str(folder/'grandchild'),3 if failure else 0)
clock=SimpleNamespace(phase='primary',work_end=time.monotonic()+35,phase_hard=time.monotonic()+36,end=c.now()+timedelta(seconds=36),reserve=lambda _:None,check=lambda:None)
receipt={'stages':[]}; error=None
try: c.bounded_stage(receipt,folder,[sys.executable,'-c',leader],35,clock,owned,lambda:None)
except ValueError as exc: error=str(exc)
assert bool(error)==failure
assert not pathlib.Path('/proc', (folder/'grandchild').read_text()).exists()
assert receipt['stages'][0]['cleanup']['state']=='all_owned_descendants_absent'
receipt.update(fixture_only=True,state='passed',host_wall_s=time.monotonic()-started,platform=sys.platform,subreaper=True)
(folder/'cleanup-result.json').write_text(json.dumps(receipt))
'''
    result=subprocess.run([sys.executable,'-c',script,str(tmp_path),str(failure)],cwd=client.ROOT,
                          capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stdout+result.stderr
