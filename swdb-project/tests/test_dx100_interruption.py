"""Durable interrupted execution precedes optional postmortem work. Date: 2026-09-26 ET.
Updated: 2026-10-09 ET (code review of ticket 06: the adapter runs in explicit Extensa fixture mode)."""
import json
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest
import yaml

from test_dx100 import EXTENSA, case, execution_request
from swdb import artifacts, dx100, profile
from swdb.processes import stop_group
from swdb.store import Store


@pytest.fixture
def interruption_case(case, records):
    """Keep the actual host's lane policy in the interrupted public execution."""
    machine = records.read('machines/fixturehost.yaml')
    if machine['hostname'] == 'mbit10':
        machine['lane_required'] = True
        records.write('machines/fixturehost.yaml', machine)
    return case


def interruption_lane(machine):
    if machine['hostname'] != 'mbit10':
        return '0'  # Explicit local contract fixture; no physical lane claim.
    verified = profile._verified_lane(machine, None)
    lane = verified.split(' ', 1)[0].removeprefix('mbit10-evaluation-node')
    assert lane in {'0', '1'} and '(verified: affinity, bind:' in verified
    return lane


@pytest.mark.parametrize('node', [0, 1])
def test_interruption_lane_uses_verified_helper_node(monkeypatch, node):
    machine = {'hostname': 'mbit10', 'lane_required': True}
    def verified(actual, claimed):
        assert actual is machine and claimed is None
        return f'mbit10-evaluation-node{node} (verified: affinity, bind:{node}, lease held, generation 1)'
    # This only tests argument propagation; actual Linux cases use the real guard.
    monkeypatch.setattr(profile, '_verified_lane', verified)
    assert interruption_lane(machine) == str(node)


@pytest.mark.parametrize('hostname', ['mbit10.eecs.umich.edu', 'local-contract-fixture'])
def test_interruption_case_preserves_host_lane_policy(request, records, monkeypatch, hostname):
    monkeypatch.setattr(socket, 'gethostname', lambda: hostname)
    selected = request.getfixturevalue('interruption_case')
    machine = records.read('machines/fixturehost.yaml')
    monkeypatch.delenv('LACT_SOCKET_LANE_PID', raising=False)
    if hostname.startswith('mbit10.'):
        # Reach the real lane guard; fixture status must not opt mbit10 out.
        with pytest.raises(profile.Failure, match='LACT_SOCKET_LANE_PID is not set'):
            dx100._prepare(SimpleNamespace(lane=None), 'execute', Store(records.path),
                           selected[0](), {'id': 'lane-admission-only'})
        assert machine['lane_required'] is True
    else:
        assert machine['lane_required'] is False
        assert profile._verified_lane(machine, None) is None


@pytest.mark.parametrize('postmortem', ['raises', 'stalls'])
def test_public_interruption_is_durable_before_postmortem(interruption_case, records, postmortem):
    request = execution_request(interruption_case, 'timeout')
    _, _, folder = interruption_case
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
        '--runs-dir', str(folder / 'runs'), '--lane',
        interruption_lane(records.read('machines/fixturehost.yaml')), '--format', 'json', *EXTENSA]
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
        machine = records.read('machines/fixturehost.yaml')
        if machine['hostname'] == 'mbit10':
            assert machine['lane_required'] is True
            assert '(verified: affinity, bind:' in retained['context']['lane']
        else:
            assert retained['context']['lane'] == 'mbit10-evaluation-node0'
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
