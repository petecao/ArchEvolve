#!/usr/bin/env bash
# cpud ticket 10: rerun fine-grained ticket 09 (split check) on the .a3 estimates.
# Created 2026-10-12 ET. Runs on mbit10 inside ONE socket lane (socket_lane.sh), from a clean
# detached checkout of the pushed cpud/10-split-check commit. Order (C12, F43, F44):
#   guard (estimates exist, numeric, and dated before today ET) -> scratch store copy ->
#   evaluate baseline -> evaluate candidate (source 0 only, 20 reps, LLVM 22, evaluator v3) ->
#   bfs-profile baseline -> bfs-profile candidate (region thread-CPU timing, memory off) ->
#   checked attribute (swdb.split_check.v2) -> whole-store validate.
# Usage: bash run.sh <checkout root> <lane node 0|1> <raw folder>
#   --check   parse arguments and print the plan; run nothing.
# Exit codes avoid socket_lane.sh's 2/4/5: 12 setup, 13 dirty checkout, 15 guard refused,
# 16/17 scratch store, 11 evaluate, 21 bfs-profile, 31 attribute, 41 validate.
set -uo pipefail
CHECK=0
if [ "${1:-}" = "--check" ]; then CHECK=1; shift; fi
[ $# -eq 3 ] || { echo "usage: bash run.sh [--check] <checkout root> <lane node 0|1> <raw folder>" >&2; exit 2; }
CO=$1; N=$2; RAW=$3
case "$N" in 0|1) ;; *) echo "lane node must be 0 or 1" >&2; exit 2;; esac
case "$RAW" in /data/yanruj/EvolveSWDB_runs/*|/data1/yanruj/EvolveSWDB_runs/*) ;;
  *) echo "raw folder must be under /data/yanruj/EvolveSWDB_runs or /data1/yanruj/EvolveSWDB_runs" >&2; exit 2;; esac
SRC=$CO/swdb-project
EV=.scratch/cpu-description-t75-pricing-2026-10-12/evidence/10-rerun-09
LANE=mbit10-evaluation-node$N
BC=typed-library-bfs-scalar-profile-20261003-a1.baseline
CC=extensa-native-bfs-20261005-a8.it1.kronecker.a0
BES=fga03.t75-baseline.uniform22.t1.estimate.a3
CES=fga03.t75-candidate.uniform22.t1.estimate.a3
BEV=cpud10.t75-baseline.uniform22.t1.s0.evaluation.a1
CEV=cpud10.t75-candidate.uniform22.t1.s0.evaluation.a1
BPR=cpud10.t75-baseline.uniform22.t1.s0.profile.a1
CPR=cpud10.t75-candidate.uniform22.t1.s0.profile.a1
REP=fga03.t75.uniform22.t1.attribution.a3.split-check
KEPT=/data/yanruj/EvolveSWDB_runs/fga03-real-pair-20261011-a1/a2
S=$RAW/records10
if [ $CHECK -eq 1 ]; then
  printf 'checkout=%s\nsrc=%s\nlane=%s\nraw=%s\nstore=%s\nevaluations=%s %s\nprofiles=%s %s\nreport=%s\n' \
    "$CO" "$SRC" "$LANE" "$RAW" "$S" "$BEV" "$CEV" "$BPR" "$CPR" "$REP"
  for side in baseline candidate; do
    for kind in evaluation profile; do
      f="$SRC/$EV/cpud10.t75-$side.uniform22.t1.s0.$kind.a1.request.yaml"
      [ -f "$f" ] && echo "request ok: $f" || echo "request MISSING: $f"
    done
  done
  exit 0
fi
export PYTHONDONTWRITEBYTECODE=1
cd "$SRC" || exit 12
mkdir -p "$RAW/runs" || exit 12
log() { echo "$(TZ=America/New_York date '+%Y-%m-%d %H:%M:%S ET') 10 $*" | tee -a "$RAW/order.log"; }
step() { local name=$1; shift; log "step $name begin"; /usr/bin/time -v "$@" > "$RAW/$name.out" 2> "$RAW/$name.stderr"; local rc=$?; log "step $name end rc=$rc"; return $rc; }
envsnap() { { TZ=America/New_York date; uptime; who | awk '{print $1}' | sort -u | tr '\n' ' '; echo; df -h /data1 /data;
  cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor; cat /sys/devices/system/cpu/intel_pstate/no_turbo;
  uname -a; numactl --show; git rev-parse HEAD; } > "$RAW/env-$1.txt" 2>&1; }
test -z "$(git status --porcelain)" || { log "dirty checkout"; exit 13; }
log "start commit=$(git rev-parse HEAD) lane=$LANE"
envsnap 10-start
# Kept counted binaries/wrappers (ticket 03): the .a3 protocols' run arguments name the wrappers.
# Identity before use (LR-06 evidence); compared with the ticket-03 manifest table afterwards.
for d in baseline-counted candidate-counted swdb-protected-cpu-wrapper-8yok3jhh swdb-protected-cpu-wrapper-bjvc5lh_; do
  ( cd "$KEPT/$d" && echo "$d files=$(find . -type f | wc -l) bytes=$(find . -type f -printf '%s\n' | awk '{s+=$1} END {print s}') manifest=$(find . -type f | sort | xargs sha256sum | sha256sum | cut -d' ' -f1)" ) >> "$RAW/kept-identity-before.txt" 2>&1
done
# Guard: both .a3 estimates exist with numeric seconds, and today (ET) is strictly later than both (F43).
python3 - "$BES" "$CES" <<'PY' || { log "guard refused"; exit 15; }
import sys
from swdb.store import Store
from swdb.writer import today
store = Store('records')
dates = []
for rid in sys.argv[1:]:
    e = store.get(rid, 'estimate')
    assert e is not None, f'{rid} missing'
    assert isinstance(e.get('seconds'), (int, float)), f'{rid} seconds is {e.get("seconds")!r}'
    dates.append(str(e['created']))
assert today() > max(dates), f'today {today()} is not after the estimates ({max(dates)})'
print('guard ok: today', today(), 'estimates', dates)
PY
test ! -e "$S" || { log "scratch store exists"; exit 16; }
cp -a records "$S" || exit 17
log "scratch store copied ($(du -sh "$S" | cut -f1))"
for side in baseline candidate; do
  step "evaluate-$side" timeout 10800 python3 -m swdb evaluate "$EV/cpud10.t75-$side.uniform22.t1.s0.evaluation.a1.request.yaml" \
    --records "$S" --runs-dir "$RAW/runs" --lane "$LANE" --format json || exit 11
done
for side in baseline candidate; do
  step "profile-$side" timeout 14400 python3 -m swdb bfs-profile "$EV/cpud10.t75-$side.uniform22.t1.s0.profile.a1.request.yaml" \
    --records "$S" --runs-dir "$RAW/runs" --lane "$LANE" --format json || exit 21
done
step attribute timeout 7200 python3 -m swdb attribute --records "$S" --library "$SRC/library" \
  --baseline-estimate "$BES" --candidate-estimate "$CES" --baseline-source "$BC" --candidate-source "$CC" \
  --baseline-profile "$BPR" --candidate-profile "$CPR" --id "$REP" --format json || exit 31
step validate timeout 7200 python3 -m swdb validate --records "$S" --library "$SRC/library" || exit 41
( cd "$S" && sha256sum "evaluations/$BEV.yaml" "evaluations/$CEV.yaml" "region_profiles/$BPR.yaml" \
  "region_profiles/$CPR.yaml" "attributions/$REP.yaml" ) > "$RAW/records-sha256.txt" 2>&1
envsnap 10-end
log "job 10 done"
