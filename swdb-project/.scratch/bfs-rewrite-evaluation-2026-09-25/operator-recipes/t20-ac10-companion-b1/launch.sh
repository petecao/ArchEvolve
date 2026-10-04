#!/usr/bin/env bash
# Created 2026-09-29 ET. T20 AC10 companion b1: one correctness-only public dx100-execute of the
# t20 context6 timed primary on the re-registered A2 collision graph (gapbs sg64), inside one
# socket_lane.sh job on the root-assigned node. No retry; the companion refuses an existing run ID.
# Usage (from the runtime checkout root): NODE=1 WORKLOAD=<registered id> bash <this>
set -eu
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONUSERBASE PYTHONOPTIMIZE PYTEST_ADDOPTS PYTEST_PLUGINS LD_PRELOAD LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PATH=/usr/bin:/bin
: "${NODE:?root-assigned lane node required}"
: "${WORKLOAD:?registered b1 workload ID required}"
HELPER=/data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner/scripts/host/socket_lane.sh
HELPER_SHA=00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8
RUN=bfs-t20-ac10-companion-20260929-b1
ROOT_DIR=/data/yanruj/EvolveSWDB_runs/bfs-t20-ac10-companion-20260929-b1
A3=/data/yanruj/EvolveSWDB_runs/bfs-t17-t20-routes-simulator-batch-20260928-a3/bfs-t17-t20-routes-simulator-batch-20260928-a3.t20.uniform18
TEMPLATE=$A3/bfs-t20-routes-20260928-a3.candidate.uniform18/bfs-t20-routes-20260928-a3.candidate.uniform18.driver/bfs-t20-routes-20260928-a3.candidate.uniform18.s0.r0.primary.evaluation.request.json
RECIPE="$(cd "$(dirname "$0")" && pwd)"
[[ "$(sha256sum "$HELPER" | cut -d' ' -f1)" == "$HELPER_SHA" ]] || { echo "lane helper differs"; exit 64; }
[[ -z "$(git status --porcelain --untracked-files=no)" ]] || { echo "runtime checkout has tracked modifications"; exit 64; }
[[ ! -e "$ROOT_DIR" ]] || { echo "fresh run root required"; exit 64; }
mkdir -p "$ROOT_DIR"
{ echo "commit $(git rev-parse HEAD)"; date --iso-8601=ns; uptime; df -h /data /data1; } > "$ROOT_DIR/env.txt"
set +e
timeout --signal=TERM --kill-after=30s 3600s bash "$HELPER" "$NODE" "$RUN" --record "$ROOT_DIR/lane.json" -- \
  /usr/bin/python3.12 -s -B "$RECIPE/companion.py" --run-id "$RUN" --root "$ROOT_DIR" --template "$TEMPLATE" \
  --primary-build bfs-t20-context6-primary-build-20260927-c3 --lane "$NODE" --workload "$WORKLOAD" --application gapbs \
  >"$ROOT_DIR/companion.stdout" 2>"$ROOT_DIR/companion.stderr"
echo $? > "$ROOT_DIR/outer.exit"
date --iso-8601=ns > "$ROOT_DIR/outer.finished"
