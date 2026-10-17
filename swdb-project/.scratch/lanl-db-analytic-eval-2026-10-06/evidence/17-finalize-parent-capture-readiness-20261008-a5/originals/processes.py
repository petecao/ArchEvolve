"""Shutdown of evaluator-owned process groups. Updated: 2026-09-26 ET."""
import os
import signal
import subprocess


def stop_group(child, *, grace_seconds=20):
    """Reap an owned session leader and kill its remaining same-group children.

    Call only for a Popen started with start_new_session=True. A returned or
    reaped leader does not establish that its process group is empty.
    """
    if child is None:
        return
    try:
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            child.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            pass
    finally:
        # Also finish cleanup if a second interruption unwinds the grace wait.
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait(timeout=5)
