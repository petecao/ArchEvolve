#!/usr/bin/env bash
# Created: 2026-10-15 ET. Run inside a coordinated mbit10 socket lane; output is external to Git.
set -euo pipefail
# Usage: run_acceptance.sh <full frozen commit SHA> <matrix|safe|unsafe|constructs|native|entry-windows|bounded-windows|owner> [extra pytest arguments...]
PROBATA_EXPECTED_COMMIT="${1:?pass the full frozen commit SHA}"
PROBATA_SHARD="${2:?pass matrix, safe, unsafe, constructs, native, entry-windows, bounded-windows, or owner}"
shift 2
case "$PROBATA_EXPECTED_COMMIT" in *[!0-9a-f]*|'') exit 2 ;; esac
[ "${#PROBATA_EXPECTED_COMMIT}" -eq 40 ] || exit 2
case "$PROBATA_SHARD" in
  matrix)
    # Exact ticket27 original/qualified acceptance, serial. No broad catalog run.
    PROBATA_TESTS=(
      tests/test_proof_semantics.py::test_wp_proves_every_unit_cbmc_proves_with_the_same_proof_semantics
      tests/test_proof_semantics.py::test_wp_leaves_every_unit_cbmc_refutes_not_proven_never_refuted
      tests/test_proof_semantics.py::test_wp_capacity_agrees_at_32_and_leaves_33_not_proven
      tests/test_proof_semantics.py::test_a_store_frame_bound_that_omits_a_possible_write_stays_not_proven
      tests/test_proof_semantics.py::test_a_safe_unit_proves_pins_the_proof_semantics_and_lists_it_and_the_reduction_as_assumptions
      tests/test_proof_semantics.py::test_moving_any_one_tile_read_before_its_wait_is_refuted_at_that_reads_probe_on_both_forms
      tests/test_proof_semantics.py::test_get_tile_size_before_the_covering_wait_is_refuted_and_after_it_proves
      tests/test_proof_semantics.py::test_a_cpu_write_into_a_tile_an_uncovered_command_reads_is_refuted_and_a_read_is_not
      tests/test_proof_semantics.py::test_the_wait_rule_as_gem5_runs_it_proves
      tests/test_proof_semantics.py::test_reads_the_wait_rule_does_not_cover_are_refuted
      tests/test_proof_semantics.py::test_values_at_issue_prove_and_a_wrong_value_is_refuted
      tests/test_proof_semantics.py::test_an_address_in_an_uncovered_gathers_footprint_is_a_member_and_one_outside_is_not
      tests/test_proof_semantics.py::test_32_uncovered_commands_prove_and_33_end_not_proven_ghost_capacity
      tests/test_proof_semantics.py::test_a_record_that_pins_an_older_proof_semantics_version_stops_counting
      tests/test_proof_semantics.py::test_the_bfs_proof_semantics_entry_validates_with_a_version_and_one_contract_per_inventory_call
      tests/test_proof_semantics.py::test_framac_type_checks_the_ghost_state_logic_and_every_call_contract
      tests/test_proof_semantics.py::test_without_framac_the_contracts_are_reported_unchecked_never_valid
      tests/test_proof_semantics.py::test_the_call_inventory_is_read_from_the_read_offload_lowerings_and_tdstepmaa
      tests/test_proof_semantics.py::test_each_proof_semantics_check_is_shown_by_its_control
      tests/test_proof_semantics.py::test_a_ghost_array_declared_again_in_the_c_model_is_refused
      tests/test_proof_semantics.py::test_a_ghost_capacity_outside_the_command_mask_width_is_rejected_before_tools
      tests/test_proof_semantics_native.py)
    PROBATA_SELECTION=() ;;
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
