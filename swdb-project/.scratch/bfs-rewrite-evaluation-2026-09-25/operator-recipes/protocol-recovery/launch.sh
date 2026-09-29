#!/usr/bin/env bash
# Fixed one-attempt 600-second group; created 2026-09-27 ET.
set -eu
: "${OPERATOR:?Git-materialized reviewed operator path required}"
: "${OPERATOR_SHA:?reviewed exact operator hash required}"
: "${CONFIG:?prospectively sealed configuration path required}"
: "${CONFIG_SHA:?reviewed exact configuration hash required}"
: "${TMUX:?run in a named tmux caller}"
[[ "$(sha256sum "$OPERATOR" | cut -d' ' -f1)" == "$OPERATOR_SHA" ]] || exit 64
[[ "$(sha256sum "$CONFIG" | cut -d' ' -f1)" == "$CONFIG_SHA" ]] || exit 64
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONUSERBASE PYTHONOPTIMIZE PYTEST_ADDOPTS PYTEST_PLUGINS LD_PRELOAD LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PATH=/usr/bin:/bin
readarray -t CLOCK < <(/usr/bin/python3.12 -I -B - <<'PYCODE'
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
start=datetime.now(ZoneInfo('America/New_York'))
print(start.isoformat());print((start+timedelta(seconds=600)).isoformat())
PYCODE
)
[[ ${#CLOCK[@]} -eq 2 ]] || exit 64
remaining=$(/usr/bin/python3.12 -I -B - "${CLOCK[1]}" <<'PYCODE'
import sys
from datetime import datetime
end=datetime.fromisoformat(sys.argv[1]);seconds=(end-datetime.now(end.tzinfo)).total_seconds()-1
assert seconds>0
print(str(seconds)+'s')
PYCODE
)
exec timeout --signal=TERM --kill-after=1s "$remaining" /usr/bin/python3.12 -I -B "$OPERATOR" run "$CONFIG" "${CLOCK[0]}" "${CLOCK[1]}"
