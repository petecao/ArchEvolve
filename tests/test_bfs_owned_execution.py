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
