#!/bin/bash
# Host-side (mbit10), created 2026-10-12 ET from ticket 08's when-free.sh: wait until a socket
# lease is released, then run run.sh in that lane through socket_lane.sh (one job, one lane).
# Retries when another session wins the lease first (exit 4) or the load gate refuses (exit 5).
# Gives up after 12 h (exit 9).
# Usage: bash when-free.sh <checkout root> <raw folder>
CO=$1; RAW=$2; L=/data1/yanruj/lact-host-lease
EV=.scratch/cpu-description-t75-pricing-2026-10-12/evidence/10-rerun-09
[ -n "$CO" ] && [ -n "$RAW" ] || { echo "usage: bash when-free.sh <checkout root> <raw folder>" >&2; exit 2; }
mkdir -p "$RAW" || exit 2
bash "$CO/swdb-project/$EV/run.sh" --check "$CO" 0 "$RAW" > "$RAW/plan.txt" || exit 2
deadline=$(( $(date +%s) + 43200 ))
cd /data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner || exit 2
while [ "$(date +%s)" -lt $deadline ]; do
  for N in 0 1; do
    if grep -q '"state":"released"' "$L/mbit10-evaluation-node$N.meta.json"; then
      echo "$(TZ=America/New_York date '+%Y-%m-%d %H:%M:%S ET') try node$N" >> "$RAW/when-free.log"
      bash scripts/host/socket_lane.sh "$N" cpud10-split-check --lease-timeout-s 30 --record "$RAW/lane-10.json" -- \
        bash "$CO/swdb-project/$EV/run.sh" "$CO" "$N" "$RAW" >> "$RAW/lane-10.out" 2>&1
      rc=$?; echo "lane_rc=$rc node=$N" >> "$RAW/lane-10.out"
      echo "$(TZ=America/New_York date '+%Y-%m-%d %H:%M:%S ET') node$N rc=$rc" >> "$RAW/when-free.log"
      case $rc in 4|5) ;; *) exit $rc;; esac
    fi
  done
  sleep 60
done
exit 9
