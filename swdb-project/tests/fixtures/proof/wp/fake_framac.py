"""A stand-in `frama-c` for scripted faults of the WP adapter (Probata PoC 21 tests). Created: 2026-10-14 ET.

Run as SWDB_FRAMA_C="<python> fake_framac.py". `-version` answers 33.0. Otherwise FAKE_WP_MODE picks the fault:
- unknown: one goal unknown, its property Unknown; solver_error: one goal failed (a solver error);
- crash: an internal Frama-C error, exit 125; silent: exit 0 with no report (an outcome with no class);
- user_error: a Frama-C user error, exit 1 (ticket 35; WP goal generation with -wp-prover none passes through);
- wrap: run the real Frama-C (FAKE_WP_REAL, a command line) and append start/end times to FAKE_WP_TIMES.
"""
import json
import os
import shlex
import subprocess
import sys
import time

args = sys.argv[1:]
if "-version" in args:
    print("33.0 (Arsenic)")
    sys.exit(0)
mode = os.environ.get("FAKE_WP_MODE", "")
no_prover = "-wp-prover" in args and args[args.index("-wp-prover") + 1] == "none"
if "-wp" not in args or no_prover:        # not a WP job (a parse-only check, the hint check): the real Frama-C
    sys.exit(subprocess.run([*shlex.split(os.environ["FAKE_WP_REAL"]), *args]).returncode)


def target(flag):
    return args[args.index(flag) + 1]


if mode == "wrap":
    with open(os.environ["FAKE_WP_TIMES"], "a") as times:
        times.write(f"start {time.time():.6f} {os.getpid()}\n")
    done = subprocess.run([*shlex.split(os.environ["FAKE_WP_REAL"]), *args])
    with open(os.environ["FAKE_WP_TIMES"], "a") as times:
        times.write(f"end {time.time():.6f} {os.getpid()}\n")
    sys.exit(done.returncode)
if mode == "crash":
    print("[kernel] Parsing wp_input.c (with preprocessing)\n[kernel] Current source was: wp_input.c:3\n"
          "  The full backtrace is:\n[kernel] Unexpected error (Stack_overflow).\n  Please report as 'crash'")
    sys.exit(125)
if mode == "user_error":                  # ticket 35: WP's own user error (hints are parsed before WP runs)
    print("[kernel] Parsing wp_input.c (with preprocessing)\n[kernel] wp_input.c:3: User Error: scripted fault\n"
          "[kernel] Frama-C aborted: invalid user input.")
    sys.exit(1)
if mode == "silent":
    print("[kernel] Parsing wp_input.c (with preprocessing)")
    sys.exit(0)
verdict = {"unknown": "unknown", "solver_error": "failed"}[mode]
# The goal belongs to the unit's function (-wp-fct): the reader keeps only the unit's goals (ticket 24).
f = next((a.split("=", 1)[1] for a in args if a.startswith("-wp-fct=")), "f")
goal = {"goal": f"typed_real_{f}_ensures", "property": f"{f}_ensures", "file": "wp_input.c", "line": 4, "function": f,
        "smoke": False, "passed": False, "verdict": verdict,
        "provers": [{"prover": "Z3:5.1.0", "time": 0.01, "success": 0}]}
with open(target("-wp-report-json"), "w") as out:
    json.dump([goal], out)
if os.environ.get("SWDB_PROOF_REPORT_OUT"):
    with open(os.environ["SWDB_PROOF_REPORT_OUT"], "w") as out:
        json.dump({"version": "1", "complete": True, "goals": [{**goal, "results": [verdict]}], "properties": []}, out)
with open(target("-report-csv"), "w") as out:
    out.write("directory\tfile\tline\tfunction\tproperty kind\tstatus\tproperty\n"
              f".\twp_input.c\t4\t{f}\tpostcondition\tUnknown\t\\result >= 0\n")
print(f"[wp] [{verdict.capitalize()}] typed_real_{f}_ensures (Z3)")
