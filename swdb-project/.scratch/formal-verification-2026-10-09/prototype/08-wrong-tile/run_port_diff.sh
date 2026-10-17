#!/bin/zsh
# PROTOTYPE (ticket 08): differential check of the port against the real strict layer.
# Builds tests/fixtures/strict_wait_rule.cc four ways (real/port x old/gem5 rule) per TILE_SIZE,
# runs every scenario, and diffs stdout + exit code.
set -u
ROOT=../../../..
FIX=$ROOT/tests/fixtures/strict_wait_rule.cc
SCEN=(store_source_wait store_result_wait store_no_wait source_ready_before_wait condition_only_wait range_filled range_unfilled read_offload_chunk stall_source stall_condition constant_hold)
mkdir -p diffbuild; fail=0
for ts in 4 16 1024; do for rule in old gem5; do
  def=(); [[ $rule == gem5 ]] && def=(-DSWDB_STRICT_WAIT_RULE_GEM5)
  g++-16 -std=c++17 -O1 -fopenmp -DTILE_SIZE=$ts $def -I $ROOT/library/dx100/strict $FIX -o diffbuild/real-$ts-$rule || exit 3
  g++-16 -std=c++17 -O1 -DTILE_SIZE=$ts $def -I port/include $FIX -o diffbuild/port-$ts-$rule || exit 3
  for s in $SCEN; do
    a=$(./diffbuild/real-$ts-$rule $s 2>&1; echo "exit=$?"); b=$(./diffbuild/port-$ts-$rule $s 2>&1; echo "exit=$?")
    if [[ "$a" != "$b" ]]; then echo "DIFF ts=$ts rule=$rule $s"; echo "real: $a" | tr '\n' ' '; echo; echo "port: $b" | tr '\n' ' '; echo; fail=1; fi
  done
done; done
echo "scenarios=${#SCEN} tile_sizes=3 rules=2 diff_failures=$fail"
