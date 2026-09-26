"""Local subprocess cleanup; no provider or host execution. Updated: 2026-09-26 ET."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from types import SimpleNamespace

import pytest

from scripts import bfs_native_campaign as campaign
from swdb import artifacts


@pytest.fixture
def driver(tmp_path, monkeypatch):
    app = tmp_path / 'app'; package = app / 'swdb'; package.mkdir(parents=True)
    (package / '__init__.py').write_text('')
    monkeypatch.setattr(campaign, 'ROOT', app)
    monkeypatch.setattr(campaign, 'Store', lambda _: SimpleNamespace(get=lambda *_: {}))
    monkeypatch.setattr(campaign.profile, '_verified_lane', lambda *_: 'local fixture')
    monkeypatch.setattr(campaign.os, 'statvfs', lambda _: SimpleNamespace(f_bavail=100*1024**3, f_frsize=1))
    args = SimpleNamespace(id='cleanup', protocol='fixture', lane='fixture', total_seconds=30,
        runs_dir=tmp_path, source_runs_dir=tmp_path, records=tmp_path, repair_config=None)
    return campaign.Driver(args), package / '__main__.py'


def running(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    # Linux container init may retain an orphan zombie; it has terminated.
    status = Path(f'/proc/{pid}/stat')
    if status.exists():
        try:
            return status.read_text().rsplit(')', 1)[1].split()[0] != 'Z'
        except FileNotFoundError:
            return False
    return True


def test_timeout_kills_term_resistant_descendant_after_leader_exits(driver, tmp_path):
    worker, main = driver
    descendant = tmp_path / 'descendant.pid'
    leader = tmp_path / 'leader.pid'
    child_code = ('import os,signal,time; from pathlib import Path; '
        'signal.signal(signal.SIGTERM, signal.SIG_IGN); '
        f'Path({str(descendant)!r}).write_text(str(os.getpid())); '
        'print("descendant ready",flush=True); time.sleep(60)')
    main.write_text('import os,subprocess,sys,time\nfrom pathlib import Path\n'
        f'Path({str(leader)!r}).write_text(str(os.getpid()))\n'
        f'subprocess.Popen([sys.executable,"-c",{child_code!r}])\n'
        f'while not Path({str(descendant)!r}).exists(): time.sleep(.01)\n'
        'print("leader ready",flush=True)\ntime.sleep(60)\n')
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            worker.call('fixture', timeout=2)
        pid, group = int(descendant.read_text()), int(leader.read_text())
        until = time.monotonic() + 3
        while running(pid) and time.monotonic() < until:
            time.sleep(.02)
        assert not running(pid), 'same-group TERM-resistant descendant survived cleanup'
        assert not running(group), 'leader survived cleanup'
        saved = json.loads((worker.folder / 'driver.json').read_text())['stages'][0]
        assert saved['state'] == 'interrupted_or_timeout' and saved['returncode'] == -signal.SIGTERM
        assert 'leader ready' in Path(saved['stdout']).read_text()
        assert saved['stdout_sha256'] == artifacts.file_hash(saved['stdout'])
        assert saved['stderr_sha256'] == artifacts.file_hash(saved['stderr'])
        assert saved['host_wall_s'] > 0
    finally:
        if leader.exists():
            try: os.killpg(int(leader.read_text()), signal.SIGKILL)
            except ProcessLookupError: pass


@pytest.mark.parametrize('returncode,required', [(0, True), (3, False), (3, True)])
def test_completed_and_failed_commands_keep_json_and_receipt_semantics(driver, returncode, required):
    worker, main = driver
    main.write_text(f'import sys\nprint(\'{{"recorded":true}}\',flush=True)\nsys.exit({returncode})\n')
    if required and returncode:
        with pytest.raises(RuntimeError, match='fixture failed'):
            worker.call('fixture', required=required)
    else:
        assert worker.call('fixture', required=required) == {'recorded': True}
    saved = json.loads((worker.folder / 'driver.json').read_text())['stages'][0]
    assert saved['returncode'] == returncode
    assert saved['state'] == ('failed' if returncode else 'complete')
    assert saved['stdout_sha256'] == artifacts.file_hash(saved['stdout'])


def test_spawn_failure_is_retained_and_budget_preflight_starts_no_child(driver, monkeypatch):
    worker, _ = driver
    def fail(*args, **kwargs):
        raise OSError('fixture spawn failure')
    monkeypatch.setattr(campaign.subprocess, 'Popen', fail)
    with pytest.raises(OSError, match='fixture spawn failure'):
        worker.call('fixture')
    saved = json.loads((worker.folder / 'driver.json').read_text())['stages'][0]
    assert saved['state'] == 'failed' and saved['returncode'] is None
    assert saved['stdout_sha256'] == artifacts.file_hash(saved['stdout'])
    worker.started -= 100
    with pytest.raises(TimeoutError, match='total wall budget'):
        worker.call('fixture')
    assert len(worker.receipt['stages']) == 1
