#!/usr/bin/env bash
# Created: 2026-10-15 ET. Run inside a coordinated mbit10 socket lane; output is external to Git.
set -euo pipefail
# Usage: run_acceptance.sh <full frozen commit SHA> <safe|unsafe|constructs|native|entry-windows|bounded-windows|owner> [extra pytest arguments...]
PROBATA_EXPECTED_COMMIT="${1:?pass the full frozen commit SHA}"
PROBATA_SHARD="${2:?pass safe, unsafe, constructs, native, entry-windows, bounded-windows, or owner}"
shift 2
case "$PROBATA_EXPECTED_COMMIT" in *[!0-9a-f]*|'') exit 2 ;; esac
[ "${#PROBATA_EXPECTED_COMMIT}" -eq 40 ] || exit 2
case "$PROBATA_SHARD" in
  safe)
    PROBATA_TESTS=(tests/test_proof_semantics.py tests/test_proof_semantics_admission.py
      tests/test_proof_semantics_native.py tests/test_memory_admission_dependencies.py
      tests/test_bounded_initialization.py tests/test_bounded_pointers.py)
    PROBATA_SELECTION=( -k 'not wp_leaves' ) ;;
  unsafe)
    PROBATA_TESTS=(tests/test_proof_semantics.py)
    PROBATA_SELECTION=( -k wp_leaves ) ;;
  constructs)
    PROBATA_TESTS=(tests/test_wp_subset.py)
    PROBATA_SELECTION=() ;;
  native)
    # Compiler/differential checkpoint only; this shard does not run WP/CBMC.
    PROBATA_TESTS=(tests/test_c_lowering.py tests/test_proof_semantics_native.py
      tests/test_array_domain_math.py tests/test_array_domains.py)
    PROBATA_SELECTION=(-k 'not cbmc') ;;
  entry-windows)
    PROBATA_TESTS=(tests/test_entry_array_domains.py)
    PROBATA_SELECTION=() ;;
  bounded-windows)
    PROBATA_TESTS=(tests/test_bounded_entry_windows.py tests/test_bounded_entry_window_view.py)
    PROBATA_SELECTION=() ;;
  owner)
    PROBATA_TESTS=(tests/test_vector_ownership_wp.py)
    PROBATA_SELECTION=() ;;
  *) exit 2 ;;
esac
PROBATA_ACTUAL_COMMIT="$(git rev-parse HEAD)"
[ "$PROBATA_ACTUAL_COMMIT" = "$PROBATA_EXPECTED_COMMIT" ] || {
  echo 'acceptance source differs from the frozen commit' >&2; exit 2;
}
[ -z "$(git status --porcelain --untracked-files=no)" ] || {
  echo 'acceptance source has tracked changes' >&2; exit 2;
}
: "${PROBATA_OUTPUT:?set PROBATA_OUTPUT to the external run directory}"
: "${PROBATA_PYTHON:?set PROBATA_PYTHON to the pytest interpreter}"
mkdir -p "$PROBATA_OUTPUT/tmp" "$PROBATA_OUTPUT/cache"
export TMPDIR="$PROBATA_OUTPUT/tmp" XDG_CACHE_HOME="$PROBATA_OUTPUT/cache"
export SWDB_VERIFIER_RSS_CAP_BYTES=8589934592
# Each output belongs to one leased socket. One verifier per socket; the coordinator reserves at most two.
export SWDB_VERIFIER_LOCK="$PROBATA_OUTPUT/verifier.lock"
cd "$(git rev-parse --show-toplevel)/swdb-project"
git rev-parse HEAD > "$PROBATA_OUTPUT/source-commit.txt"
printf '%s\n' "$PROBATA_SHARD" > "$PROBATA_OUTPUT/shard.txt"
printf '%q ' "$PROBATA_PYTHON" -m pytest "${PROBATA_TESTS[@]}" "${PROBATA_SELECTION[@]}" "$@" \
  > "$PROBATA_OUTPUT/selection.txt"
{
  date -u
  uptime
  df -h /data1 /data
  printf 'logged_in_users:\n'
  who | awk '{print $1}' | sort -u
  for PROBATA_HOST_SETTING in \
      /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor \
      /sys/devices/system/cpu/intel_pstate/no_turbo; do
    printf '%s=' "$PROBATA_HOST_SETTING"
    if [ -r "$PROBATA_HOST_SETTING" ]; then cat "$PROBATA_HOST_SETTING"; else printf 'unavailable\n'; fi
  done
  uname -a
  lscpu
  numactl --hardware
  printf 'verifier_lock=%s\n' "$SWDB_VERIFIER_LOCK"
  printf 'rss_cap_bytes=%s\n' "$SWDB_VERIFIER_RSS_CAP_BYTES"
  grep -H '"state"' /data1/yanruj/lact-host-lease/mbit10-evaluation*.meta.json
} > "$PROBATA_OUTPUT/environment.txt"
set +e
"$PROBATA_PYTHON" -m pytest "${PROBATA_TESTS[@]}" "${PROBATA_SELECTION[@]}" -q --tb=short \
  --basetemp "$PROBATA_OUTPUT/pytest" --report-log "$PROBATA_OUTPUT/report.jsonl" "$@" \
  > "$PROBATA_OUTPUT/pytest.log" 2>&1
status=$?
printf '%s\n' "$status" > "$PROBATA_OUTPUT/exit-code.txt"
exit "$status"
