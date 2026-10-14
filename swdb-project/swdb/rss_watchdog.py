"""The RSS watchdog of one proof worker: a process tree's resident set size, its peak, and a cap.

Created: 2026-10-14 ET (Probata proof of concept ticket 57; design O9: an 8 GB RSS watchdog per
worker, because `ulimit -v` caps virtual address space, not RSS, and the JVM and GHC reserve far more
address space than they touch).

- `tree_rss_bytes(root)`: the summed RSS of `root` and every descendant. Linux reads `/proc` (no
  psutil on mbit10's system Python); macOS asks `ps` once per poll.
- `TreeWatch(root, cap_bytes)`: a polling thread that keeps the tree's peak and, above the cap,
  kills the tree (or only the descendants, when the root is the watching process itself).
- `run(command, ...)`: one command in its own session under a `TreeWatch`, with a timeout, an
  optional `ulimit -v` and a pinned CPU; returns exit code, peak RSS, wall and CPU time.
"""

import os
import resource
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

GIB = 1024 ** 3
DEFAULT_CAP_BYTES = 8 * GIB          # design O9
POLL_SECONDS = 0.1
_PAGE = os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else 4096


def _processes():
    """{pid: (ppid, rss_bytes)} of every process this user can see."""
    table = {}
    if sys.platform.startswith("linux"):
        for entry in os.scandir("/proc"):
            if not entry.name.isdigit():
                continue
            try:
                with open(f"/proc/{entry.name}/stat", "rb") as handle:
                    text = handle.read().decode(errors="replace")
            except OSError:
                continue
            fields = text[text.rfind(")") + 2:].split()       # after "pid (comm) "
            table[int(entry.name)] = (int(fields[1]), int(fields[21]) * _PAGE)
        return table
    try:
        import psutil              # the Mac (no /proc); `ps` is refused inside the agent sandbox
    except ImportError:
        out = subprocess.run(["ps", "-A", "-o", "pid=,ppid=,rss="], capture_output=True, text=True).stdout
        for line in out.splitlines():
            parts = line.split()
            if len(parts) == 3 and parts[0].isdigit():
                table[int(parts[0])] = (int(parts[1]), int(parts[2]) * 1024)
        return table
    for process in psutil.process_iter(["ppid", "memory_info"]):
        info = process.info
        if info.get("memory_info") is not None:
            table[process.pid] = (info["ppid"], info["memory_info"].rss)
    return table


def tree(root):
    """{pid: rss_bytes} of `root` and its descendants."""
    table = _processes()
    children = {}
    for pid, (ppid, _rss) in table.items():
        children.setdefault(ppid, []).append(pid)
    found, todo = {}, [root]
    while todo:
        pid = todo.pop()
        if pid in table and pid not in found:
            found[pid] = table[pid][1]
            todo.extend(children.get(pid, []))
    return found


def tree_rss_bytes(root):
    return sum(tree(root).values())


class TreeWatch:
    """Watch the tree under `root`; above `cap_bytes`, kill it and set `tripped`.

    `spare_root`: kill only the descendants (the watching process watches itself)."""
    active = True

    def __init__(self, root, cap_bytes, spare_root=False, interval=POLL_SECONDS):
        self.root, self.cap, self.spare_root, self.interval = root, cap_bytes, spare_root, interval
        self.peak, self.tripped, self.error = 0, False, None
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join()

    def _loop(self):
        while not self._stop.is_set():
            try:
                pids = tree(self.root)
            except Exception as exc:          # a watchdog that cannot read RSS must not fail silently
                self.error = f"the RSS watchdog cannot read the process tree: {type(exc).__name__}: {exc}"
                if not self.spare_root:
                    try:
                        os.killpg(self.root, signal.SIGKILL)     # `run` starts the root as a session leader
                    except (ProcessLookupError, PermissionError):
                        pass
                return
            self.peak = max(self.peak, sum(pids.values()))
            if self.peak > self.cap and not self.tripped:
                self.tripped = True
                self._kill(pids)
            self._stop.wait(self.interval)

    def _kill(self, pids):
        for pid in pids:
            if self.spare_root and pid == self.root:
                continue
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass


@dataclass
class Result:
    exit_code: int
    peak_rss_bytes: int
    out_of_memory: bool
    timed_out: bool
    wall_seconds: float
    cpu_seconds: float


def run(command, *, log, cap_bytes=DEFAULT_CAP_BYTES, timeout=None, cwd=None, env=None, core=None,
        address_space_cap=None):
    """Run `command` in its own session under the watchdog; stdout and stderr go to `log`.

    `core`: pin the command to this one CPU (Linux). `address_space_cap`: an `ulimit -v` in bytes."""
    def setup():
        if core is not None:
            os.sched_setaffinity(0, {core})
        if address_space_cap:
            resource.setrlimit(resource.RLIMIT_AS, (address_space_cap, address_space_cap))

    with open(log, "wb") as out:
        start = time.perf_counter()
        process = subprocess.Popen(command, stdout=out, stderr=subprocess.STDOUT, cwd=cwd, env=env,
                                   start_new_session=True, preexec_fn=setup)
        timed_out, status, usage = False, None, None
        with TreeWatch(process.pid, cap_bytes) as watch:
            while status is None:
                pid, wait_status, ru = os.wait4(process.pid, os.WNOHANG)
                if pid:
                    status, usage = wait_status, ru
                    break
                if timeout is not None and time.perf_counter() - start > timeout and not timed_out:
                    timed_out = True
                    watch._kill(tree(process.pid))
                time.sleep(0.02)
        process.returncode = os.waitstatus_to_exitcode(status)
        wall = time.perf_counter() - start
    if watch.error:
        raise RuntimeError(watch.error)
    scale = 1 if sys.platform == "darwin" else 1024             # ru_maxrss: bytes on macOS, KiB on Linux
    peak = max(watch.peak, usage.ru_maxrss * scale)            # floor for jobs shorter than one poll
    return Result(process.returncode, peak, watch.tripped, timed_out, wall, usage.ru_utime + usage.ru_stime)


def cap_from_environment(name="SWDB_WORKER_RSS_CAP_BYTES"):
    """The worker's RSS cap a lane batch hands `swdb prove` (None outside a lane batch)."""
    value = os.environ.get(name)
    return int(value) if value else None


def sha256(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
