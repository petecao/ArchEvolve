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


def test_unknown_missing_metadata_is_not_zero(tmp_path, monkeypatch):
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


def test_actual_sqlite_journal_unlinked_between_enumeration_and_stat(tmp_path, monkeypatch):
    """A real DELETE-journal commit removes the exact file already enumerated."""
    import sqlite3
    import threading
    ready, commit, finished = (threading.Event() for _ in range(3))
    errors = []
    db = tmp_path/'.swdb.sqlite.fixture.tmp'
    with sqlite3.connect(db) as connection:
        connection.execute('create table retained(value integer)')
        connection.execute('insert into retained values(1)')
    def transaction():
        try:
            with sqlite3.connect(db) as connection:
                connection.execute('pragma journal_mode=delete')
                connection.execute('update retained set value=2')
                ready.set()
                if not commit.wait(2):raise TimeoutError('fixture never reached journal observation')
                connection.commit()
        except BaseException as error:errors.append(error)
        finally:finished.set()
    writer=threading.Thread(target=transaction);writer.start()
    stat=storage.os.stat;observed=[]
    def lookup(name, *args, **kwargs):
        if str(name).endswith('-journal') and not observed:
            observed.append(str(name));commit.set()
            assert finished.wait(2), 'real SQLite commit did not finish'
        return stat(name,*args,**kwargs)
    try:
        assert ready.wait(2) and Path(str(db)+'-journal').exists()
        monkeypatch.setattr(storage.os,'stat',lookup)
        measured=storage.allocated_bytes([tmp_path])
    finally:
        commit.set();writer.join(2)
    assert not writer.is_alive() and not errors and observed
    assert not Path(str(db)+'-journal').exists()
    assert measured==du_bytes(tmp_path)


@pytest.mark.parametrize('operation',['unlink','rename'])
def test_nested_directory_disappearing_before_open_is_confirmed_without_escape(tmp_path,monkeypatch,operation):
    root=tmp_path/'root';root.mkdir();nested=root/'nested';nested.mkdir()
    (nested/'payload').write_bytes(b'x'*32768)
    moved=tmp_path/'outside';original=storage.os.open;changed=[]
    def move(name,flags,*args,**kwargs):
        if name=='nested' and not changed:
            changed.append(True)
            if operation=='rename':nested.rename(moved)
            else:(nested/'payload').unlink();nested.rmdir()
        return original(name,flags,*args,**kwargs)
    monkeypatch.setattr(storage.os,'open',move)
    assert storage.allocated_bytes([root])==du_bytes(root)
    assert changed


def test_entry_reappearing_after_enoent_is_measured_without_following_symlink(tmp_path,monkeypatch):
    import errno
    root=tmp_path/'root';root.mkdir();entry=root/'entry';entry.write_bytes(b'old')
    outside=tmp_path/'outside';outside.mkdir();(outside/'large').write_bytes(b'x'*1024**2)
    stat=storage.os.stat;changed=[]
    def replace(name,*args,**kwargs):
        if name=='entry' and not changed:
            changed.append(True);entry.unlink();entry.symlink_to(outside,target_is_directory=True)
            raise FileNotFoundError(errno.ENOENT,'entry was replaced',name)
        return stat(name,*args,**kwargs)
    monkeypatch.setattr(storage.os,'stat',replace)
    assert storage.allocated_bytes([root])==du_bytes(root)
    assert changed


def test_root_disappearing_after_preflight_is_still_an_error(tmp_path,monkeypatch):
    root=tmp_path/'root';root.mkdir();original=storage.os.open
    def remove(name,flags,*args,**kwargs):
        if name==root:root.rmdir()
        return original(name,flags,*args,**kwargs)
    monkeypatch.setattr(storage.os,'open',remove)
    with pytest.raises(FileNotFoundError):storage.allocated_bytes([root])


def test_enoent_confirmation_cannot_hide_permission_failure(tmp_path,monkeypatch):
    import errno
    root=tmp_path/'root';root.mkdir();(root/'entry').touch();original=storage.os.stat;calls=[]
    def fail(name,*args,**kwargs):
        if name=='entry':
            calls.append(1)
            if len(calls)==1:raise FileNotFoundError(errno.ENOENT,'observed absence',name)
            raise PermissionError(errno.EACCES,'cannot confirm absence',name)
        return original(name,*args,**kwargs)
    monkeypatch.setattr(storage.os,'stat',fail)
    with pytest.raises(PermissionError):storage.allocated_bytes([root])


def test_concurrent_real_sqlite_commit_walks_finish_with_quiescent_du_parity(tmp_path):
    import sqlite3
    stop=threading.Event();ready=threading.Event();errors=[];commits=[]
    db=tmp_path/'swdb.sqlite'
    with sqlite3.connect(db) as connection:
        connection.execute('create table record(value integer)')
        connection.execute('insert into record values(0)')
    def write():
        try:
            with sqlite3.connect(db) as connection:
                ready.set()
                while not stop.is_set():
                    connection.execute('update record set value=value+1');connection.commit();commits.append(1)
        except BaseException as error:errors.append(error)
    writer=threading.Thread(target=write);writer.start()
    try:
        assert ready.wait(2)
        for _ in range(30):assert storage.allocated_bytes([tmp_path],deadline=time.monotonic()+2)>=0
    finally:stop.set();writer.join(2)
    assert not writer.is_alive() and commits and not errors
    assert storage.allocated_bytes([tmp_path])==du_bytes(tmp_path)


def test_root_symlink_substitution_between_preflight_and_visit_is_rejected(tmp_path,monkeypatch):
    root=tmp_path/'root';root.mkdir();outside=tmp_path/'outside';outside.mkdir()
    original=storage.os.stat;replaced=[]
    def replace(name,*args,**kwargs):
        if name==root and 'dir_fd' in kwargs and kwargs.get('follow_symlinks') is False and not replaced:
            root.rmdir();root.symlink_to(outside,target_is_directory=True);replaced.append(True)
        return original(name,*args,**kwargs)
    monkeypatch.setattr(storage.os,'stat',replace)
    with pytest.raises(ValueError,match='root became a symlink'):
        storage.allocated_bytes([root])


def test_root_removed_during_child_lookup_does_not_become_zero_observation(tmp_path,monkeypatch):
    root=tmp_path/'root';root.mkdir();child=root/'entry';child.write_bytes(b'x')
    stat=storage.os.stat;removed=[]
    def remove(name,*args,**kwargs):
        if name=='entry' and not removed:
            child.unlink();root.rmdir();removed.append(True)
        return stat(name,*args,**kwargs)
    monkeypatch.setattr(storage.os,'stat',remove)
    with pytest.raises(FileNotFoundError):storage.allocated_bytes([root])
    assert removed
