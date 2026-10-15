#!/usr/bin/env bash
# Created: 2026-10-15 ET. Run inside a coordinated mbit10 socket lane; output is external to Git.
set -euo pipefail
: "${PROBATA_OUTPUT:?set PROBATA_OUTPUT to the external run directory}"
: "${PROBATA_PYTHON:?set PROBATA_PYTHON to the pytest interpreter}"
mkdir -p "$PROBATA_OUTPUT/tmp" "$PROBATA_OUTPUT/cache"
export TMPDIR="$PROBATA_OUTPUT/tmp" XDG_CACHE_HOME="$PROBATA_OUTPUT/cache"
export SWDB_VERIFIER_RSS_CAP_BYTES=8589934592
# Each output belongs to one leased socket. One verifier per socket; the coordinator reserves at most two.
export SWDB_VERIFIER_LOCK="$PROBATA_OUTPUT/verifier.lock"
cd "$(git rev-parse --show-toplevel)/swdb-project"
git rev-parse HEAD > "$PROBATA_OUTPUT/source-commit.txt"
{
  date -u
  uptime
  df -h /data1 /data
  uname -a
  lscpu
  numactl --hardware
  printf 'verifier_lock=%s\n' "$SWDB_VERIFIER_LOCK"
  printf 'rss_cap_bytes=%s\n' "$SWDB_VERIFIER_RSS_CAP_BYTES"
  grep -H '"state"' /data1/yanruj/lact-host-lease/mbit10-evaluation*.meta.json
} > "$PROBATA_OUTPUT/environment.txt"
set +e
"$PROBATA_PYTHON" -m pytest tests/test_proof_semantics.py -q --tb=short \
  --basetemp "$PROBATA_OUTPUT/pytest" --report-log "$PROBATA_OUTPUT/report.jsonl" "$@" \
  > "$PROBATA_OUTPUT/pytest.log" 2>&1
status=$?
printf '%s\n' "$status" > "$PROBATA_OUTPUT/exit-code.txt"
exit "$status"
