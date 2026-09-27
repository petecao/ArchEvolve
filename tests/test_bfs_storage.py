"""Process-free allocated storage and owned-monitor boundaries. 2026-09-26 ET."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from scripts import bfs_scalar_v2_builds as scalar
from scripts import bfs_owned_execution as owned
from scripts import bfs_storage as storage
from test_bfs_scalar_v2_builds import worker, FixtureOwned

ACTUAL_OWNED = owned.Owned


def du_bytes(path):
    result = subprocess.run(['du', '-sk', str(path)], check=True, capture_output=True,
                            text=True, timeout=5, env={**os.environ, 'LC_ALL': 'C'})
    return int(result.stdout.split()[0]) * 1024


def test_allocation_matches_separate_du_roots_with_links_and_sparse_files(tmp_path):
    root = tmp_path / 'charged'; root.mkdir()
    nested = root / 'nested'; nested.mkdir()
    data = root / 'data'; data.write_bytes(b'x' * 17000)
    os.link(data, nested / 'hardlink')
    sparse = nested / 'sparse'
    with sparse.open('wb') as stream:
        stream.seek(8 * 1024**2); stream.write(b'last')
    external = tmp_path / 'external'; external.mkdir()
    (external / 'large').write_bytes(b'x' * 1024**2)
    (root / 'external-link').symlink_to(external, target_is_directory=True)
    (root / 'broken-link').symlink_to(tmp_path / 'absent')
    (root / 'nested-link').symlink_to(nested, target_is_directory=True)
    # Separate roots intentionally charge a hard-linked file again, like prior du calls.
    roots = [root, data, nested / 'hardlink']
    assert storage.allocated_bytes(roots) == sum(du_bytes(path) for path in roots)


def test_per_root_rounding_does_not_change_historical_kib_charges(tmp_path, monkeypatch):
    roots = [tmp_path / 'one', tmp_path / 'two']
    for root in roots: root.touch()
    original = storage.os.stat
    def half_kib(path, *args, **kwargs):
        result = original(path, *args, **kwargs)
        if Path(path) in roots and kwargs.get('follow_symlinks') is False:
            return SimpleNamespace(st_dev=result.st_dev, st_ino=result.st_ino,
                                   st_mode=result.st_mode, st_blocks=1)
        return result
    monkeypatch.setattr(storage.os, 'stat', half_kib)
    assert storage.allocated_bytes(roots) == 2048
    assert storage.allocated_bytes([roots[0], roots[0]]) == 2048


@pytest.mark.parametrize('kind', ['missing', 'relative', 'symlink', 'noncanonical'])
def test_unsafe_or_missing_roots_fail_closed(tmp_path, kind):
    root = tmp_path / 'root'; root.mkdir()
    if kind == 'missing': value = tmp_path / 'missing'
    elif kind == 'relative': value = Path('relative')
    elif kind == 'symlink':
        value = tmp_path / 'link'; value.symlink_to(root, target_is_directory=True)
    else: value = root / '..' / 'root'
    with pytest.raises((ValueError, FileNotFoundError)):
        storage.allocated_bytes([value])


def test_walk_never_spawns_and_preserves_caller_failure(tmp_path, monkeypatch):
    (tmp_path / 'file').write_bytes(b'x')
    def forbidden(*args, **kwargs): raise AssertionError('storage must not spawn a child')
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    assert storage.allocated_bytes([tmp_path]) > 0
    sentinel = RuntimeError('original enclosing clock expired')
    def exhausted(): raise sentinel
    with pytest.raises(RuntimeError) as error:
        storage.allocated_bytes([tmp_path], check=exhausted)
    assert error.value is sentinel


def test_original_deadline_and_maximum_walk_are_checked_during_traversal(tmp_path, monkeypatch):
    (tmp_path / 'file').write_bytes(b'x')
    with pytest.raises(TimeoutError): storage.allocated_bytes([tmp_path], deadline=time.monotonic()-1)
    current = [100.]
    monkeypatch.setattr(storage.time, 'monotonic', lambda: current[0])
    def advance(): current[0] += 11
    with pytest.raises(TimeoutError, match='existing observation bound'):
        storage.allocated_bytes([tmp_path], check=advance)


def test_directory_replaced_with_symlink_cannot_escape_root(tmp_path, monkeypatch):
    root = tmp_path / 'root'; root.mkdir()
    nested = root / 'nested'; nested.mkdir()
    external = tmp_path / 'external'; external.mkdir()
    (external / 'unaccounted').write_bytes(b'x' * 1024**2)
    original = storage.os.open
    replaced = []
    def replace(name, flags, *args, **kwargs):
        if name == 'nested' and not replaced:
            nested.rmdir(); nested.symlink_to(external, target_is_directory=True); replaced.append(True)
        return original(name, flags, *args, **kwargs)
    monkeypatch.setattr(storage.os, 'open', replace)
    with pytest.raises(OSError): storage.allocated_bytes([root])
    assert replaced


def test_unreadable_or_disappearing_metadata_is_not_zero(tmp_path, monkeypatch):
    root = tmp_path / 'root'; root.mkdir(); (root / 'file').write_bytes(b'x')
    original = storage.os.stat
    def disappear(name, *args, **kwargs):
        if name == 'file': raise FileNotFoundError('entry vanished during observation')
        return original(name, *args, **kwargs)
    monkeypatch.setattr(storage.os, 'stat', disappear)
    with pytest.raises(FileNotFoundError, match='entry vanished'):
        storage.allocated_bytes([root])


def test_live_monitor_accounting_survives_owned_descendant_cleanup(worker, monkeypatch):
    """Real accounting children/OS signals; portable identity fixture, not Linux proof."""
    children={}; started=threading.Event(); sampled=threading.Event(); calls=[]
    original_popen=subprocess.Popen
    class PortableOwner(ACTUAL_OWNED):
        def __init__(self,budget):self.budget=budget;self.history={};self.lock=threading.RLock()
        def sample(self):
            value=FixtureOwned.sample(self)
            for child in list(children.values()):
                if child.poll() is None:
                    row={'pid':child.pid,'parent_pid':os.getpid(),'start_ticks':1,'rss_pages':1,'rss_bytes':4096,'state':'R'}
                    self.history[row['pid'],row['start_ticks']]=row
                    value['processes'].append(row);value['rss_bytes']+=4096
            return value
        def signal(self,row,signum):
            child=children[row['pid']]
            if child.poll() is None:
                child.send_signal(signum);child.wait(timeout=1)
    def popen(command,*args,**kwargs):
        if command[0]=='du':
            # Slow only this real accounting child to make the lifetime overlap deterministic.
            original=list(command)
            command=[sys.executable,'-c','import os,sys,time;time.sleep(.3);os.execvp(sys.argv[1],sys.argv[1:])',*original]
            child=original_popen(command,*args,**kwargs);children[child.pid]=child;started.set();return child
        return original_popen(command,*args,**kwargs)
    worker.guard.stop(time.monotonic()+1)
    worker.owner=PortableOwner(worker.budget)
    monkeypatch.setattr(owned,'SAMPLE_INTERVAL_SECONDS',.01)
    def observe():
        value=worker.observe();calls.append(1)
        if len(calls)>1:sampled.set()
        return value
    worker.guard=owned.Monitor(observe,interrupt=False);worker.guard.start()
    monkeypatch.setattr(subprocess,'Popen',popen)
    until=time.monotonic()+2
    while not (started.is_set() or sampled.is_set()) and time.monotonic()<until:time.sleep(.001)
    assert started.is_set() or sampled.is_set()
    worker.receipt['state']='complete'
    try:
        worker.finalize(None)
        assert worker.receipt['state']=='complete' and worker.receipt['final_accounting']['artifact_bytes']>0
        assert not children, 'resource accounting must not spawn cleanup-owned subprocesses'
    finally:
        worker.guard.stop_event.set();worker.guard.thread.join(1)
        for child in children.values():
            if child.poll() is None:child.kill()
            child.wait(timeout=1)
