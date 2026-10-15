"""Shared-runner protocol through its CLI, 2026-10-15 ET; Python stand-ins only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

RUNNER = Path(__file__).with_name('counted_verifier.py')


def test_a_bounded_queue_wait_never_launches_or_releases_another_owner(tmp_path):
    lock=tmp_path/'verifier.lock';lock.mkdir()
    (lock/'owner').write_text(f'owner=test pid={os.getpid()}\n')
    output=tmp_path/'log';started=tmp_path/'started'
    result=subprocess.run([sys.executable,str(RUNNER),'--lock',str(lock),'--log',str(output),
        '--queue-timeout','0.15','--timeout','1','--',sys.executable,'-c',
        f'from pathlib import Path; Path({str(started)!r}).touch()'],capture_output=True,text=True,timeout=5)
    assert result.returncode==124, result.stderr+result.stdout
    assert not started.exists() and lock.is_dir()
    assert not list((tmp_path/'verifier.queue').iterdir())
    summary=json.loads(Path(str(output)+'.summary.json').read_text())
    assert summary['clock']=='continuous_monotonic' and summary['queue_timed_out']
    assert summary['exit_code']==124 and summary['lock_wait_s']>0


def _wait(predicate):
    import time
    end=time.monotonic()+8
    while not predicate():
        assert time.monotonic()<end, 'stand-in protocol deadline'
        time.sleep(0.01)


def _start(tmp_path,name,lock,code,timeout='3'):
    return subprocess.Popen([sys.executable,str(RUNNER),'--lock',str(lock),'--log',str(tmp_path/name),
        '--queue-timeout','5','--timeout',timeout,'--',sys.executable,'-c',code],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)


def _stopped(pid):
    import psutil
    try:return psutil.Process(pid).status() in {psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD}
    except psutil.NoSuchProcess:return True


def test_two_atomic_slots_admit_only_the_first_two_live_tickets(tmp_path):
    import shutil
    lock=tmp_path/'verifier.lock';second=tmp_path/'verifier.slot2.lock'
    for slot in (lock,second):
        slot.mkdir();(slot/'owner').write_text(f'owner=fixture pid={os.getpid()}\n')
    (tmp_path/'verifier.slots').write_text('2\n')
    events=tmp_path/'events';release=tmp_path/'release';processes=[]
    try:
        for ordinal,name in enumerate(['a','b','c'],1):
            code=(f'from pathlib import Path; import time; '
                  f'p=Path({str(release)!r}); '
                  f'open({str(events)!r},"a").write({name!r}+"\\n"); '
                  'exec("while not p.exists(): time.sleep(0.01)")')
            processes.append(_start(tmp_path,name,lock,code))
            _wait(lambda:len(list((tmp_path/'verifier.queue').glob('*')))==ordinal)
        shutil.rmtree(lock);shutil.rmtree(second)
        _wait(lambda:events.exists() and len(events.read_text().splitlines())==2)
        assert set(events.read_text().splitlines())=={'a','b'}
        release.touch()
        for process in processes:
            stdout,stderr=process.communicate(timeout=8)
            assert process.returncode==0,stderr+stdout
        assert events.read_text().splitlines()[-1]=='c'
        assert not lock.exists() and not second.exists()
        assert not list((tmp_path/'verifier.queue').iterdir())
    finally:
        for process in processes:
            if process.poll() is None:process.terminate()
        for process in processes:
            if process.poll() is None:process.wait(timeout=8)


def test_signal_stops_the_child_and_escaped_descendant_before_releasing_the_lease(tmp_path):
    import signal
    lock=tmp_path/'verifier.lock';pids=tmp_path/'pids'
    code=('import subprocess,sys,os,time,json; '
          'p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"],start_new_session=True); '
          f'open({str(pids)!r},"w").write(json.dumps([os.getpid(),p.pid])); time.sleep(30)')
    process=_start(tmp_path,'signal.log',lock,code)
    try:
        _wait(lambda:pids.exists())
        children=json.loads(pids.read_text())
        process.send_signal(signal.SIGTERM)
        stdout,stderr=process.communicate(timeout=8)
        assert process.returncode==128+signal.SIGTERM,stderr+stdout
        assert all(_stopped(pid) for pid in children)
        assert not lock.exists()
        summary=json.loads((tmp_path/'signal.log.summary.json').read_text())
        assert summary['clock']=='continuous_monotonic' and summary['unconfirmed_children']==[]
    finally:
        if process.poll() is None:process.terminate();process.wait(timeout=8)


def test_job_timeout_keeps_the_lease_until_the_child_is_stopped(tmp_path):
    lock=tmp_path/'verifier.lock';pids=tmp_path/'pid'
    code=f'import os,time; open({str(pids)!r},"w").write(str(os.getpid())); time.sleep(30)'
    process=_start(tmp_path,'timeout.log',lock,code,timeout='0.15')
    stdout,stderr=process.communicate(timeout=8)
    assert process.returncode==137,stderr+stdout
    assert _stopped(int(pids.read_text())) and not lock.exists()
    summary=json.loads((tmp_path/'timeout.log.summary.json').read_text())
    assert summary['timed_out'] and summary['unconfirmed_children']==[]


def test_rss_limit_stops_an_overbudget_child_before_releasing_the_lease(tmp_path):
    lock=tmp_path/'verifier.lock';pids=tmp_path/'pid'
    code=f'import os,time; open({str(pids)!r},"w").write(str(os.getpid())); data=bytearray(64*1024*1024); time.sleep(30)'
    output=tmp_path/'memory.log'
    process=subprocess.Popen([sys.executable,str(RUNNER),'--lock',str(lock),'--log',str(output),
        '--cap-gb','0.03','--timeout','3','--',sys.executable,'-c',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    stdout,stderr=process.communicate(timeout=8)
    assert process.returncode==137,stderr+stdout
    assert _stopped(int(pids.read_text())) and not lock.exists()
    summary=json.loads(Path(str(output)+'.summary.json').read_text())
    assert summary['killed_by_watchdog'] and summary['unconfirmed_children']==[]


def test_exited_root_with_empty_snapshot_stops_owned_group_but_cannot_certify_unseen_escapes(tmp_path):
    import counted_verifier as V
    import psutil
    code=('import subprocess,sys,json; '
          'child=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"]); '
          'escaped=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"],start_new_session=True); '
          'print(json.dumps([child.pid,escaped.pid]),flush=True)')
    root=subprocess.Popen([sys.executable,'-c',code],stdout=subprocess.PIPE,text=True,start_new_session=True)
    children=json.loads(root.stdout.readline())
    root.wait(timeout=5)
    assert root.returncode==0 and all(not _stopped(pid) for pid in children)
    try:
        known={}
        unconfirmed=V._stop(root,known)
        assert _stopped(children[0]), 'same owned process group survived cleanup'
        assert unconfirmed, 'an empty ancestry snapshot cannot certify escaped unseen descendants'
    finally:
        for pid in children:
            try:psutil.Process(pid).kill()
            except psutil.NoSuchProcess:pass


def test_reused_or_unobserved_root_pid_never_targets_another_process_group():
    import counted_verifier as V
    from types import SimpleNamespace
    # This live PID is not the old Popen child. Cleanup must stop before killpg.
    old=SimpleNamespace(pid=os.getpid(),poll=lambda:0)
    assert V._stop(old,{os.getpid():-1})==['root-pid-reused-or-unobserved']


@pytest.mark.parametrize('via_wp_environment', [False, True])
def test_cli_cleans_a_new_session_child_forked_after_the_last_tree_sample(tmp_path, via_wp_environment):
    """A stopped supervisor cannot poll the final fork; inherited identity must cover it."""
    import signal
    import psutil
    lock=tmp_path/'verifier.lock';ready=tmp_path/'ready';release=tmp_path/'release';escaped=tmp_path/'escaped'
    code=('import os,subprocess,sys,time; from pathlib import Path; '
          f'Path({str(ready)!r}).write_text(str(os.getpid())); '
          f'exec("while not Path({str(release)!r}).exists(): time.sleep(0.01)"); '
          'child=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"],start_new_session=True); '
          f'Path({str(escaped)!r}).write_text(str(child.pid)); os._exit(0)')
    if via_wp_environment:
        # Exercise the production env-i boundary, replacing only external opam.
        opam=tmp_path/'opam'
        opam.write_text('#!'+sys.executable+'\n'+code+'\n');opam.chmod(0o755)
        shell=RUNNER.with_name('wp_run.sh')
        code=('import os; '+f'os.environ["PATH"]={str(tmp_path)!r}+":"+os.environ["PATH"]; '
              f'os.execv({str(shell)!r},[{str(shell)!r},"parse",{str(tmp_path)!r},"fixture.c"])')
    process=_start(tmp_path,'escaped.log',lock,code)
    child=None
    try:
        _wait(ready.exists)
        import time
        time.sleep(.2)  # the root exists across many ordinary 20ms samples
        process.send_signal(signal.SIGSTOP)
        _wait(lambda:psutil.Process(process.pid).status()==psutil.STATUS_STOPPED)
        release.touch()
        _wait(escaped.exists)
        child=int(escaped.read_text())
        _wait(lambda:_stopped(int(ready.read_text())))
        assert not _stopped(child)
        process.send_signal(signal.SIGCONT)
        stdout,stderr=process.communicate(timeout=8)
        assert process.returncode==0,stderr+stdout
        assert _stopped(child), 'unsampled reparented new-session child survived successful cleanup'
        assert not lock.exists()
        summary=json.loads((tmp_path/'escaped.log.summary.json').read_text())
        assert summary['unconfirmed_children']==[]
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGCONT);process.terminate();process.wait(timeout=8)
        if child is not None:
            try:psutil.Process(child).kill()
            except psutil.NoSuchProcess:pass


@pytest.mark.parametrize('persistent_denial', [True, False])
def test_marker_inspection_denial_quarantines_the_private_lease(tmp_path, persistent_denial):
    """A system inspection error cannot become absence of inherited descendants."""
    lock=tmp_path/'private.lock';output=tmp_path/'denied.log';wrapper=tmp_path/'runner.py'
    wrapper.write_text('import sys\n'+f'sys.path.insert(0,{str(RUNNER.parent)!r})\n'+
        'import counted_verifier as V\n'+
        'original=V.psutil.Process.environ\ncalls=[0]\n'+
        'def denied(self):\n calls[0]+=1\n'+f' if {persistent_denial!r} or calls[0]==1: raise V.psutil.AccessDenied(self.pid)\n'+
        ' return original(self)\n'+
        'V.psutil.Process.environ=denied\nraise SystemExit(V.main())\n')
    process=subprocess.run([sys.executable,str(wrapper),'--lock',str(lock),'--log',str(output),
        '--timeout','2','--',sys.executable,'-c','import time;time.sleep(.1)'],
        capture_output=True,text=True,timeout=8)
    summary=json.loads(Path(str(output)+'.summary.json').read_text())
    if persistent_denial:
        assert process.returncode==137,process.stderr+process.stdout
        assert lock.exists() and 'pid=1 ' in (lock/'owner').read_text()
        assert summary['unconfirmed_children'] and summary['exit_code']==137
    else:
        assert process.returncode==0,process.stderr+process.stdout
        assert not lock.exists() and summary['unconfirmed_children']==[]
