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
from zoneinfo import ZoneInfo

SUPERVISOR = '5e8b750b14679d5962d1e4b40cd5fa0f1b6981b0'
SUP = Path('/data1/yanruj/EvolveSWDB_bfs_reader_20260926_a2')
COLLECTOR = Path('/data1/yanruj/EvolveSWDB_native_one_thread_20260926_a1')
RAW = Path('/data/yanruj/EvolveSWDB_runs/bfs-native-one-thread-readback-20260926-a2')


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


class Observations:
    """Read-only process sampling and durable events; no cleanup authority."""
    def __init__(self, folder, pane):
        from scripts.bfs_owned_execution import Monitor, identity, ancestry
        from scripts.bfs_owned_rss import DescendantRSS
        self.folder, self.pane = folder, pane
        self.driver = identity(os.getpid())
        self.ancestry = ancestry(self.driver, pane)
        self.sampler = DescendantRSS(os.getpid())
        self.monitor = Monitor(self.sample)
        self.history = {}; self.events = []; self.peak = 0
        self.samples_path, self.events_path = folder/'resource-samples.jsonl', folder/'reader-events.jsonl'
        self.samples_path.touch(exist_ok=False); self.events_path.touch(exist_ok=False)
        self.path = folder/'process-observations.json'
        self.sampling_finished = False
        self.persist()

    @staticmethod
    def append(path, value):
        with path.open('a') as stream:
            stream.write(json.dumps(value,sort_keys=True,allow_nan=False)+'\n')
            stream.flush(); os.fsync(stream.fileno())

    def remember(self):
        for pid,start in self.sampler.known.items():
            self.history.setdefault((pid,start),{'pid':pid,'start_ticks':start})

    def persist(self):
        self.remember()
        value={'format':'swdb.bfs.native-readback-observations.v1',
            'driver_identity':self.driver,'pane_identity':self.pane,'ancestry':self.ancestry,
            'owned_processes':list(self.history.values()),'sampling_finished':self.sampling_finished,
            'cleanup_verified':False,'peak_sampled_rss_bytes':self.peak,
            'bounds':{'sampled_rss_bytes':16*1024**3,'samples_bytes':16*1024**2,
                      'events_bytes':64*1024,'nominal_interval_seconds':5,'maximum_gap_seconds':30},
            'maximum_gap_seconds':self.monitor.maximum_gap_seconds,
            'maximum_guard_seconds':self.monitor.maximum_guard_seconds,
            'resource_samples_path':str(self.samples_path),'reader_events_path':str(self.events_path),
            'observed_at':datetime.now(timezone.utc).isoformat()}
        temporary=self.path.with_suffix('.pending')
        with temporary.open('w') as stream:
            json.dump(value,stream,sort_keys=True,allow_nan=False); stream.write('\n')
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary,self.path)
        directory=os.open(self.folder,os.O_RDONLY)
        try: os.fsync(directory)
        finally: os.close(directory)

    def sample(self):
        try:
            sample=self.sampler.sample()
            for row in sample['processes']: self.history[row['pid'],row['start_ticks']]=dict(row)
            self.peak=max(self.peak,sample['rss_bytes'])
            self.append(self.samples_path,sample)
            if sample['rss_bytes']>16*1024**3: raise ValueError('readback sampled RSS exceeds16GiB')
            if self.samples_path.stat().st_size>16*1024**2: raise ValueError('readback samples exceed16MiB')
        except BaseException as error:
            try: self.persist()
            except BaseException as secondary: error.add_note('Observation persistence also failed: '+str(secondary))
            raise
        else:
            self.persist()

    def reader(self,event):
        if not self.monitor.lock.acquire(timeout=.5): raise TimeoutError('reader observation lock unavailable')
        try:
            row=event.get('identity')
            if row is not None:
                self.sampler.known[row['pid']]=row['start_ticks']
                self.history[row['pid'],row['start_ticks']]=dict(row)
            self.append(self.events_path,event)
            if self.events_path.stat().st_size>64*1024: raise ValueError('reader events exceed64KiB')
            self.events.append(event); self.persist()
        finally:
            self.monitor.lock.release()
        self.monitor.check()

    def finish(self,deadline):
        self.monitor.interrupt=False
        error=None
        try: self.monitor.observe()
        except BaseException as exc: error=exc
        try: self.monitor.stop(deadline)
        except BaseException as exc: error=error or exc
        if time.monotonic()>deadline: error=error or TimeoutError('observation finalization exceeded original budget')
        self.sampling_finished=error is None
        try: self.persist()
        except BaseException as secondary:
            if error is None: error=secondary
            else: error.add_note('Observation persistence also failed: '+str(secondary))
        if time.monotonic()>deadline: error=error or TimeoutError('observation persistence exceeded original budget')
        if error is not None: raise error



def linux_proof(reference, before):
    """Bind the separately audited one-case proof; never create/upgrade proof."""
    from scripts import bfs_one_thread_calibration as c
    from scripts.bfs_linux_fixture import junit_cases
    from swdb.artifacts import file_hash
    proof=c.read(reference,128*1024)
    selector='tests/test_bfs_one_thread_freeze.py::test_linux_fast_reader_retains_actual_unreaped_identity'
    if (proof.get('format')!='swdb.bfs.native-reader-linux-proof.v1' or proof.get('state')!='passed'
            or proof.get('host')!='mbit10' or proof.get('platform')!='linux'
            or proof.get('evidence_kind')!='contract_fixture' or proof.get('code_commit')!=SUPERVISOR
            or proof.get('selector')!=selector or type(proof.get('returncode')) is not int or proof['returncode']!=0):
        raise ValueError('manual Linux reader proof identity/outcome differs')
    start,end,finished,audited=(datetime.fromisoformat(proof[key]) for key in
                              ('outer_started','outer_deadline','finished','audited_at'))
    if (any(x.utcoffset() is None for x in (start,end,finished,audited))
            or end-start!=timedelta(seconds=90) or not start<=finished<=end
            or not finished<=audited<=before):
        raise ValueError('manual Linux reader proof original clock differs')
    python=proof['python']
    if Path(python['path']).resolve()!=Path(sys.executable).resolve() or file_hash(Path(python['path']))!=python['sha256']:
        raise ValueError('manual Linux proof Python differs')
    for key in ('junit','stdout','stderr','events'):
        ref=proof[key]; path=Path(ref['path'])
        if not path.is_file() or path.is_symlink() or path.stat().st_size>512*1024**2 or file_hash(path)!=ref['sha256']:
            raise ValueError('manual Linux proof artifact changed: '+key)
    junit_cases(Path(proof['junit']['path']),{selector.split('::')[-1]})
    event_bytes=Path(proof['events']['path']).read_bytes()
    if len(event_bytes)>64*1024: raise ValueError('manual reader events exceed64KiB')
    events=[json.loads(line) for line in event_bytes.splitlines()]
    if len(events)!=2 or [event.get('event') for event in events]!=['spawn','finished']:
        raise ValueError('manual reader proof event sequence differs')
    first,last=events; identity=first['identity']; pytest=proof['pytest_identity']
    if (any(type(identity.get(k)) is not int or identity[k]<=0 for k in ('pid','start_ticks'))
            or identity['parent_pid']!=pytest['pid'] or last['identity']!=identity
            or last.get('pid')!=identity['pid'] or last.get('direct_reaped') is not True
            or type(last.get('returncode')) is not int or last['returncode']!=0):
        raise ValueError('manual reader proof process events differ')
    audit=c.read(proof['terminal_audit'],1024*1024)
    # This is the independently sealed manual audit, not a new cleanup action.
    if (audit.get('state') not in ('terminal_and_reaped','terminal_no_live_owned_processes')
            or audit.get('lease_released') is not True
            or not (audit.get('owned_processes_absent') is True or audit.get('owned_processes_nonrunning') is True)):
        raise ValueError('manual Linux proof terminal closure differs')
    union={(row['pid'],row['start_ticks']) for row in audit['owned_processes']}
    if not {(identity['pid'],identity['start_ticks']),(pytest['pid'],pytest['start_ticks'])}<=union:
        raise ValueError('manual Linux proof omits retained direct process identities')
    return {'proof':reference,'terminal_audit':proof['terminal_audit'],'selector':selector,'code_commit':SUPERVISOR}


def main():
    if sys.flags.optimize or Path.cwd() != SUP:
        raise ValueError('unoptimized Python in exact supervision checkout required')
    input_path = RAW/'selection.json'
    with input_path.open('rb') as stream: raw = stream.read(128*1024+1)
    if len(raw) > 128*1024: raise ValueError('oversized input')
    values = json.loads(raw)
    outer_start, outer_end = (datetime.fromisoformat(values[key]) for key in ('outer_started','outer_deadline'))
    if outer_start.tzinfo is None or outer_end.tzinfo is None: raise ValueError('aware outer clock required')
    local = outer_start.astimezone(ZoneInfo('America/New_York'))
    if not datetime.fromisoformat('2026-09-26T19:00:00-04:00') <= local <= datetime.fromisoformat('2026-09-26T23:43:30-04:00') \
            or outer_end > datetime.fromisoformat('2026-09-27T00:00:00-04:00'):
        raise ValueError('corrected readback fixed window differs')
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
    observations = None
    original_error = None
    with interruption_signals():
        try:
            observations = Observations(out,values['pane_identity'])
            observations.monitor.start()
            runtime = campaign_runtime(SUPERVISOR)
            proof = linux_proof(values['linux_proof'],outer_start)
            budget.check()
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
            control, evaluations = c.qualify(spec, [], store, identities, gates,reader_observer=observations.reader)
            policy, runtime_evidence = c.calibrated_runtime(control)
            budget.check()
            if gates or control['state'] != 'qualified' or budget.calls != 1 or evaluations:
                raise ValueError('readback gates or fixed invocation scope differ')
            if campaign_runtime(SUPERVISOR) != runtime: raise ValueError('supervisor changed during readback')
            c.terminal_closure(selected['terminal_receipt'],selected['driver_receipt'],receipt)
            budget.check()
            result.update(state='complete',control=control,record_identities=identities,terminal_cleanup=cleanup,
                          native_runtime=policy,runtime_evidence=runtime_evidence,supervisor_runtime=runtime,linux_proof=proof,
                          reader_invocations=budget.calls,reader_elapsed_seconds=budget.reader_seconds,
                          ancillary_elapsed_seconds=budget.mono()-budget.before-budget.reader_seconds,
                          finished=datetime.now(timezone.utc).isoformat())
            pending.write_text(json.dumps(result,sort_keys=True,allow_nan=False)+'\n')
            budget.check()
            observations.finish(min(budget.until,budget.before+budget.reader_seconds+60))
            observation_end=time.monotonic()
            result['process_observations']={
                'path':str(observations.path),'sha256':artifacts.file_hash(observations.path)}
            result['reader_events']={'path':str(observations.events_path),'sha256':artifacts.file_hash(observations.events_path)}
            result['resource_samples']={'path':str(observations.samples_path),'sha256':artifacts.file_hash(observations.samples_path)}
            result.update(ancillary_elapsed_seconds=budget.mono()-budget.before-budget.reader_seconds,
                          finished=datetime.now(timezone.utc).isoformat(),own_cleanup_verified=False)
            pending.write_text(json.dumps(result,sort_keys=True,allow_nan=False)+'\n')
            budget.check()
            os.link(pending,published)
            digest = artifacts.file_hash(published)
            budget.check()
            if time.monotonic()-observation_end>30: raise TimeoutError('final metadata exceeded30s after sampling')
            print(json.dumps({'state':'complete','path':str(published),'sha256':digest,'gain_claim':False,'protocol_freeze':False}),flush=True)
            budget.check()
        except BaseException as exc:
            original_error=exc
            if observations is not None: observations.monitor.interrupt=False
            if published.exists(): published.unlink()
            raise
        finally:
            c.pinned_readback = original
            if observations is not None and not observations.monitor.stop_event.is_set():
                try:
                    budget.check()
                    observations.finish(min(budget.until,budget.before+budget.reader_seconds+60))
                    budget.check()
                except BaseException as observation_error:
                    if original_error is None: raise
                    original_error.add_note('Observation finalization also failed: '+str(observation_error))
            budget.alarm = False; signal.setitimer(signal.ITIMER_REAL,0)


if __name__ == '__main__': main()
