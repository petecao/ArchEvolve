"""One host-local, read-only native receipt review. Created: 2026-09-26 ET.
No measurements, publication, retry, or changes to either pinned checkout.
"""
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time
from datetime import datetime, timedelta, timezone

SUPERVISOR = '3f38a2bf9cde4fb23edebd787a9d4d8ab9549e07'
SUP = Path('/data1/yanruj/EvolveSWDB_bfs_supervision_20260926_a1')
COLLECTOR = Path('/data1/yanruj/EvolveSWDB_native_one_thread_20260926_a1')
RAW = Path('/data/yanruj/EvolveSWDB_runs/bfs-native-one-thread-readback-20260926-a1')


class Accounting:
    """Time only: delegates the original reader with identical arguments/results."""
    def __init__(self, outer_start, outer_end, mono=time.monotonic, wall=None):
        self.mono = mono
        current = (wall or (lambda: datetime.now(timezone.utc)))()
        if outer_end-outer_start != timedelta(seconds=990) or not outer_start <= current < outer_end:
            raise ValueError('original aware990s outer clock is invalid')
        self.before = mono()-(current-outer_start).total_seconds()
        self.until = self.before+990
        self.reader_seconds = 0.0
        self.calls = 0
        self.alarm = False

    def check(self):
        elapsed = self.mono()-self.before
        if elapsed > 990 or elapsed-self.reader_seconds > 60:
            raise TimeoutError('original whole990 or cumulative ancillary60 exhausted')

    def arm(self):
        if self.alarm:
            remaining = min(self.until-self.mono(), 60-(self.mono()-self.before-self.reader_seconds))
            signal.setitimer(signal.ITIMER_REAL, max(.000001, remaining))

    def wrap(self, original):
        def timed(*args, **kwargs):
            self.check()
            if self.calls:
                raise ValueError('a second pinned reader invocation is forbidden')
            self.calls += 1
            if self.alarm: signal.setitimer(signal.ITIMER_REAL, 0)
            started = self.mono()
            try:
                return original(*args, **kwargs)
            finally:
                self.reader_seconds += self.mono()-started
                self.arm()
        return timed


def main():
    if sys.flags.optimize or Path.cwd() != SUP:
        raise ValueError('unoptimized Python in exact supervision checkout required')
    input_path = RAW/'selection.json'
    with input_path.open('rb') as stream: raw = stream.read(128*1024+1)
    if len(raw) > 128*1024: raise ValueError('oversized input')
    values = json.loads(raw)
    outer_start, outer_end = (datetime.fromisoformat(values[key]) for key in ('outer_started','outer_deadline'))
    if outer_start.tzinfo is None or outer_end.tzinfo is None: raise ValueError('aware outer clock required')
    budget = Accounting(outer_start, outer_end)
    budget.check()
    def expired(_sig, _frame): raise TimeoutError('cumulative ancillary60 expired')
    signal.signal(signal.SIGALRM, expired); budget.alarm = True; budget.arm()
    sys.path.insert(0, str(SUP))
    from scripts import bfs_one_thread_calibration as c, bfs_dx100_coverage_a2 as a2
    from scripts.bfs_native_campaign import campaign_runtime
    from scripts.bfs_process import interruption_signals
    from swdb import artifacts, yamlio
    from swdb.store import Store
    out = RAW/'result'; out.mkdir(exist_ok=False)
    pending, published = out/'readback.pending.json', out/'readback.json'
    result = {'state':'pending','role':'independent_native_receipt_readback','gain_claim':False,
              'protocol_freeze':False,'measurements':False,'outer_started':values['outer_started'],
              'outer_deadline':values['outer_deadline'],'input_sha256':hashlib.sha256(raw).hexdigest(),
              'recipe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'bounds':{'whole_seconds':990,'reader_work_seconds':900,'reader_cleanup_seconds':30,'ancillary_seconds':60}}
    pending.write_text(json.dumps(result,sort_keys=True)+'\n')
    original = c.pinned_readback
    try:
        with interruption_signals():
            runtime = campaign_runtime(SUPERVISOR)
            spec = values['spec']; selected = c.selection(spec)
            if selected['collector_checkout'] != str(COLLECTOR): raise ValueError('collector path differs')
            store = Store(COLLECTOR/'records')
            if store.problems: raise ValueError('record catalog contains parse failures')
            receipt = c.read(selected['driver_receipt']); audit = c.read(selected['terminal_receipt'])
            lane = c.read(audit['lane'])['socket_lane']
            if lane['lease_generation'] != 402 or receipt['outer_start'] != '2026-09-26T15:07:35.041327-04:00' \
                    or receipt['outer_end'] != '2026-09-26T20:11:35.041327-04:00':
                raise ValueError('original generation402/clock differs')
            cleanup = a2.native_terminal(selected['terminal_receipt'],yamlio.load(a2.PLAN),store,datetime.now(timezone.utc))
            budget.check()
            if receipt['state'] != 'complete': raise ValueError('terminal study is not qualified for full readback')
            c.pinned_readback = budget.wrap(original)
            identities, gates = {}, []
            control, evaluations = c.qualify(spec, [], store, identities, gates)
            policy, runtime_evidence = c.calibrated_runtime(control)
            budget.check()
            if gates or control['state'] != 'qualified' or budget.calls != 1 or evaluations:
                raise ValueError('readback gates or fixed invocation scope differ')
            if campaign_runtime(SUPERVISOR) != runtime: raise ValueError('supervisor changed during readback')
            c.terminal_closure(selected['terminal_receipt'],selected['driver_receipt'],receipt)
            budget.check()
            result.update(state='complete',control=control,record_identities=identities,terminal_cleanup=cleanup,
                          native_runtime=policy,runtime_evidence=runtime_evidence,supervisor_runtime=runtime,
                          reader_invocations=budget.calls,reader_elapsed_seconds=budget.reader_seconds,
                          ancillary_elapsed_seconds=budget.mono()-budget.before-budget.reader_seconds,
                          finished=datetime.now(timezone.utc).isoformat())
            pending.write_text(json.dumps(result,sort_keys=True,allow_nan=False)+'\n')
            budget.check()
            os.link(pending,published)
            digest = artifacts.file_hash(published)
            budget.check()
            print(json.dumps({'state':'complete','path':str(published),'sha256':digest,'gain_claim':False,'protocol_freeze':False}),flush=True)
            budget.check()
    except BaseException:
        if published.exists(): published.unlink()
        raise
    finally:
        c.pinned_readback = original
        budget.alarm = False; signal.setitimer(signal.ITIMER_REAL,0)


if __name__ == '__main__': main()
