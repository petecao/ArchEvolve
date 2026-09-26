"""Durable interrupted execution precedes optional postmortem work. Date: 2026-09-26 ET."""
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest
import yaml

from test_dx100 import case, execution_request
from swdb import artifacts
from swdb.processes import stop_group


@pytest.mark.parametrize('postmortem', ['raises', 'stalls'])
def test_public_interruption_is_durable_before_postmortem(case, records, postmortem):
    request = execution_request(case, 'timeout')
    _, _, folder = case
    request['verification'] = {'checker': 'dx100.bfs.verifier.v1', 'max_ticks': 1000000}
    model = Path(request['model_root'])
    for name in ('bfs.cc', 'benchmark.h'):
        path = model / 'benchmarks/gapbs/src' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('// Explicit source identity fixture, not simulator evidence.\n')
    request_path = folder / 'request.yaml'
    request_path.write_text(yaml.safe_dump(request))
    marker, release = folder / 'postmortem-entered', folder / 'postmortem-release'
    driver = '''import pathlib,sys,time
from swdb import dx100
from swdb.bfs_native import StageFailure
from swdb.cli import main
marker,release,mode=pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3]
def postmortem(*args):
    marker.write_text('entered')
    if mode=='stalls':
        deadline=time.monotonic()+15
        while not release.exists() and time.monotonic()<deadline: time.sleep(.01)
    raise StageFailure('missing_observation','explicit postmortem fixture error')
dx100._correctness=postmortem
sys.argv=['swdb',*sys.argv[4:]]
raise SystemExit(main())
'''
    command = [sys.executable, '-c', driver, str(marker), str(release), postmortem,
        'dx100-execute', str(request_path), '--records', str(records.path),
        '--runs-dir', str(folder / 'runs'), '--lane', '0', '--format', 'json']
    child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, start_new_session=True)
    canonical = records.path / 'evaluations' / (request['id'] + '.yaml')
    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if canonical.exists():
                value = yaml.safe_load(canonical.read_text())
                if value['outcome'] == {'state': 'running', 'stage': 'simulation', 'reason': None}:
                    break
            assert child.poll() is None, child.communicate()
            time.sleep(.02)
        else:
            pytest.fail('fixture did not reach its simulation stage')
        child.send_signal(signal.SIGTERM)
        while not marker.exists() and time.monotonic() < deadline:
            assert child.poll() is None, child.communicate()
            time.sleep(.02)
        assert marker.exists(), 'postmortem entry was not observed'
        # Reopen the public canonical record while postmortem is still blocked.
        retained = yaml.safe_load(canonical.read_text())
        assert retained['outcome']['state'] == 'interrupted', retained['outcome']
        assert retained['outcome']['stage'] == 'simulation'
        assert 'SIGTERM' in retained['outcome']['reason']
        assert retained['timing'] == [] and retained['correctness']['state'] == 'unverified'
        assert retained['stages'][-1]['stage'] == 'simulation'
        assert retained['stages'][-1]['state'] == 'interrupted'
        assert any(stage['stage'] == 'checkpoint' and stage['state'] == 'complete'
                   for stage in retained['stages'])
        checkpoint = retained['context']['checkpoint_manifest']
        assert artifacts.file_hash(checkpoint['path']) == checkpoint['sha256']
        artifacts.verify(json.loads(Path(checkpoint['path']).read_text())['artifact'])
        if postmortem == 'stalls':
            assert child.poll() is None
            retrieved = records.swdb('get', request['id'], '--format', 'json')
            assert retrieved.returncode == 0, retrieved.stderr
            assert json.loads(retrieved.stdout)['outcome'] == retained['outcome']
        release.write_text('continue')
        stdout, stderr = child.communicate(timeout=20)
        assert child.returncode == 1, stderr
        result = json.loads(stdout)
        assert result['outcome'] == retained['outcome']
        assert result['context']['postmortem']['state'] == 'failed'
        assert 'postmortem fixture error' in result['context']['postmortem']['reason']
        assert result['correctness']['state'] == 'unverified' and result['gain_claim'] is False
    finally:
        release.write_text('continue')
        stop_group(child, grace_seconds=1)
