#!/bin/bash
R=/data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-cert17-recert-20261013-a1
W=/data/yanruj/ArchEvolve-cert17-recert-20261013-a1
cd $R
{ date -Is; uptime; who | awk "{print \$1}" | sort -u; df -h /data1 /data; cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor; cat /sys/devices/system/cpu/intel_pstate/no_turbo; uname -a; git -C $W rev-parse HEAD; grep -H "\"state\"" /data1/yanruj/lact-host-lease/mbit10-evaluation*.meta.json; } > env.txt 2>&1
lscpu > lscpu.txt; numactl --hardware > numa.txt
cd /data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner
git -C /data1/yanruj/Memacc-evolveswdb-lane rev-parse HEAD >> $R/env.txt
bash scripts/host/socket_lane.sh 0 swdb-cert17-bfs-functional-recert --record $R/lane.json -- bash -c "cd $W/swdb-project && timeout 4h python3 -m swdb certify contract.bfs_read_offload --candidate bfs-functional-read-offload-20261006-a1.proposal.candidate-1 --threads 4 --runs-dir $R/strict-certification"
echo exit=$? > $R/exit.txt; date -Is >> $R/exit.txt
