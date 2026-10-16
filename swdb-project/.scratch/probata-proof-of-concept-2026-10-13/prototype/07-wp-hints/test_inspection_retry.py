"""Public runner inspection policy controls, 2026-10-15 ET; no solver jobs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

RUNNER = Path(__file__).with_name('counted_verifier.py')


@pytest.fixture(params=['AccessDenied', 'SystemError'])
def environment_error(request):
    return request.param


def _environment_failure(kind):
    if kind == 'AccessDenied':
        return 'raise V.psutil.AccessDenied(self.pid)'
    return 'raise SystemError("<built-in function proc_environ> returned a result with an exception set")'


def test_live_environment_denial_can_recover_after_the_old_short_window(tmp_path, environment_error):
    """A150ms denial on one real live identity must not become a permanent refusal."""
    lock = tmp_path/'private.lock'
    output = tmp_path/'inspection.log'
    pid_file = tmp_path/'owned.pid'
    wrapper = tmp_path/'runner.py'
    wrapper.write_text(
        'import sys,time\nfrom pathlib import Path\n'
        + f'sys.path.insert(0,{str(RUNNER.parent)!r})\n'
        + 'import counted_verifier as V\noriginal=V.psutil.Process.environ\nfirst=[None]\n'
        + 'def environ(self):\n'
        + f' p=Path({str(pid_file)!r})\n'
        + ' if p.exists() and self.pid==int(p.read_text()):\n'
        + '  first[0]=time.monotonic() if first[0] is None else first[0]\n'
        + f'  if time.monotonic()-first[0]<.15: {_environment_failure(environment_error)}\n'
        + ' return original(self)\n'
        + 'V.psutil.Process.environ=environ\nraise SystemExit(V.main())\n')
    child = ('import os,time;from pathlib import Path;'
             + f'Path({str(pid_file)!r}).write_text(str(os.getpid()));time.sleep(.7)')
    result = subprocess.run(
        [sys.executable,str(wrapper),'--lock',str(lock),'--log',str(output),
         '--timeout','2','--',sys.executable,'-c',child],
        capture_output=True,text=True,timeout=8)
    report = json.loads(Path(str(output)+'.summary.json').read_text())
    assert result.returncode == 0, result.stderr+result.stdout+str(report.get('inspection_failure'))
    assert report['error'] is None and report['unconfirmed_children'] == []
    assert not lock.exists()
    denied = [e for e in report['inspection_events'] if e['outcome']==('denied' if environment_error=='AccessDenied' else 'inspection-error')]
    recovered = [e for e in report['inspection_events'] if e['outcome']=='recovered']
    assert denied and recovered
    assert denied[0]['expected_birth'] == denied[-1]['expected_birth']
    assert recovered[-1]['clock_s']-denied[0]['clock_s'] >= .12
    assert not report['timed_out'] and not report['killed_by_watchdog']


def test_persistent_live_environment_denial_still_refuses_and_quarantines(tmp_path, environment_error):
    lock = tmp_path/'private.lock'
    output = tmp_path/'inspection.log'
    pid_file = tmp_path/'owned.pid'
    wrapper = tmp_path/'runner.py'
    wrapper.write_text(
        'import sys\nfrom pathlib import Path\n'
        + f'sys.path.insert(0,{str(RUNNER.parent)!r})\n'
        + 'import counted_verifier as V\noriginal=V.psutil.Process.environ\n'
        + 'def environ(self):\n'
        + f' p=Path({str(pid_file)!r})\n'
        + f' if p.exists() and self.pid==int(p.read_text()): {_environment_failure(environment_error)}\n'
        + ' return original(self)\n'
        + 'V.psutil.Process.environ=environ\nraise SystemExit(V.main())\n')
    child = ('import os,time;from pathlib import Path;'
             + f'Path({str(pid_file)!r}).write_text(str(os.getpid()));time.sleep(2)')
    secret = 'private-inspection-fixture-never-persist'
    result = subprocess.run(
        [sys.executable,str(wrapper),'--lock',str(lock),'--log',str(output),
         '--timeout','3','--',sys.executable,'-c',child],
        env={**os.environ,'PROBATA_PRIVATE_FIXTURE':secret},
        capture_output=True,text=True,timeout=8)
    text = Path(str(output)+'.summary.json').read_text()
    report = json.loads(text)
    assert result.returncode != 0 and report['error'].startswith(environment_error)
    failure = report['inspection_failure']
    assert failure['identity_state'] == 'live' and failure['requested_operation'] == 'environ'
    assert failure['expected_birth'] == failure['observed_birth']
    decision = failure.get('retry_expiry', failure)
    assert decision['retry_elapsed_s'] >= .19 and failure['attempt'] <= 21
    if 'retry_expiry' in failure:
        assert failure['clock_s'] < decision['clock_s']
    assert report['unconfirmed_children'] and lock.exists()
    assert report['primary_inspection_failure']['stage'] == 'supervision'
    assert report['cleanup_inspection_failure']['stage'] == 'cleanup'
    assert secret not in text+result.stdout+result.stderr
    import psutil
    try:
        assert psutil.Process(int(pid_file.read_text())).status() in {psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD}
    except psutil.NoSuchProcess:
        pass


def test_unknown_identity_after_denial_never_certifies_absence_or_signals(tmp_path, environment_error):
    import psutil
    lock = tmp_path/'private.lock'
    output = tmp_path/'inspection.log'
    identity_file = tmp_path/'identity.json'
    wrapper = tmp_path/'runner.py'
    wrapper.write_text(
        'import sys,json\nfrom pathlib import Path\n'
        + f'sys.path.insert(0,{str(RUNNER.parent)!r})\n'
        + 'import counted_verifier as V\noriginal_env=V.psutil.Process.environ\noriginal_birth=V.psutil.Process.create_time\ndenied=[False]\n'
        + f'def target():\n p=Path({str(identity_file)!r})\n return json.loads(p.read_text())["pid"] if p.exists() else None\n'
        + 'def birth(self):\n'
        + ' if denied[0] and self.pid==target(): raise V.psutil.AccessDenied(self.pid)\n'
        + ' return original_birth(self)\n'
        + 'def environ(self):\n'
        + f' if self.pid==target():\n  denied[0]=True\n  {_environment_failure(environment_error)}\n'
        + ' return original_env(self)\n'
        + 'V.psutil.Process.create_time=birth\nV.psutil.Process.environ=environ\nraise SystemExit(V.main())\n')
    child = ('import os,time,json,psutil;from pathlib import Path;'
             + f'Path({str(identity_file)!r}).write_text(json.dumps({{"pid":os.getpid(),"birth":psutil.Process().create_time()}}));time.sleep(4)')
    try:
        result = subprocess.run(
            [sys.executable,str(wrapper),'--lock',str(lock),'--log',str(output),
             '--timeout','3','--',sys.executable,'-c',child],
            capture_output=True,text=True,timeout=8)
        report = json.loads(Path(str(output)+'.summary.json').read_text())
        assert result.returncode != 0 and report['inspection_failure']['identity_state']=='unknown'
        identity_error = report['inspection_failure']['identity_exception']
        assert identity_error['operation'] == 'identity_validation.create_time'
        assert identity_error['exception']['type'] == 'AccessDenied'
        assert report['unconfirmed_children'] and lock.exists()
        identity = json.loads(identity_file.read_text())
        live = psutil.Process(identity['pid'])
        assert live.create_time() == identity['birth'] and live.is_running()
        assert live.status() not in {psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD}, 'unknown identity was signaled'
    finally:
        if identity_file.exists():
            identity = json.loads(identity_file.read_text())
            try:
                live = psutil.Process(identity['pid'])
                if live.create_time() == identity['birth']:
                    live.kill()
                    live.wait(timeout=3)
            except psutil.NoSuchProcess:
                pass


def test_reused_pid_with_foreign_marker_is_not_adopted_or_signaled(tmp_path, environment_error):
    """Model PID reuse at the OS boundary; never force kernel PID allocation."""
    import psutil
    lock = tmp_path/'private.lock'
    output = tmp_path/'inspection.log'
    identity_file = tmp_path/'identity.json'
    wrapper = tmp_path/'runner.py'
    wrapper.write_text(
        'import sys,json\nfrom pathlib import Path\n'
        + f'sys.path.insert(0,{str(RUNNER.parent)!r})\n'
        + 'import counted_verifier as V\noriginal_env=V.psutil.Process.environ\noriginal_birth=V.psutil.Process.create_time\nreused=[False]\n'
        + f'def target():\n p=Path({str(identity_file)!r})\n return json.loads(p.read_text())["pid"] if p.exists() else None\n'
        + 'def birth(self):\n value=original_birth(self)\n return value+1 if reused[0] and self.pid==target() else value\n'
        + 'def environ(self):\n'
        + ' if self.pid==target():\n'
        + f'  if not reused[0]:\n   reused[0]=True\n   {_environment_failure(environment_error)}\n'
        + '  return {V.RUN_TOKEN_ENV:"foreign-marker-fixture"}\n'
        + ' return original_env(self)\n'
        + 'V.psutil.Process.create_time=birth\nV.psutil.Process.environ=environ\nraise SystemExit(V.main())\n')
    child = ('import os,time,json,psutil;from pathlib import Path;'
             + f'Path({str(identity_file)!r}).write_text(json.dumps({{"pid":os.getpid(),"birth":psutil.Process().create_time()}}));time.sleep(4)')
    try:
        result = subprocess.run(
            [sys.executable,str(wrapper),'--lock',str(lock),'--log',str(output),
             '--timeout','.3','--',sys.executable,'-c',child],
            capture_output=True,text=True,timeout=8)
        text = Path(str(output)+'.summary.json').read_text()
        report = json.loads(text)
        assert result.returncode != 0 and report['timed_out']
        assert report['unconfirmed_children']==['root-pid-reused-or-unobserved'] and lock.exists()
        assert any(e['identity_state']=='reused' and e['outcome']=='confirmed-reused' for e in report['inspection_events'])
        assert 'foreign-marker-fixture' not in text
        identity = json.loads(identity_file.read_text())
        live = psutil.Process(identity['pid'])
        assert live.create_time()==identity['birth'] and live.status() not in {psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD}
    finally:
        if identity_file.exists():
            identity = json.loads(identity_file.read_text())
            try:
                live = psutil.Process(identity['pid'])
                if live.create_time()==identity['birth']:
                    live.kill()
                    live.wait(timeout=3)
            except psutil.NoSuchProcess:
                pass


def test_foreign_unmarked_process_survives_recovered_inspection_and_is_not_charged(tmp_path, environment_error):
    import time
    import psutil
    lock = tmp_path/'private.lock'
    output = tmp_path/'inspection.log'
    ready = tmp_path/'foreign.ready'
    foreign_env = dict(os.environ)
    foreign_env.pop('SWDB_VERIFIER_RUN_TOKEN',None)
    secret = 'foreign-environment-value-never-persist'
    foreign_env['PROBATA_PRIVATE_FIXTURE'] = secret
    code = ('import time;from pathlib import Path;data=bytearray(64*1024*1024);'
            'data[::4096]=b"x"*(len(data)//4096);'
            + f'Path({str(ready)!r}).touch();time.sleep(5)')
    foreign = subprocess.Popen([sys.executable,'-c',code],env=foreign_env)
    identity = psutil.Process(foreign.pid).create_time()
    try:
        deadline = time.monotonic()+3
        while not ready.exists():
            assert time.monotonic()<deadline
            time.sleep(.005)
        assert psutil.Process(foreign.pid).memory_info().rss > 32*1024**2
        wrapper = tmp_path/'runner.py'
        wrapper.write_text(
            'import sys,time\n'
            + f'sys.path.insert(0,{str(RUNNER.parent)!r})\n'
            + 'import counted_verifier as V\noriginal=V.psutil.Process.environ\nfirst=[None]\n'
            + 'def environ(self):\n'
            + f' if self.pid=={foreign.pid}:\n'
            + '  first[0]=time.monotonic() if first[0] is None else first[0]\n'
            + f'  if time.monotonic()-first[0]<.15: {_environment_failure(environment_error)}\n'
            + ' return original(self)\n'
            + 'V.psutil.Process.environ=environ\nraise SystemExit(V.main())\n')
        result = subprocess.run(
            [sys.executable,str(wrapper),'--lock',str(lock),'--log',str(output),
             '--cap-gb','.03','--timeout','2','--',sys.executable,'-c','import time;time.sleep(.5)'],
            capture_output=True,text=True,timeout=8)
        text = Path(str(output)+'.summary.json').read_text()
        report = json.loads(text)
        assert result.returncode==0, result.stderr+result.stdout
        assert report['unconfirmed_children']==[] and not lock.exists()
        assert not report['killed_by_watchdog'] and report['peak_rss_mb'] < .03*1024
        assert any(e['pid']==foreign.pid and e['outcome']=='recovered' for e in report['inspection_events'])
        current = psutil.Process(foreign.pid)
        assert current.create_time()==identity and current.status() not in {psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD}
        assert secret not in text+result.stdout+result.stderr
    finally:
        try:
            current = psutil.Process(foreign.pid)
            if current.create_time()==identity:
                current.kill()
                foreign.wait(timeout=3)
        except psutil.NoSuchProcess:
            pass


@pytest.mark.parametrize('limit',['rss','deadline'])
def test_recovered_denial_does_not_waive_rss_or_counted_deadline(tmp_path,limit,environment_error):
    lock = tmp_path/'private.lock'
    output = tmp_path/'inspection.log'
    wrapper = tmp_path/'runner.py'
    wrapper.write_text(
        'import sys,time\n'
        + f'sys.path.insert(0,{str(RUNNER.parent)!r})\n'
        + 'import counted_verifier as V\noriginal=V.psutil.Process.environ\nfirst=[None]\n'
        + 'def environ(self):\n data=original(self)\n'
        + ' if data.get(V.RUN_TOKEN_ENV):\n'
        + '  first[0]=time.monotonic() if first[0] is None else first[0]\n'
        + f'  if time.monotonic()-first[0]<.15: {_environment_failure(environment_error)}\n'
        + ' return data\n'
        + 'V.psutil.Process.environ=environ\nraise SystemExit(V.main())\n')
    child = ('import time;time.sleep(.05);data=bytearray(64*1024*1024);'
             'data[::4096]=b"x"*(len(data)//4096);time.sleep(.8)')
    result = subprocess.run(
        [sys.executable,str(wrapper),'--lock',str(lock),'--log',str(output),
         '--cap-gb','.03' if limit=='rss' else '8',
         '--timeout','2' if limit=='rss' else '.06','--',sys.executable,'-c',child],
        capture_output=True,text=True,timeout=8)
    report = json.loads(Path(str(output)+'.summary.json').read_text())
    assert result.returncode==137, result.stderr+result.stdout
    assert report['unconfirmed_children']==[] and not lock.exists()
    assert report['error'] is None and report['inspection_failure'] is None
    assert any(e['outcome']=='recovered' for e in report['inspection_events'])
    assert report['wall_s'] >= .12, 'retry wait disappeared from counted process time'
    assert report['clock']=='continuous_monotonic'
    if limit=='rss':
        assert report['killed_by_watchdog'] and report['peak_rss_mb'] > .03*1024
        assert not report['timed_out']
    else:
        assert report['timed_out'] and not report['killed_by_watchdog']
        assert report['wall_s'] > report['timeout_s']


def test_environ_retry_cannot_start_after_its_continuous_retry_deadline(tmp_path,environment_error):
    lock=tmp_path/'private.lock';log=tmp_path/'inspection.log';pid=tmp_path/'owned.pid';elapsed=tmp_path/'next-environ-time';wrapper=tmp_path/'runner.py'
    wrapper.write_text('import sys,time\nfrom pathlib import Path\n'+f'sys.path.insert(0,{str(RUNNER.parent)!r})\n'+
      'import counted_verifier as V\noriginal_env=V.psutil.Process.environ\noriginal_sleep=V.time.sleep\nfirst=[None]\npaused=[False]\n'+
      'def environ(self):\n'+f' p=Path({str(pid)!r})\n'+
      ' if p.exists() and self.pid==int(p.read_text()):\n'+
      f'  if first[0] is None:\n   first[0]=time.monotonic()\n   {_environment_failure(environment_error)}\n'+
      f'  q=Path({str(elapsed)!r})\n'+
      '  if not q.exists():q.write_text(str(time.monotonic()-first[0]))\n'+
      ' return original_env(self)\n'+
      'def sleep(seconds):\n'+
      ' if first[0] is not None and not paused[0] and seconds<=.010001:\n  paused[0]=True\n  return original_sleep(.25)\n'+
      ' return original_sleep(seconds)\n'+
      'V.psutil.Process.environ=environ\nV.time.sleep=sleep\nraise SystemExit(V.main())\n')
    child='import os,time;from pathlib import Path;'+f'Path({str(pid)!r}).write_text(str(os.getpid()));time.sleep(.8)'
    result=subprocess.run([sys.executable,str(wrapper),'--lock',str(lock),'--log',str(log),'--timeout','2','--',sys.executable,'-c',child],capture_output=True,text=True,timeout=8)
    report=json.loads(Path(str(log)+'.summary.json').read_text())
    assert result.returncode!=0, 'retry began and recovered after continuous retry deadline: '+json.dumps({'next_environ_elapsed_s':float(elapsed.read_text()),'recovered':[e for e in report['inspection_events']if e['outcome']=='recovered']})
    assert report['error'].startswith(environment_error)
    assert not report['timed_out'] and not report['killed_by_watchdog']
    failure=report['inspection_failure'];expiry=failure['retry_expiry']
    assert failure['attempt']==1 and failure['identity_state']=='live'
    assert expiry['retry_expired_before_attempt']==2 and expiry['retry_elapsed_s']>=.2
    assert expiry['last_error_clock_s']==failure['clock_s']<expiry['clock_s']
    if environment_error=='AccessDenied':
        assert expiry['last_denial_clock_s']==failure['clock_s']
    assert report['unconfirmed_children']==[] and not lock.exists()
