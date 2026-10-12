#!/usr/bin/env bash
# cpud ticket 01, phase A: C3 team-safe probe and the two t75 OpenMP call projections (C7).
# Created 2026-10-12 ET. Runs on mbit10 under the node1 socket lane from a clean worktree:
#   /data1/yanruj/ArchEvolve-cpud01-trial-20261012/swdb-project
# Static only: no application is linked or run (projection receipt says application_execution: false).
set -uo pipefail
RAW=/data/yanruj/EvolveSWDB_runs/cpud01-trial-20261012-a1
A2=/data/yanruj/EvolveSWDB_runs/fga03-real-pair-20261011-a1/a2
LLVM=/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin
E=.scratch/cpu-description-t75-pricing-2026-10-12/evidence/01-trial-bind
export PYTHONDONTWRITEBYTECODE=1
cd /data1/yanruj/ArchEvolve-cpud01-trial-20261012/swdb-project || exit 3
mkdir -p "$RAW"
log() { echo "$(TZ=America/New_York date '+%Y-%m-%d %H:%M:%S ET') A $*" | tee -a "$RAW/order.log"; }
step() { local name=$1; shift; log "step $name begin"; "$@" > "$RAW/$name.json" 2> "$RAW/$name.stderr"; local rc=$?; log "step $name end rc=$rc"; return $rc; }
test -z "$(git status --porcelain)" || { log "dirty checkout"; exit 4; }
log "start commit=$(git rev-parse HEAD)"
{ TZ=America/New_York date; uptime; who | awk '{print $1}' | sort -u | tr '\n' ' '; echo; df -h /data1 /data;
  cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor; cat /sys/devices/system/cpu/intel_pstate/no_turbo;
  uname -a; numactl --show; git rev-parse HEAD; } > "$RAW/env-start-a.txt" 2>&1
step team-safe python3 "$E/team_safe_probe.py" || { log "C3 team-safe FAILED: stop"; exit 10; }
for side in baseline candidate; do
  CASE=$RAW/projection-$side
  mkdir -p "$CASE"
  cp records/workload_characterizations/fga03.t75-$side.uniform22.t1.characterization.a2.yaml "$CASE/characterization.yaml"
  sha256sum records/workload_characterizations/fga03.t75-$side.uniform22.t1.characterization.a2.yaml "$CASE/characterization.yaml" \
    "$A2/$side-counted/normalized.bc" "$A2/$side-counted/source.json" > "$CASE/inputs.sha256"
  step "projection-$side" python3 -m scripts.openmp_call_projection --characterization "$CASE/characterization.yaml" \
    --source-ir "$A2/$side-counted/normalized.bc" --source-map "$A2/$side-counted/source.json" \
    --llvm-bin "$LLVM" --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
    --timeout-s 180 --output-directory "$CASE/projection" || exit $((20 + ${#side}))
done
{ TZ=America/New_York date; uptime; df -h /data1 /data; } > "$RAW/env-end-a.txt" 2>&1
log "phase A done"
