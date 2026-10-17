"""Real local descendants; no lab or provider calls. Updated: 2026-10-05 ET (shared tests/testkit); 2026-09-26 ET."""
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

import pytest
import yaml

from scripts.dx100_build import stop as stop_build
from scripts.bfs_process import run_stage
from swdb.artifacts import file_hash
from swdb.dx100 import _terminate
from swdb.processes import stop_group
from test_bfs_campaign_cleanup import running, driver
from test_dx100 import case


def program(folder, leader_exits):
    descendant = folder / 'descendant.pid'
    leader = folder / 'leader.pid'
    child_code = ('import os,signal,time; from pathlib import Path; '
        'signal.signal(signal.SIGTERM,signal.SIG_IGN); '
        f'Path({str(descendant)!r}).write_text(str(os.getpid())); time.sleep(60)')
    return ('import os,subprocess,sys,time\nfrom pathlib import Path\n'
        f'Path({str(leader)!r}).write_text(str(os.getpid()))\n'
        f'subprocess.Popen([sys.executable,"-c",{child_code!r}])\n'
        f'while not Path({str(descendant)!r}).exists(): time.sleep(.01)\n'
        'print("ready",flush=True)\n' + ('' if leader_exits else 'time.sleep(60)\n'))


def cleanup(folder):
    if (folder / 'leader.pid').exists():
        try:
            os.killpg(int((folder / 'leader.pid').read_text()), signal.SIGKILL)
        except ProcessLookupError:
            pass


@pytest.mark.parametrize('stop', [stop_group, _terminate, stop_build],
                         ids=['shared', 'dx100-adapter', 'dx100-build'])
@pytest.mark.parametrize('leader_exits', [False, True], ids=['term-exit', 'already-reaped'])
def test_stop_reaps_owned_descendants_even_after_leader_exits(tmp_path, stop, leader_exits):
    child = subprocess.Popen([sys.executable, '-c', program(tmp_path, leader_exits)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    try:
        assert select.select([child.stdout], [], [], 5)[0], 'fixture did not start'
        assert child.stdout.readline() == b'ready\n'
        if leader_exits:
            assert child.wait(timeout=3) == 0
        stop(child)
        assert child.returncode == (0 if leader_exits else -signal.SIGTERM)
        assert select.select([child.stdout], [], [], 3)[0], 'descendant still holds stdout open'
        assert child.stdout.read() == b''
    finally:
        cleanup(tmp_path)
        child.wait(timeout=3)
        child.stdout.close()
        child.stderr.close()


@pytest.mark.parametrize('leader_exits', [False, True], ids=['timeout', 'successful-leader'])
def test_public_dx100_build_cleans_descendants_and_retains_outcome(case, leader_exits):
    request, invoke, folder = case
    data = request('owned-group')
    data['budget']['total_seconds'] = 2
    data['fixture_command'] = [sys.executable, '-c', program(folder, leader_exits)]
    try:
        result = invoke('dx100-build', data)
        assert result['outcome']['state'] in ({'complete'} if leader_exits else {'timed_out', 'budget_exhausted'})
        assert result['stages'][-1]['log_sha256']
        pid = int((folder / 'descendant.pid').read_text())
        until = time.monotonic() + 3
        while running(pid) and time.monotonic() < until:
            time.sleep(.02)
        assert not running(pid), 'public adapter left an owned descendant running'
    finally:
        cleanup(folder)


@pytest.mark.parametrize('mode', ['timeout', 'completed', 'failed'])
def test_public_provider_reaps_descendant_and_retains_outcome(proposal_setup, tmp_path, mode):
    records, runs, _, request = proposal_setup
    config = tmp_path / 'provider.yaml'
    code = program(tmp_path, mode != 'timeout')
    response = {'interpretation': 'Explicit fixture response.', 'patch': '', 'unresolved': ['Fixture cannot rewrite.']}
    code = code.replace('print("ready",flush=True)', 'print(' + repr(json.dumps(response)) + ',flush=True)')
    if mode == 'failed':
        code += 'raise SystemExit(7)\n'
    config.write_text(yaml.safe_dump({'kind': 'external_fixture', 'workspace': False,
        'command': [sys.executable, '-c', code],
        'timeout_s': 1, 'max_repairs': 1, 'total_seconds': 10}))
    try:
        result = records.swdb('submit', request(payload={'kind': 'natural_language', 'content': 'Adjust alpha to 14.'}),
            '--provider-config', config, '--runs-dir', runs, '--format', 'json')
        assert result.returncode == 1, result.stderr
        data = json.loads(result.stdout)
        assert data['repair_budget']['used_seconds'] > 0
        state = 'interrupted_or_timeout' if mode == 'timeout' else mode
        assert data['attempts'][0]['provider']['state'] == state
        if mode == 'timeout':
            assert data['repair_budget']['used_seconds'] >= 1
        else:
            assert data['attempts'][0]['provider']['returncode'] == (0 if mode == 'completed' else 7)
        assert records.swdb('get', data['id']).returncode == 0
        pid = int((tmp_path / 'descendant.pid').read_text())
        until = time.monotonic() + 3
        while running(pid) and time.monotonic() < until:
            time.sleep(.02)
        assert not running(pid), 'provider left an owned descendant running'
    finally:
        cleanup(tmp_path)


@pytest.mark.parametrize('mode', ['success', 'failure', 'timeout'])
def test_generic_driver_retains_outcome_without_claiming_post_reap_tree_cleanup(tmp_path, mode):
    receipt = {'stages': []}
    command = [sys.executable, '-c', program(tmp_path, mode != 'timeout') +
               ('raise SystemExit(7)\n' if mode == 'failure' else '')]
    try:
        if mode == 'success':
            run_stage(receipt, tmp_path, command, timeout=1, deadline=time.monotonic()+5, cwd=tmp_path)
        else:
            expected = RuntimeError if mode == 'failure' else subprocess.TimeoutExpired
            with pytest.raises(expected):
                run_stage(receipt, tmp_path, command, timeout=1, deadline=time.monotonic()+5, cwd=tmp_path)
        row = json.loads((tmp_path / 'driver.json').read_text())['stages'][0]
        assert row['state'] == {'success':'complete', 'failure':'failed', 'timeout':'interrupted_or_timeout'}[mode]
        assert row['stdout_sha256'] == file_hash(row['output'])
        pid = int((tmp_path / 'descendant.pid').read_text())
        # A reaped leader does not authorize stale numeric group signaling.
        # The actual Linux Owned tests establish prospective whole-tree cleanup.
        assert running(pid)
    finally:
        cleanup(tmp_path)


@pytest.mark.parametrize('returncode', [0, 3])
def test_generic_campaign_preserves_json_without_stale_post_reap_signal(driver, tmp_path, returncode):
    worker, main = driver
    code = program(tmp_path, True).replace('print("ready",flush=True)', 'print(\'{"recorded":true}\',flush=True)')
    main.write_text(code + f'raise SystemExit({returncode})\n')
    try:
        assert worker.call('fixture', required=False) == {'recorded': True}
        row = json.loads((worker.folder / 'driver.json').read_text())['stages'][0]
        assert row['returncode'] == returncode
        assert row['state'] == ('complete' if returncode == 0 else 'failed')
        assert row['stdout_sha256'] == file_hash(row['stdout'])
        pid = int((tmp_path / 'descendant.pid').read_text())
        assert running(pid), 'generic path makes no post-reap descendant claim'
    finally:
        cleanup(tmp_path)
