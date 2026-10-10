#!/usr/bin/env bash
# Stream B native protocol operation (prepare or publish), 2026-09-27 ET.
# Usage: prepare.sh ACTION SOURCE   (ACTION prepare|publish, SOURCE dx100-scalar|upstream-do)
set -u
ACTION=$1; SRC=$2
R=/data1/yanruj/EvolveSWDB_native_routes_runtime_20260927_b1
V=/data/yanruj/EvolveSWDB_runs/bfs-native-protocol-20260927-b1
OP=$V/$ACTION-$SRC
mkdir "$OP" || exit 64
{ date --iso-8601=ns; uptime; who | awk '{print $1}' | sort -u | tr '\n' ' '; echo; df -h /data1 /data;
  git -C "$R" rev-parse HEAD; git -C "$R" status --short | wc -l;
  grep -H '"state"' /data1/yanruj/lact-host-lease/mbit10-evaluation*.meta.json | cut -c1-200; } > "$OP/environment.txt" 2>&1
if [ "$ACTION" = prepare ]; then IN=$R/.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/native-acceptance/protocol/$SRC.selection.json
else IN=$V/prepare-$SRC/review/review.json; fi
sha256sum "$IN" > "$OP/input.sha256"
cd "$R"
env -u PYTHONPATH -u PYTHONHOME -u PYTHONSTARTUP -u PYTHONUSERBASE -u PYTHONOPTIMIZE -u LD_PRELOAD -u LD_LIBRARY_PATH \
  PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PATH=/usr/bin:/bin \
  timeout --signal=TERM --kill-after=30s 1500s \
  /usr/bin/python3.12 -s -B scripts/bfs_freeze_pilot.py $ACTION "$IN" --records "$V/records" \
  --db "$OP/swdb.sqlite" --output "$OP/review" > "$OP/stdout.json" 2> "$OP/stderr.txt"
echo $? > "$OP/exit"
date --iso-8601=ns >> "$OP/environment.txt"
