#!/usr/bin/env bash
# Ticket 03 (fine-grained attribution), attempt a2: t75 pair counts, fresh protocol, estimates.
# Created 2026-10-11 ET. Runs from /data1/yanruj/ArchEvolve-fga03/swdb-project at d0c80a8a.
# Order (LR-02): count baseline, count candidate, freeze protocol, estimate baseline, estimate candidate.
set -uo pipefail
RAW=/data/yanruj/EvolveSWDB_runs/fga03-real-pair-20261011-a1
A=$RAW/a2
LLVM=/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin
TD=mbit10.cpu.lanl20261006.t1.services.v1
WL=bfs-20261004-uniform22.2f83a134a6bef789
BC=typed-library-bfs-scalar-profile-20261003-a1.baseline
CC=extensa-native-bfs-20261005-a8.it1.kronecker.a0
BCH=fga03.t75-baseline.uniform22.t1.characterization.a2
CCH=fga03.t75-candidate.uniform22.t1.characterization.a2
BES=fga03.t75-baseline.uniform22.t1.estimate.a2
CES=fga03.t75-candidate.uniform22.t1.estimate.a2
export PYTHONDONTWRITEBYTECODE=1
cd /data1/yanruj/ArchEvolve-fga03/swdb-project || exit 3
mkdir -p "$A"
log() { echo "$(TZ=America/New_York date '+%Y-%m-%d %H:%M:%S ET') a2 $*" | tee -a "$RAW/order.log"; }
log "start commit=$(git rev-parse HEAD)"
{ date -u; uptime; who | awk '{print $1}' | sort -u | tr '\n' ' '; echo; df -h /data1 /data;
  cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor; cat /sys/devices/system/cpu/intel_pstate/no_turbo;
  uname -a; numactl --show; } > "$A/env-start.txt" 2>&1
step() { local name=$1; shift; log "step $name begin"; "$@" > "$A/$name.json" 2> "$A/$name.stderr"; local rc=$?; log "step $name end rc=$rc"; return $rc; }
count() { # side candidate id
  step "char-$1" python3 -m swdb characterize --records "$RAW/records" --candidate "$2" --adapter registered-cpu \
    --evaluation-request "$RAW/fga03.t75-$1.uniform22.t1.request.a1.yaml" --input "$WL" --threads 1 --trials 1 \
    --source-position 0 --repetition 0 --object-scopes --counting-pipeline source-normalized-v2 --llvm-bin "$LLVM" \
    --output "$A/$1-counted" --timeout-s 3600 --id "$3" --format json; }
count baseline "$BC" "$BCH" || exit 21
count candidate "$CC" "$CCH" || exit 22
python3 - "$A" "$TD" "$WL" "$BC" "$CC" <<'PY' || exit 30
import json, sys, yaml
a, td, wl, bc, cc = sys.argv[1:]
b = json.load(open(f'{a}/char-baseline.json')); c = json.load(open(f'{a}/char-candidate.json'))
same = b['source']['run_arguments'] == c['source']['run_arguments']
sides = [('pair', b, [bc, cc])] if same else [('baseline', b, [bc]), ('candidate', c, [cc])]
for name, ch, sources in sides:
    req = {'message_version': '1.0', 'id': f'fga03.t75-{name}.uniform22.t1.estimate.protocol.a2', 'version': 1,
           'settings': {'mode': 'estimated', 'estimator_version': 'swdb.analytic.v1', 'target_description': td,
                        'threads': 1, 'roi': ch['binding']['roi'], 'sources': sources, 'inputs': [wl],
                        'input_run_arguments': {wl: ch['source']['run_arguments']}}}
    yaml.safe_dump(req, open(f'{a}/freeze-{name}.yaml', 'w'), sort_keys=False)
print('protocols:', [s[0] for s in sides])
PY
for f in "$A"/freeze-*.yaml; do n=$(basename "$f" .yaml); step "$n" python3 -m swdb freeze-protocol "$f" --records "$RAW/records" --format json || exit 31; done
pid() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' "$1"; }
if [ -f "$A/freeze-pair.json" ]; then BP=$(pid "$A/freeze-pair.json"); CP=$BP; else BP=$(pid "$A/freeze-baseline.json"); CP=$(pid "$A/freeze-candidate.json"); fi
log "protocols baseline=$BP candidate=$CP"
step est-baseline python3 -m swdb estimate --records "$RAW/records" --characterization "$BCH" --target-description "$TD" --protocol "$BP" --id "$BES" --format json || exit 41
step est-candidate python3 -m swdb estimate --records "$RAW/records" --characterization "$CCH" --target-description "$TD" --protocol "$CP" --id "$CES" --format json || exit 42
{ date -u; uptime; df -h /data1 /data; } > "$A/env-end.txt" 2>&1
log "estimates done"
