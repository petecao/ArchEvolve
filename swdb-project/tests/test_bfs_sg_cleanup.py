"""Streaming registration owns its compiler/parser processes. Updated: 2026-09-25 ET."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from conftest import REPO


@pytest.mark.parametrize('phase', ['compile', 'parse'])
def test_interrupting_stream_registration_reaps_owned_processes(tmp_path, phase):
    # A separately launched interpreter lets this test send a real TERM without
    # changing pytest's own signal handling. All executables are explicit fixtures.
    helper = tmp_path / 'helper'
    helper.write_text(f'#!{sys.executable}\n' + '''import os,pathlib,time
pathlib.Path(os.environ['SG_FIXTURE_PID']).write_text(str(os.getpid()))
time.sleep(60)
''')
    helper.chmod(0o755)
    compiler = tmp_path / 'compiler'
    compiler.write_text(f'#!{sys.executable}\n' + '''import os,pathlib,shutil,signal,subprocess,sys,time
if os.environ['SG_FIXTURE_PHASE']=='compile':
 child=subprocess.Popen([os.environ['SG_FIXTURE_HELPER']])
 def stop(signum,frame):
  child.wait(timeout=2)
  sys.exit(143)
 signal.signal(signal.SIGTERM,stop)
 child.wait()
else:
 shutil.copyfile(os.environ['SG_FIXTURE_HELPER'],sys.argv[-1])
 pathlib.Path(sys.argv[-1]).chmod(0o755)
''')
    compiler.chmod(0o755)
    graph = tmp_path / 'input.sg'
    graph.write_bytes(b'explicit parser fixture')
    pid_path = tmp_path / 'helper.pid'
    command = '''import os,pathlib,sys
from swdb import sg_stream
from swdb.cli import Failure
sg_stream.shutil.which=lambda name: os.environ['SG_FIXTURE_COMPILER']
try:
 sg_stream.inspect(pathlib.Path(sys.argv[1]),4,{'work_dir':sys.argv[2],'compile_timeout_s':30,'timeout_s':30})
except Failure as exc:
 print(str(exc),flush=True)
 sys.exit(23)
'''
    env = {**os.environ, 'SG_FIXTURE_PHASE': phase, 'SG_FIXTURE_HELPER': str(helper),
           'SG_FIXTURE_COMPILER': str(compiler), 'SG_FIXTURE_PID': str(pid_path)}
    parent = subprocess.Popen([sys.executable, '-c', command, str(graph), str(tmp_path / 'work')],
                              cwd=REPO, env=env, start_new_session=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    helper_pid = None
    try:
        end = time.monotonic() + 10
        while not pid_path.exists() and parent.poll() is None and time.monotonic() < end:
            time.sleep(0.02)
        assert pid_path.exists(), parent.communicate(timeout=2)
        helper_pid = int(pid_path.read_text())
        os.kill(parent.pid, signal.SIGTERM)
        out, err = parent.communicate(timeout=5)
        assert parent.returncode == 23 and 'interrupted' in out, out + err
        end = time.monotonic() + 2
        while time.monotonic() < end:
            try:
                os.kill(helper_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.02)
        else:
            pytest.fail('owned compiler/parser child survived registration interruption')
        assert not list((tmp_path / 'work').glob('swdb-sg-*'))
    finally:
        # Also clean the deliberately reproduced old failure path.
        for pid in (helper_pid, parent.pid):
            if pid is not None:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        try:
            os.killpg(parent.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        parent.wait(timeout=5)
