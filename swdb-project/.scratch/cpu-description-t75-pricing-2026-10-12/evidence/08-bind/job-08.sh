#!/usr/bin/env bash
# cpud ticket 08: bind services.v2 into a scratch store copy, then whole-store validate.
# Created 2026-10-12 ET. Runs on mbit10 inside one socket lane (socket_lane.sh), from a clean
# detached worktree of the pushed branch commit. Writes only into $RAW (never the repo store).
# No application timing: workload bfs-20261004-uniform22 is not run by any binary (C12).
# Usage: bash job-08.sh <checkout root>
set -uo pipefail
SRC=$1/swdb-project
RAW=/data/yanruj/EvolveSWDB_runs/cpud0809-20261012-a1
E=.scratch/cpu-description-t75-pricing-2026-10-12/evidence/08-bind
TD=mbit10.cpu.lanl20261006.t1.services.v2
V1=records/target_descriptions/mbit10.cpu.lanl20261006.t1.services.v1.yaml
export PYTHONDONTWRITEBYTECODE=1
cd "$SRC" || exit 3
log() { echo "$(TZ=America/New_York date '+%Y-%m-%d %H:%M:%S ET') 08 $*" | tee -a "$RAW/order.log"; }
step() { local name=$1; shift; log "step $name begin"; /usr/bin/time -v "$@" > "$RAW/$name.out" 2> "$RAW/$name.stderr"; local rc=$?; log "step $name end rc=$rc"; return $rc; }
envsnap() { { TZ=America/New_York date; uptime; who | awk '{print $1}' | sort -u | tr '\n' ' '; echo; df -h /data1 /data;
  cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor; cat /sys/devices/system/cpu/intel_pstate/no_turbo;
  uname -a; numactl --show; git rev-parse HEAD; } > "$RAW/env-$1.txt" 2>&1; }
test -z "$(git status --porcelain)" || { log "dirty checkout"; exit 4; }
log "start commit=$(git rev-parse HEAD)"
envsnap 08-start
test ! -e "$RAW/records08" || { log "scratch store exists"; exit 5; }
cp -a records "$RAW/records08" || exit 6
log "scratch store copied ($(du -sh "$RAW/records08" | cut -f1))"
step bind timeout 7200 python3 -m swdb.cpu_service_binding --records "$RAW/records08" $(cat "$E/bind-args.txt") || exit 30
sha256sum "$V1" "$RAW/records08/target_descriptions/$(basename "$V1")" "$RAW/records08/target_descriptions/$TD.yaml" | tee "$RAW/bind-sha256.txt"
cmp "$V1" "$RAW/records08/target_descriptions/$(basename "$V1")" && log "services.v1 byte-identical" || log "services.v1 CHANGED"
step validate timeout 7200 python3 -m swdb validate --records "$RAW/records08" --library "$SRC/library"
envsnap 08-end
log "job 08 done"
