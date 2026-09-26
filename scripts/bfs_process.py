"""Owned subprocess cleanup and durable driver stages. Updated: 2026-09-26 ET."""
from contextlib import contextmanager
import json
from pathlib import Path
import signal
import subprocess
import time

from swdb.artifacts import file_hash
from swdb.processes import stop_group


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
    folder = Path(folder)
    step = f"{len(receipt['stages']):02d}"
    out = Path(output) if output is not None else folder / (step + '.stdout')
    err = Path(stderr) if stderr is not None else folder / (step + '.stderr')
    row = {'command': list(map(str, command)), 'output': str(out),
           'stderr': str(err), 'state': 'running'}
    receipt['stages'].append(row)
    save_receipt(folder, receipt)
    before = time.monotonic()
    child = None
    try:
        with out.open('w') as stdout, err.open('w') as errors:
            allowed = min(timeout, deadline - time.monotonic())
            if allowed <= 0:
                raise TimeoutError('driver total time budget exhausted')
            row['timeout_s'] = allowed
            child = subprocess.Popen(row['command'], cwd=cwd, env=env, stdout=stdout,
                                     stderr=errors, start_new_session=True)
            try:
                until = time.monotonic() + allowed
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
            finally:
                # Public evaluators own additional compiler/simulator sessions.
                # TERM gives them time to stop those children and retain failure.
                stop_group(child)
        row['state'] = 'complete' if child.returncode == 0 else 'failed'
        if child.returncode:
            raise RuntimeError(f'command failed; retained {out} and {err}')
    except BaseException as exc:
        row.update(state='interrupted_or_timeout' if isinstance(
            exc, (InterruptedError, TimeoutError, subprocess.TimeoutExpired)) else 'failed',
            reason=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        row.update(returncode=child.returncode if child is not None else None,
                   host_wall_s=time.monotonic() - before,
                   stdout_sha256=file_hash(out) if out.is_file() else None,
                   stderr_sha256=file_hash(err) if err.is_file() else None)
        save_receipt(folder, receipt)
    return row
