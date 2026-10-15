"""The RSS watchdog's timeout and the CBMC replay's fault matching (code review 2026-10-14 ET)."""

import os
import sys
import time

from swdb import rss_watchdog
from swdb.cbmc_adapter import _same_fault


def test_a_timeout_kills_every_process_in_the_jobs_session(tmp_path):
    pids = tmp_path / "pids"
    child = f"import os, time; open({str(pids)!r}, 'a').write(f'{{os.getpid()}}\\n'); time.sleep(60)"
    code = (f"import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', {child!r}]); "
            f"subprocess.Popen([sys.executable, '-c', {child!r}]); time.sleep(60)")
    started = time.monotonic()
    result = rss_watchdog.run([sys.executable, "-c", code], log=tmp_path / "log", timeout=1.0)
    assert result.timed_out and time.monotonic() - started < 30
    time.sleep(0.5)
    for pid in map(int, pids.read_text().split()):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            continue
        raise AssertionError(f"child {pid} outlived the timeout")


def test_stdin_reaches_the_job(tmp_path):
    given = tmp_path / "in.txt"
    given.write_text("7 8\n")
    with open(given) as stdin:
        result = rss_watchdog.run([sys.executable, "-c", "print(input())"], log=tmp_path / "log", stdin=stdin)
    assert result.exit_code == 0 and (tmp_path / "log").read_text().strip() == "7 8"


def test_a_sanitizer_report_matches_only_its_own_kind_of_cbmc_check():
    assert _same_fault("f.overflow.2", "x.cc:3:5: runtime error: signed integer overflow") is True
    assert _same_fault("f.overflow.2", "ERROR: AddressSanitizer: heap-buffer-overflow") is True   # 'overflow'
    assert _same_fault("f.division-by-zero.1", "runtime error: signed integer overflow") is False
    assert _same_fault("f.array_bounds.1", "ERROR: AddressSanitizer: heap-buffer-overflow") is True
    assert _same_fault("f.assertion.1", "runtime error: anything") is None

