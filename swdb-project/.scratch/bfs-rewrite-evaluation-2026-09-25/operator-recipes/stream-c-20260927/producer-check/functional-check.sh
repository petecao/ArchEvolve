#!/usr/bin/env bash
# Producer-side functional check of the context5 reference helper. Created 2026-09-27 ET.
# usage: CXX=<clang++ or g++ with OpenMP> bash functional-check.sh OUT_DIR
# Runs upstream GAPBS with the reference helper on the pinned DX100 *functional* model
# (software emulation of the MAA operations) and on the CPU-only build, 16 trials per graph,
# with GAPBS's own verifier. It checks the test client's intent is coherent; it is not
# candidate, correctness-of-candidate, DX100 timing or accelerator-execution evidence.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(git -C "$HERE" rev-parse --show-toplevel)
OUT=${1:?output directory required}
mkdir -p "$OUT"
CXX=${CXX:-c++}
FLAGS=(-std=c++11 -O2 -Wall -fopenmp -I"$ROOT/apps/gapbs/src" ${LDFLAGS:-})
"$CXX" "${FLAGS[@]}" -DMAA -DNUM_CORES=4 -DTILE_SIZE=16384 -I"$ROOT/apps/dx100/benchmarks/API" \
  "$HERE/functional-harness.cc" -o "$OUT/bfs_functional"
"$CXX" "${FLAGS[@]}" "$HERE/reference-bfs.cc" -o "$OUT/bfs_cpu"
for binary in bfs_functional bfs_cpu; do
  for graph in "-g 14" "-g 16" "-u 16" "-g 18" "-u 18"; do
    # shellcheck disable=SC2086
    OMP_NUM_THREADS=4 "$OUT/$binary" $graph -n 16 -v -l > "$OUT/run.txt" 2>&1
    printf '%s %s trials=%s pass=%s fail=%s dx100_steps=%s\n' "$binary" "$graph" \
      "$(grep -c '^Trial Time' "$OUT/run.txt")" "$(grep -c 'Verification: *PASS' "$OUT/run.txt")" \
      "$(grep -c 'Verification: *FAIL' "$OUT/run.txt" || true)" "$(grep -c '^td-dx100' "$OUT/run.txt" || true)"
  done
done
