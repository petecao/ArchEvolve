#!/usr/bin/env bash
# One context submission; prepared 2026-09-26 ET. Run in one named tmux pane.
set -eu
# Caller also uses this controlled environment before starting Bash.
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONUSERBASE PYTHONOPTIMIZE PYTEST_PLUGINS LD_PRELOAD LD_LIBRARY_PATH
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PATH=/usr/bin:/bin
: "${RECIPE:?exact Git-materialized operational recipe required}"
: "${RECIPE_SHA:?exact reviewed recipe hash required}"
RAW=/data/yanruj/EvolveSWDB_runs/bfs-provider-context1-20260926-a1
DISPATCH="${RAW}.dispatch"
HELPER=/data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner/scripts/host/socket_lane.sh
[[ ! -e "$RAW" && ! -e "$DISPATCH" ]]
[[ "$(sha256sum "$RECIPE" | cut -d' ' -f1)" == "$RECIPE_SHA" ]]
[[ "$(sha256sum "$HELPER" | cut -d' ' -f1)" == 00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8 ]]
mkdir "$DISPATCH"
PANE_PID=$BASHPID
readarray -t CLOCK < <(/usr/bin/python3.12 -I -B - "$PANE_PID" "$DISPATCH" <<'PY'
import json,sys
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
start=datetime.now(ZoneInfo('America/New_York'));end=start+timedelta(seconds=750)
pid=int(sys.argv[1]);fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
value={'outer_started':start.isoformat(),'outer_deadline':end.isoformat(),'outer_seconds':750,
'work_seconds':720,'cleanup_seconds':30,'pane_identity':{'pid':pid,'start_ticks':int(fields[19])}}
(Path(sys.argv[2])/'launch.json').write_text(json.dumps(value,indent=2)+'\n')
for x in (value['outer_started'],value['outer_deadline'],pid,int(fields[19])):print(x)
PY
)
[[ ${#CLOCK[@]} -eq 4 ]]
remaining=$(/usr/bin/python3.12 -I -B - "${CLOCK[1]}" <<'PY'
import sys
from datetime import datetime
end=datetime.fromisoformat(sys.argv[1]);remaining=(end-datetime.now(end.tzinfo)).total_seconds()-30
assert remaining>0
print(f'{remaining:.6f}s')
PY
)
set +e
timeout --signal=TERM --kill-after=30s "$remaining" bash "$HELPER" 1 swdb-bfs-provider-context1-a1 --record "$DISPATCH/lane.json" -- \
  env -u PYTHONPATH -u PYTHONHOME -u PYTHONSTARTUP -u PYTHONUSERBASE -u PYTHONOPTIMIZE -u PYTEST_PLUGINS -u LD_PRELOAD -u LD_LIBRARY_PATH \
  PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PATH=/usr/bin:/bin CLAUDE_CONFIG_DIR=/data1/yanruj/.claude \
  /usr/bin/python3.12 -I -B -c 'import runpy,sys; recipe=sys.argv.pop(1); runpy.run_path(recipe)["wrapper_entry"]()' "$RECIPE" --outer-started "${CLOCK[0]}" --outer-deadline "${CLOCK[1]}" --pane-pid "${CLOCK[2]}" --pane-start-ticks "${CLOCK[3]}" \
  > "$DISPATCH/outer.stdout" 2> "$DISPATCH/outer.stderr"
result=$?
printf '%s\n' "$result" > "$DISPATCH/outer.exit"
date --iso-8601=ns > "$DISPATCH/outer.finished"
exit "$result"
