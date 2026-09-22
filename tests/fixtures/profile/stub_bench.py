#!/usr/bin/env python3
"""A stub benchmark that prints gapbs-style lines (Created 2026-09-22), for profile tests.

It reads -n (trials), -v (verify), -l (log steps), and ignores the graph arguments. Trial
times fall with OMP_NUM_THREADS up to 4 threads, then stay flat. STUB_SLEEP=<s> makes it
sleep before printing, and STUB_SLEEP_TIMING=<s> only when not verifying (to test timeouts);
STUB_FAIL_VERIFY=1 makes verification fail; STUB_FAIL_LOG=1 makes the -l run exit 1 after
printing its step lines.
"""
import os
import sys
import time

args = sys.argv[1:]
trials = int(args[args.index("-n") + 1]) if "-n" in args else 16
threads = int(os.environ.get("OMP_NUM_THREADS", "1"))
time.sleep(float(os.environ.get("STUB_SLEEP", "0")))
if "-v" not in args:
    time.sleep(float(os.environ.get("STUB_SLEEP_TIMING", "0")))
print("Read Time:           0.00010")
print("Build Time:          0.00020")
print("Graph has 8 nodes and 9 undirected edges for degree: 1")
for trial in range(trials):
    if "-l" in args:
        for step, error in enumerate([0.5, 0.05, 0.00009]):
            print(f"{step:5d}{error:23.5f}")
    print(f"{'Trial Time:':<21}{0.08 / min(threads, 4) + 0.001 * trial:3.5f}")
    if "-v" in args:
        print(f"{'Verification:':<21}{'FAIL' if os.environ.get('STUB_FAIL_VERIFY') else 'PASS':>7}")
        print(f"{'Verification Time:':<21}{0.0001:3.5f}")
print(f"{'Average Time:':<21}{0.05:3.5f}")
if "-l" in args and os.environ.get("STUB_FAIL_LOG"):
    sys.exit(1)
