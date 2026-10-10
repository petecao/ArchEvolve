#!/usr/bin/env bash
# Prepared 2026-09-27 ET; one batch in one named tmux pane, no retries.
set -eu
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONUSERBASE PYTHONOPTIMIZE PYTEST_ADDOPTS PYTEST_PLUGINS LD_PRELOAD LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PATH=/usr/bin:/bin
: "${OPERATOR:?Git-materialized simulator recovery operator required}"
: "${OPERATOR_SHA:?reviewed operator SHA required}"
: "${CONFIG:?sealed prospective config required}"
: "${CONFIG_SHA:?reviewed config SHA required}"
: "${KIND:?t15 or t16 required}"
: "${ADMISSION_SHA:?exact admission SHA required}"
[[ "$KIND" == t15 || "$KIND" == t16 ]] || exit 64
[[ "$(sha256sum "$OPERATOR" | cut -d' ' -f1)" == "$OPERATOR_SHA" ]] || exit 64
[[ "$(sha256sum "$CONFIG" | cut -d' ' -f1)" == "$CONFIG_SHA" ]] || exit 64
D="/data/yanruj/EvolveSWDB_runs/bfs-${KIND}-supervision-recovery-simulator-batch-20260926-a1.dispatch"
[[ -d "$D" && ! -e "$D/outer.exit" && ! -e "$D/outer.stdout" && ! -e "$D/outer.stderr" ]] || exit 64
PANE_PID=$BASHPID
TICKS=$(/usr/bin/python3.12 -I -B - "$PANE_PID" <<'PY'
import sys
from pathlib import Path
print(int(Path('/proc',sys.argv[1],'stat').read_text().rsplit(')',1)[1].split()[19]))
PY
)
set +e
/usr/bin/python3.12 -I -B "$OPERATOR" launch "$KIND" "$CONFIG" --admission-sha256 "$ADMISSION_SHA" --pane-pid "$PANE_PID" --pane-start-ticks "$TICKS" >"$D/outer.stdout" 2>"$D/outer.stderr"
result=$?
printf '%s\n' "$result" >"$D/outer.exit"
date --iso-8601=ns >"$D/outer.finished"
exit "$result"
