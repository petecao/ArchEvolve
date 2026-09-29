"""Local subprocess supervision fixtures, not a3 execution. Date: 2026-09-26 ET."""
from datetime import timedelta
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from scripts import bfs_witness_launch as launch


@pytest.mark.parametrize('offset,delta,okay', [(0,1200,True), (1,1200,False), (0,1201,False), (0,1199,False)])
def test_original_outer_window_cannot_move_or_grow(offset, delta, okay):
    started = launch.a3.DEADLINE-timedelta(seconds=1200)+timedelta(seconds=offset)
    deadline = started+timedelta(seconds=delta)
    if okay:
        assert launch.window(started, deadline, started+timedelta(seconds=10)) == (1160,1190)
    else:
        with pytest.raises(ValueError): launch.window(started, deadline, started)


def fixture_commands(tmp_path, deadline, *, driver_exit=0, observer_exit=0, observer_wrong=False, slow_driver=False, wrong_deadline=False):
    driver = tmp_path/'fixture-driver.py'
    driver.write_text('import sys,time,signal\nfrom pathlib import Path\n'
        f'path=Path({str(tmp_path / "driver-terminated")!r})\n'
        'def stop(*args):\n path.write_text("owned SIGTERM observed")\n raise SystemExit(143)\n'
        'signal.signal(signal.SIGTERM,stop)\n'
        f'Path({str(tmp_path / "driver-started")!r}).write_text("ready")\n'
        f'time.sleep({10 if slow_driver else .15})\nsys.exit({driver_exit})\n')
    observer = tmp_path/'fixture-observer.py'
    observer.write_text('''import json,os,sys,time
from pathlib import Path
from datetime import datetime,timezone
pid,start,folder,deadline,code,wrong=sys.argv[1:]
pid=int(pid);start=int(start);code=int(code)
if code:
 time.sleep(.1)
 raise SystemExit(code)
began=datetime.now(timezone.utc).isoformat()
until=time.monotonic()+4
while time.monotonic()<until:
 try: os.kill(pid,0)
 except ProcessLookupError: break
 time.sleep(.02)
else: raise SystemExit(9)
folder=Path(folder);folder.mkdir()
receipt={'state':'driver_terminated','sampling_complete':True,'cleanup_verified':False,
 'driver_identity':{'pid':pid,'start_ticks':start},'launcher_identity':{'pid':7,'start_ticks':8},
 'observer_identity':{'pid':os.getpid(),'start_ticks':os.getpid()},
 'deadline':deadline,'started':began,'finished':datetime.now(timezone.utc).isoformat()}
if wrong=='yes':receipt['observer_identity']['start_ticks']+=1
(folder/'process-observations.json').write_text(json.dumps(receipt))
''')
    def command(identity, folder):
        return [sys.executable,str(observer),str(identity['pid']),str(identity['start_ticks']),str(folder),
                (deadline+timedelta(seconds=1) if wrong_deadline else deadline).isoformat(),str(observer_exit),'yes' if observer_wrong else 'no']
    return [sys.executable,str(driver)], command


def run_fixture(tmp_path, **kwargs):
    deadline=launch.observer.now()+timedelta(seconds=6)
    commands=fixture_commands(tmp_path,deadline,**kwargs)
    receipt=launch.supervise(tmp_path/'supervisor',*commands,driver_cwd=tmp_path,observer_cwd=tmp_path,
        outer_deadline=deadline,work_deadline=time.monotonic()+3,hard_deadline=time.monotonic()+6,
        pane={'pid':7,'start_ticks':8},identify=lambda pid:{'pid':pid,'start_ticks':pid},poll_interval=.02)
    return receipt


def assert_reaped(receipt):
    for row in receipt['children'].values():
        assert row['reaped'] is True and type(row['returncode']) is int
        with pytest.raises(ChildProcessError): os.waitpid(row['identity']['pid'],os.WNOHANG)


@pytest.mark.parametrize('driver_exit,observer_exit', [(0,0),(7,0),(0,9)])
def test_separate_actual_exit_codes_and_combined_failure(tmp_path,driver_exit,observer_exit):
    receipt=run_fixture(tmp_path,driver_exit=driver_exit,observer_exit=observer_exit)
    assert receipt['combined_exit']==(0 if driver_exit==observer_exit==0 else 1)
    assert receipt['cleanup_verified'] is False and receipt['automatic_retry_allowed'] is False
    assert receipt['children']['observer']['returncode']==observer_exit
    if observer_exit==0: assert receipt['children']['driver']['returncode']==driver_exit
    assert_reaped(receipt)
    for role in ('driver','observer'):
        assert (tmp_path/f'supervisor/{role}.exit').read_text().strip()==str(receipt['children'][role]['returncode'])
    assert json.loads((tmp_path/'supervisor/launcher.json').read_text())==receipt


def test_failed_observer_stops_only_owned_driver_and_reaps_both(tmp_path):
    sentinel=subprocess.Popen([sys.executable,'-c','import time; time.sleep(5)'],start_new_session=True)
    try:
        receipt=run_fixture(tmp_path,observer_exit=7,slow_driver=True)
        assert receipt['state']=='failed' and receipt['children']['observer']['returncode']==7
        assert (tmp_path/'driver-terminated').read_text()=='owned SIGTERM observed'
        assert sentinel.poll() is None
        assert_reaped(receipt)
    finally:
        sentinel.terminate();sentinel.wait(timeout=2)


@pytest.mark.parametrize('fault', ['observer_wrong', 'wrong_deadline'])
def test_successful_exit_with_wrong_observer_identity_is_rejected(tmp_path, fault):
    receipt=run_fixture(tmp_path,**{fault:True})
    assert receipt['state']=='failed' and receipt['combined_exit']==1
    assert 'launched driver/pane' in receipt['reason']
    assert_reaped(receipt)


def test_observer_spawn_failure_cleans_and_reaps_started_driver(tmp_path):
    deadline=launch.observer.now()+timedelta(seconds=5)
    commands=fixture_commands(tmp_path,deadline,slow_driver=True)
    def missing_observer(*args):
        until=time.monotonic()+1
        while not (tmp_path/'driver-started').exists() and time.monotonic()<until:time.sleep(.01)
        assert (tmp_path/'driver-started').exists()
        return ['/absent/fixture-observer']
    receipt=launch.supervise(tmp_path/'supervisor',commands[0],missing_observer,
        driver_cwd=tmp_path,observer_cwd=tmp_path,outer_deadline=deadline,
        work_deadline=time.monotonic()+2,hard_deadline=time.monotonic()+5,
        pane={'pid':7,'start_ticks':8},identify=lambda pid:{'pid':pid,'start_ticks':pid})
    assert receipt['state']=='failed' and receipt['combined_exit']==1
    assert receipt['children']['driver']['reaped'] is True
    assert (tmp_path/'supervisor/observer.exit').read_text()=='not_started\n'
    with pytest.raises(ChildProcessError):os.waitpid(receipt['children']['driver']['identity']['pid'],os.WNOHANG)


def test_work_deadline_stops_and_reaps_both_without_retry(tmp_path):
    deadline=launch.observer.now()+timedelta(seconds=5)
    commands=fixture_commands(tmp_path,deadline,slow_driver=True)
    folder=tmp_path/'supervisor'
    receipt=launch.supervise(folder,*commands,driver_cwd=tmp_path,observer_cwd=tmp_path,
        outer_deadline=deadline,work_deadline=time.monotonic()+.25,hard_deadline=time.monotonic()+5,
        pane={'pid':7,'start_ticks':8},identify=lambda pid:{'pid':pid,'start_ticks':pid},poll_interval=.02)
    assert receipt['state']=='failed' and 'work deadline exhausted' in receipt['reason']
    assert_reaped(receipt)
    with pytest.raises(FileExistsError):
        launch.supervise(folder,*commands,driver_cwd=tmp_path,observer_cwd=tmp_path,
            outer_deadline=deadline,work_deadline=time.monotonic()+1,hard_deadline=time.monotonic()+5,
            pane={'pid':7,'start_ticks':8},identify=lambda pid:{'pid':pid,'start_ticks':pid})


def test_real_supervisor_sigterm_cleans_owned_children_and_retains_failure(tmp_path):
    deadline=launch.observer.now()+timedelta(seconds=6)
    commands=fixture_commands(tmp_path,deadline,slow_driver=True)
    outer=tmp_path/'fixture-supervisor.py'
    # The production signal context and supervisor loop run in a real child;
    # only procfs PID/start lookup is a labeled Mac fixture.
    outer.write_text(f'''import sys,time
from pathlib import Path
sys.path.insert(0,{str(launch.ROOT)!r})
from scripts import bfs_witness_launch as launch
folder=Path({str(tmp_path/'supervisor')!r})
deadline=launch.a3.stamp({deadline.isoformat()!r})
def observer_command(identity,folder):
 return [sys.executable,{str(tmp_path/'fixture-observer.py')!r},str(identity['pid']),str(identity['start_ticks']),str(folder),deadline.isoformat(),'0','no']
with launch.interruption_signals():
 result=launch.supervise(folder,{commands[0]!r},observer_command,driver_cwd={str(tmp_path)!r},observer_cwd={str(tmp_path)!r},outer_deadline=deadline,work_deadline=time.monotonic()+3,hard_deadline=time.monotonic()+6,pane={{'pid':7,'start_ticks':8}},identify=lambda pid:{{'pid':pid,'start_ticks':pid}},poll_interval=.02)
raise SystemExit(result['combined_exit'])
''')
    child=subprocess.Popen([sys.executable,str(outer)],start_new_session=True)
    try:
        until=time.monotonic()+3
        receipt_path=tmp_path/'supervisor/launcher.json'
        while time.monotonic()<until:
            try: receipt=json.loads(receipt_path.read_text())
            except (FileNotFoundError,json.JSONDecodeError): receipt={}
            if receipt.get('state')=='running' and (tmp_path/'driver-started').exists():break
            time.sleep(.02)
        assert receipt.get('state')=='running'
        child.send_signal(signal.SIGTERM)
        assert child.wait(timeout=6)==1
        receipt=json.loads(receipt_path.read_text())
        assert receipt['state']=='failed' and 'interrupted by signal' in receipt['reason']
        assert all(row['reaped'] is True for row in receipt['children'].values())
        assert (tmp_path/'driver-terminated').exists()
    finally:
        if child.poll() is None:child.terminate();child.wait(timeout=6)


@pytest.mark.parametrize('fault',[None,'imported_code','commit','request'])
def test_driver_preflight_binds_imported_code_and_request_to_fixed_checkout(tmp_path,monkeypatch,fault):
    # A throwaway Git fixture, never a commit to the shared project repository.
    client=tmp_path/launch.DRIVER_PATH;client.parent.mkdir();client.write_text('# fixture client\n')
    dependency=tmp_path/'swdb/processes.py';dependency.parent.mkdir();dependency.write_text('# fixture cleanup\n')
    request=tmp_path/launch.a3.REQUEST.relative_to(launch.a3.ROOT)
    request.parent.mkdir(parents=True);request.write_bytes(launch.a3.REQUEST.read_bytes())
    def git(*args):
        return subprocess.check_output(['git','-c','user.name=Fixture','-c','user.email=fixture@example.invalid',*args],cwd=tmp_path,text=True)
    git('init','-q');git('add','.');git('commit','-qm','fixture')
    commit=git('rev-parse','HEAD').strip()
    monkeypatch.setattr(launch,'DRIVER_COMMIT',commit)
    monkeypatch.setattr(launch,'DRIVER_SHA256',launch.artifacts.file_hash(client))
    if fault=='imported_code':dependency.write_text('# unreviewed imported cleanup change\n')
    if fault=='commit':git('commit','--allow-empty','-qm','another fixture commit')
    if fault=='request':request.write_text(json.dumps({'id':'changed'}))
    if fault:
        with pytest.raises(ValueError,match='changed'):launch.validate_driver(tmp_path)
    else:assert launch.validate_driver(tmp_path)==request


def test_already_reaped_child_never_receives_a_group_signal(monkeypatch):
    child=type('Child',(),{'pid':123,'poll':lambda self:0})()
    def forbidden(*args):pytest.fail('already reaped numeric identity was reused')
    monkeypatch.setattr(launch.os,'killpg',forbidden)
    launch.stop_owned(child,{'pid':123,'start_ticks':8},time.monotonic()+1,
                      launch.observer.now()+timedelta(seconds=1),forbidden)


@pytest.mark.parametrize('remaining',[0,.25])
def test_cleanup_waits_never_extend_exhausted_shared_reserve(monkeypatch,remaining):
    clock=[0.0];waits=[];signals=[]
    began=launch.observer.now()
    class Child:
        pid=123
        def poll(self):return None
        def wait(self,timeout):
            waits.append(timeout);clock[0]+=timeout
            raise subprocess.TimeoutExpired('fixture',timeout)
    monkeypatch.setattr(launch.time,'monotonic',lambda:clock[0])
    monkeypatch.setattr(launch.observer,'now',lambda:began+timedelta(seconds=clock[0]))
    monkeypatch.setattr(launch.os,'getpgid',lambda pid:pid)
    monkeypatch.setattr(launch.os,'killpg',lambda pid,sig:signals.append((pid,sig)))
    with pytest.raises((ValueError,TimeoutError),match='shared.*deadline'):
        launch.stop_owned(Child(),{'pid':123,'start_ticks':8},remaining,began+timedelta(seconds=remaining),
                          lambda pid:{'pid':pid,'start_ticks':8})
    assert sum(waits)<=remaining and all(value<=remaining for value in waits)
    assert len(signals)==(0 if remaining==0 else 2)


def test_changed_live_pid_identity_fails_without_signaling(monkeypatch):
    child=type('Child',(),{'pid':123,'poll':lambda self:None})()
    monkeypatch.setattr(launch.os,'killpg',lambda *args:pytest.fail('signal sent to reused child PID'))
    with pytest.raises(ValueError,match='identity changed'):
        launch.stop_owned(child,{'pid':123,'start_ticks':8},time.monotonic()+1,
            launch.observer.now()+timedelta(seconds=1),lambda pid:{'pid':pid,'start_ticks':99})


@pytest.mark.parametrize('missing',['identity','group'])
def test_child_disappearing_after_poll_is_reaped_without_a_signal(monkeypatch,missing):
    waits=[]
    class Child:
        pid=123
        def poll(self):return None
        def wait(self,timeout):waits.append(timeout);return 0
    def group(pid):raise ProcessLookupError('fixture exited between poll and group lookup')
    monkeypatch.setattr(launch.os,'getpgid',group)
    monkeypatch.setattr(launch.os,'killpg',lambda *args:pytest.fail('signal sent after child disappeared'))
    launch.stop_owned(Child(),{'pid':123,'start_ticks':8},time.monotonic()+.5,
        launch.observer.now()+timedelta(seconds=.5),lambda pid:None if missing=='identity' else {'pid':pid,'start_ticks':8})
    assert len(waits)==1 and 0<=waits[0]<=.5


def test_cleanup_error_still_waits_for_direct_child_and_retains_failure(tmp_path,monkeypatch):
    def denied(*args):raise PermissionError('fixture signal unavailable')
    monkeypatch.setattr(launch,'stop_owned',denied)
    receipt=run_fixture(tmp_path,observer_exit=7)
    assert receipt['state']=='failed' and any('PermissionError' in value for value in receipt['cleanup_errors'])
    assert_reaped(receipt)
