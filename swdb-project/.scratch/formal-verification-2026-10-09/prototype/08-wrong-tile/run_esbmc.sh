#!/bin/zsh
# PROTOTYPE (ticket 08): run ESBMC on the TDStepMAA harness.
# Usage: run_esbmc.sh <tag> <unwind> <timeout> [extra -D flags...]
set -u
tag=$1; unwind=$2; to=$3; shift 3
mkdir -p logs
start=$(date +%s.%N)
esbmc tdstep_harness.cpp -DSWDB_PORT_VERIFY -DNUM_CORES=1 "$@" --unwind $unwind --timeout $to > logs/esbmc-$tag.log 2>&1
rc=$?
end=$(date +%s.%N)
verdict=$(grep -E "^VERIFICATION (SUCCESSFUL|FAILED)|ERROR: Timed out|PARSING ERROR|unwinding assertion" logs/esbmc-$tag.log | tail -1)
prop=$(grep -o '"P[0-9A-Za-z_]*"\|"port_[a-z_]*"\|unwinding assertion loop [0-9]*' logs/esbmc-$tag.log | tail -1)
echo "tag=$tag flags=($*) unwind=$unwind rc=$rc seconds=$(printf %.1f $(( end - start ))) verdict=[$verdict] property=$prop" | tee -a logs/summary.txt
