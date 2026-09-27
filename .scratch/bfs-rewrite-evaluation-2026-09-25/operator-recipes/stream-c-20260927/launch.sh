#!/usr/bin/env bash
# Stream C bounded public-job launcher. Created 2026-09-27 ET (resume plan R4/R9).
# usage (inside a named tmux pane on mbit10, from a clean Git checkout under /data1/yanruj):
#   CODE_COMMIT=<sha> bash launch.sh JOB NODE OUTER_SECONDS
# JOB names jobs/JOB.sh. NODE is 0 or 1 (enter that socket lane via socket_lane.sh; root
# assigns it) or "none" (no lane: provider-only jobs that run no build or measurement).
# Every public call runs under its own timeout inside the outer timeout. Raw evidence and
# dispatch receipts go to /data/yanruj/EvolveSWDB_runs/stream-c-20260927/; new records go
# to the checkout's records/ and are committed on the host afterwards. No retry.
set -eu
[[ $# -eq 3 ]] || { echo "usage: CODE_COMMIT=sha launch.sh JOB NODE OUTER_SECONDS" >&2; exit 64; }
JOB=$1 NODE=$2 OUTER=$3
[[ "$JOB" =~ ^[a-z0-9][a-z0-9.-]*$ && "$OUTER" =~ ^[0-9]+$ ]] || exit 64
[[ "$NODE" == 0 || "$NODE" == 1 || "$NODE" == none ]] || exit 64
HERE=$(cd "$(dirname "$0")" && pwd)
CODE=$(git -C "$HERE" rev-parse --show-toplevel)
: "${CODE_COMMIT:?exact checkout commit required}"
[[ "$CODE" == /data1/yanruj/* ]] || exit 64
[[ "$(git -C "$CODE" rev-parse HEAD)" == "$CODE_COMMIT" ]] || { echo "checkout is not $CODE_COMMIT" >&2; exit 64; }
[[ -z "$(git -C "$CODE" status --porcelain --untracked-files=no)" ]] || { echo "tracked changes present" >&2; exit 64; }
[[ -f "$HERE/jobs/$JOB.sh" ]] || exit 64
HELPER=/data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner/scripts/host/socket_lane.sh
HELPER_SHA=00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8
[[ "$(sha256sum "$HELPER" | cut -d' ' -f1)" == "$HELPER_SHA" ]] || { echo "lane helper changed" >&2; exit 64; }
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONUSERBASE PYTHONOPTIMIZE
unset GCC_EXEC_PREFIX COMPILER_PATH LIBRARY_PATH CPATH CPLUS_INCLUDE_PATH C_INCLUDE_PATH LD_PRELOAD LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/data1/yanruj/tmp
export PATH=/usr/bin:/bin:/data1/yanruj/.npm-global/bin
RUNROOT=/data/yanruj/EvolveSWDB_runs/stream-c-20260927
DISPATCH=$RUNROOT/$JOB
mkdir -p "$RUNROOT/raw"
mkdir "$DISPATCH"   # fails if the job ID was already used: no retry under one ID

observe() {  # host record per the mbit10 measurement protocol
  {
    echo "== $1 $(date --iso-8601=ns)"; uptime; who | awk '{print $1}' | sort -u | tr '\n' ' '; echo
    df -h /data1 /data
    cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor /sys/devices/system/cpu/intel_pstate/no_turbo 2>&1
    grep -H '"state"' /data1/yanruj/lact-host-lease/mbit10-evaluation*.meta.json
    echo "code $CODE $(git -C "$CODE" rev-parse --abbrev-ref HEAD) $(git -C "$CODE" rev-parse HEAD)"
  } >> "$DISPATCH/host.txt" 2>&1
}
observe start
{ uname -a; lscpu; numactl --hardware; } > "$DISPATCH/machine.txt" 2>&1 || true
printf '{"job":"%s","node":"%s","outer_seconds":%s,"code":"%s","commit":"%s","pane_pid":%s,"started":"%s"}\n' \
  "$JOB" "$NODE" "$OUTER" "$CODE" "$CODE_COMMIT" "$$" "$(date --iso-8601=ns)" > "$DISPATCH/launch.json"
set +e
if [[ "$NODE" == none ]]; then
  JOB_NODE=none timeout --signal=TERM --kill-after=30s "$OUTER" \
    bash "$HERE/jobs/$JOB.sh" "$CODE" "$DISPATCH" "$RUNROOT/raw" > "$DISPATCH/outer.stdout" 2> "$DISPATCH/outer.stderr"
else
  JOB_NODE=$NODE timeout --signal=TERM --kill-after=30s "$OUTER" bash "$HELPER" "$NODE" "swdb-streamc-$JOB" \
    --record "$DISPATCH/lane.json" -- bash "$HERE/jobs/$JOB.sh" "$CODE" "$DISPATCH" "$RUNROOT/raw" \
    > "$DISPATCH/outer.stdout" 2> "$DISPATCH/outer.stderr"
fi
status=$?
printf '%s\n' "$status" > "$DISPATCH/outer.exit"
date --iso-8601=ns > "$DISPATCH/outer.finished"
observe end
( cd "$DISPATCH" && sha256sum -- * > SHA256SUMS.txt ) 2>/dev/null
exit "$status"
