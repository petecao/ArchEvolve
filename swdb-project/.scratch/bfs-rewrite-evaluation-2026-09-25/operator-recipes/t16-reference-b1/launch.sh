#!/usr/bin/env bash
# Created 2026-09-27 ET. One T16 reference lane job in one named tmux pane; no retries.
# Updated 2026-09-28 ET: JOB selects b1 (default) or the split jobs m, s1, s2.
set -eu
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONUSERBASE PYTHONOPTIMIZE PYTEST_ADDOPTS PYTEST_PLUGINS LD_PRELOAD LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PATH=/usr/bin:/bin
: "${OPERATOR:?runtime checkout operator path required}"
: "${OPERATOR_SHA:?reviewed operator SHA required}"
: "${ADMISSION_SHA:?exact admission SHA required}"
[[ "$(sha256sum "$OPERATOR" | cut -d' ' -f1)" == "$OPERATOR_SHA" ]] || exit 64
JOB=${JOB:-b1}
case "$JOB" in
  b1) PLAN_ID=bfs-t16-reference-simulator-batch-20260927-b1 ;;
  m|s1|s2) PLAN_ID=bfs-t16-reference-$JOB-simulator-batch-20260928-c1 ;;
  m-c2|s1-c2|s2-c2) PLAN_ID=bfs-t16-reference-${JOB%-c2}-simulator-batch-20260929-c2 ;;
  *) exit 64 ;;
esac
D=/data/yanruj/EvolveSWDB_runs/$PLAN_ID.dispatch
[[ -d "$D" && ! -e "$D/outer.exit" && ! -e "$D/outer.stdout" ]] || exit 64
PANE_PID=$BASHPID
TICKS=$(/usr/bin/python3.12 -I -B - "$PANE_PID" <<'PY'
import sys
from pathlib import Path
print(int(Path('/proc',sys.argv[1],'stat').read_text().rsplit(')',1)[1].split()[19]))
PY
)
set +e
/usr/bin/python3.12 -I -B "$OPERATOR" launch --job "$JOB" --admission-sha256 "$ADMISSION_SHA" --pane-pid "$PANE_PID" --pane-start-ticks "$TICKS" >"$D/outer.stdout" 2>"$D/outer.stderr"
result=$?
printf '%s\n' "$result" >"$D/outer.exit"
date --iso-8601=ns >"$D/outer.finished"
exit "$result"
