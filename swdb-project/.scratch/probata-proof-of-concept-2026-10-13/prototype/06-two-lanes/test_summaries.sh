#!/bin/sh
# Ticket 06 spike (b), 2026-10-14 ET. Throwaway. Runs the summary tests (test_summaries.saw)
# through the verifier lock. Exit 0 = both tests pass.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
RUNS=${RUNS:-/tmp/claude/probata-runs/t06}
SAWBIN=$HOME/opt/verifiers/saw-1.6/saw-1.6-macos-15-ARM64-with-solvers/bin
d=$(mktemp -d "$RUNS/scratch-test.XXXXXX")
/opt/homebrew/opt/llvm/bin/clang++ -std=c++17 -c -emit-llvm -g -O0 "$HERE/test_summaries.cpp" -o "$d/test.bc"
cp "$HERE/ghost.cry" "$HERE/summaries.saw" "$HERE/units.saw" "$HERE/test_summaries.saw" "$d/"
(cd "$d" && PATH="$SAWBIN:$PATH" /tmp/claude/probata-tools/verifier_run.py --log "$RUNS/test_summaries.log" \
   --owner t06 --timeout 300 -- "$SAWBIN/saw" test_summaries.saw) || true
rm -rf "$d"
grep -q 'TEST range_only: PASS' "$RUNS/test_summaries.log" && grep -q 'TEST range_body: PASS' "$RUNS/test_summaries.log" \
  && grep -q 'TEST range_body_symbolic_parent: PASS' "$RUNS/test_summaries.log"
