#!/usr/bin/env python3
"""Method19 runner, 2026-10-15 ET: shared FIFO leases and one continuous clock.

Scoped successor of /tmp/claude/probata-tools/verifier_run.py. The external file is
unchanged. Queue/slot paths, timestamp/PID tickets, atomic mkdir and owner PID
format remain compatible. Duration/status data explicitly name their clock.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time
import uuid

import psutil
import staged_search as S

RUN_TOKEN_ENV = 'SWDB_VERIFIER_RUN_TOKEN'


def _json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=1))
    temporary.replace(path)


def _alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _owner(path):
    try:
        return int((path/'owner').read_text().split('pid=')[1].split()[0])
    except (OSError, ValueError, IndexError):
        return None


def _tickets(queue):
    live = []
    for path in sorted(queue.iterdir()):
        try:
            pid = int(path.name.split('-')[1])
        except (ValueError, IndexError):
            pid = None
        if pid is not None and _alive(pid):
            live.append(path.name)
        else:
            path.unlink(missing_ok=True)
    return live


# Only sanitized inspection metadata is retained; never environment values.
_INSPECTION_EVENTS = []
_CLEANUP_INSPECTION_FAILURES = []
_INSPECTION_STAGE = 'supervision'
_NATIVE_ENVIRON_ERROR = '<built-in function proc_environ> returned a result with an exception set'


def _exception_metadata(exc):
    """Record types, numeric identifiers and code locations, never args or locals."""
    chain, seen, current, relation = [], set(), exc, 'raised'
    while current is not None and id(current) not in seen and len(chain) < 6:
        seen.add(id(current))
        row = {'type':type(current).__name__, 'module':type(current).__module__, 'relation':relation}
        for key in ('errno', 'pid'):
            value = getattr(current, key, None)
            if isinstance(value, int) and not isinstance(value, bool):
                row[key] = value
        chain.append(row)
        if current.__cause__ is not None:
            current, relation = current.__cause__, 'cause'
        elif current.__context__ is not None and not current.__suppress_context__:
            current, relation = current.__context__, 'context'
        else:
            current = None
    frames, tb = [], exc.__traceback__
    while tb is not None and len(frames) < 8:
        frames.append({'path':tb.tb_frame.f_code.co_filename,
                       'function':tb.tb_frame.f_code.co_name, 'line':tb.tb_lineno})
        tb = tb.tb_next
    return {'exception':chain[0], 'exception_chain':chain, 'traceback':frames,
            'known_native_environ_signature':isinstance(exc, SystemError) and str(exc) == _NATIVE_ENVIRON_ERROR}


def _inspection_context(process, operation, observing, born, snapshot_birth, exc):
    return {'stage':_INSPECTION_STAGE, 'operation':observing, 'requested_operation':operation,
            'pid':process.pid, 'expected_birth':born if born is not None else snapshot_birth,
            'snapshot_birth':snapshot_birth, **_exception_metadata(exc)}


def _error_text(exc):
    detail = getattr(exc, 'inspection_detail', None)
    if detail is not None:
        # Even cause messages may contain unrelated process-environment values.
        # Only this fixed native signature is admitted as diagnostic message text.
        text = _NATIVE_ENVIRON_ERROR if detail.get('known_native_environ_signature') else 'process inspection failed'
        return f'{type(exc).__name__}: {text}'
    return f'{type(exc).__name__}: {exc}'


def _cleanup_inspection_failure(exc):
    detail = getattr(exc, 'inspection_detail', None)
    if detail is not None:
        _CLEANUP_INSPECTION_FAILURES.append(detail)
        del _CLEANUP_INSPECTION_FAILURES[:-16]


class _IdentityChanged(psutil.NoSuchProcess):
    """The numeric PID exists but no longer names the captured identity."""


def _inspect(process, operation, born=None, **kwargs):
    """Bound inspection retries; persistent live/unknown failure fails closed."""
    snapshot_birth = None
    # The environment observation may be briefly unavailable on a fresh process.
    # This bounded availability policy does not establish the cause of a denial.
    # Every retry still revalidates the immutable identity; no denied observation
    # is treated as an absent marker. The existing RSS/deadline checks follow this
    # counted pause, so it grants no proof time or hard sampling-latency guarantee.
    retry_window = .2 if operation == 'environ' else None
    retry_limit = 21 if retry_window is not None else 3
    retry_started = S.clock()
    last_failure = last_failure_event = None
    for attempt in range(1, retry_limit + 1):
        if attempt > 1 and retry_window is not None and S.clock()-retry_started >= retry_window:
            break
        try:
            # Preserve children/process_iter snapshot identity. Refreshing the
            # target before retaining its birth could adopt an unrelated PID.
            observing = 'snapshot.create_time'
            snapshot_birth = process.create_time()
            expected = snapshot_birth if born is None else born
            observing = 'identity_before.create_time'
            if snapshot_birth != expected or psutil.Process(process.pid).create_time() != expected:
                raise _IdentityChanged(process.pid)
            # Revalidation is an OS operation too: it may cross the deadline.
            # Admit the requested retry only after the last identity check.
            if attempt > 1 and retry_window is not None and S.clock()-retry_started >= retry_window:
                break
            observing = operation
            result = getattr(process, operation)(**kwargs)
            observing = 'identity_after.create_time'
            if psutil.Process(process.pid).create_time() != expected:
                raise _IdentityChanged(process.pid)
        except (psutil.AccessDenied, SystemError) as exc:
            context = _inspection_context(process, operation, observing, born, snapshot_birth, exc)
            if isinstance(exc, SystemError) and not (
                    operation == observing == 'environ' and context['known_native_environ_signature']):
                # A native error in identity checks, or an unknown native message,
                # must not acquire the environment retry policy by coincidence.
                event = {**context, 'identity_state':'unknown', 'observed_birth':None,
                         'attempt':attempt, 'clock_s':S.clock(), 'wall_unix_s':time.time(),
                         'outcome':'inspection-failed'}
                _INSPECTION_EVENTS.append(event)
                del _INSPECTION_EVENTS[:-128]
                exc.inspection_detail = dict(event)
                raise
            observed = None
            state = 'unknown'
            identity_error = None
            try:
                # Fresh objects avoid psutil's cached create_time during revalidation.
                identity_observing = 'identity_validation.create_time'
                observed = psutil.Process(process.pid).create_time()
                expected = snapshot_birth if born is None else born
                state = 'reused' if expected is not None and observed != expected else 'live'
                if state != 'reused':
                    identity_observing = 'identity_validation.status'
                    status = psutil.Process(process.pid).status()
                    if status in {psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD}:
                        state = 'gone'
            except psutil.NoSuchProcess:
                state = 'gone'
            except psutil.AccessDenied as identity_exc:
                identity_error = {'operation':identity_observing,
                                  **_exception_metadata(identity_exc)}
            except Exception as identity_exc:
                # A failure in the independent identity validation is not an
                # environ failure. Do not grant it that operation's retry policy
                # or let it escape without sanitized primary/secondary context.
                identity_error = {'operation':identity_observing,
                                  **_exception_metadata(identity_exc)}
                event = {**_inspection_context(process, operation, identity_observing,
                                               born, snapshot_birth, identity_exc),
                         'environment_failure':context, 'identity_exception':identity_error,
                         'observed_birth':observed, 'identity_state':'unknown',
                         'attempt':attempt, 'retry_elapsed_s':S.clock()-retry_started,
                         'clock_s':S.clock(), 'wall_unix_s':time.time(),
                         'outcome':'inspection-failed'}
                _INSPECTION_EVENTS.append(event)
                del _INSPECTION_EVENTS[:-128]
                identity_exc.inspection_detail = dict(event)
                raise
            retry_elapsed = S.clock() - retry_started
            event = {**context,
                     'exception_pid':getattr(exc, 'pid', None),
                     'observed_birth':observed, 'identity_state':state,
                     'attempt':attempt, 'retry_elapsed_s':retry_elapsed, 'retry_window_s':retry_window,
                     'retry_limit_attempts':retry_limit,
                     'clock_s':S.clock(), 'wall_unix_s':time.time(),
                     'outcome':'denied' if isinstance(exc, psutil.AccessDenied) else 'inspection-error'}
            if identity_error is not None:
                event['identity_exception'] = identity_error
            _INSPECTION_EVENTS.append(event)
            del _INSPECTION_EVENTS[:-128]
            last_failure, last_failure_event = exc, dict(event)
            if state in {'gone', 'reused'}:
                event['outcome'] = 'confirmed-'+state
                if state == 'reused':
                    raise _IdentityChanged(process.pid) from exc
                raise psutil.NoSuchProcess(process.pid) from exc
            if attempt == retry_limit or (retry_window is not None and retry_elapsed >= retry_window):
                exc.inspection_detail = dict(event)
                raise
            time.sleep(.01 if retry_window is None else min(.01, max(0, retry_window-retry_elapsed)))
        except Exception as exc:
            if not isinstance(exc, psutil.NoSuchProcess):
                event = {**_inspection_context(process, operation, observing, born, snapshot_birth, exc),
                         'identity_state':'unknown', 'observed_birth':None, 'attempt':attempt,
                         'clock_s':S.clock(), 'wall_unix_s':time.time(), 'outcome':'inspection-failed'}
                _INSPECTION_EVENTS.append(event)
                del _INSPECTION_EVENTS[:-128]
                exc.inspection_detail = dict(event)
            raise
        else:
            if attempt > 1:
                _INSPECTION_EVENTS.append({'stage':_INSPECTION_STAGE, 'operation':operation,
                    'pid':process.pid, 'expected_birth':born, 'attempt':attempt,
                    'clock_s':S.clock(), 'wall_unix_s':time.time(), 'outcome':'recovered'})
                del _INSPECTION_EVENTS[:-128]
            return result
    # A delayed retry was never started. Retain the original failure observation
    # separately from this later admission decision; do not invent a fresh failure
    # or claim its old live/gone state was observed at the expiry timestamp.
    decision = S.clock()
    expiry = {'stage':_INSPECTION_STAGE, 'operation':operation, 'pid':process.pid,
              'expected_birth':last_failure_event['expected_birth'],
              'clock_s':decision, 'wall_unix_s':time.time(),
              'retry_elapsed_s':decision-retry_started, 'retry_window_s':retry_window,
              'retry_expired_before_attempt':attempt,
              'last_error_clock_s':last_failure_event['clock_s'],
              'outcome':'retry-window-expired'}
    if isinstance(last_failure, psutil.AccessDenied):
        expiry['last_denial_clock_s'] = last_failure_event['clock_s']
    _INSPECTION_EVENTS.append(expiry)
    del _INSPECTION_EVENTS[:-128]
    last_failure.inspection_detail = {**last_failure_event, 'retry_expiry':dict(expiry)}
    raise last_failure


def _tree(root, known):
    try:
        parent = psutil.Process(root)
        born = _inspect(parent, 'create_time', known.get(root))
        known[root] = born
        processes = [parent, *_inspect(parent, 'children', born, recursive=True)]
    except psutil.NoSuchProcess:
        return
    for process in processes:
        try:
            known[process.pid] = _inspect(process, 'create_time', known.get(process.pid))
        except psutil.NoSuchProcess:
            pass


def _running(known):
    active = []
    for pid, born in known.items():
        try:
            process = psutil.Process(pid)
            if _inspect(process, 'create_time', born) == born and _inspect(process, 'status', born) not in {psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD}:
                active.append(process)
        except psutil.NoSuchProcess:
            pass
    return active


def _known_rss(known):
    """Sum each live PID/birth identity once, including reparented descendants."""
    total = 0
    for process in _running(known):
        try:
            total += _inspect(process, 'memory_info', known[process.pid]).rss
        except psutil.NoSuchProcess:
            pass
    return total


def _group(root, known):
    """Inventory the original start_new_session group, including reparented members."""
    for process in psutil.process_iter():
        try:
            if os.getpgid(process.pid) == root and os.getsid(process.pid) == root:
                known[process.pid] = _inspect(process, 'create_time', known.get(process.pid))
        except (psutil.NoSuchProcess, ProcessLookupError):
            pass


def _token_tree(token, born_after, known, *, root_pid=None):
    """Find inherited run identity even after reparenting/session changes.

    Trusted toolchain descendants must preserve the marker. This does not contain
    hostile descendants that scrub their environment. Environment values never
    leave this comparison; only matching PID/birth identities are retained.
    """
    # Fresh handles avoid process_iter's cached old identities. A new captured
    # birth may replace a stale nonroot record only after exact marker checking.
    for pid in psutil.pids():
        try:
            process = psutil.Process(pid)
            born = _inspect(process, 'create_time')
            if born < born_after or _inspect(process, 'uids', born).real != os.getuid():
                continue
            if _inspect(process, 'status', born) in {psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD}:
                continue
            if _inspect(process, 'environ', born).get(RUN_TOKEN_ENV) == token:
                if process.pid == root_pid and known.get(process.pid) != born:
                    raise RuntimeError('owned root identity changed or was never captured')
                known[process.pid] = born
        except psutil.NoSuchProcess:
            pass
        # Persistent live/unknown denial propagates: absence is unconfirmed.


def _stop(process, known, *, token=None, born_after=None):
    """Stop owned/observed/inherited-marker processes, or quarantine the lease."""
    if process is None:
        return []
    unconfirmed = []
    root_alive = process.poll() is None
    try:
        leader = psutil.Process(process.pid)
        if not root_alive and process.pid not in known:
            return ['root-pid-reused-or-unobserved']
        birth = _inspect(leader, 'create_time', known.get(process.pid))
        # A reaped Popen PID can be reused. Never target its replacement group.
        if not root_alive and known.get(process.pid) != birth:
            return ["root-pid-reused-or-unobserved"]
        if os.getpgid(process.pid) != process.pid or os.getsid(process.pid) != process.pid:
            return ["owned-process-group-unconfirmed"]
    except _IdentityChanged:
        return ['root-pid-reused-or-unobserved']
    except (psutil.NoSuchProcess, ProcessLookupError):
        pass  # descendants may retain the original session/group after root exit
    except (psutil.Error, PermissionError, SystemError) as exc:
        _cleanup_inspection_failure(exc)
        return ["group-leader-inspection-unconfirmed"]
    if not root_alive and process.pid not in known and token is None:
        # An unsampled child might already have changed session and been
        # reparented. Draining the old group cannot establish its absence.
        unconfirmed.append("root-ancestry-never-sampled")
    try:
        _tree(process.pid, known)
        _group(process.pid, known)
        if token is not None:
            _token_tree(token, born_after, known, root_pid=process.pid)
    except (psutil.Error, PermissionError, SystemError) as exc:
        _cleanup_inspection_failure(exc)
        unconfirmed.append(f"tree-inspection-unconfirmed:{type(exc).__name__}:pid={getattr(exc, 'pid', None)}")
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    end = S.clock() + 5
    empty_since = None
    empty_sweeps = 0
    while True:
        try:
            _group(process.pid, known)
            if token is not None:
                _token_tree(token, born_after, known, root_pid=process.pid)
        except (psutil.Error, PermissionError, SystemError) as exc:
            _cleanup_inspection_failure(exc)
            unconfirmed.append(f"group-inspection-unconfirmed:{type(exc).__name__}:pid={getattr(exc, 'pid', None)}")
        active = _running(known)
        for child in active:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        if active:
            empty_since = None
            empty_sweeps = 0
        else:
            # A marked parent may fork/exit after a PID snapshot but before
            # _running. Rediscover across separate empty sweeps before release.
            empty_sweeps += 1
            empty_since = S.clock() if empty_since is None else empty_since
            if empty_sweeps >= 3 and S.clock()-empty_since >= .05:
                process.wait(timeout=1)
                return sorted(set(unconfirmed))
        if S.clock() >= end:
            return [*sorted(set(unconfirmed)), 'cleanup-did-not-settle', *[p.pid for p in _running(known)]]
        time.sleep(0.02)


def main():
    global _INSPECTION_STAGE
    _INSPECTION_EVENTS.clear()
    _CLEANUP_INSPECTION_FAILURES.clear()
    _INSPECTION_STAGE = 'supervision'
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', required=True)
    ap.add_argument('--cap-gb', type=float, default=8)
    ap.add_argument('--timeout', type=float, default=1800)
    ap.add_argument('--queue-timeout', type=float, default=7200)
    ap.add_argument('--owner', default=os.environ.get('USER', '?'))
    ap.add_argument('--lock', default='/tmp/claude/swdb-verifier.lock')
    ap.add_argument('cmd', nargs=argparse.REMAINDER)
    a = ap.parse_args()
    command = a.cmd[1:] if a.cmd and a.cmd[0] == '--' else a.cmd
    if not command or any(not math.isfinite(x) or x <= 0 for x in (a.cap_gb, a.timeout, a.queue_timeout)):
        ap.error('a command and finite positive resource limits are required')
    clock_info = S.clock_info()  # fail before touching leases if unavailable
    lock = Path(a.lock)
    stem = lock.name[:-5] if lock.name.endswith('.lock') else lock.name
    queue = lock.with_name(stem+'.queue')
    policy = lock.with_name(stem+'.slots')
    queue.mkdir(parents=True, exist_ok=True)
    log = Path(a.log).resolve()
    log.parent.mkdir(parents=True, exist_ok=True)
    status = Path(str(log)+'.wait.json')
    stopped = [None]
    def on_signal(signum, frame):
        stopped[0] = signum  # no asynchronous exception between spawn and PID capture
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, on_signal)
    ticket = queue/f'{time.time_ns():020d}-{os.getpid()}'
    ticket.write_text(f'owner={a.owner} pid={os.getpid()}\n')
    queued = S.clock()
    _json(status, {'runner_pid':os.getpid(),'clock_info':clock_info,'clock':clock_info['kind'], 'pending_since':queued, 'settled_s':0.0})
    taken = None
    process = None
    token = None
    born_after = None
    known = {}
    peak = 0
    killed = timed_out = queue_timed_out = False
    wait_s = 0.0
    active_start = None
    rc = 1
    error = None
    inspection_failure = None
    primary_inspection_failure = None
    cleanup_inspection_failure = None
    cleanup_failed = []
    try:
        while taken is None and not stopped[0]:
            if S.clock()-queued >= a.queue_timeout:
                queue_timed_out = True
                break
            try:
                slots = min(2, max(1, int(policy.read_text().split()[0])))
            except (OSError, ValueError, IndexError):
                slots = 1
            candidates = [lock] + [lock.with_name(stem+f'.slot{k}.lock') for k in range(2, slots+1)]
            # Acquired owners remove their queue ticket. Eligibility must shrink
            # by occupied slots; otherwise the third waiter can overtake the
            # second while the first owner is already running.
            for candidate in candidates:
                if candidate.exists():
                    pid = _owner(candidate)
                    try:
                        if (pid is None or not _alive(pid)) and time.time()-candidate.stat().st_mtime > 10:
                            shutil.rmtree(candidate)
                    except FileNotFoundError:
                        pass
            available = sum(not candidate.exists() for candidate in candidates)
            if ticket.name in _tickets(queue)[:available]:
                for candidate in candidates:
                    try:
                        candidate.mkdir()
                    except FileExistsError:
                        continue
                    taken = candidate
                    wait_s = S.clock()-queued
                    (taken/'owner').write_text(f'owner={a.owner} pid={os.getpid()} clock={clock_info["kind"]}\n')
                    break
            if taken is None:
                time.sleep(0.02)
        if taken is None:
            wait_s = S.clock()-queued
            rc = 128+stopped[0] if stopped[0] else 124
        else:
            ticket.unlink(missing_ok=True)
            _json(status, {'runner_pid':os.getpid(),'clock_info':clock_info,'clock':clock_info['kind'], 'pending_since':None, 'settled_s':wait_s})
            if stopped[0]:
                rc = 128+stopped[0]
            else:
                active_start = S.clock()
                with log.open('wb') as output:
                    token = uuid.uuid4().hex
                    born_after = time.time()-1  # identity window only; counted durations use S.clock
                    environment = {**os.environ, RUN_TOKEN_ENV: token}
                    process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT,
                                               start_new_session=True, env=environment)
                    next_marker_scan = 0
                    while process.poll() is None:
                        _tree(process.pid, known)
                        if S.clock() >= next_marker_scan:
                            _token_tree(token, born_after, known, root_pid=process.pid)
                            next_marker_scan = S.clock()+.1
                        peak = max(peak, _known_rss(known))
                        killed = peak > a.cap_gb*1024**3
                        timed_out = S.clock()-active_start >= a.timeout
                        if stopped[0] or killed or timed_out:
                            break
                        time.sleep(0.02)
                    rc = process.poll()
                    if rc is None:
                        rc = 137
                    if stopped[0]:
                        rc = 128+stopped[0]
                    elif killed or timed_out:
                        rc = 137
    except Exception as exc:
        error = _error_text(exc)
        primary_inspection_failure = getattr(exc, 'inspection_detail', None)
        inspection_failure = primary_inspection_failure
        rc = 1
    finally:
        ticket.unlink(missing_ok=True)
        # Signals and exceptional exits cannot free a lease before tree cleanup.
        _INSPECTION_STAGE = 'cleanup'
        try:
            cleanup_failed = _stop(process, known, token=token, born_after=born_after)
        except Exception as exc:
            cleanup_failed = ['cleanup-unconfirmed']
            error = error or _error_text(exc)
            cleanup_inspection_failure = getattr(exc, 'inspection_detail', None)
            inspection_failure = inspection_failure or cleanup_inspection_failure
        if cleanup_inspection_failure is None and _CLEANUP_INSPECTION_FAILURES:
            cleanup_inspection_failure = _CLEANUP_INSPECTION_FAILURES[0]
            inspection_failure = inspection_failure or cleanup_inspection_failure
        if taken is not None and _owner(taken) == os.getpid():
            if cleanup_failed:
                # Reserve the slot with a permanently live sentinel until an
                # operator verifies the listed children. Dead-owner cleanup by
                # other compatible runners must not admit another job here.
                (taken/'owner').write_text(f'owner={a.owner} pid=1 quarantined_runner={os.getpid()} children={cleanup_failed}\n')
            else:
                shutil.rmtree(taken)
    log.touch(exist_ok=True)
    if cleanup_failed:
        rc = 137
    scale = 1 if sys.platform=='darwin' else 1024
    peak = max(peak, resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*scale)
    wall = S.clock()-active_start if active_start is not None else 0.0
    summary = {'cmd':command,'exit_code':rc,'wall_s':wall,'peak_rss_mb':peak/1024**2,'cap_gb':a.cap_gb,
        'killed_by_watchdog':killed,'timed_out':timed_out,'queue_timed_out':queue_timed_out,
        'timeout_s':a.timeout,'queue_timeout_s':a.queue_timeout,'lock_wait_s':wait_s,
        'runner_pid':os.getpid(),'clock':clock_info['kind'],'clock_info':clock_info,'log':str(log),
        'inspection_events':_INSPECTION_EVENTS, 'inspection_failure':inspection_failure,
        'primary_inspection_failure':primary_inspection_failure,
        'cleanup_inspection_failure':cleanup_inspection_failure,
        'cleanup_inspection_failures':_CLEANUP_INSPECTION_FAILURES,
        'inspection_retry_boundary':'AccessDenied uses a 200 ms environ retry admission window and 21-attempt cap, or three attempts for other operations; only the exact proc_environ SystemError raised by the requested environ operation shares that policy; individual OS calls are not forcibly timed; all pauses count and RSS/deadline checks remain mandatory after inspection; only independently confirmed gone/zombie or changed birth is skipped; persistent live or unknown failure fails closed',
        'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'unconfirmed_children':cleanup_failed,'error':error,
        'cleanup_boundary':'owned group, observed descendants, and inherited marker with three empty sweeps spanning50ms; trusted toolchain must preserve marker; polling is not atomic or hostile-process containment',
        'rss_scope':'live union of current ancestry, retained PID/birth identities and periodic inherited-marker matches; sampled, not a kernel quota',
        'finished':time.strftime('%Y-%m-%d %H:%M:%S %Z')}
    _json(str(log)+'.summary.json',summary)
    _json(status, {'runner_pid':os.getpid(),'clock_info':clock_info,'clock':clock_info['kind'],'pending_since':None,'settled_s':wait_s})
    print(json.dumps(summary))
    return rc if rc >= 0 else 128-rc


if __name__=='__main__':
    raise SystemExit(main())
