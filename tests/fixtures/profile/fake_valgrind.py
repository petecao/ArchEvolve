#!/usr/bin/env python3
"""Stands in for valgrind in Mac tests (Created 2026-09-22): copies the canned cachegrind
output next to it to the --cachegrind-out-file path. FAKE_VALGRIND_SLEEP=<s> sleeps first
(to test the cachegrind timeout); FAKE_VALGRIND_NO_OUTPUT=1 exits 0 without writing it."""
import os
import shutil
import sys
import time
from pathlib import Path

time.sleep(float(os.environ.get("FAKE_VALGRIND_SLEEP", "0")))
out = next(a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--cachegrind-out-file="))
if not os.environ.get("FAKE_VALGRIND_NO_OUTPUT"):
    shutil.copy(Path(__file__).with_name("cachegrind.out"), out)
print("==1== Cachegrind, a high-precision tracing profiler (fake)")
