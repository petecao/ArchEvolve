#!/usr/bin/env bash
# cpud full suite (2026-10-13 ET): run_suite.sh <side> <checkout> [idfile]. Full suite unless idfile given.
set -u
SIDE=$1; CHECKOUT=$2; IDS=${3:-}
R=/data/yanruj/EvolveSWDB_runs/cpud-fullsuite-20261013; O=$R/$SIDE; mkdir -p $O/tmp/xdg
cd $CHECKOUT/swdb-project
export TMPDIR=$O/tmp XDG_CACHE_HOME=$O/tmp/xdg PIP_CACHE_DIR=$O/tmp/pip
export SWDB_TOOLCHAIN_FLAGS=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13
export PYTHONPATH=$R/plugin SWDB_REAPER_LOG=$O/sources-ns.log
cap() { { date -Is; uptime; who | awk '{print $1}' | sort -u; df -h /data1 /data;
  cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>&1; cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>&1;
  git rev-parse --abbrev-ref HEAD; git rev-parse HEAD; grep MemFree /sys/devices/system/node/node*/meminfo;
  grep oom_kill /proc/vmstat; grep Cpus_allowed_list /proc/self/status; } > $O/env-$1.txt 2>&1
  lscpu > $O/lscpu.txt 2>&1; numactl --hardware > $O/numactl.txt 2>&1; uname -a > $O/uname.txt; }
cap start
A=(); if [ -n "$IDS" ]; then mapfile -t A < "$IDS"; fi
s=$(date +%s)
timeout -s INT -k 600 21600 /data1/yanruj/venvs/swdb-test/bin/python -m pytest -p swdb_tmp_reaper -n 8 --dist worksteal "${A[@]}" \
  --basetemp=$O/bt -o tmp_path_retention_policy=none -rfE --durations=30 \
  --junitxml=$O/junit.xml --report-log=$O/report.jsonl > $O/pytest.log 2>&1 &
TP=$!; echo $TP > $O/timeout.pid
wait $TP; rc=$?
echo "rc=$rc wall_s=$(( $(date +%s)-s ))" > $O/result.txt; cap end
rm -rf $O/bt
exit $rc
