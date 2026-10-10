#!/usr/bin/env bash
# Created 2026-09-27 ET. One T17/T20 routes lane job in one named tmux pane; no retries.
set -eu
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONUSERBASE PYTHONOPTIMIZE PYTEST_ADDOPTS PYTEST_PLUGINS LD_PRELOAD LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PATH=/usr/bin:/bin
: "${OPERATOR:?runtime checkout operator path required}"
: "${OPERATOR_SHA:?reviewed operator SHA required}"
: "${ADMISSION_SHA:?exact admission SHA required}"
[[ "$(sha256sum "$OPERATOR" | cut -d' ' -f1)" == "$OPERATOR_SHA" ]] || exit 64
D=/data/yanruj/EvolveSWDB_runs/bfs-t17-t20-routes-simulator-batch-20260928-a1.dispatch
[[ -d "$D" && ! -e "$D/outer.exit" && ! -e "$D/outer.stdout" ]] || exit 64
PANE_PID=$BASHPID
TICKS=$(/usr/bin/python3.12 -I -B - "$PANE_PID" <<'PY'
import sys
from pathlib import Path
print(int(Path('/proc',sys.argv[1],'stat').read_text().rsplit(')',1)[1].split()[19]))
PY
)
set +e
/usr/bin/python3.12 -I -B "$OPERATOR" launch --admission-sha256 "$ADMISSION_SHA" --pane-pid "$PANE_PID" --pane-start-ticks "$TICKS" >"$D/outer.stdout" 2>"$D/outer.stderr"
result=$?
printf '%s\n' "$result" >"$D/outer.exit"
date --iso-8601=ns >"$D/outer.finished"
exit "$result"
