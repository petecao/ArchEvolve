"""2026-10-15 ET. Serialize compiler/native control workers; not a proof guard.

Usage: pinned-python this-file -- existing-guard-and-command ...
The command must retain its own RSS/time watchdog. Actual formal jobs require
the separate coordinator admission and verifier lease; this lock admits none.
"""
import fcntl
import subprocess
import sys

assert len(sys.argv) > 2 and sys.argv[1] == "--", "expected -- COMMAND ..."
with open('/private/tmp/probata-mac-compiler-worker-b.lock', 'a+') as lease:
    fcntl.flock(lease, fcntl.LOCK_EX)
    child = subprocess.Popen(sys.argv[2:], pass_fds=(lease.fileno(),))
    status = child.wait()
raise SystemExit(status if status >= 0 else 128 - status)
