"""Owned nested-process cleanup, without remote or simulator work. Updated: 2026-09-25."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from swdb import artifacts


def test_driver_deadline_gracefully_reaps_nested_evaluator_child_and_retains_failure(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[1] / 'scripts/dx100_compile_smoke.py'
    spec = importlib.util.spec_from_file_location('compile_smoke_fixture', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    package = tmp_path / 'swdb'
    package.mkdir()
    (package / '__main__.py').write_text('''import json,os,pathlib,signal,subprocess,sys,time
command=sys.argv[1]
if command=='source-snapshot':
 print(json.dumps({'id':'source','artifact':{'sha256':'a'*64}}))
elif command=='baseline-candidate':
 print(json.dumps({'id':'candidate','artifact':{'sha256':'a'*64}}))
else:
 child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
 pathlib.Path('nested.pid').write_text(str(child.pid))
 def stop(signum,frame):
  os.killpg(child.pid,signal.SIGTERM)
  child.wait(timeout=5)
  print('FIXTURE_INTERRUPTED_AND_REAPED',flush=True)
  sys.exit(143)
 signal.signal(signal.SIGTERM,stop)
 print('FIXTURE_COMPILER_STARTED',flush=True)
 time.sleep(60)
''')
    class FixtureStore:
        def get(self, name, kind):
            if kind == 'machine': return {}
            if kind == 'implementation': return {'function': 'DOBFS'}
            return {'id': 'model', 'outcome': {'state': 'complete', 'stage': 'build'},
                    'evidence_kind': 'execution', 'context': {'model_root': '/fixture/model'}}
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, 'Store', lambda path: FixtureStore())
    monkeypatch.setattr(module.profile, '_verified_lane', lambda *args: None)
    monkeypatch.setattr(module, 'OUTER_SECONDS', 3)
    monkeypatch.setattr(module, 'CLEANUP_RESERVE_SECONDS', 1)
    monkeypatch.setattr(module.subprocess, 'check_output', lambda *args, **kwargs: 'fixture-commit\n')
    runs = tmp_path / 'runs'
    relative = Path.is_relative_to
    monkeypatch.setattr(Path, 'is_relative_to', lambda self, other: True if self == runs else relative(self, other))
    monkeypatch.setattr(sys, 'argv', [str(script), '--id', 'fixture', '--build-evaluation', 'model',
                                    '--runs-dir', str(runs), '--lane', '1'])
    with pytest.raises(subprocess.TimeoutExpired):
        module.main()
    receipt = json.loads((runs / 'fixture.driver/driver.json').read_text())
    assert receipt['state'] == 'failed' and receipt['guest_execution'] is False
    stage = receipt['stages'][-1]
    assert stage['state'] == 'interrupted_or_timeout' and stage['returncode'] == 143
    assert stage['host_wall_s'] < 3
    assert stage['stdout_sha256'] == artifacts.file_hash(stage['output'])
    assert stage['stderr_sha256'] == artifacts.file_hash(stage['stderr'])
    assert 'FIXTURE_INTERRUPTED_AND_REAPED' in Path(stage['output']).read_text()
    nested = int((tmp_path / 'nested.pid').read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(nested, 0)
