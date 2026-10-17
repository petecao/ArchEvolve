"""Finite prospective process-budget regressions; dated 2026-09-26 ET."""
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest
from scripts import bfs_owned_execution as owned


def ledger(tmp_path, monkeypatch=None):
    if sys.platform != 'linux':
        monkeypatch.setattr(owned, 'identity', lambda pid: {'pid': pid, 'start_ticks': 1})
    path = tmp_path/'cleanup.json'
    binding = owned.SharedCleanup.create(path, (datetime.now(owned.ET)+timedelta(seconds=60)).isoformat())
    return owned.SharedCleanup(path, binding, time.monotonic()+60)


def test_shared_reservation_is_settled_and_cannot_reset(tmp_path, monkeypatch):
    budget = ledger(tmp_path, monkeypatch)
    with budget.reservation() as until:
        assert until > time.monotonic()
        second = owned.SharedCleanup(budget.path, budget.binding, budget.deadline)
        during = second.snapshot()
        assert len(during['reservations']) == 1
        assert next(iter(during['reservations'].values()))['seconds'] <= 5
    after = budget.snapshot()
    assert not after['reservations'] and after['spent_seconds'] > 0
    assert after['events'][0]['elapsed_seconds'] > 0
    changed = json.loads(budget.path.read_text()); changed['budget_seconds'] = 31
    budget.path.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match='identity changed'): budget.snapshot()


def test_reservation_never_holds_file_lock_during_action(tmp_path, monkeypatch):
    budget = ledger(tmp_path, monkeypatch)
    with budget.reservation():
        with budget.reservation():
            snapshot = budget.snapshot()
            assert sum(row['seconds'] for row in snapshot['reservations'].values()) <= 30
    assert len(budget.snapshot()['events']) == 2


def test_dead_supervisor_reservation_is_not_reclaimed(tmp_path, monkeypatch):
    budget = ledger(tmp_path, monkeypatch)
    value = json.loads(budget.path.read_text())
    value['reservations'] = {'dead': {'pid': 999999, 'seconds': 30}}
    budget.path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='reserve exhausted'):
        with budget.reservation(): pass


def test_resource_guard_rejects_stale_sample_and_slow_final_guard(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(owned.time, 'monotonic', lambda: clock[0])
    monitor = owned.Monitor(lambda: None, interrupt=False)
    monitor.observe(); clock[0] = 30.01
    with pytest.raises(ValueError, match='stale'): monitor.check()
    with pytest.raises(ValueError, match='gap'): monitor.observe()
    fresh = owned.Monitor(lambda: clock.__setitem__(0, clock[0]+31), interrupt=False)
    with pytest.raises(ValueError, match='guard exceeded'): fresh.observe()


def test_ancestry_stops_at_owned_pane(monkeypatch):
    rows = {4: {'pid': 4, 'parent_pid': 3, 'start_ticks': 40},
            3: {'pid': 3, 'parent_pid': 2, 'start_ticks': 30},
            2: {'pid': 2, 'parent_pid': 1, 'start_ticks': 20}}
    monkeypatch.setattr(owned, 'identity', rows.get)
    assert [r['pid'] for r in owned.ancestry(rows[4], rows[3])] == [4, 3]
    with pytest.raises(ValueError, match='changed'):
        owned.ancestry(rows[4], {'pid': 3, 'start_ticks': 31})


@pytest.mark.skipif(sys.platform != 'linux', reason='actual Linux subreaper/pidfd proof required')
@pytest.mark.parametrize('failure', [False, True])
def test_linux_owned_stage_reaps_detached_child(tmp_path, failure):
    # Separate supervisor prevents subreaper state from leaking into pytest.
    script = '''
from pathlib import Path
from datetime import datetime,timedelta
import json,sys,time,resource
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
from scripts.bfs_owned_execution import *
folder=Path(sys.argv[1]); failure=sys.argv[2]=='True'
p=folder/'budget.json'; binding=SharedCleanup.create(p,(datetime.now(ET)+timedelta(seconds=15)).isoformat())
budget=SharedCleanup(p,binding,time.monotonic()+15); owner=Owned(budget)
code="import subprocess,sys; subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'],start_new_session=True); sys.exit("+str(3 if failure else 0)+")"
receipt={'stages':[]}
try: run_stage(receipt,folder,[sys.executable,'-c',code],timeout=5,deadline=time.monotonic()+10,cwd=Path.cwd(),owned=owner)
except ValueError:
 assert failure
assert receipt['stages'][0]['returncode']==(3 if failure else 0)
assert receipt['stages'][0]['cleanup']['state']=='all_owned_descendants_absent'
assert owner.finish()['state']=='all_owned_descendants_absent'
print(json.dumps(budget.snapshot()))
'''
    result = subprocess.run([sys.executable, '-c', script, str(tmp_path), str(failure)],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['spent_seconds'] < 30


@pytest.mark.skipif(sys.platform != 'linux', reason='actual Linux nested shared-budget proof required')
def test_linux_nested_interruption_uses_one_cleanup_budget(tmp_path):
    script = '''
from pathlib import Path
from datetime import datetime,timedelta
import json,sys,time,resource
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
from scripts.bfs_owned_execution import *
folder=Path(sys.argv[1]); p=folder/'budget.json'
binding=SharedCleanup.create(p,(datetime.now(ET)+timedelta(seconds=18)).isoformat())
budget=SharedCleanup(p,binding,time.monotonic()+18); owner=Owned(budget)
childcode="""
from pathlib import Path
import sys,time
from scripts.bfs_owned_execution import *
from scripts.bfs_process import interruption_signals
p,binding=sys.argv[1:]; budget=SharedCleanup(p,binding,time.monotonic()+15); owner=Owned(budget)
f=Path(p).parent/'child';f.mkdir();r={'stages':[]}
with interruption_signals():
 try: run_stage(r,f,[sys.executable,'-c','import time; time.sleep(60)'],timeout=12,deadline=time.monotonic()+12,cwd=Path.cwd(),owned=owner)
 except InterruptedError: pass
"""
r={'stages':[]}
try: run_stage(r,folder,[sys.executable,'-c',childcode,str(p),binding],timeout=.5,deadline=time.monotonic()+16,cwd=Path.cwd(),owned=owner)
except subprocess.TimeoutExpired: pass
assert r['stages'][0]['cleanup']['state']=='all_owned_descendants_absent'
v=budget.snapshot(); assert not v['reservations'] and v['spent_seconds']<=30
assert len({e['pid'] for e in v['events']})==2
print(json.dumps(v))
'''
    result = subprocess.run([sys.executable, '-c', script, str(tmp_path)], capture_output=True, text=True, timeout=22)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('fault', ['negative_reservation','overspent','nonfinite'])
def test_shared_ledger_rejects_impossible_mutable_accounting(tmp_path, monkeypatch, fault):
    budget=ledger(tmp_path,monkeypatch); value=json.loads(budget.path.read_text())
    if fault=='negative_reservation': value['reservations']={'x':{'seconds':-1}}
    elif fault=='overspent': value['spent_seconds']=31
    else: value['spent_seconds']=float('nan')
    budget.path.write_text(json.dumps(value))
    with pytest.raises(ValueError): budget.snapshot()


@pytest.mark.parametrize('fault', [None,'gap','endgap','rss','arithmetic','duplicate'])
def test_actual_resource_stream_enforces_declared_samples(tmp_path,fault):
    start=datetime(2026,9,26,15,tzinfo=owned.ET)
    row={'pid':100,'parent_pid':99,'start_ticks':123,'rss_pages':1,'rss_bytes':4096}
    sample={'sampled_at':(start+timedelta(seconds=1)).isoformat(),'rss_bytes':4096,
            'processes':[row], 'rss_source':owned.RSS_SOURCE,'page_size_bytes':4096}
    end=start+timedelta(seconds=2)
    if fault=='gap': sample['sampled_at']=(start+timedelta(seconds=31)).isoformat();end=start+timedelta(seconds=32)
    elif fault=='endgap':end=start+timedelta(seconds=32)
    elif fault=='rss': row.update(rss_pages=owned.SAMPLED_RSS_BYTES//4096+1,rss_bytes=owned.SAMPLED_RSS_BYTES+4096);sample['rss_bytes']=row['rss_bytes']
    elif fault=='arithmetic':row['rss_pages']=2
    elif fault=='duplicate':sample['processes'].append(row.copy());sample['rss_bytes']=8192
    path=tmp_path/'samples';path.write_text(json.dumps(sample)+'\n')
    if fault:
        with pytest.raises(ValueError):owned.validate_samples(path,start.isoformat(),end.isoformat())
    else:
        result=owned.validate_samples(path,start.isoformat(),end.isoformat())
        assert result['samples']==1 and result['peak_sampled_rss_bytes']==4096


def local_owned(tmp_path, monkeypatch):
    """Real Popen lifecycle with explicit fixture ownership on non-Linux hosts."""
    import threading
    from types import SimpleNamespace
    budget=ledger(tmp_path,monkeypatch)
    supervisor=object.__new__(owned.Owned)
    supervisor.budget=budget;supervisor.lock=threading.RLock();supervisor.history={}
    supervisor.sampler=SimpleNamespace(known={})
    root={'pid':os.getpid(),'parent_pid':os.getppid(),'start_ticks':1,'rss_bytes':0}
    supervisor.sample=lambda:{'processes':[root]}
    monkeypatch.setattr(owned,'identity',lambda pid:{'pid':pid,'parent_pid':os.getpid(),'start_ticks':2,'rss_bytes':0})
    return supervisor


def test_signal_error_still_reaps_real_child_and_preserves_first_stage_error(tmp_path,monkeypatch):
    supervisor=local_owned(tmp_path,monkeypatch)
    supervisor.signal=lambda *args: (_ for _ in ()).throw(PermissionError('fixture signal denied'))
    receipt={'stages':[]}
    def failure():raise RuntimeError('original monitored failure')
    with pytest.raises(RuntimeError,match='original monitored failure'):
        owned.run_stage(receipt,tmp_path,[sys.executable,'-c','import time;time.sleep(.03);raise SystemExit(9)'],
            timeout=1,deadline=time.monotonic()+2,cwd=tmp_path,owned=supervisor,monitor=failure)
    stage=receipt['stages'][0]
    assert stage['returncode']==9 and stage['cleanup']['direct_reaped'] is True
    assert 'PermissionError' in stage['cleanup']['errors'][0]
    assert stage['reason']=='RuntimeError: original monitored failure'
    assert json.loads((tmp_path/'driver.json').read_text())['stages'][0]['state']=='failed'


def test_post_spawn_setup_cannot_extend_original_stage_deadline(tmp_path,monkeypatch):
    supervisor=local_owned(tmp_path,monkeypatch)
    supervisor.signal=lambda *args:None
    real=owned.save_receipt
    def slow(folder,value):
        real(folder,value)
        if value['stages'][-1].get('identity') and value['stages'][-1]['state']=='running':time.sleep(.06)
    monkeypatch.setattr(owned,'save_receipt',slow)
    receipt={'stages':[]}
    with pytest.raises((ValueError,subprocess.TimeoutExpired)):
        owned.run_stage(receipt,tmp_path,[sys.executable,'-c','pass'],timeout=.02,
            deadline=time.monotonic()+.04,cwd=tmp_path,owned=supervisor)
    assert receipt['stages'][0]['returncode']==0 and receipt['stages'][0]['state']=='failed'


def test_monitor_lock_wait_is_bounded(tmp_path):
    import threading
    held,release=threading.Event(),threading.Event()
    monitor=owned.Monitor(lambda:None,interrupt=False)
    def lock():
        with monitor.lock:held.set();release.wait(2)
    worker=threading.Thread(target=lock);worker.start();assert held.wait(1)
    before=time.monotonic()
    try:
        with pytest.raises(ValueError,match='monitor lock'):monitor.observe()
        assert time.monotonic()-before < 1
    finally:release.set();worker.join(1)


def test_grace_cannot_spend_last_ten_seconds(tmp_path,monkeypatch):
    budget=ledger(tmp_path,monkeypatch)
    value=json.loads(budget.path.read_text());value['spent_seconds']=20
    budget.path.write_text(json.dumps(value))
    with pytest.raises(owned.GraceExhausted):
        with budget.reservation(grace=True):pass
    with budget.reservation() as until:assert until > time.monotonic()
    assert budget.snapshot()['spent_seconds'] < 30


@pytest.mark.skipif(sys.platform != 'linux', reason='actual Linux TERM-resistant nested proof required')
def test_linux_term_resistant_nested_cleanup_keeps_final_kill_reserve(tmp_path):
    script='''
from pathlib import Path
from datetime import datetime,timedelta
import json,sys,time,resource
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
from scripts.bfs_owned_execution import *
folder=Path(sys.argv[1]);p=folder/'budget.json';binding=SharedCleanup.create(p,(datetime.now(ET)+timedelta(seconds=18)).isoformat())
budget=SharedCleanup(p,binding,time.monotonic()+18);owner=Owned(budget)
# Retained earlier cleanup is charged, not reset by the nested supervisor.
with budget._locked() as value:value['spent_seconds']=5
childcode="""
from pathlib import Path
import sys,time
from scripts.bfs_owned_execution import *
from scripts.bfs_process import interruption_signals
p,binding=sys.argv[1:];budget=SharedCleanup(p,binding,time.monotonic()+15);owner=Owned(budget)
f=Path(p).parent/'child';f.mkdir();r={'stages':[]}
code="import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)"
with interruption_signals():
 try:run_stage(r,f,[sys.executable,'-c',code],timeout=12,deadline=time.monotonic()+12,cwd=Path.cwd(),owned=owner)
 except InterruptedError:pass
"""
r={'stages':[]}
try:run_stage(r,folder,[sys.executable,'-c',childcode,str(p),binding],timeout=.5,deadline=time.monotonic()+16,cwd=Path.cwd(),owned=owner)
except subprocess.TimeoutExpired:pass
assert r['stages'][0]['cleanup']['state']=='all_owned_descendants_absent'
assert r['stages'][0]['returncode'] in (-9,0)
v=budget.snapshot();assert v['spent_seconds']+sum(x['seconds'] for x in v['reservations'].values())<=30
assert any(e['purpose']=='grace' for e in v['events'])
assert any(e['purpose']=='cleanup_or_finalization' for e in v['events'])
assert len({e['pid'] for e in v['events']})==2
print(json.dumps(v))
'''
    result=subprocess.run([sys.executable,'-c',script,str(tmp_path)],capture_output=True,text=True,timeout=22)
    assert result.returncode==0,result.stderr


def test_stage_hashing_and_persistence_spend_the_shared_reserve(tmp_path,monkeypatch):
    supervisor=local_owned(tmp_path,monkeypatch);supervisor.signal=lambda *args:None
    original=owned.file_hash
    def slow(path):time.sleep(.02);return original(path)
    monkeypatch.setattr(owned,'file_hash',slow)
    receipt={'stages':[]}
    owned.run_stage(receipt,tmp_path,[sys.executable,'-c','pass'],timeout=1,
                    deadline=time.monotonic()+2,cwd=tmp_path,owned=supervisor)
    account=supervisor.budget.snapshot()
    assert len(account['events'])>=2
    assert account['spent_seconds'] >= .14  # two50ms tails + two actual20ms hashes
    assert receipt['stages'][0]['state']=='complete'


@pytest.mark.parametrize('failure',[False,True])
def test_final_owned_cleanup_rejects_retained_errors_after_absence(failure):
    from types import SimpleNamespace
    calls=[]
    def finish(*args):
        calls.append(args)
        return {'state':'all_owned_descendants_absent','errors':['signal denied'] if failure else []}
    owner=SimpleNamespace(finish=finish)
    if failure:
        with pytest.raises(ValueError,match='retained errors'):owned.verified_finish(owner)
    else:
        assert owned.verified_finish(owner)['state']=='all_owned_descendants_absent'
    assert len(calls)==1


@pytest.mark.skipif(sys.platform != 'linux', reason='actual Linux SQLite unlink proof required')
def test_linux_storage_observation_handles_sqlite_journal_unlink(tmp_path, monkeypatch):
    """A real DELETE-journal commit removes the exact file already enumerated."""
    import sqlite3
    from scripts import bfs_storage as storage
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
    result = subprocess.run(['du','-sk',str(tmp_path)],check=True,capture_output=True,
                            text=True,timeout=5,env={**os.environ,'LC_ALL':'C'})
    assert measured == int(result.stdout.split()[0])*1024


# 2026-09-26: procfs identity-read races, including pidfd signal admission.
def _identity_proc(tmp_path,monkeypatch,pid=991991,start=1001,pages=7):
    from tests.test_bfs_owned_rss import process
    folder=process(tmp_path,pid,1,start,pages=pages)
    original=Path
    monkeypatch.setattr(owned,'Path',lambda value: tmp_path/str(value).removeprefix('/proc/')
                        if str(value).startswith('/proc/') else original(value))
    return pid,folder


def test_identity_esrch_exit_requires_independently_absent_directory(tmp_path,monkeypatch):
    import errno,shutil
    pid,folder=_identity_proc(tmp_path,monkeypatch)
    read=Path.read_text
    def exiting(path,*args,**kwargs):
        if path==folder/'stat':
            shutil.rmtree(folder)
            raise ProcessLookupError(errno.ESRCH,'proc descriptor lost on exit')
        return read(path,*args,**kwargs)
    monkeypatch.setattr(Path,'read_text',exiting)
    assert owned.identity(pid) is None


@pytest.mark.parametrize('reuse',[False,True])
def test_identity_esrch_reopens_actual_identity_and_rss(tmp_path,monkeypatch,reuse):
    import errno
    from tests.test_bfs_owned_rss import process
    pid,folder=_identity_proc(tmp_path,monkeypatch);read=Path.read_text;calls=0
    def replaced(path,*args,**kwargs):
        nonlocal calls
        if path==folder/'stat':
            calls+=1
            if calls==1:
                if reuse:process(tmp_path,pid,999,9001,pages=13)
                raise ProcessLookupError(errno.ESRCH,'old proc descriptor')
        return read(path,*args,**kwargs)
    monkeypatch.setattr(Path,'read_text',replaced)
    row=owned.identity(pid)
    assert calls==2 and row['pid']==pid and row['start_ticks']==(9001 if reuse else 1001)
    assert row['rss_bytes']==(13 if reuse else 7)*os.sysconf('SC_PAGE_SIZE')


@pytest.mark.parametrize('fault',['live-esrch','permission','io','malformed','confirmation-esrch'])
def test_identity_does_not_suppress_ambiguous_or_invalid_telemetry(tmp_path,monkeypatch,fault):
    import errno
    pid,folder=_identity_proc(tmp_path,monkeypatch);read=Path.read_text;stat=Path.stat
    def invalid(path,*args,**kwargs):
        if path==folder/'stat':
            if fault=='permission':raise PermissionError(errno.EACCES,'denied')
            if fault=='io':raise OSError(errno.EIO,'I/O error')
            if fault=='malformed':return 'broken stat'
            raise ProcessLookupError(errno.ESRCH,'still-live proc')
        return read(path,*args,**kwargs)
    def confirm(path,*args,**kwargs):
        if path==folder and fault=='confirmation-esrch':raise ProcessLookupError(errno.ESRCH,'unknown confirmation')
        return stat(path,*args,**kwargs)
    monkeypatch.setattr(Path,'read_text',invalid);monkeypatch.setattr(Path,'stat',confirm)
    with pytest.raises((ValueError,OSError,IndexError)):owned.identity(pid)


@pytest.mark.parametrize('fault',['reused','confirmation-esrch'])
def test_signal_never_admits_reused_or_unknown_identity(tmp_path,monkeypatch,fault):
    import errno
    pid,folder=_identity_proc(tmp_path,monkeypatch,start=9001);sent=[];closed=[]
    monkeypatch.setattr(owned.os,'pidfd_open',lambda value:77,raising=False)
    monkeypatch.setattr(owned.os,'close',closed.append)
    monkeypatch.setattr(owned.signal,'pidfd_send_signal',lambda *args:sent.append(args),raising=False)
    owner=object.__new__(owned.Owned)
    if fault=='confirmation-esrch':
        def unknown(value):raise ProcessLookupError(errno.ESRCH,'independent confirmation unavailable')
        monkeypatch.setattr(owned,'identity',unknown)
        with pytest.raises(ProcessLookupError,match='confirmation'):owner.signal({'pid':pid,'start_ticks':1001},owned.signal.SIGTERM)
    else:owner.signal({'pid':pid,'start_ticks':1001},owned.signal.SIGTERM)
    assert not sent and closed==[77]


# Resume decisions R1-R3 (2026-09-27 ET): prospective regressions only.

def test_dead_owner_reservation_is_charged_in_full_as_spent():
    value = {'budget_seconds': 30, 'spent_seconds': 20.5,
             'reservations': {'a': {'pid': 11, 'seconds': 0.25, 'start_ticks': 7},
                              'b': {'pid': 12, 'seconds': 2}}}
    result = owned.charge_dead_owner_reservations(value, observe=lambda pid: None)
    assert result['dead_owner_reservations'] == 2
    assert result['conservative_spent_seconds'] == pytest.approx(22.75)
    # A reused PID is dead only when the recorded start disproves identity.
    reused = lambda pid: {'pid': pid, 'start_ticks': 8}
    assert owned.charge_dead_owner_reservations(
        {**value, 'reservations': {'a': value['reservations']['a']}}, observe=reused)['dead_owner_seconds'] == .25
    with pytest.raises(ValueError, match='live or its identity'):
        owned.charge_dead_owner_reservations(value, observe=reused)  # 'b' lacks start_ticks
    with pytest.raises(ValueError, match='live or its identity'):
        owned.charge_dead_owner_reservations(value, observe=lambda pid: {'pid': pid, 'start_ticks': 7})
    with pytest.raises(ValueError, match='exceed the fixed cleanup reserve'):
        owned.charge_dead_owner_reservations({**value, 'spent_seconds': 29}, observe=lambda pid: None)
    for row in (None, 12, ['pid', 12]):  # 2026-09-28: non-mapping rows are malformed, not AttributeError
        with pytest.raises(ValueError, match='dead-owner reservation is malformed'):
            owned.charge_dead_owner_reservations({**value, 'reservations': {'c': row}}, observe=lambda pid: None)


def test_new_reservations_record_owner_start(tmp_path, monkeypatch):
    budget = ledger(tmp_path, monkeypatch)
    with budget.reservation():
        row = next(iter(budget.snapshot()['reservations'].values()))
    assert type(row['start_ticks']) is int and row['pid'] == os.getpid()


def test_terminal_reader_keeps_strict_default_and_opt_in_dead_owner_charge():
    import inspect
    from scripts import bfs_simulator_batch_terminal as terminal
    assert inspect.signature(terminal.validate_cleanup_ledger).parameters['charge_dead_owners'].default is False


def _sample_line(at, pid=1):
    row = {'pid': pid, 'parent_pid': 0, 'start_ticks': 1, 'state': 'S', 'rss_pages': 1, 'rss_bytes': 4096}
    return json.dumps({'sampled_at': at.isoformat(), 'processes': [row], 'rss_bytes': 4096,
                       'rss_source': owned.RSS_SOURCE, 'page_size_bytes': 4096}) + '\n'


def test_sample_bound_is_derived_from_coverage_interval(tmp_path):
    start = datetime(2026, 9, 27, 12, tzinfo=owned.ET)
    assert owned.sample_count_bound(start, start + timedelta(seconds=14400)) == 20000
    assert owned.sample_count_bound(start, start + timedelta(seconds=172800)) == 2 * 34560 + 64
    # A long run at the nominal period exceeds the old fixed cap and passes.
    count = 20100
    path = tmp_path / 'long.jsonl'
    path.write_text(''.join(_sample_line(start + timedelta(seconds=5 * i)) for i in range(count)))
    end = start + timedelta(seconds=5 * (count - 1) + 1)
    assert owned.validate_samples(path, start.isoformat(), end.isoformat())['samples'] == count
    # Many more lines than the interval supports are still rejected.
    dense = tmp_path / 'dense.jsonl'
    dense.write_text(''.join(_sample_line(start + timedelta(milliseconds=i)) for i in range(20001)))
    with pytest.raises(ValueError, match='read bound exceeded'):
        owned.validate_samples(dense, start.isoformat(), (start + timedelta(seconds=21)).isoformat())


def test_gem5_slot_is_exclusive_and_bounded(tmp_path):
    from scripts.bfs_simulator_series import acquire_gem5_slot
    fd, index, waited = acquire_gem5_slot(tmp_path, 1, time.monotonic() + 5, lambda: None)
    assert index == 0 and waited < 1
    checks = []
    with pytest.raises(TimeoutError, match='slot wait'):
        acquire_gem5_slot(tmp_path, 1, time.monotonic() + .3, lambda: checks.append(1), pause=.05)
    assert checks
    os.close(fd)
    again, _, _ = acquire_gem5_slot(tmp_path, 1, time.monotonic() + 5, lambda: None)
    os.close(again)


def test_dx100_releases_inherited_slot_descriptor(tmp_path, monkeypatch):
    import fcntl
    from swdb import dx100
    from scripts.bfs_simulator_series import acquire_gem5_slot
    fd, _, _ = acquire_gem5_slot(tmp_path, 1, time.monotonic() + 5, lambda: None)
    monkeypatch.setenv('SWDB_GEM5_SLOT_FD', str(fd))
    dx100._release_gem5_slot()
    assert 'SWDB_GEM5_SLOT_FD' not in os.environ
    with pytest.raises(OSError):
        os.fstat(fd)
    probe = os.open(tmp_path / 'gem5-slot-0.lock', os.O_RDWR)
    fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB); os.close(probe)
    dx100._release_gem5_slot()  # absent variable is a no-op


@pytest.mark.skipif(sys.platform != 'linux', reason='actual Linux subreaper/pidfd proof required')
def test_linux_gem5_slot_is_released_by_child_not_parent(tmp_path):
    script = '''
from pathlib import Path
from datetime import datetime,timedelta
import json,os,sys,threading,time
from scripts.bfs_owned_execution import *
from scripts.bfs_simulator_series import acquire_gem5_slot
folder=Path(sys.argv[1]); slots=folder/'slots'; slots.mkdir()
p=folder/'budget.json'; binding=SharedCleanup.create(p,(datetime.now(ET)+timedelta(seconds=20)).isoformat())
budget=SharedCleanup(p,binding,time.monotonic()+20); owner=Owned(budget)
fd,_,_=acquire_gem5_slot(slots,1,time.monotonic()+5,lambda:None); holder={'fd':fd}
def spawned():
    os.close(holder['fd']); holder['fd']=None
code=("import os,time; time.sleep(1); os.close(int(os.environ['SWDB_GEM5_SLOT_FD'])); "
      "open(os.environ['MARK'],'w').close(); time.sleep(2)")
env={**os.environ,'SWDB_GEM5_SLOT_FD':str(fd),'MARK':str(folder/'released')}
observed={}
def probe():
    time.sleep(.5)
    try: acquire_gem5_slot(slots,1,time.monotonic()+.2,lambda:None,pause=.05); observed['early']=True
    except TimeoutError: observed['early']=False
    while not (folder/'released').exists(): time.sleep(.02)
    f,_,_=acquire_gem5_slot(slots,1,time.monotonic()+1,lambda:None,pause=.05); os.close(f); observed['late']=time.monotonic()
t=threading.Thread(target=probe); t.start()
receipt={'stages':[]}
run_stage(receipt,folder,[sys.executable,'-c',code],timeout=10,deadline=time.monotonic()+15,cwd=Path.cwd(),
          owned=owner,env=env,pass_fds=(fd,),spawned=spawned)
finished=time.monotonic(); t.join(5)
assert holder['fd'] is None and observed['early'] is False and observed['late'] < finished
assert receipt['stages'][0]['cleanup']['state']=='all_owned_descendants_absent'
print(json.dumps(budget.snapshot()))
'''
    result = subprocess.run([sys.executable, '-c', script, str(tmp_path)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['spent_seconds'] < 30
