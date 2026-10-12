#!/usr/bin/env bash
# cpud ticket 01, phase B: C4 trial bind (services.v1 inputs + the two t75 counts in the allowlist,
# plus their OpenMP projections), trial protocols, both estimates, unknowns summary.
# Created 2026-10-12 ET. Runs on mbit10 under the node1 socket lane from a clean worktree.
# Writes only into the scratch store $RAW/records (never the repo store). No timing of any
# application: estimates are analytic (C12; workload bfs-20261004-uniform22 is not timed).
set -uo pipefail
RAW=/data/yanruj/EvolveSWDB_runs/cpud01-trial-20261012-a1
A2=/data/yanruj/EvolveSWDB_runs/fga03-real-pair-20261011-a1/a2
E=.scratch/cpu-description-t75-pricing-2026-10-12/evidence/01-trial-bind
FGA=.scratch/fine-grained-attribution-2026-10-11/evidence/03-first-real-pair
BASE=mbit10.cpu.lanl20261006a2.v2.t1
TD=mbit10.cpu.lanl20261006.t1.services.cpud01-trial.a1
BCH=fga03.t75-baseline.uniform22.t1.characterization.a2
CCH=fga03.t75-candidate.uniform22.t1.characterization.a2
export PYTHONDONTWRITEBYTECODE=1
cd /data1/yanruj/ArchEvolve-cpud01-trial-20261012/swdb-project || exit 3
log() { echo "$(TZ=America/New_York date '+%Y-%m-%d %H:%M:%S ET') B $*" | tee -a "$RAW/order.log"; }
step() { local name=$1; shift; log "step $name begin"; "$@" > "$RAW/$name.json" 2> "$RAW/$name.stderr"; local rc=$?; log "step $name end rc=$rc"; return $rc; }
test -z "$(git status --porcelain)" || { log "dirty checkout"; exit 4; }
log "start commit=$(git rev-parse HEAD)"
{ TZ=America/New_York date; uptime; who | awk '{print $1}' | sort -u | tr '\n' ' '; echo; df -h /data1 /data;
  cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor; cat /sys/devices/system/cpu/intel_pstate/no_turbo;
  uname -a; numactl --show; git rev-parse HEAD; } > "$RAW/env-start-b.txt" 2>&1
test ! -e "$RAW/records" || { log "scratch store exists"; exit 5; }
cp -a records "$RAW/records" || exit 6
log "scratch store copied ($(du -sh "$RAW/records" | cut -f1))"
step bind python3 -m swdb.cpu_service_binding --records "$RAW/records" \
  --target-description "$BASE" \
  --characterization bfs.kron-g16.t1.characterization.objects.a1 \
  --scope-characterization bc.kron-g16.t1.characterization.objects.a1 \
  --scope-characterization bfs.kron-g17.t1.characterization.objects.a1 \
  --scope-characterization bc.kron-g17.t1.characterization.objects.a1 \
  --scope-characterization "$BCH" \
  --scope-characterization "$CCH" \
  --calibration mbit10.cpu.lanl20261006.service.clock.a2 \
  --calibration mbit10.cpu.lanl20261006.resource.allocator.a1 \
  --calibration mbit10.cpu.lanl20261006.resource.allocator-extra.a1 \
  --calibration mbit10.cpu.lanl20261006.resource.memory.a1 \
  --calibration mbit10.cpu.lanl20261006.resource.float-memory.a1 \
  --calibration mbit10.cpu.lanl20261006.service.byte-read.a1 \
  --calibration mbit10.cpu.lanl20261006.resource.bulk-total.a1 \
  --calibration mbit10.cpu.lanl20261006.resource.bulk-total.a2 \
  --calibration mbit10.cpu.lanl20261006.service.openmp.a1 \
  --memory-footprint-bytes 8388608 \
  --memory-cas-policy max_constructed_success_failure_median \
  --bulk-profile-policy max_constructed_profiles_median \
  --bulk-copy-calibration mbit10.cpu.lanl20261006.resource.bulk-total.a1 \
  --openmp-next-policy max_constructed_success_failure_median \
  --openmp-projection .scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-openmp-bfs.g16-projection-mbit10-20261006-a1.json \
  --openmp-projection .scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-openmp-bc.g16-projection-mbit10-20261006-a1.json \
  --openmp-projection .scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-openmp-bfs.g17-projection-mbit10-20261006-a1.json \
  --openmp-projection .scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-openmp-bc.g17-projection-mbit10-20261006-a1.json \
  --openmp-projection "$E/openmp-t75-baseline-projection-mbit10-20261012-a1.json" \
  --openmp-projection "$E/openmp-t75-candidate-projection-mbit10-20261012-a1.json" \
  --id "$TD" --format json || exit 30
python3 - "$RAW" "$TD" "$FGA" <<'PY' || exit 31
import sys, yaml
raw, td, fga = sys.argv[1:]
for side in ('baseline', 'candidate'):
    req = yaml.safe_load(open(f'{fga}/freeze-{side}.yaml'))
    req['id'] = f'cpud01.t75-{side}.uniform22.t1.estimate.protocol.trial-a1'
    req['settings']['target_description'] = td
    yaml.safe_dump(req, open(f'{raw}/freeze-{side}.yaml', 'w'), sort_keys=False)
PY
for side in baseline candidate; do
  step "freeze-$side" python3 -m swdb freeze-protocol "$RAW/freeze-$side.yaml" --records "$RAW/records" --format json || exit 32
done
pid() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' "$1"; }
BP=$(pid "$RAW/freeze-baseline.json"); CP=$(pid "$RAW/freeze-candidate.json")
log "protocols baseline=$BP candidate=$CP"
step est-baseline python3 -m swdb estimate --records "$RAW/records" --characterization "$BCH" --target-description "$TD" \
  --protocol "$BP" --id cpud01.t75-baseline.uniform22.t1.estimate.trial-a1 --format json || exit 41
step est-candidate python3 -m swdb estimate --records "$RAW/records" --characterization "$CCH" --target-description "$TD" \
  --protocol "$CP" --id cpud01.t75-candidate.uniform22.t1.estimate.trial-a1 --format json || exit 42
log "step summary begin"
python3 "$E/unknowns_summary.py" --records "$RAW/records" \
  --estimate baseline=cpud01.t75-baseline.uniform22.t1.estimate.trial-a1 \
  --estimate candidate=cpud01.t75-candidate.uniform22.t1.estimate.trial-a1 \
  --output "$RAW/unknowns-summary-trial.json" \
  --note "C4 trial: $TD (scratch store $RAW/records, not committed)" 2> "$RAW/summary.stderr"
log "step summary end rc=$?"
{ TZ=America/New_York date; uptime; df -h /data1 /data; } > "$RAW/env-end-b.txt" 2>&1
log "phase B done"
