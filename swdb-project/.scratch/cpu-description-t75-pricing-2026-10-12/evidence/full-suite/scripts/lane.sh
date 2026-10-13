#!/usr/bin/env bash
# lane.sh <node> <side> <checkout> [idfile]
R=/data/yanruj/EvolveSWDB_runs/cpud-fullsuite-20261013
cd /data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner
bash scripts/host/socket_lane.sh $1 cpud-suite-$2 --record $R/lane-$2.json -- bash $R/run_suite.sh $2 $3 ${4:-} > $R/lane-$2.log 2>&1
echo "lane_rc=$?" >> $R/lane-$2.log
