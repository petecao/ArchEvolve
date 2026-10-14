#!/bin/sh
# PROTOTYPE (Probata PoC ticket 07, continuation t07c), throwaway. Created 2026-10-14 ET.
# Syntax and proof check of the prompt examples (method change b): Frama-C 33 parse, then WP with the
# frozen provers at 30 s (no cache, fresh session). Run through verifier_run.py with the sandbox off.
# Usage: check_examples.sh <out_dir>
set -e
src=$(cd "$(dirname "$0")" && pwd)
out="$1"; mkdir -p "$out"; cp "$src/acsl_examples.c" "$src/errors_fixed.c" "$out/"
cd "$out"
for f in acsl_examples.c errors_fixed.c; do
  rm -rf "s-$f" && mkdir "s-$f"
  env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" opam exec --switch=framac-33 -- frama-c -machdep x86_64 "$f" \
    -wp -wp-cache none -wp-session "s-$f" -wp-prover alt-ergo,z3,cvc5 -wp-timeout 30 -wp-par 12 -wp-smoke-tests \
    -wp-report-json "goals-$f.json" -then -report > "wp-$f.log" 2>&1 || { echo "FAIL $f"; tail -20 "wp-$f.log"; exit 1; }
  python3 - "goals-$f.json" "$f" <<'EOF'
import json, sys
g = json.load(open(sys.argv[1]))
bad = [x["goal"] for x in g if (not x.get("smoke") and not x.get("passed")) or (x.get("smoke") and not x.get("passed"))]
print(sys.argv[2], "goals", sum(1 for x in g if not x.get("smoke")), "smoke", sum(1 for x in g if x.get("smoke")),
      "NOT OK:" if bad else "all proven, smoke tests passed", bad)
EOF
done
