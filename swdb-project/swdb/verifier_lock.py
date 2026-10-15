"""The machine-wide verifier lock: at most N real verifier jobs at a time on a host (the Mac rule).

Created: 2026-10-14 ET (Probata proof of concept ticket 21). `swdb prove` takes it before any real
verifier job; every real adapter (21 WP, 22 CBMC, 46 CIVL, 47 GenMC) inherits it through `swdb prove`
and none rebuilds it. The scripted adapter takes no lock. Format: docs/reference/format-v0.4-c-lowering-wp.md.

- Same protocol as the Mac's shared runner `verifier_run.py`, so the two exclude each other: the lock is
  a directory created with `mkdir` (atomic) holding an `owner` file (`pid=<pid>`), and waiters queue
  first-in, first-out as ticket files `<ns time>-<pid>` in the queue folder beside it. A waiting job
  queues; it never fails. A lock whose holder is dead and that is older than 10 s is stale and removed.
- Where: `SWDB_VERIFIER_LOCK` (a path), else `/tmp/claude/swdb-verifier.lock` when `/tmp/claude` exists
  (the Mac), else `/tmp/swdb-verifier-<uid>.lock`. The queue is the same path with `.queue` for `.lock`.
- Slots (2026-10-14, Yan-Ru approved two): the machine policy file `<lock without .lock>.slots` (one
  integer, default 1) sets N. Slot 1 is the lock path itself; slot k > 1 is `<name>.slot<k>.lock`. A waiter
  among the first N live tickets takes any free slot, so at most N jobs run and the queue stays FIFO.
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


def _stem(lock):
    return lock.name[:-len(".lock")] if lock.name.endswith(".lock") else lock.name


def slots(lock=None):
    """The configured slot count (policy file beside the lock; default 1, never below 1)."""
    lock = Path(lock) if lock else path()
    try:
        return max(1, int(lock.with_name(f"{_stem(lock)}.slots").read_text().split()[0]))
    except (OSError, ValueError, IndexError):
        return 1


def slot_paths(lock=None):
    lock = Path(lock) if lock else path()
    return [lock] + [lock.with_name(f"{_stem(lock)}.slot{k}.lock") for k in range(2, slots(lock) + 1)]


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
    ancestors = _ancestors()
    held = [s for s in slot_paths(lock) if s.is_dir() and _owner_pid(s) in ancestors]
    nested = bool(held)
    started = time.monotonic()
    if nested:
        target = held[0] / "nested"
        _acquire([target], owner, held[0] / "nested.queue", 1)
    else:
        target = _acquire(slot_paths(lock), owner, _queue(lock), len(slot_paths(lock)))
    try:
        yield {"lock": str(target), "nested": nested, "waited_seconds": round(time.monotonic() - started, 3)}
    finally:
        if _owner_pid(target) == os.getpid():
            shutil.rmtree(target, ignore_errors=True)


def _acquire(candidates, owner, queue, admit):
    """Queue FIFO; once among the first `admit` live tickets, take the first free candidate. Returns it."""
    candidates[0].parent.mkdir(parents=True, exist_ok=True)
    queue.mkdir(parents=True, exist_ok=True)
    ticket = queue / f"{time.time_ns():020d}-{os.getpid()}"
    ticket.write_text(f"owner={owner} pid={os.getpid()}\n")
    try:
        while True:
            if ticket.name in _live(queue)[:admit]:
                for lock in candidates:
                    try:
                        lock.mkdir()
                        (lock / "owner").write_text(f"owner={owner} pid={os.getpid()} "
                                                    f"since={time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
                        return lock
                    except FileExistsError:
                        _clear_if_stale(lock)
                    except FileNotFoundError:             # nested lock whose holder just released the outer one
                        raise RuntimeError(f"the verifier lock {lock.parent} was released under a nested job")
            time.sleep(POLL_SECONDS)
    finally:
        ticket.unlink(missing_ok=True)


def _live(queue):
    """Live tickets in FIFO order; dead waiters' tickets are removed."""
    live = []
    for name in sorted(os.listdir(queue)):
        try:
            pid = int(name.split("-")[1])
        except (IndexError, ValueError):
            pid = None
        if pid is not None and _alive(pid):
            live.append(name)
        else:
            (queue / name).unlink(missing_ok=True)
    return live


def _first_live(queue):
    live = _live(queue)
    return live[0] if live else None


def _clear_if_stale(lock):
    pid = _owner_pid(lock)
    if pid is not None and _alive(pid):
        return
    try:
        if time.time() - lock.stat().st_mtime > STALE_SECONDS:
            shutil.rmtree(lock, ignore_errors=True)
    except FileNotFoundError:
        pass
