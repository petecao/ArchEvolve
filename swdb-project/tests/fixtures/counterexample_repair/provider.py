"""Scripted rewriting provider for counterexample-guided repair tests (Probata ticket 13).

Created: 2026-10-14 ET. Emulates the Codex CLI's final-message file; runs in the provider workspace.
Every call that opens appends one line to the plan's `calls` file, so a test counts calls and sees what
the workspace held. Modes: `genuine` keeps the offload and changes code; `drop` removes the gather call;
`baseline` writes the baseline implementation back. Contract-fixture code only.
"""

import json
import re
import sys
from pathlib import Path

if "--version" in sys.argv:
    print("0.0-counterexample-repair-fixture")
    raise SystemExit(0)
plan = json.loads(Path(sys.argv[1]).read_text())
root = Path.cwd()
source = root / "src" / "bfs.cc"
text = source.read_text()
context = sorted(str(p.relative_to(root)) for p in (root / ".swdb-context").rglob("*") if p.is_file())
with open(plan["calls"], "a") as calls:
    calls.write(json.dumps({"mode": plan["mode"], "context": context}) + "\n")
if plan["mode"] == "baseline":
    # The baseline implementation back: the fixture function removed (protected placeholders stay).
    text = re.sub(r"\n// Contract-fixture code \(Probata ticket 13\): never compiled\.\n.*?\n}\n", "", text,
                  flags=re.S)
else:
    text = re.sub(r"int probata_round = (\d+);", lambda m: f"int probata_round = {int(m.group(1)) + 1};", text)
    if plan["mode"] == "drop":
        text = re.sub(r"\n *__dxc_gather\([^;]*\);", "", text)
source.write_text(text)
result = {"interpretation": f"Scripted {plan['mode']} repair of the counterexample.", "unresolved": []}
final = Path(sys.argv[sys.argv.index("--output-last-message") + 1])
final.write_text(json.dumps(result))
print(json.dumps({"type": "turn.completed", "usage": {"output_tokens": 10}}), flush=True)
