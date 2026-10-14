"""A stand-in `cbmc` for scripted faults of the CBMC adapter (Probata PoC 22 tests). Created: 2026-10-14 ET.

Run as SWDB_CBMC="<python> fake_cbmc.py". `--version` answers 6.11.0. Otherwise FAKE_CBMC_MODE picks the fault:
- parse_error: CBMC's parsing error, exit 6; solver_error: a SAT solver error, exit 6;
- crash: exit 139 with no result; silent: exit 0 with no property result (an outcome with no class);
- sleep: run past any small wall budget; spurious: a failed property (FAKE_CBMC_PROPERTY) whose trace's oracle
  values are all zero, so it cannot replay on the C++;
- wrap: run the real CBMC (FAKE_CBMC_REAL, a command line) and append start/end times to FAKE_CBMC_TIMES.
"""
import json
import os
import shlex
import subprocess
import sys
import time

args = sys.argv[1:]
if "--version" in args:
    print("6.11.0 (cbmc-6.11.0)")
    sys.exit(0)
mode = os.environ.get("FAKE_CBMC_MODE", "")


def emit(messages, code):
    print(json.dumps(messages))
    sys.exit(code)


if mode == "wrap":
    with open(os.environ["FAKE_CBMC_TIMES"], "a") as times:
        times.write(f"start {time.time():.6f} {os.getpid()}\n")
    done = subprocess.run([*shlex.split(os.environ["FAKE_CBMC_REAL"]), *args])
    with open(os.environ["FAKE_CBMC_TIMES"], "a") as times:
        times.write(f"end {time.time():.6f} {os.getpid()}\n")
    sys.exit(done.returncode)
if mode == "parse_error":
    emit([{"messageText": "job.c:3:1: syntax error before 'int'", "messageType": "ERROR"},
          {"messageText": "PARSING ERROR", "messageType": "ERROR"}], 6)
if mode == "solver_error":
    emit([{"messageText": "SAT checker: the solver returned an error", "messageType": "ERROR"}], 6)
if mode == "crash":
    print("Segmentation fault while building the formula")
    sys.exit(139)
if mode == "silent":
    emit([{"messageText": "CBMC version 6.11.0", "messageType": "STATUS-MESSAGE"}], 0)
if mode == "sleep":
    time.sleep(60)
    sys.exit(0)
if mode == "spurious":
    trace = [{"stepType": "assignment", "lhs": "goto_symex$$return_value$$swdb_next", "hidden": False,
              "value": {"data": "0ll", "name": "integer"}} for _ in range(5)]
    emit([{"result": [
        {"property": "main.assertion.1", "description": os.environ["FAKE_CBMC_PROPERTY"], "status": "FAILURE",
         "sourceLocation": {"function": "swdb_run", "line": "1"}, "trace": trace},
        {"property": "main.assertion.2", "description": "swdb_reach.end", "status": "FAILURE",
         "sourceLocation": {"function": "swdb_run", "line": "2"}, "trace": trace}]},
        {"messageText": "VERIFICATION FAILED", "messageType": "STATUS-MESSAGE"}], 10)
print(f"fake_cbmc: unknown FAKE_CBMC_MODE {mode!r}", file=sys.stderr)
sys.exit(2)
