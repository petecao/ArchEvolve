"""Prospective Linux ownership and shared teardown budgets. Dated 2026-09-26 ET.
Updated 2026-09-27 ET: resume decisions R1 (dead-owner reservations are spent),
R2 (resource-sample count derived from coverage interval) and R3 (a stage may
inherit a lane gem5-slot descriptor that the caller closes after spawn).

RSS is sampled from one procfs stat record, never a hard memory quota. The
shared cleanup file accounts for nested supervisors without holding its lock
while signaling, waiting, or reaping. Historical clients do not import this.
"""
from contextlib import contextmanager
from datetime import datetime
import ctypes
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import uuid
from zoneinfo import ZoneInfo

from scripts.bfs_owned_rss import DescendantRSS, MAX_IDENTITIES, RSS_SOURCE
from scripts.bfs_process import save_receipt
from swdb.artifacts import file_hash

ET = ZoneInfo('America/New_York')
FORMAT = 'swdb.bfs.shared-cleanup.v1'
MAX_GAP_SECONDS = 30
SAMPLE_INTERVAL_SECONDS = 5
SAMPLED_RSS_BYTES = 52 * 1024**3


def require(value, reason):
    if not value:
        raise ValueError(reason)


def stamp():
    return datetime.now(ET).isoformat()


def identity(pid):
    folder = Path(f'/proc/{pid}')
    raw = DescendantRSS._read_proc_text(folder/'stat', folder, f'PID {pid} identity')
    if raw is None:
        return None
    fields = raw.rsplit(')', 1)[1].split()
    require(int(raw.split(' (', 1)[0]) == pid, 'process identity changed')
    return {'pid': pid, 'parent_pid': int(fields[1]), 'start_ticks': int(fields[19]),
            'state': fields[0], 'rss_bytes': int(fields[21]) * os.sysconf('SC_PAGE_SIZE')}


def ancestry(driver, pane):
    """Stop at the exact owned pane, excluding shared tmux/server ancestors."""
    rows, current = [], driver
    for _ in range(64):
        require(current is not None, 'owned pane is not an ancestor')
        require((current['pid'], current['start_ticks']) not in
                {(row['pid'], row['start_ticks']) for row in rows}, 'ancestry cycle')
        rows.append(current)
        if current['pid'] == pane['pid']:
            require(current['start_ticks'] == pane['start_ticks'], 'owned pane identity changed')
            return rows
        current = identity(current['parent_pid'])
    raise ValueError('owned ancestry bound exceeded')


class GraceExhausted(ValueError):
    pass


class SharedCleanup:
    """Short reservations make concurrent teardown conservative and nonblocking.

    A supervisor that dies with a reservation consumes that entire reservation.
    No PID-based reclamation or resetting is allowed. A delayed action that
    exceeds its grant fails closed and records actual elapsed cost.
    """
    def __init__(self, path, expected_binding, deadline):
        self.path, self.binding, self.deadline = Path(path), expected_binding, deadline
        self.deadline = min(self.deadline, self.snapshot()['monotonic_end'])

    @staticmethod
    def create(path, absolute_end, *, seconds=30, deadline=None):
        require(seconds == 30, 'shared cleanup reserve must remain 30 seconds')
        value = {'format': FORMAT, 'budget_seconds': seconds, 'absolute_end': absolute_end,
                 'created': stamp(), 'creator': identity(os.getpid()), 'spent_seconds': 0.0,
                 'monotonic_end': min(deadline if deadline is not None else float('inf'),
                     time.monotonic()+(datetime.fromisoformat(absolute_end)-datetime.now(ET)).total_seconds()),
                 'reservations': {}, 'events': []}
        binding = SharedCleanup.binding_of(value)
        with Path(path).open('x') as stream:
            stream.write(json.dumps(value) + '\n'); stream.flush(); os.fsync(stream.fileno())
        return binding

    @staticmethod
    def binding_of(value):
        stable = {key: value[key] for key in ('format', 'budget_seconds', 'absolute_end', 'monotonic_end', 'created', 'creator')}
        return hashlib.sha256(json.dumps(stable, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    @contextmanager
    def _locked(self):
        require(self.path.is_absolute() and not self.path.is_symlink(), 'unsafe cleanup ledger path')
        before = time.monotonic()
        with self.path.open('r+') as stream:
            while True:
                try:
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB); break
                except BlockingIOError:
                    require(time.monotonic() - before < .5 and time.monotonic() < self.deadline,
                            'shared cleanup metadata lock exceeded its bound')
                    time.sleep(.005)
            try:
                raw = stream.read(256 * 1024 + 1)
                require(len(raw) <= 256 * 1024, 'cleanup ledger size exceeded')
                value = json.loads(raw)
                require(value['format'] == FORMAT and self.binding_of(value) == self.binding,
                        'shared cleanup immutable identity changed')
                require(type(value['spent_seconds']) in (int, float) and math.isfinite(value['spent_seconds'])
                        and value['spent_seconds'] >= 0, 'cleanup expenditure is malformed')
                require(isinstance(value['reservations'], dict) and len(value['reservations']) <= 64
                        and all(type(row.get('seconds')) in (int,float) and math.isfinite(row['seconds'])
                        and 0 < row['seconds'] <= 30 for row in value['reservations'].values()),
                        'cleanup reservations are malformed')
                require(value['spent_seconds']+sum(row['seconds'] for row in value['reservations'].values()) <= 30,
                        'cleanup ledger exceeds its fixed reserve')
                yield value
                stream.seek(0); json.dump(value, stream); stream.write('\n'); stream.truncate()
                stream.flush(); os.fsync(stream.fileno())
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def snapshot(self):
        with self._locked() as value:
            return json.loads(json.dumps(value))

    @contextmanager
    def reservation(self, maximum=5, *, grace=False):
        began = time.monotonic(); key = uuid.uuid4().hex
        with self._locked() as value:
            held = sum(row['seconds'] for row in value['reservations'].values())
            remaining = value['budget_seconds'] - value['spent_seconds'] - held
            wall = (datetime.fromisoformat(value['absolute_end']) - datetime.now(ET)).total_seconds()
            # Grace may not consume the last ten seconds reserved for KILL,
            # direct reap and durable finalization. Concurrent reservations count.
            spendable = remaining-10 if grace else remaining
            grant = min(maximum, spendable, self.deadline - began, wall)
            if grace and grant <= .2: raise GraceExhausted('shared graceful allowance exhausted')
            require(grant > .05, 'shared cleanup reserve exhausted')
            require(len(value['events']) < 2048, 'cleanup event bound exceeded')
            value['reservations'][key] = {'pid': os.getpid(), 'seconds': grant, 'started': stamp(),
                                          'purpose': 'grace' if grace else 'cleanup_or_finalization',
                                          **_owner_start()}
        try:
            require(time.monotonic() < began + grant, 'cleanup reservation metadata exceeded grant')
            yield min(self.deadline, began + grant)
        finally:
            with self._locked() as value:
                row = value['reservations'].pop(key)
                # Charge a declared 50-ms settlement tail; the post-write check
                # rejects slow fsync/unlock instead of omitting that cost.
                elapsed = time.monotonic() - began + .05
                value['spent_seconds'] += elapsed
                value['events'].append({**row, 'elapsed_seconds': elapsed, 'finished': stamp(),
                                        'exceeded_grant': elapsed > grant})
            require(time.monotonic()-began <= elapsed and elapsed <= grant
                    and value['spent_seconds'] <= value['budget_seconds'],
                    'cleanup exceeded its shared reservation')


def _owner_start():
    """R1: record the reserving process start so a later reader can prove death."""
    try:
        row = identity(os.getpid())
    except (OSError, ValueError):
        row = None
    return {'start_ticks': row['start_ticks']} if row else {}


def charge_dead_owner_reservations(value, *, observe=identity):
    """R1 (2026-09-27): after closure, charge each absent owner's full grant.

    The ledger rule is that a supervisor dying with a reservation consumes all
    of it. A reservation whose owner is still live, or whose PID is reused
    without a recorded start time to disprove identity, is not settled here.
    Returns the conservative spent total; it never edits the ledger file.
    """
    rows = value.get('reservations')
    require(isinstance(rows, dict), 'cleanup reservations are malformed')
    charged = []
    for row in rows.values():
        seconds = row.get('seconds') if isinstance(row, dict) else None
        require(type(row.get('pid')) is int and row['pid'] > 0 and type(seconds) in (int, float)
                and math.isfinite(seconds) and 0 < seconds <= 30, 'dead-owner reservation is malformed')
        live = observe(row['pid'])
        start = row.get('start_ticks')
        require(live is None or (type(start) is int and live['start_ticks'] != start),
                'cleanup reservation owner is live or its identity cannot be disproved')
        charged.append(seconds)
    spent = value.get('spent_seconds')
    require(type(spent) in (int, float) and math.isfinite(spent) and spent >= 0, 'cleanup spent is malformed')
    total = spent + math.fsum(charged)
    require(total <= value.get('budget_seconds', 30), 'dead-owner charges exceed the fixed cleanup reserve')
    return {'dead_owner_reservations': len(charged), 'dead_owner_seconds': math.fsum(charged),
            'settled_seconds': spent, 'conservative_spent_seconds': total}


class Owned:
    """Serialize robust observation and pidfd operations over our adopted tree."""
    def __init__(self, budget):
        require(sys.platform == 'linux' and hasattr(os, 'pidfd_open')
                and hasattr(signal, 'pidfd_send_signal'), 'Linux subreaper/pidfd required')
        libc = ctypes.CDLL(None, use_errno=True)
        require(libc.prctl(36, 1, 0, 0, 0) == 0, 'cannot enable owned subreaper')
        active = ctypes.c_int()
        require(libc.prctl(37, ctypes.byref(active), 0, 0, 0) == 0 and active.value == 1,
                'owned subreaper was not established')
        self.sampler, self.budget = DescendantRSS(os.getpid()), budget
        self.lock, self.history = threading.RLock(), {}

    @contextmanager
    def locked(self):
        require(self.lock.acquire(timeout=min(.5, max(0, self.budget.deadline-time.monotonic()))),
                'owned lifecycle lock exceeded bound')
        try: yield
        finally: self.lock.release()

    def remember(self, row):
        with self.locked():
            require(row and row['parent_pid'] == os.getpid(), 'direct child identity is unavailable')
            self.sampler.known[row['pid']] = row['start_ticks']
            self.history[row['pid'], row['start_ticks']] = dict(row)
            require(len(self.history) <= MAX_IDENTITIES, 'owned history bound exceeded')

    def sample(self):
        with self.locked():
            try:
                result = self.sampler.sample()
            finally:
                # Preserve even identities discovered before a telemetry error.
                for pid, start in self.sampler.known.items():
                    self.history.setdefault((pid, start), {'pid': pid, 'start_ticks': start})
            for row in result['processes']:
                self.history[row['pid'], row['start_ticks']] = row
            require(len(self.history) <= MAX_IDENTITIES, 'owned history bound exceeded')
            return result

    def signal(self, row, signum):
        require(row['pid'] != os.getpid(), 'cannot signal the supervisor')
        try: fd = os.pidfd_open(row['pid'])
        except ProcessLookupError: return
        try:
            current = identity(row['pid'])
            if current and current['start_ticks'] == row['start_ticks']:
                try: signal.pidfd_send_signal(fd, signum)
                except ProcessLookupError: pass  # pidfd target exited after verification
        finally: os.close(fd)

    def finish(self, child=None, direct=None):
        observed, errors, graceful_until = {}, [], None
        force = child is None or child.poll() is not None
        while True:
            try:
                with self.budget.reservation(grace=not force) as until:
                    rows = []
                    try:
                        with self.locked():
                            if child is not None and child.poll() is None:
                                require(direct is not None, 'live child lacks captured identity')
                                if graceful_until is None:
                                    graceful_until = min(self.budget.deadline, time.monotonic()+20)
                                    self.signal(direct, signal.SIGTERM)
                                if force or time.monotonic() >= graceful_until:
                                    force = True; self.signal(direct, signal.SIGKILL)
                            try:
                                rows = [row for row in self.sample()['processes'] if row['pid'] != os.getpid()]
                            except ValueError as exc:
                                errors.append(str(exc)); force = True
                                rows = [row for row in self.history.values() if row['pid'] != os.getpid()]
                            for row in rows:
                                observed[row['pid'], row['start_ticks']] = row
                                if child is not None and child.poll() is None and not force:
                                    continue
                                self.signal(row, signal.SIGKILL)
                    except (OSError, ValueError) as exc:
                        errors.append(f'{type(exc).__name__}: {exc}'); force = True
                    finally:
                        # Direct Popen reap is independent of observer/signal success.
                        # Never replace its real status by a waitpid(-1) side effect.
                        if child is not None:
                            try: child.wait(timeout=max(0,min(.1,until-time.monotonic())))
                            except subprocess.TimeoutExpired: pass
                    for row in rows:
                        if child is not None and row['pid'] == child.pid: continue
                        try: os.waitpid(row['pid'], os.WNOHANG)
                        except ChildProcessError: pass
                    require(time.monotonic() <= until, 'owned cleanup observation exceeded reservation')
                    with self.locked():
                        live = [row for row in self.sample()['processes'] if row['pid'] != os.getpid()]
                    if not live and (child is None or child.returncode is not None):
                        return {'state': 'all_owned_descendants_absent', 'subreaper': True,
                                'observed': list(observed.values()), 'checked_at': stamp(),
                                'direct_reaped': child is None or child.returncode is not None,
                                'shared_budget': str(self.budget.path), 'errors': errors}
                    require(len(errors) <= 128, 'cleanup telemetry/signaling remained unavailable')
                    time.sleep(min(.02, max(0,until-time.monotonic())))
            except GraceExhausted:
                force = True
            except BaseException:
                # Even exhausted accounting must not omit an already-waitable
                # direct child's reap. This zero-wait attempt cannot extend time.
                if child is not None:
                    try: child.wait(timeout=0)
                    except subprocess.TimeoutExpired: pass
                raise


def verified_finish(owner, child=None, direct=None):
    result = owner.finish(child, direct)
    require(result.get('state') == 'all_owned_descendants_absent' and not result.get('errors'),
            'owned cleanup retained errors or did not establish absence: '+str(result.get('errors', [])))
    return result


class Monitor:
    """Continuous sampled guard; slow/missing observations cannot imply success."""
    def __init__(self, callback, *, interrupt=True):
        self.callback, self.interrupt = callback, interrupt
        self.stop_event, self.lock = threading.Event(), threading.RLock()
        self.last_started, self.error, self.thread = None, None, None
        self.maximum_gap_seconds = self.maximum_guard_seconds = 0.0

    def observe(self):
        require(self.lock.acquire(timeout=.5), 'resource monitor lock exceeded bounded wait')
        try:
            before = time.monotonic()
            if self.last_started is not None:
                gap = before - self.last_started
                self.maximum_gap_seconds = max(self.maximum_gap_seconds, gap)
                require(gap <= MAX_GAP_SECONDS, 'resource telemetry gap exceeded 30 seconds')
            result = self.callback()
            elapsed = time.monotonic() - before
            self.maximum_guard_seconds = max(self.maximum_guard_seconds, elapsed)
            require(elapsed <= MAX_GAP_SECONDS, 'resource guard exceeded 30 seconds')
            self.last_started = before
            return result
        finally:
            self.lock.release()

    def check(self):
        if self.error is not None: raise self.error
        require(self.last_started is not None and time.monotonic()-self.last_started <= MAX_GAP_SECONDS,
                'resource telemetry is stale')

    def _run(self):
        while not self.stop_event.wait(SAMPLE_INTERVAL_SECONDS):
            try: self.observe()
            except BaseException as exc:
                self.error = exc
                if self.interrupt and not self.stop_event.is_set(): os.kill(os.getpid(), signal.SIGTERM)
                return

    def start(self):
        self.observe()
        self.thread = threading.Thread(target=self._run, daemon=True); self.thread.start()

    def stop(self, deadline):
        self.stop_event.set()
        if self.thread: self.thread.join(timeout=max(0, min(.5, deadline-time.monotonic())))
        require(not self.thread or not self.thread.is_alive(), 'resource guard still running at cleanup')
        self.check()


def run_stage(receipt, folder, command, *, timeout, deadline, cwd, owned, monitor=None,
              output=None, stderr=None, env=None, pass_fds=(), spawned=None):
    """A public stage and every detached descendant share one cleanup reserve.

    ``pass_fds`` lets the child inherit a lane gem5-slot lock (R3); ``spawned``
    runs right after Popen so the caller can close its own copy of that lock.
    """
    folder = Path(folder); step = str(len(receipt['stages'])).zfill(2)
    out = Path(output) if output else folder/(step+'.stdout')
    err = Path(stderr) if stderr else folder/(step+'.stderr')
    row = {'command': list(map(str, command)), 'started': stamp(), 'state': 'running',
           'output': str(out), 'stderr': str(err)}
    receipt['stages'].append(row); save_receipt(folder, receipt)
    before = time.monotonic(); child = direct = original_error = None
    try:
        allowed = min(timeout, deadline-time.monotonic())
        require(allowed > 0, 'stage deadline exhausted')
        with out.open('x') as stdout, err.open('x') as errors:
            try:
                child = subprocess.Popen(row['command'], cwd=cwd, env=env, stdout=stdout, stderr=errors,
                                         start_new_session=True, pass_fds=tuple(pass_fds))
            finally:
                if spawned: spawned()
            direct = identity(child.pid); owned.remember(direct); row['identity'] = direct
            row['timeout_s'] = allowed; save_receipt(folder, receipt)
            until = min(deadline, before+timeout)
            while child.poll() is None:
                if monitor: monitor()
                remaining = until-time.monotonic()
                if remaining <= 0: raise subprocess.TimeoutExpired(row['command'], allowed)
                try: child.wait(timeout=min(.25, remaining))
                except subprocess.TimeoutExpired: pass
            require(child.returncode == 0, f'public stage exited {child.returncode}')
            require(time.monotonic() <= until, 'stage setup/return exceeded original work deadline')
        row['state'] = 'complete'
    except BaseException as exc:
        original_error = exc
        row.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        cleanup_error = None
        try:
            row['cleanup'] = owned.finish(child, direct)
            require(not row['cleanup'].get('errors'), 'owned cleanup had retained observation/signal errors')
        except BaseException as exc:
            cleanup_error = exc
            row.update(state='failed', cleanup_error=f'{type(exc).__name__}: {exc}')
        try:
            with owned.budget.reservation():
                row.update(returncode=child.returncode if child else None, finished=stamp(),
                           host_wall_s=time.monotonic()-before,
                           stdout_sha256=file_hash(out) if out.is_file() else None,
                           stderr_sha256=file_hash(err) if err.is_file() else None)
                save_receipt(folder, receipt)
        except BaseException as exc:
            cleanup_error = cleanup_error or exc
            row.update(state='failed', finalization_error=f'{type(exc).__name__}: {exc}')
            # The parent/outer failure receipt remains authoritative if this
            # exhausted reserve cannot durably update the child stage; no
            # uncharged emergency persistence or success promotion is allowed.
        if cleanup_error is not None and original_error is None:
            raise cleanup_error
    return row


def sample_count_bound(started, finished):
    """R2 (2026-09-27): cap lines by the declared interval, not a fixed 20,000.

    At most two writers (the periodic monitor and throttled stage polls) each
    emit one sample per SAMPLE_INTERVAL_SECONDS; the factor two plus 64 lines
    covers startup/finalization observations. The historical 20,000-line cap
    remains a floor so earlier short streams keep their accepted bound.
    """
    seconds = max(0.0, (finished - started).total_seconds())
    return max(20000, 2 * math.ceil(seconds / SAMPLE_INTERVAL_SECONDS) + 64)


def validate_samples(path, started, finished, *, nested=False):
    """Stream resource receipt consistency; this cannot detect unsampled peaks."""
    previous, count, peak = datetime.fromisoformat(started), 0, 0
    end = datetime.fromisoformat(finished)
    require(previous.utcoffset() is not None and end.utcoffset() is not None and end >= previous,
            'resource coverage interval is invalid')
    limit = sample_count_bound(previous, end)
    known = set()
    with Path(path).open() as stream:
        for line in stream:
            require(len(line) <= 2*1024**2 and count < limit, 'resource sample read bound exceeded')
            sample = json.loads(line)
            if nested: sample = sample['owned_processes']
            observed = datetime.fromisoformat(sample['sampled_at'])
            require(observed.utcoffset() is not None and 0 <= (observed-previous).total_seconds() <= MAX_GAP_SECONDS
                    and observed <= end, 'resource sample gap/order exceeds its declared bound')
            rows = sample['processes']; page = sample['page_size_bytes']
            require(sample['rss_source'] == RSS_SOURCE and type(page) is int and 0 < page <= 1024**2
                    and isinstance(rows,list) and 0 < len(rows) <= MAX_IDENTITIES,
                    'resource sample basis is unavailable')
            identities = {(row['pid'],row['start_ticks']) for row in rows}
            require(len(identities) == len(rows), 'resource sample duplicates an identity')
            for row in rows:
                require(all(type(row[key]) is int and row[key] >= 0 for key in
                        ('pid','parent_pid','start_ticks','rss_pages','rss_bytes')) and row['pid'] > 0
                        and row['rss_bytes'] == row['rss_pages']*page, 'resource row arithmetic is invalid')
            require(type(sample['rss_bytes']) is int and sample['rss_bytes'] == sum(row['rss_bytes'] for row in rows)
                    and sample['rss_bytes'] <= SAMPLED_RSS_BYTES, 'sampled whole-tree RSS exceeds its bound')
            known.update(identities); require(len(known) <= MAX_IDENTITIES, 'retained resource identities exceeded')
            peak = max(peak,sample['rss_bytes']); previous=observed; count+=1
    require(count > 0 and 0 <= (end-previous).total_seconds() <= MAX_GAP_SECONDS,
            'resource telemetry does not cover finalization')
    return {'samples':count,'peak_sampled_rss_bytes':peak,'observed_identities':
            [{'pid':pid,'start_ticks':start} for pid,start in sorted(known)],'hard_memory_quota':False}
