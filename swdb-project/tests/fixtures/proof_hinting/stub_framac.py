"""A stand-in `frama-c` for the proof_hinting wrapper tests (Probata PoC ticket 34). Created: 2026-10-14 ET.

Run as SWDB_FRAMA_C="<python> stub_framac.py <log>". `-version` answers 33.0. A WP job appends one JSON line
to <log> (argv, start and end time, the WP input's text) and writes one valid goal, or, when the WP input
holds `STUB_ALLOCATE`, holds 600 MB of memory for 5 s (for the RSS watchdog).
"""
import json
import sys
import time
from pathlib import Path

log, args = sys.argv[1], sys.argv[2:]
if "-version" in args:
    print("33.0 (Arsenic)")
    raise SystemExit(0)
started = time.time()
source = next(a for a in args if a.endswith(".c"))
text = Path(source).read_text()
if "STUB_ALLOCATE" in text:
    block = bytearray(600 * 1024 * 1024)
    for index in range(0, len(block), 4096):
        block[index] = 1
    time.sleep(5)
time.sleep(0.2)
goal = {"goal": "typed_f_ensures", "property": "f_ensures", "file": source, "line": 4, "function": "f",
        "smoke": False, "passed": True, "verdict": "valid", "provers": [{"prover": "Alt-Ergo:2.6.4", "time": 0.01,
                                                                          "success": 1}]}
Path(args[args.index("-wp-report-json") + 1]).write_text(json.dumps([goal]))
Path(args[args.index("-report-csv") + 1]).write_text(
    "directory\tfile\tline\tfunction\tproperty kind\tstatus\tproperty\n"
    f".\t{source}\t4\tf\tpostcondition\tValid\t\\result >= 0\n")
with open(log, "a") as handle:
    handle.write(json.dumps({"argv": args, "start": started, "end": time.time(), "input": text}) + "\n")
print("[wp] [Valid] typed_f_ensures (Alt-Ergo)")
