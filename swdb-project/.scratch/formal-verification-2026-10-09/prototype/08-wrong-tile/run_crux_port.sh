#!/bin/zsh
# PROTOTYPE (ticket 08): crux-llvm on the TDStepMAA harness over the strict-layer port.
# Usage: run_crux_port.sh <tag> [extra -D flags...]
set -u
CRUX=~/opt/verifiers/crux-llvm-0.12/crux-llvm-0.12-macos-15-ARM64
LLVM=/opt/homebrew/opt/llvm/bin
tag=$1; shift
mkdir -p bc logs
$LLVM/clang++ -std=c++17 -O0 -g -fno-exceptions -fno-threadsafe-statics -c -emit-llvm -DSWDB_PORT_VERIFY -DSWDB_PORT_NO_REGION_CHECK -DNUM_CORES=1 "$@" tdstep_harness.cpp -o bc/$tag.main.bc || exit 3
$LLVM/clang -O0 -g -c -emit-llvm -I $CRUX/c-src/includes stub/crux_verifier.c -o bc/$tag.shim.bc || exit 3
$LLVM/llvm-link bc/$tag.main.bc bc/$tag.shim.bc -o bc/$tag.raw.bc || exit 3
$LLVM/llvm-dis bc/$tag.raw.bc -o - | grep -v -E 'call void @llvm.assume\(i1 true\) \[ "align"' > bc/$tag.ll
grep -q '\[ "' bc/$tag.ll && { echo "other operand bundles remain"; exit 3; }
$LLVM/llvm-as bc/$tag.ll -o bc/$tag.bc || exit 3
rm -rf crux-out/$tag
start=$(date +%s.%N)
timeout -k 10 ${CRUX_TIMEOUT:-300} $CRUX/bin/crux-llvm --no-compile --solver=${CRUX_SOLVER:-z3} ${CRUX_FLAGS:-} --output-directory=$PWD/crux-out/$tag $PWD/bc/$tag.bc > logs/crux-$tag.log 2>&1
rc=$?
end=$(date +%s.%N)
verdict=$(grep -o "Overall status: [A-Za-z]*" logs/crux-$tag.log | tail -1)
goals=$(grep -A5 "Goal status" logs/crux-$tag.log | tr -s ' \n' ' ' | sed 's/\[Crux\]//g')
prop=$(grep -o '"P[0-9A-Za-z_]*"\|"[a-z_]*" *$' logs/crux-$tag.log | sort -u | tr '\n' ' ')
echo "tag=$tag flags=($*) rc=$rc seconds=$(printf %.1f $(( end - start ))) [$verdict] $goals props=$prop" | tee -a logs/summary.txt
rm -rf crux-out/$tag  # counterexample builds are large; the log keeps the verdict
