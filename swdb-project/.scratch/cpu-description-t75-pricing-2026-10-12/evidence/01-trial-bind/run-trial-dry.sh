#!/usr/bin/env bash
# cpud ticket 01, phase B fallback: both trial estimates in memory (not persisted) + summary.
# Created 2026-10-12 ET. Used because /data had 0-68 MB free from 03:38 ET (another session's
# pytest basetemp, 90 GB) and /data1 sits at 21 GB (rule floor 20 GB), so two committed estimates
# plus the sqlite rebuild (~2.5 GB peak) fit on neither disk. Writes only a small JSON on /data1.
set -uo pipefail
RAW=/data/yanruj/EvolveSWDB_runs/cpud01-trial-20261012-a1
OUT=/data1/yanruj/EvolveSWDB_runs/cpud01-trial-20261012-a1-small
E=.scratch/cpu-description-t75-pricing-2026-10-12/evidence/01-trial-bind
TD=mbit10.cpu.lanl20261006.t1.services.cpud01-trial.a1
BP=cpud01.t75-baseline.uniform22.t1.estimate.protocol.trial-a1.4994e86b6d3d6ef6
CP=cpud01.t75-candidate.uniform22.t1.estimate.protocol.trial-a1.620dd3e002a2d764
export PYTHONDONTWRITEBYTECODE=1
cd /data1/yanruj/ArchEvolve-cpud01-trial-20261012/swdb-project || exit 3
mkdir -p "$OUT"
log() { echo "$(TZ=America/New_York date '+%Y-%m-%d %H:%M:%S ET') D $*" | tee -a "$OUT/order.log"; }
test -z "$(git status --porcelain)" || { log "dirty checkout"; exit 4; }
log "dry start commit=$(git rev-parse HEAD) protocols baseline=$BP candidate=$CP"
{ TZ=America/New_York date; uptime; who | awk '{print $1}' | sort -u | tr '\n' ' '; echo; df -h /data1 /data;
  cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor; cat /sys/devices/system/cpu/intel_pstate/no_turbo;
  uname -a; numactl --show; git rev-parse HEAD; } > "$OUT/env-start-d.txt" 2>&1
log "step dry-estimates begin"
python3 "$E/dry_estimate_summary.py" --records "$RAW/records" --target-description "$TD" \
  --side "baseline=fga03.t75-baseline.uniform22.t1.characterization.a2,$BP" \
  --side "candidate=fga03.t75-candidate.uniform22.t1.characterization.a2,$CP" \
  --output "$OUT/unknowns-summary-trial.json" --detail "$OUT/unknown-regions-trial.json" 2> "$OUT/dry.stderr"
rc=$?
log "step dry-estimates end rc=$rc"
{ TZ=America/New_York date; uptime; df -h /data1 /data; } > "$OUT/env-end-d.txt" 2>&1
log "dry done"
exit $rc
