#!/usr/bin/env bash
# Run a list of profiles one after another in one lane on mbit10. Created 2026-09-22.
#
# USAGE (on mbit10, inside tmux)
#   bash scripts/mbit10/profile_batch.sh <node> <list-file>
# Each line of <list-file>: <implementation> <input> [swdb profile options...]; blank
# lines and lines starting with # are skipped. Every run goes through profile_in_lane.sh.
# A failed run is reported and the batch goes on; the exit code is the number of failures.
set -uo pipefail
NODE="$1"; LIST="$2"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
failures=0
while read -r impl input rest; do
  case "$impl" in ''|'#'*) continue ;; esac
  echo "=== $(date -u +%FT%TZ) start $impl $input $rest"
  # shellcheck disable=SC2086
  if bash "$HERE/profile_in_lane.sh" "$NODE" "$impl" "$input" $rest </dev/null; then
    echo "=== $(date -u +%FT%TZ) done $impl $input"
  else
    rc=$?
    echo "=== $(date -u +%FT%TZ) FAILED ($rc) $impl $input"
    failures=$((failures + 1))
  fi
done < "$LIST"
echo "=== $(date -u +%FT%TZ) batch finished, $failures failure(s)"
exit "$failures"
