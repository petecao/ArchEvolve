#!/bin/bash
# Host-side (mbit10), created 2026-10-12 ET from ticket 07's when-free.sh: wait until either
# socket lease is released, then run one job in that lane through socket_lane.sh. Retries if
# another session wins the lease first (socket_lane exit 4). Gives up after 12 h (exit 9).
# Usage: bash when-free.sh <job: 08|09> <checkout root>
RAW=/data/yanruj/EvolveSWDB_runs/cpud0809-20261012-a1; J=$1; CO=$2; L=/data1/yanruj/lact-host-lease
deadline=$(( $(date +%s) + 43200 ))
cd /data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner || exit 2
while [ "$(date +%s)" -lt $deadline ]; do
  for N in 0 1; do
    if grep -q '"state":"released"' "$L/mbit10-evaluation-node$N.meta.json"; then
      bash scripts/host/socket_lane.sh "$N" "cpud0809-job-$J" --lease-timeout-s 30 --record "$RAW/lane-$J.json" -- bash "$RAW/scripts/job-$J.sh" "$CO" > "$RAW/lane-$J.out" 2>&1
      rc=$?; echo "lane_rc=$rc" >> "$RAW/lane-$J.out"
      [ $rc -eq 4 ] || exit $rc
    fi
  done
  sleep 60
done
exit 9
