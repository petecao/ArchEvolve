"""A stand-in `crux-llvm` for scripted faults of the crux-llvm adapters (Probata PoC 23 tests). Created: 2026-10-14 ET.

Run as SWDB_CRUX="<python> fake_crux.py". `--version` answers crux-llvm 0.12. FAKE_CRUX_MODES picks the fault per
form: `cxx=<mode>,c=<mode>` (the form is read from the job's folder, crux-llvm-cxx or crux-llvm-c); a form not
named runs the real crux-llvm (FAKE_CRUX_REAL, a command line). Modes:
- parse_error: crux's bitcode reader refuses the file; unsupported: an unsupported LLVM construct;
- solver_error: the SMT solver fails; crash: exit 139 with no goal status; silent: exit 0 with no goal status;
- sleep: run past any small wall budget; spurious: a disproved named property (FAKE_CRUX_PROPERTY) whose
  counterexample gives every oracle value 0, so it cannot replay on the C++.
"""
import os
import re
import shlex
import subprocess
import sys
import time

args = sys.argv[1:]
if "--version" in args:
    print("[Crux] version: 0.9, crux-llvm version: 0.12")
    sys.exit(0)
bitcode = args[-1]
form = "cxx" if "/crux-llvm-cxx/" in bitcode else "c"
modes = dict(part.split("=", 1) for part in os.environ.get("FAKE_CRUX_MODES", "").split(",") if "=" in part)
mode = modes.get(form)
if mode is None:
    sys.exit(subprocess.run([*shlex.split(os.environ["FAKE_CRUX_REAL"]), *args]).returncode)
if mode == "parse_error":
    print("Invalid magic number\n  bitstream\n  llvm-bitstream")
    sys.exit(1)
if mode == "unsupported":
    print("[Crux] Simulating function main\n[Crux] unsupported LLVM instruction: callbr")
    sys.exit(1)
if mode == "solver_error":
    print("[Crux] Attempting to prove verification conditions.\n[Crux] z3 error: the solver process exited unexpectedly")
    sys.exit(1)
if mode == "crash":
    print("Segmentation fault while translating the module")
    sys.exit(139)
if mode == "silent":
    sys.exit(0)
if mode == "sleep":
    time.sleep(120)
    sys.exit(0)
if mode == "spurious":
    out = next(a.split("=", 1)[1] for a in args if a.startswith("--output-directory="))
    os.makedirs(out, exist_ok=True)
    with open(out + "/counter-example-7.c", "w") as handle:
        handle.write("const char* crucible_names_int64_t[] = { };\nint64_t const crucible_values_int64_t[] = { };\n")
    print("[Crux] Found counterexample for verification goal\n"
          f"[Crux]   {os.environ['FAKE_CRUX_PROPERTY']}:7:0: error: in swdb_run\n[Crux]   crucible_assert\n[Crux] \n"
          "[Crux] Found counterexample for verification goal\n[Crux]   swdb_reach.end:8:0: error: in swdb_run\n"
          "[Crux]   crucible_assert\n[Crux] Overall status: Invalid.\n[Crux] Goal status:\n[Crux]   Total: 3\n"
          "[Crux]   Proved: 1\n[Crux]   Disproved: 2\n[Crux]   Incomplete: 0\n[Crux]   Unknown: 0")
    sys.exit(1)
print(f"fake_crux: unknown mode {mode!r}", file=sys.stderr)
sys.exit(2)
