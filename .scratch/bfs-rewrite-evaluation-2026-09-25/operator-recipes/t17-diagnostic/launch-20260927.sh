#!/usr/bin/env bash
# Prospective guarded launch, created 2026-09-27 ET. Admission SHA remains explicit; no dispatch by preparation.
# Invoke Bash itself with loader overrides unset. No clock starts with placeholders.
set -eu
CODE=/data1/yanruj/EvolveSWDB_supervision_recovery_runtime_20260927_a1
CODE_COMMIT=8cbfee600f23416a8e9578fa8d3ce3f0e19fced8
: "${ADMISSION_SHA:?sealed exact admission SHA required}"
NODE=1
[[ "$CODE" == /data1/yanruj/* && "$CODE_COMMIT" =~ ^[0-9a-f]{40}$ && "$ADMISSION_SHA" =~ ^[0-9a-f]{64}$ ]] || exit 64
[[ "$NODE" == 0 || "$NODE" == 1 ]] || exit 64
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONUSERBASE PYTHONOPTIMIZE PYTEST_ADDOPTS PYTEST_PLUGINS
unset GCC_EXEC_PREFIX COMPILER_PATH LIBRARY_PATH CPATH CPLUS_INCLUDE_PATH C_INCLUDE_PATH LD_PRELOAD LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PATH=/usr/bin:/bin
PY=/usr/bin/python3.12
RAW=/data/yanruj/EvolveSWDB_runs/bfs-t17-diagnostic-build-only-20260926-a1
DISPATCH="${RAW}.dispatch"
HELPER=/data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner/scripts/host/socket_lane.sh
[[ ! -e "$RAW" && -d "$DISPATCH" && ! -L "$DISPATCH" ]] || exit 64
[[ -f "$DISPATCH/admission.json" && ! -L "$DISPATCH/admission.json" ]] || exit 64
[[ "$(sha256sum "$DISPATCH/admission.json" | cut -d' ' -f1)" == "$ADMISSION_SHA" ]] || exit 64
[[ "$(sha256sum "$PY" | cut -d' ' -f1)" == e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f ]] || exit 64
[[ "$(sha256sum "$HELPER" | cut -d' ' -f1)" == 00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8 ]] || exit 64
[[ "$(git -C "$CODE" rev-parse HEAD)" == "$CODE_COMMIT" ]] || exit 64
# Full runtime/import inventory, fixed request and sealed five-case proof are
# checked before this wrapper is admitted; the existing driver repeats them.
PREPARER=/data1/yanruj/EvolveSWDB_t17_operator_20260927_a1/.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/t17-diagnostic/prepare.py
MANIFEST="$(dirname "$PREPARER")/runtime-manifest.json"
PREPARER_SHA=7dae8d604d19c874066e715e049b974c68fbbd29018cc7200e3e90355c0d73da
MANIFEST_SHA=447ff528f5015587c702d42007a3607cf0373a800714d8ab59a515cdf9c7afc9
[[ "$(sha256sum "$PREPARER" | cut -d' ' -f1)" == "$PREPARER_SHA" ]] || exit 64
[[ "$(sha256sum "$MANIFEST" | cut -d' ' -f1)" == "$MANIFEST_SHA" ]] || exit 64
PANE_PID=$BASHPID
readarray -t CLOCK < <("$PY" -I -B - "$PANE_PID" "$DISPATCH" <<'PY'
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import json,os,sys
begin=datetime.now(ZoneInfo('America/New_York'));end=begin+timedelta(seconds=600)
pid=int(sys.argv[1]);fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
value={'outer_started':begin.isoformat(),'outer_deadline':end.isoformat(),'outer_seconds':600,
       'work_seconds':570,'cleanup_seconds':30,'pane_identity':{'pid':pid,'start_ticks':int(fields[19])}}
with (Path(sys.argv[2])/'launch.json').open('x') as stream:
    json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
for x in (value['outer_started'],value['outer_deadline'],pid,int(fields[19])):print(x)
PY
)
[[ ${#CLOCK[@]} -eq 4 ]] || exit 64
remaining=$("$PY" -I -B - "${CLOCK[1]}" <<'PY'
from datetime import datetime
import sys
end=datetime.fromisoformat(sys.argv[1]);left=(end-datetime.now(end.tzinfo)).total_seconds()-30
assert left>0
print(f'{left:.6f}s')
PY
)
set +e
timeout --signal=TERM --kill-after=30s "$remaining" bash "$HELPER" "$NODE" swdb-t17-diagnostic-a1 --record "$DISPATCH/lane.json" -- \
  "$PY" -I -B "$PREPARER" invoke --manifest "$MANIFEST" --manifest-sha256 "$MANIFEST_SHA" \
  --expected-commit "$CODE_COMMIT" --admission "$DISPATCH/admission.json" --admission-sha256 "$ADMISSION_SHA" --lane "$NODE" \
  --outer-started "${CLOCK[0]}" --outer-deadline "${CLOCK[1]}" --pane-pid "${CLOCK[2]}" --pane-start-ticks "${CLOCK[3]}" \
  > "$DISPATCH/outer.stdout" 2> "$DISPATCH/outer.stderr"
status=$?
printf '%s\n' "$status" > "$DISPATCH/outer.exit"
date --iso-8601=ns > "$DISPATCH/outer.finished"
exit "$status"
