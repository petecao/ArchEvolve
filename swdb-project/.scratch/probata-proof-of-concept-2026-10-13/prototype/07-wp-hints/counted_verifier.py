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


def _tree(root, known):
    try:
        parent = psutil.Process(root)
        processes = [parent, *parent.children(recursive=True)]
    except psutil.NoSuchProcess:
        return 0
    total = 0
    for process in processes:
        try:
            known[process.pid] = process.create_time()
            total += process.memory_info().rss
        except psutil.NoSuchProcess:
            pass
    return total


def _running(known):
    active = []
    for pid, born in known.items():
        try:
            process = psutil.Process(pid)
            if process.create_time() == born and process.status() not in {psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD}:
                active.append(process)
        except psutil.NoSuchProcess:
            pass
    return active


def _group(root, known):
    """Inventory the original start_new_session group, including reparented members."""
    for process in psutil.process_iter(["pid", "create_time"]):
        try:
            if os.getpgid(process.pid) == root and os.getsid(process.pid) == root:
                known[process.pid] = process.info["create_time"]
        except (psutil.NoSuchProcess, ProcessLookupError):
            pass


def _token_tree(token, born_after, known):
    """Find inherited run identity even after reparenting/session changes.

    Trusted toolchain descendants must preserve the marker. This does not contain
    hostile descendants that scrub their environment. Environment values never
    leave this comparison; only matching PID/birth identities are retained.
    """
    for process in psutil.process_iter(['pid', 'create_time', 'uids']):
        try:
            info = process.info
            if info['uids'].real != os.getuid() or info['create_time'] < born_after:
                continue
            if process.status() in {psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD}:
                continue
            for attempt in range(3):
                try:
                    if process.environ().get(RUN_TOKEN_ENV) == token:
                        known[process.pid] = info['create_time']
                    break
                except psutil.AccessDenied:
                    # procargs can race with exec/exit on Darwin. Retry the
                    # inspection itself; persistent live denial fails closed.
                    if process.status() in {psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD}:
                        break
                    if attempt == 2:
                        raise
                    time.sleep(.01)
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            # Darwin can report EACCES when procargs races with process exit.
            # Only an independently confirmed gone/zombie process is harmless.
            try:
                if process.status() not in {psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD}:
                    raise
            except psutil.NoSuchProcess:
                pass
        # AccessDenied/other inspection errors propagate: absence is unconfirmed.


def _stop(process, known, *, token=None, born_after=None):
    """Stop owned/observed/inherited-marker processes, or quarantine the lease."""
    if process is None:
        return []
    unconfirmed = []
    root_alive = process.poll() is None
    try:
        leader = psutil.Process(process.pid)
        birth = leader.create_time()
        # A reaped Popen PID can be reused. Never target its replacement group.
        if not root_alive and known.get(process.pid) != birth:
            return ["root-pid-reused-or-unobserved"]
        if os.getpgid(process.pid) != process.pid or os.getsid(process.pid) != process.pid:
            return ["owned-process-group-unconfirmed"]
    except (psutil.NoSuchProcess, ProcessLookupError):
        pass  # descendants may retain the original session/group after root exit
    except (psutil.Error, PermissionError):
        return ["group-leader-inspection-unconfirmed"]
    if not root_alive and process.pid not in known and token is None:
        # An unsampled child might already have changed session and been
        # reparented. Draining the old group cannot establish its absence.
        unconfirmed.append("root-ancestry-never-sampled")
    try:
        _tree(process.pid, known)
        _group(process.pid, known)
        if token is not None:
            _token_tree(token, born_after, known)
    except (psutil.Error, PermissionError) as exc:
        unconfirmed.append(f"tree-inspection-unconfirmed:{type(exc).__name__}:pid={getattr(exc, 'pid', None)}")
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    end = S.clock() + 5
    while True:
        try:
            _group(process.pid, known)
            if token is not None:
                _token_tree(token, born_after, known)
        except (psutil.Error, PermissionError) as exc:
            unconfirmed.append(f"group-inspection-unconfirmed:{type(exc).__name__}:pid={getattr(exc, 'pid', None)}")
        active = _running(known)
        for child in active:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        if not active:
            process.wait(timeout=1)
            return sorted(set(unconfirmed))
        if S.clock() >= end:
            return [*sorted(set(unconfirmed)), *[p.pid for p in _running(known)]]
        time.sleep(0.02)


def main():
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
                    while process.poll() is None:
                        peak = max(peak, _tree(process.pid, known))
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
        error = f'{type(exc).__name__}: {exc}'
        rc = 1
    finally:
        ticket.unlink(missing_ok=True)
        # Signals and exceptional exits cannot free a lease before tree cleanup.
        try:
            cleanup_failed = _stop(process, known, token=token, born_after=born_after)
        except Exception as exc:
            cleanup_failed = ['cleanup-unconfirmed']
            error = error or f'{type(exc).__name__}: {exc}'
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
        'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'unconfirmed_children':cleanup_failed,'error':error,
        'cleanup_boundary':'owned group, observed descendants, and inherited marker; trusted toolchain must preserve marker; hostile environment scrubbing unsupported',
        'finished':time.strftime('%Y-%m-%d %H:%M:%S %Z')}
    _json(str(log)+'.summary.json',summary)
    _json(status, {'runner_pid':os.getpid(),'clock_info':clock_info,'clock':clock_info['kind'],'pending_since':None,'settled_s':wait_s})
    print(json.dumps(summary))
    return rc if rc >= 0 else 128-rc


if __name__=='__main__':
    raise SystemExit(main())
