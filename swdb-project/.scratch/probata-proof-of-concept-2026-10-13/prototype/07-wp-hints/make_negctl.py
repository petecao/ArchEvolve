#!/usr/bin/env python3
# PROTOTYPE (Probata PoC ticket 07), throwaway. Created 2026-10-14 ET.
# Negative control: a copy of the stand-in with its covering wait on the parent gather's result tile
# (`__dxc_wait(c.tile[5]);`) removed. Only that statement changes; anchors stay.
# Usage: make_negctl.py <out.c>
import sys
from pathlib import Path

src = (Path(__file__).resolve().parent / "standin" / "tdstep_standin.c").read_text()
target = "          __dxc_wait(c.tile[5]);\n"
assert src.count(target) == 1, "covering wait not found exactly once"
Path(sys.argv[1]).write_text(src.replace(target, "", 1))
print("removed:", target.strip())
