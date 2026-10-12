#!/usr/bin/env bash
# cpud ticket 01, phase B resume: both estimates and the unknowns summary.
# Created 2026-10-12 ET. Needed because the candidate freeze-protocol (run-trial.sh) wrote and
# validated its protocol record at 03:32 ET but exited 120 at 03:38 ET: /data reached 0 bytes
# free (another session's pytest basetemp), so the sqlite rebuild and the stdout flush failed.
# The two frozen protocol IDs are taken from the scratch store, not re-frozen.
set -uo pipefail
RAW=/data/yanruj/EvolveSWDB_runs/cpud01-trial-20261012-a1
E=.scratch/cpu-description-t75-pricing-2026-10-12/evidence/01-trial-bind
TD=mbit10.cpu.lanl20261006.t1.services.cpud01-trial.a1
BCH=fga03.t75-baseline.uniform22.t1.characterization.a2
CCH=fga03.t75-candidate.uniform22.t1.characterization.a2
BP=cpud01.t75-baseline.uniform22.t1.estimate.protocol.trial-a1.4994e86b6d3d6ef6
CP=cpud01.t75-candidate.uniform22.t1.estimate.protocol.trial-a1.620dd3e002a2d764
export PYTHONDONTWRITEBYTECODE=1
cd /data1/yanruj/ArchEvolve-cpud01-trial-20261012/swdb-project || exit 3
log() { echo "$(TZ=America/New_York date '+%Y-%m-%d %H:%M:%S ET') C $*" | tee -a "$RAW/order.log"; }
step() { local name=$1; shift; log "step $name begin"; "$@" > "$RAW/$name.json" 2> "$RAW/$name.stderr"; local rc=$?; log "step $name end rc=$rc"; return $rc; }
space() { local free; free=$(df -B1G --output=avail /data | tail -1 | tr -d ' '); log "/data free ${free}G"; [ "$free" -ge 4 ] || { log "under 4G free on /data: stop"; exit 7; }; }
test -z "$(git status --porcelain)" || { log "dirty checkout"; exit 4; }
log "resume commit=$(git rev-parse HEAD) protocols baseline=$BP candidate=$CP"
for p in "$BP" "$CP"; do test -f "$RAW/records/protocols/$p.yaml" || { log "missing $p"; exit 5; }; done
{ TZ=America/New_York date; uptime; who | awk '{print $1}' | sort -u | tr '\n' ' '; echo; df -h /data1 /data;
  cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor; cat /sys/devices/system/cpu/intel_pstate/no_turbo;
  uname -a; numactl --show; git rev-parse HEAD; } > "$RAW/env-start-c.txt" 2>&1
space
step est-baseline python3 -m swdb estimate --records "$RAW/records" --characterization "$BCH" --target-description "$TD" \
  --protocol "$BP" --id cpud01.t75-baseline.uniform22.t1.estimate.trial-a1 --format json || exit 41
space
step est-candidate python3 -m swdb estimate --records "$RAW/records" --characterization "$CCH" --target-description "$TD" \
  --protocol "$CP" --id cpud01.t75-candidate.uniform22.t1.estimate.trial-a1 --format json || exit 42
log "step summary begin"
python3 "$E/unknowns_summary.py" --records "$RAW/records" \
  --estimate baseline=cpud01.t75-baseline.uniform22.t1.estimate.trial-a1 \
  --estimate candidate=cpud01.t75-candidate.uniform22.t1.estimate.trial-a1 \
  --output "$RAW/unknowns-summary-trial.json" \
  --note "C4 trial: $TD (scratch store $RAW/records, not committed)" 2> "$RAW/summary.stderr"
log "step summary end rc=$?"
{ TZ=America/New_York date; uptime; df -h /data1 /data; } > "$RAW/env-end-c.txt" 2>&1
log "resume done"
