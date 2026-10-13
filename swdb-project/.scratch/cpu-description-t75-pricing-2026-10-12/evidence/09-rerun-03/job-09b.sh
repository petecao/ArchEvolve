#!/usr/bin/env bash
# cpud ticket 09, step b: rerun the unchecked `swdb attribute` on the saved .a3 estimates with the
# review-F1 floor fix (cpud/integration 4324b546). Created 2026-10-12 ET.
# The estimates and protocols are NOT redone: they stay the ones frozen and estimated at c9f9df67
# (job-09.sh). The store is a copy of job 09's store without its first attribution report.
# Runs on mbit10 inside one socket lane (socket_lane.sh). No application timing (C12).
# Usage: bash job-09b.sh <checkout root at 4324b546>
set -uo pipefail
SRC=$1/swdb-project
RAW=/data/yanruj/EvolveSWDB_runs/cpud0809-20261012-a1
BC=typed-library-bfs-scalar-profile-20261003-a1.baseline
CC=extensa-native-bfs-20261005-a8.it1.kronecker.a0
BES=fga03.t75-baseline.uniform22.t1.estimate.a3
CES=fga03.t75-candidate.uniform22.t1.estimate.a3
REP=fga03.t75.uniform22.t1.attribution.a3
S=$RAW/records09b
export PYTHONDONTWRITEBYTECODE=1
cd "$SRC" || exit 3
log() { echo "$(TZ=America/New_York date '+%Y-%m-%d %H:%M:%S ET') 09b $*" | tee -a "$RAW/order.log"; }
step() { local name=$1; shift; log "step $name begin"; /usr/bin/time -v "$@" > "$RAW/$name.out" 2> "$RAW/$name.stderr"; local rc=$?; log "step $name end rc=$rc"; return $rc; }
envsnap() { { TZ=America/New_York date; uptime; who | awk '{print $1}' | sort -u | tr '\n' ' '; echo; df -h /data1 /data;
  cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor; cat /sys/devices/system/cpu/intel_pstate/no_turbo;
  uname -a; numactl --show; git rev-parse HEAD; } > "$RAW/env-$1.txt" 2>&1; }
test -z "$(git status --porcelain)" || { log "dirty checkout"; exit 4; }
log "start commit=$(git rev-parse HEAD)"
envsnap 09b-start
test ! -e "$S" || { log "scratch store exists"; exit 6; }
cp -a "$RAW/records09" "$S" || exit 7
rm -rf "$S/attributions"
log "store copied from records09 without attributions/"
step attribute-b timeout 7200 python3 -m swdb attribute --records "$S" --library "$SRC/library" \
  --baseline-estimate "$BES" --candidate-estimate "$CES" --baseline-source "$BC" --candidate-source "$CC" \
  --id "$REP" --format json
step validate-b timeout 7200 python3 -m swdb validate --records "$S" --library "$SRC/library"
envsnap 09b-end
log "job 09b done"
