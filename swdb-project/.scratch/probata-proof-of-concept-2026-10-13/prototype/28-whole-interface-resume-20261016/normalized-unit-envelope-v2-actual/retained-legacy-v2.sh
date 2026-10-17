#!/bin/bash
set -euo pipefail
source /data1/yanruj/probata-verifiers/env.sh
unset CPLUS_INCLUDE_PATH
export PATH=/data/yanruj/EvolveSWDB_runs/probata-source-gate-native-20261015-1102-node0/compiler-bin:$PATH SWDB_CLANG=clang++
export PYTHONPATH=/data1/yanruj/probata-composed-0e7f2327/swdb-project PYTHONDONTWRITEBYTECODE=1
export LIBRARY_PATH=/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu:/usr/lib/gcc/x86_64-linux-gnu/13
export LD_LIBRARY_PATH=/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu:${LD_LIBRARY_PATH:-}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PROBATA_PYTHON=/data1/yanruj/venvs/swdb-test/bin/python
export PROBATA_OUTPUT=/data/yanruj/EvolveSWDB_runs/probata-composed-0e7f2327-t27-negative
export TMPDIR=$PROBATA_OUTPUT/tmp XDG_CACHE_HOME=$PROBATA_OUTPUT/cache
export SWDB_VERIFIER_LOCK=$PROBATA_OUTPUT/verifier.lock SWDB_VERIFIER_RSS_CAP_BYTES=8589934592
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
cd /data1/yanruj/probata-composed-0e7f2327
"$PROBATA_PYTHON" "$PROBATA_OUTPUT/watch.py"
