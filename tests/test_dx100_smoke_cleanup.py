"""Driver interruption preserves evidence and reaps nested jobs. Updated: 2026-09-25 ET."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

import pytest

from swdb import artifacts


@pytest.mark.parametrize('name', ['dx100_smoke', 'dx100_candidate_smoke'])
@pytest.mark.parametrize('interruption', ['deadline', 'signal'])
def test_smoke_reaps_nested_evaluator_and_preserves_failure(tmp_path, monkeypatch, name, interruption):
    script = Path(__file__).resolve().parents[1] / 'scripts' / (name + '.py')
    spec = importlib.util.spec_from_file_location(name + '_fixture', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    package = tmp_path / 'swdb'
    package.mkdir()
    (package / '__main__.py').write_text('''import json,os,pathlib,signal,subprocess,sys,time
command=sys.argv[1]
if command=='register-workload':
 print(json.dumps({'id':'workload'}))
elif command=='source-snapshot':
 print(json.dumps({'id':'source','artifact':{'sha256':'a'*64}}))
elif command=='baseline-candidate':
 print(json.dumps({'id':'candidate','artifact':{'sha256':'a'*64}}))
else:
 child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
 def stop(signum,frame):
  os.killpg(child.pid,signal.SIGTERM)
  child.wait(timeout=5)
  print('FIXTURE_INTERRUPTED_AND_REAPED',flush=True)
  sys.exit(143)
 signal.signal(signal.SIGTERM,stop)
 pathlib.Path('nested.pid').write_text(str(child.pid))
 print('FIXTURE_EXECUTOR_STARTED',flush=True)
 if os.environ.get('FIXTURE_INTERRUPT')=='signal': os.kill(os.getppid(),signal.SIGTERM)
 time.sleep(60)
''')
    converter = tmp_path / 'converter'
    converter.write_text(f'#!{sys.executable}\nimport pathlib,sys\npathlib.Path(sys.argv[-1]).write_bytes(b"fixture graph")\n')
    converter.chmod(0o755)
    binaries = [{'path': str(converter), 'sha256': artifacts.file_hash(converter)},
                {'path': '/fixture/gem5.opt', 'sha256': 'b' * 64},
                {'path': '/fixture/bfs_maa', 'sha256': 'c' * 64}]

    class FixtureStore:
        def get(self, identifier, kind):
            if kind == 'machine':
                return {}
            if identifier == 'checkpoint':
                return {'id': identifier, 'evidence_kind': 'execution',
                        'context': {'checkpoint_manifest': {'fixture': True}},
                        'request': {'workload': {'id': 'fixture', 'source': 0}}}
            return {'id': 'model', 'outcome': {'state': 'complete', 'stage': 'build'},
                    'evidence_kind': 'execution', 'context': {'model_root': '/fixture/model'},
                    'build': {'details': {'binaries': binaries}, 'model_revision': 'd' * 40}}

    monkeypatch.setenv('FIXTURE_INTERRUPT', interruption)
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, 'Store', lambda path: FixtureStore())
    monkeypatch.setattr(module.profile, '_verified_lane', lambda *args: None)
    monkeypatch.setattr(module, 'OUTER_SECONDS', 3)
    monkeypatch.setattr(module, 'CLEANUP_RESERVE_SECONDS', 1)
    monkeypatch.setattr(module.subprocess, 'check_output', lambda *args, **kwargs: 'fixture-commit\n')
    if name == 'dx100_candidate_smoke':
        monkeypatch.setattr(module, 'widen_sg', lambda source, dest: dest.write_bytes(b'fixture widened graph'))
    runs = tmp_path / 'runs'
    relative = Path.is_relative_to
    monkeypatch.setattr(Path, 'is_relative_to', lambda self, other: True if self == runs else relative(self, other))
    argv = [str(script), '--id', 'fixture', '--build-evaluation', 'model', '--runs-dir', str(runs), '--lane', '1']
    if name == 'dx100_smoke':
        argv += ['--checkpoint-evaluation', 'checkpoint']
    monkeypatch.setattr(sys, 'argv', argv)
    original_handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    expected = subprocess.TimeoutExpired if interruption == 'deadline' else InterruptedError
    with pytest.raises(expected):
        module.main()
    assert all(signal.getsignal(sig) == handler for sig, handler in original_handlers.items())
    receipt = json.loads((runs / 'fixture.driver/driver.json').read_text())
    assert receipt['state'] == 'failed' and receipt['gain_claim'] is False
    stage = receipt['stages'][-1]
    assert stage['state'] == 'interrupted_or_timeout' and stage['returncode'] == 143
    assert stage['host_wall_s'] < 3
    assert stage['stdout_sha256'] == artifacts.file_hash(stage['output'])
    assert stage['stderr_sha256'] == artifacts.file_hash(stage['stderr'])
    assert 'FIXTURE_INTERRUPTED_AND_REAPED' in Path(stage['output']).read_text()
    nested = int((tmp_path / 'nested.pid').read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(nested, 0)
