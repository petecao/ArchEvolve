#!/bin/bash
# Host-side queue: run lane jobs one after another in one lane, each through socket_lane.sh.
# Usage: bash chain.sh <node> <wait-file-or-none> <job> [<job> ...]   (job = a|b|t)
# Waits until <wait-file> contains "lane_rc" (the previous lane job ended), then dispatches.
RAW=/data/yanruj/EvolveSWDB_runs/cpud07-20261012-a1
NODE=$1; WAIT=$2; shift 2
if [ "$WAIT" != none ]; then until grep -q lane_rc "$WAIT" 2>/dev/null; do sleep 30; done; fi
cd /data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner || exit 2
for J in "$@"; do
  bash scripts/host/socket_lane.sh "$NODE" "cpud07-calib-$J" --record "$RAW/lane-$J.json" -- bash "$RAW/scripts/job-$J.sh" "$NODE" > "$RAW/lane-$J.out" 2>&1
  rc=$?; echo "lane_rc=$rc" >> "$RAW/lane-$J.out"
  [ $rc -eq 0 ] || exit $rc
done
