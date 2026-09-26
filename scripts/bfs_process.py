"""Owned subprocess cleanup and durable driver stages. Updated: 2026-09-26 ET."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from swdb.artifacts import file_hash
from swdb.processes import stop_group


def finish_legacy_group(child, deadline):
    """Signal only a still-owned unreaped session; always attempt direct reap.

    A reaped leader cannot authorize signaling its stale numeric group. This
    helper claims neither same-group nor detached descendants after that point;
    prospective Linux callers establish whole-tree ownership with Owned.
    """
    if child is None:
        return
    error = None
    for signum in (signal.SIGTERM, signal.SIGKILL):
        try:
            if child.poll() is not None:
                break
            if os.getpgid(child.pid) != child.pid:
                raise ValueError('child no longer owns its declared session')
            os.killpg(child.pid, signum)
        except ProcessLookupError:
            pass
        except BaseException as exc:
            error = error or exc
        remaining = max(0, deadline-time.monotonic())
        allowance = min(20, max(0, remaining-.5)) if signum == signal.SIGTERM else remaining
        try:
            child.wait(timeout=allowance)
        except subprocess.TimeoutExpired:
            pass
        except BaseException as exc:
            error = error or exc
    # Signal/identity failures never skip direct wait. Exhaustion still permits
    # a nonblocking reap of an already-waitable direct child.
    try:
        child.wait(timeout=max(0,deadline-time.monotonic()))
    except BaseException as exc:
        error = error or exc
    if error is not None:
        raise error


@contextmanager
def interruption_signals():
    """Let the driver unwind once, without interrupting its cleanup on repeats."""
    interrupted = False

    def interrupt(signum, _frame):
        nonlocal interrupted
        if not interrupted:
            interrupted = True
            raise InterruptedError(f'driver interrupted by signal {signum}')

    handlers = {sig: signal.signal(sig, interrupt)
                for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    try:
        yield
    finally:
        for sig, handler in handlers.items():
            signal.signal(sig, handler)


def save_receipt(folder, receipt):
    (Path(folder) / 'driver.json').write_text(json.dumps(receipt, indent=2) + '\n')


def run_stage(receipt, folder, command, *, timeout, deadline, cwd, env=None,
              output=None, stderr=None, monitor=None):
    """Stream logs; on interruption allow the evaluator to reap nested groups."""
    before = time.monotonic()
    until = min(deadline, before+timeout)
    folder = Path(folder)
    step = f"{len(receipt['stages']):02d}"
    out = Path(output) if output is not None else folder / (step + '.stdout')
    err = Path(stderr) if stderr is not None else folder / (step + '.stderr')
    row = {'command': list(map(str, command)), 'output': str(out),
           'stderr': str(err), 'state': 'running'}
    receipt['stages'].append(row)
    save_receipt(folder, receipt)
    child = None
    original_error = cleanup_error = None
    try:
        with out.open('w') as stdout, err.open('w') as errors:
            allowed = until - time.monotonic()
            if allowed <= 0:
                raise TimeoutError('driver total time budget exhausted')
            row['timeout_s'] = allowed
            child = subprocess.Popen(row['command'], cwd=cwd, env=env, stdout=stdout,
                                     stderr=errors, start_new_session=True)
            try:
                while child.poll() is None:
                    if monitor is not None:
                        monitor()
                    remaining = until - time.monotonic()
                    if remaining <= 0:
                        raise subprocess.TimeoutExpired(row['command'], allowed)
                    try:
                        child.wait(timeout=min(5, remaining) if monitor is not None else remaining)
                    except subprocess.TimeoutExpired:
                        if monitor is None:
                            raise
                if time.monotonic() > until:
                    raise subprocess.TimeoutExpired(row['command'], allowed)
            except BaseException as exc:
                original_error = exc
                raise
        row['state'] = 'complete' if child.returncode == 0 else 'failed'
        if child.returncode:
            raise RuntimeError(f'command failed; retained {out} and {err}')
    except BaseException as exc:
        original_error = original_error or exc
        row.update(state='interrupted_or_timeout' if isinstance(
            exc, (InterruptedError, TimeoutError, subprocess.TimeoutExpired)) else 'failed',
            reason=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        try:
            finish_legacy_group(child, deadline)
        except BaseException as exc:
            cleanup_error = exc
            row.update(state='failed', cleanup_error=f'{type(exc).__name__}: {exc}')
        try:
            row.update(returncode=child.returncode if child is not None else None,
                       host_wall_s=time.monotonic() - before,
                       stdout_sha256=file_hash(out) if out.is_file() else None,
                       stderr_sha256=file_hash(err) if err.is_file() else None)
            save_receipt(folder, receipt)
            if time.monotonic() > deadline:
                raise TimeoutError('stage finalization exceeded its original deadline')
        except BaseException as exc:
            cleanup_error = cleanup_error or exc
            row.update(state='failed', finalization_error=f'{type(exc).__name__}: {exc}')
            # Preserve the original failure even if failure persistence also
            # fails. This compatibility path does not attest whole-tree cleanup.
            try: save_receipt(folder, receipt)
            except BaseException as persist_error:
                row['failure_persistence_error'] = f'{type(persist_error).__name__}: {persist_error}'
        if cleanup_error is not None and original_error is None:
            raise cleanup_error
    return row
