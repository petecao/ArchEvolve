#!/bin/bash
# Host-side queue for the second import store and the final validation (not measurements;
# pinned to socket 0 with numactl, no lease). Waits on the lane jobs' lane_rc lines.
RAW=/data/yanruj/EvolveSWDB_runs/cpud07-20261012-a1; S=$RAW/scripts
NUMA="numactl --cpunodebind=0 --membind=0"
waitfor() { until grep -q "$2" "$1" 2>/dev/null; do sleep 30; done; grep -q "$3" "$1"; }
[ -d "$RAW/records-c" ] || cp -a /data/yanruj/ArchEvolve-cpud07-598232ca/swdb-project/records "$RAW/records-c"
waitfor "$RAW/lane-a.out" lane_rc= lane_rc=0 || exit 61
$NUMA bash $S/job-i.sh 0 "$RAW/records-c" bulk > "$RAW/import-c1.out" 2>&1 || exit 62
waitfor "$RAW/lane-l.out" lane_rc= lane_rc=0 || exit 63
$NUMA bash $S/job-i.sh 0 "$RAW/records-c" libcall > "$RAW/import-c2.out" 2>&1 || exit 64
waitfor "$RAW/import-b3.out" ^rc= ^rc=0 || exit 65
SRC=/data/yanruj/ArchEvolve-cpud07-f2d41156/swdb-project $NUMA bash $S/job-v.sh 0 > "$RAW/validate.out" 2>&1
echo "queue_rc=$?" >> "$RAW/validate.out"
