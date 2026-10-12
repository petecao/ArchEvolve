#!/bin/zsh
# PROTOTYPE (ticket 08): compile <harness.cpp> + shims to one bitcode file and run crux-llvm.
# Usage: run_crux.sh <harness.cpp> <tag> [extra clang flags...]
set -u
CRUX=~/opt/verifiers/crux-llvm-0.12/crux-llvm-0.12-macos-15-ARM64
S=../../../../library/dx100/strict
CXX=/opt/homebrew/opt/llvm/bin/clang++
src=$1; tag=$2; shift 2
mkdir -p bc logs
flags=(-std=c++17 -O0 -g -fno-exceptions -fno-threadsafe-statics -c -emit-llvm -I stub -I $S -I $CRUX/c-src/includes -DNUM_CORES=1 "$@")
$CXX $flags $src -o bc/$tag.main.bc || exit 3
$CXX $flags stub/crux_shims.cpp -o bc/$tag.shims.bc || exit 3
/opt/homebrew/opt/llvm/bin/llvm-link bc/$tag.main.bc bc/$tag.shims.bc -o bc/$tag.raw.bc || exit 3
# crux 0.12 cannot parse operand bundles; the only ones are alignment hints on llvm.assume(true).
/opt/homebrew/opt/llvm/bin/llvm-dis bc/$tag.raw.bc -o - | grep -v -E 'call void @llvm.assume\(i1 true\) \[ "align"' > bc/$tag.ll
grep -q '\[ "' bc/$tag.ll && { echo "other operand bundles remain"; exit 3; }
/opt/homebrew/opt/llvm/bin/llvm-as bc/$tag.ll -o bc/$tag.bc || exit 3
rm -rf crux-out/$tag
start=$(date +%s.%N)
$CRUX/bin/crux-llvm --no-compile --solver=z3 --output-directory=$PWD/crux-out/$tag $PWD/bc/$tag.bc > logs/crux-$tag.log 2>&1
rc=$?
end=$(date +%s.%N)
echo "tag=$tag rc=$rc seconds=$(( end - start ))" | tee -a logs/crux-$tag.log
grep -v -E "^\[Crux\] +(Invalid record|Expected size|from:|METADATA|MODULE|value symbol|Bitstream|$)|^\[Crux\]\s*$" logs/crux-$tag.log | grep -v "Encountered the following warnings" | tail -30
