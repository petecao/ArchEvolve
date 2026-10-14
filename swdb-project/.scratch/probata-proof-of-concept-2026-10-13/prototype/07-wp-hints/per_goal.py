#!/usr/bin/env python3
# PROTOTYPE (Probata PoC ticket 07), throwaway. Created 2026-10-14 ET.
# Per-goal solver and time from WP's -wp-report-json (goals.json): which prover proved each goal.
# Usage: per_goal.py <run dir with goals.json> > per_goal.tsv
import json, sys, collections
from pathlib import Path

goals = json.loads((Path(sys.argv[1]) / "goals.json").read_text())
print("goal\tsmoke\tverdict\tpassed\tsolver\ttime_s")
by = collections.Counter()
for g in goals:
    ok = [p for p in g.get("provers", []) if p.get("success")]
    solver = ok[0]["prover"] if ok else "-"
    t = ok[0].get("time", 0) if ok else max((p.get("time", 0) for p in g.get("provers", [])), default=0)
    by[(g.get("smoke", False), g.get("verdict"), solver if not g.get("smoke") else "")] += 1
    print(f"{g['goal']}\t{int(bool(g.get('smoke')))}\t{g.get('verdict')}\t{int(bool(g.get('passed')))}\t{solver}\t{t:.3f}")
for k, v in sorted(by.items(), key=lambda kv: -kv[1]):
    print(f"# smoke={k[0]} verdict={k[1]} solver={k[2] or '-'}: {v}", file=sys.stderr)
