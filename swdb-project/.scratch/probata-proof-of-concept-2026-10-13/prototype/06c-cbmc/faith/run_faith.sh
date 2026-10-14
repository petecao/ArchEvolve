#!/bin/sh
# Ticket 06 continuation (CBMC box), 2026-10-14 ET. Throwaway. Faithfulness test 1: the C lowering
# of each unit agrees with ticket 06's C++ unit on concrete inputs.
#   * both sides link the same C stubs (dx100_stubs.h) and the same native harness (harness.h);
#   * every input of the bounded domain (harness.h SWDB_NATIVE; tile memory zero) runs on both
#     sides, safe build and every control build (13 builds per side, 2 units);
#   * each run prints: inputs | failed CHECK (ends the run) | failed P2 properties | hash of the
#     final state (queue, parent, tile memory, the whole hazard state) and of the DX100 call trace
#     (every call with its arguments, in order);
#   * pass = the two sides print identical lines for every build (sha256 of the stream compared;
#     on a mismatch the first differing lines are shown).
# Plus ticket 06's SAW concrete input (diagnostics 1 and 6), full call trace, both sides.
# Native runs only (no verifier): not under verifier_run.py. Output: $OUT (default
# /tmp/claude/probata-runs/t06c/faith); the per-run streams are not kept (sha256 and counts are).
set -eu
HERE=$(cd "$(dirname "$0")/.." && pwd)
SWDB=$(cd "$HERE/../../../.." && pwd)
OUT=${OUT:-/tmp/claude/probata-runs/t06c/faith}
B=$(mktemp -d "${TMPDIR:-/tmp}/t06c-faith.XXXXXX")
CLANG=/opt/homebrew/opt/llvm/bin/clang
CLANGXX=/opt/homebrew/opt/llvm/bin/clang++
mkdir -p "$OUT"
# build | unit | C flags | C++ flags
BUILDS='peter_safe|peter||
peter_dropped_wait|peter|-DSWDB_DXC_FAULT_DROPPED_WAIT|-DSWDB_DXC_FAULT_DROPPED_WAIT
peter_read_before_wait|peter|-DSWDB_DXC_FAULT_READ_BEFORE_WAIT|-DSWDB_DXC_FAULT_READ_BEFORE_WAIT
peter_index_wrap|peter|-DSWDB_DXC_FAULT_INDEX_WRAP|-DSWDB_DXC_FAULT_INDEX_WRAP
peter_forged_frontier|peter|-DSWDB_DXC_FAULT_FORGED_FRONTIER_V2|-DSWDB_DXC_FAULT_FORGED_FRONTIER_V2
peter_dropped_continuation|peter|-DSWDB_DXC_FAULT_DROPPED_CONTINUATION|-DSWDB_DXC_FAULT_DROPPED_CONTINUATION
peter_chunk_off_by_one|peter|-DSWDB_DXC_FAULT_CHUNK_OFF_BY_ONE|-DSWDB_DXC_FAULT_CHUNK_OFF_BY_ONE
peter_skipped_cas_recheck|peter|-DSWDB_DXC_FAULT_SKIPPED_CAS_RECHECK|-DSWDB_DXC_FAULT_SKIPPED_CAS_RECHECK
maa_safe|maa||
maa_wait_deleted|maa|-DMAA_CONTROL=1|-DMAA_CONTROL=1
maa_old_wait_rule|maa|-DMAA_CONTROL=2 -DSWDB_OLD_WAIT_RULE|-DMAA_CONTROL=2 -DSWDB_OLD_WAIT_RULE
maa_cpu_read_parent|maa|-DMAA_CONTROL=3|-DMAA_CONTROL=3
maa_wait_tile6|maa|-DMAA_CONTROL=4|-DMAA_CONTROL=4
maa_wait_tile7|maa|-DMAA_CONTROL=5|-DMAA_CONTROL=5'
SUM="$OUT/faith_summary.txt"
: > "$SUM"
fail=0
echo "$BUILDS" | while IFS='|' read -r name unit cflags xflags; do
  case "$unit" in peter) U=SWDB_UNIT_PETER;; maa) U=SWDB_UNIT_MAA;; esac
  "$CLANG" -std=c11 -O1 -Wall -DSWDB_NATIVE -DSWDB_TRACE $cflags "$HERE/unit_$unit.c" -o "$B/c_$name"
  "$CLANGXX" -std=c++17 -O1 -DSWDB_NATIVE -DSWDB_TRACE -D$U $xflags -I"$HERE/faith/shim" -I"$SWDB/library/dx100" \
    "$HERE/faith/faith_cxx.cpp" -o "$B/x_$name"
  "$B/c_$name" > "$B/c_$name.out" 2> "$B/c_$name.err"
  "$B/x_$name" > "$B/x_$name.out" 2> "$B/x_$name.err"
  hc=$(shasum -a 256 < "$B/c_$name.out" | cut -c1-64); hx=$(shasum -a 256 < "$B/x_$name.out" | cut -c1-64)
  runs=$(cat "$B/c_$name.err")
  checks=$(cut -d'|' -f2 "$B/c_$name.out" | sort | uniq -c | tr -s ' ' | tr '\n' ';')
  props=$(cut -d'|' -f3 "$B/c_$name.out" | sort | uniq -c | tr -s ' ' | tr '\n' ';')
  if [ "$hc" = "$hx" ]; then verdict=AGREE; else verdict=DIFFER; fi
  printf '%s %s c=%s cxx=%s %s\n  checks:%s\n  p2:%s\n' "$verdict" "$name" "$hc" "$hx" "$runs" "$checks" "$props" >> "$SUM"
  if [ "$verdict" = DIFFER ]; then diff "$B/c_$name.out" "$B/x_$name.out" | head -6 >> "$SUM"; fi
  # ticket 06's SAW concrete input, full trace (safe builds only)
  case "$name" in *_safe)
    "$B/c_$name" concrete > "$OUT/concrete_${unit}_c.txt"; "$B/x_$name" concrete > "$OUT/concrete_${unit}_cxx.txt"
    if cmp -s "$OUT/concrete_${unit}_c.txt" "$OUT/concrete_${unit}_cxx.txt"; then echo "AGREE concrete_$unit (SAW diag input)" >> "$SUM";
    else echo "DIFFER concrete_$unit" >> "$SUM"; fi;;
  esac
done
rm -rf "$B"
cat "$SUM"
! grep -q '^DIFFER' "$SUM"
