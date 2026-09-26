"""Bounded-process and preflight support for diagnostic drivers. Updated 2026-09-25."""
import os
import re
import signal
import socket
import subprocess
import time
from pathlib import Path


def preflight(args, store, profile):
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', args.id):
        raise RuntimeError('ID must use the record identifier syntax')
    if socket.gethostname().split('.')[0] != 'mbit10':
        raise RuntimeError('this real diagnostic driver requires mbit10')
    lane = profile._verified_lane(store.get('mbit10', 'machine'), args.lane)
    runs = args.runs_dir.resolve()
    if not any(runs.is_relative_to(base) for base in
               ('/data/yanruj/EvolveSWDB_runs', '/data1/yanruj/EvolveSWDB_runs')):
        raise RuntimeError('raw root must be under an authorized EvolveSWDB_runs directory')
    def interrupted(signum, _frame):
        raise InterruptedError(f'diagnostic driver interrupted by signal {signum}')
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    return lane


def bounded(command, stdout_path, stderr_path, seconds, *, cwd, env=None):
    """Stream output and give nested evaluator cleanup a bounded grace period."""
    before = time.monotonic()
    with Path(stdout_path).open('w') as stdout, Path(stderr_path).open('w') as stderr:
        child = subprocess.Popen(command, cwd=cwd, env=env, stdout=stdout,
                                 stderr=stderr, start_new_session=True)
        try:
            child.wait(timeout=seconds)
        except BaseException:
            try: os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: child.wait(timeout=5)
            except subprocess.TimeoutExpired: pass
            # Also remove same-group descendants if the leader already exited.
            try: os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            child.wait()
            raise
    return {'returncode':child.returncode, 'host_wall_seconds':time.monotonic()-before}
