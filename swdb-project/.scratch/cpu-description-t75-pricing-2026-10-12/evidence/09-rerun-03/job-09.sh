#!/usr/bin/env bash
# cpud ticket 09: rerun fine-grained ticket 03 with services.v2 (no recount).
# Created 2026-10-12 ET. Runs on mbit10 inside one socket lane (socket_lane.sh), from a clean
# detached worktree of the pushed cpud/integration commit that holds services.v2. Both .a3
# protocols are frozen in this one job at that one commit (F47). Order: freeze baseline,
# freeze candidate, estimate baseline, estimate candidate, unknowns summary, unchecked attribute,
# whole-store validate. No application timing: workload bfs-20261004-uniform22 is not run (C12).
# Usage: bash job-09.sh <checkout root>
set -uo pipefail
SRC=$1/swdb-project
RAW=/data/yanruj/EvolveSWDB_runs/cpud0809-20261012-a1
FGA=.scratch/fine-grained-attribution-2026-10-11/evidence/03-first-real-pair
E01=.scratch/cpu-description-t75-pricing-2026-10-12/evidence/01-trial-bind
TD=mbit10.cpu.lanl20261006.t1.services.v2
BC=typed-library-bfs-scalar-profile-20261003-a1.baseline
CC=extensa-native-bfs-20261005-a8.it1.kronecker.a0
BCH=fga03.t75-baseline.uniform22.t1.characterization.a2
CCH=fga03.t75-candidate.uniform22.t1.characterization.a2
BES=fga03.t75-baseline.uniform22.t1.estimate.a3
CES=fga03.t75-candidate.uniform22.t1.estimate.a3
REP=fga03.t75.uniform22.t1.attribution.a3
S=$RAW/records09
export PYTHONDONTWRITEBYTECODE=1
cd "$SRC" || exit 3
log() { echo "$(TZ=America/New_York date '+%Y-%m-%d %H:%M:%S ET') 09 $*" | tee -a "$RAW/order.log"; }
step() { local name=$1; shift; log "step $name begin"; /usr/bin/time -v "$@" > "$RAW/$name.out" 2> "$RAW/$name.stderr"; local rc=$?; log "step $name end rc=$rc"; return $rc; }
envsnap() { { TZ=America/New_York date; uptime; who | awk '{print $1}' | sort -u | tr '\n' ' '; echo; df -h /data1 /data;
  cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor; cat /sys/devices/system/cpu/intel_pstate/no_turbo;
  uname -a; numactl --show; git rev-parse HEAD; } > "$RAW/env-$1.txt" 2>&1; }
test -z "$(git status --porcelain)" || { log "dirty checkout"; exit 4; }
log "start commit=$(git rev-parse HEAD)"
envsnap 09-start
test -f "records/target_descriptions/$TD.yaml" || { log "services.v2 not in the checkout"; exit 5; }
test ! -e "$S" || { log "scratch store exists"; exit 6; }
cp -a records "$S" || exit 7
log "scratch store copied ($(du -sh "$S" | cut -f1))"
python3 - "$RAW" "$TD" "$FGA" <<'PY' || exit 31
import sys, yaml
raw, td, fga = sys.argv[1:]
for side in ('baseline', 'candidate'):
    req = yaml.safe_load(open(f'{fga}/freeze-{side}.yaml'))
    assert req['id'] == f'fga03.t75-{side}.uniform22.t1.estimate.protocol.a2', req['id']
    req['id'] = f'fga03.t75-{side}.uniform22.t1.estimate.protocol.a3'
    req['settings']['target_description'] = td
    yaml.safe_dump(req, open(f'{raw}/freeze-{side}.a3.yaml', 'w'), sort_keys=False)
PY
for side in baseline candidate; do
  step "freeze-$side" timeout 7200 python3 -m swdb freeze-protocol "$RAW/freeze-$side.a3.yaml" --records "$S" --format json || exit 32
done
pid() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' "$1"; }
BP=$(pid "$RAW/freeze-baseline.out"); CP=$(pid "$RAW/freeze-candidate.out")
log "protocols baseline=$BP candidate=$CP"
step est-baseline timeout 7200 python3 -m swdb estimate --records "$S" --characterization "$BCH" --target-description "$TD" \
  --protocol "$BP" --id "$BES" --format json || exit 41
step est-candidate timeout 7200 python3 -m swdb estimate --records "$S" --characterization "$CCH" --target-description "$TD" \
  --protocol "$CP" --id "$CES" --format json || exit 42
step summary timeout 3600 python3 "$E01/unknowns_summary.py" --records "$S" \
  --estimate "baseline=$BES" --estimate "candidate=$CES" --output "$RAW/unknowns-summary-a3.json" \
  --note "cpud ticket 09: $TD estimates .a3 (store copy $S)"
step attribute timeout 7200 python3 -m swdb attribute --records "$S" --library "$SRC/library" \
  --baseline-estimate "$BES" --candidate-estimate "$CES" --baseline-source "$BC" --candidate-source "$CC" \
  --id "$REP" --format json
step validate timeout 7200 python3 -m swdb validate --records "$S" --library "$SRC/library"
envsnap 09-end
log "job 09 done"
