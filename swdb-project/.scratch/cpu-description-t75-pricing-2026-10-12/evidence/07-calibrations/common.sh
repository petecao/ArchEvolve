# cpud ticket 07: common setup, sourced by job-a.sh / job-b.sh / job-t.sh. Written 2026-10-12 ET.
# Usage (inside socket_lane.sh): bash job-X.sh <node>
set -uo pipefail
SRC=${SRC:-/data/yanruj/ArchEvolve-cpud07-598232ca/swdb-project}
RAW=/data/yanruj/EvolveSWDB_runs/cpud07-20261012-a1
LLVM=/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64
NODE=$1; LANE=mbit10-evaluation-node$NODE; JOB=$2
export OMP_NUM_THREADS=1 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores
export LD_LIBRARY_PATH=$LLVM/lib/x86_64-unknown-linux-gnu
TC=(--machine mbit10 --lane "$LANE" --llvm-bin "$LLVM/bin" --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13)
mkdir -p "$RAW/logs" "$RAW/env"
cd "$SRC"
envsnap() {
  { echo "== $1 $(date -u +%FT%TZ) / $(TZ=America/New_York date '+%F %H:%M ET')"; uptime
    echo "-- users"; who | awk '{print $1}' | sort -u | tr '\n' ' '; echo
    echo "-- df"; df -h /data1 /data
    echo "-- governor"; cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>&1
    echo "-- no_turbo"; cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>&1
    echo "-- source HEAD"; git rev-parse HEAD; echo "dirty files: $(git status --short | wc -l)"
    echo "-- numactl"; numactl --show; echo "-- uname"; uname -a
    echo "-- leases"; grep -h -o '"lease_name":"[^"]*"\|"state":"[^"]*"' /data1/yanruj/lact-host-lease/mbit10-evaluation*.meta.json | paste - -
  } > "$RAW/env/$1.txt" 2>&1
}
log() { echo "$(date -u +%FT%TZ) $(TZ=America/New_York date '+%F %H:%M:%S ET') [$JOB node$NODE] $*" >> "$RAW/order.log"; }
step() {
  local name=$1 lim=$2; shift 2
  log "start $name"
  /usr/bin/time -v -o "$RAW/logs/$name.time" timeout "$lim" "$@" > "$RAW/logs/$name.out" 2> "$RAW/logs/$name.err"
  local rc=$?; log "end $name rc=$rc"; return $rc
}
