"""The machine-wide verifier lock: one real verifier job at a time on a host (the Mac rule).

Created: 2026-10-14 ET (Probata proof of concept ticket 21). `swdb prove` takes it before any real
verifier job; every real adapter (21 WP, 22 CBMC, 46 CIVL, 47 GenMC) inherits it through `swdb prove`
and none rebuilds it. The scripted adapter takes no lock. Format: docs/reference/format-v0.4-c-lowering-wp.md.

- Same protocol as the Mac's shared runner `verifier_run.py`, so the two exclude each other: the lock is
  a directory created with `mkdir` (atomic) holding an `owner` file (`pid=<pid>`), and waiters queue
  first-in, first-out as ticket files `<ns time>-<pid>` in the queue folder beside it. A waiting job
  queues; it never fails. A lock whose holder is dead and that is older than 10 s is stale and removed.
- Where: `SWDB_VERIFIER_LOCK` (a path), else `/tmp/claude/swdb-verifier.lock` when `/tmp/claude` exists
  (the Mac), else `/tmp/swdb-verifier-<uid>.lock`. The queue is the same path with `.queue` for `.lock`.
- Nested hold: when the holder is an ancestor of this process (a test run inside `verifier_run.py`), this
  process already runs inside the one machine-wide job, so it takes the nested lock `<lock>/nested`
  instead, by the same protocol. Jobs inside one holder still never overlap.
"""

import os
import shutil
import time
from contextlib import contextmanager
from pathlib import Path

STALE_SECONDS = 10
POLL_SECONDS = 0.25


def path():
    named = os.environ.get("SWDB_VERIFIER_LOCK")
    if named:
        return Path(named)
    if Path("/tmp/claude").is_dir():
        return Path("/tmp/claude/swdb-verifier.lock")
    return Path(f"/tmp/swdb-verifier-{os.getuid()}.lock")


def _queue(lock):
    name = lock.name[:-len(".lock")] if lock.name.endswith(".lock") else lock.name
    return lock.with_name(f"{name}.queue")


def _owner_pid(lock):
    try:
        text = (lock / "owner").read_text()
        return int(text.split("pid=")[1].split()[0])
    except (OSError, IndexError, ValueError):
        return None


def _alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _ancestors():
    try:
        import psutil
        return {p.pid for p in psutil.Process(os.getpid()).parents()}
    except Exception:                                    # no psutil, or a process vanished: assume none
        return set()


@contextmanager
def hold(owner, lock=None):
    """Hold the machine-wide verifier lock (or, inside its holder's process tree, the nested one).

    Yields {lock, nested, waited_seconds}."""
    lock = Path(lock) if lock else path()
    holder = _owner_pid(lock) if lock.is_dir() else None
    nested = holder is not None and holder in _ancestors()
    target = lock / "nested" if nested else lock
    started = time.monotonic()
    _acquire(target, owner)
    try:
        yield {"lock": str(target), "nested": nested, "waited_seconds": round(time.monotonic() - started, 3)}
    finally:
        if _owner_pid(target) == os.getpid():
            shutil.rmtree(target, ignore_errors=True)


def _acquire(lock, owner):
    queue = _queue(lock) if lock.name != "nested" else lock.parent / "nested.queue"
    lock.parent.mkdir(parents=True, exist_ok=True)
    queue.mkdir(parents=True, exist_ok=True)
    ticket = queue / f"{time.time_ns():020d}-{os.getpid()}"
    ticket.write_text(f"owner={owner} pid={os.getpid()}\n")
    try:
        while True:
            if _first_live(queue) == ticket.name:
                try:
                    lock.mkdir()
                    (lock / "owner").write_text(f"owner={owner} pid={os.getpid()} "
                                                f"since={time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
                    return
                except FileExistsError:
                    _clear_if_stale(lock)
                except FileNotFoundError:                 # nested lock whose holder just released the outer one
                    raise RuntimeError(f"the verifier lock {lock.parent} was released under a nested job")
            time.sleep(POLL_SECONDS)
    finally:
        ticket.unlink(missing_ok=True)


def _first_live(queue):
    for name in sorted(os.listdir(queue)):
        try:
            pid = int(name.split("-")[1])
        except (IndexError, ValueError):
            pid = None
        if pid is not None and _alive(pid):
            return name
        (queue / name).unlink(missing_ok=True)
    return None


def _clear_if_stale(lock):
    pid = _owner_pid(lock)
    if pid is not None and _alive(pid):
        return
    try:
        if time.time() - lock.stat().st_mtime > STALE_SECONDS:
            shutil.rmtree(lock, ignore_errors=True)
    except FileNotFoundError:
        pass
