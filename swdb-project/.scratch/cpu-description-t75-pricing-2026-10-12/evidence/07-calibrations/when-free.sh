#!/bin/bash
# Host-side: wait until either socket lease is released, then run job-<J> in that lane.
# Retries if another session wins the lease first (socket_lane exit 4). Gives up after 6 h.
# Usage: bash when-free.sh <job letter>
RAW=/data/yanruj/EvolveSWDB_runs/cpud07-20261012-a1; J=$1; L=/data1/yanruj/lact-host-lease
deadline=$(( $(date +%s) + 21600 ))
cd /data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner || exit 2
while [ "$(date +%s)" -lt $deadline ]; do
  for N in 0 1; do
    if grep -q '"state":"released"' "$L/mbit10-evaluation-node$N.meta.json"; then
      bash scripts/host/socket_lane.sh "$N" "cpud07-calib-$J" --lease-timeout-s 30 --record "$RAW/lane-$J.json" -- bash "$RAW/scripts/job-$J.sh" "$N" > "$RAW/lane-$J.out" 2>&1
      rc=$?; echo "lane_rc=$rc" >> "$RAW/lane-$J.out"
      [ $rc -eq 4 ] || exit $rc
    fi
  done
  sleep 60
done
exit 9
