# 39 — Prefactor: kernel plug-in seam, gem5 side

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 23
**Spec:** `../spec.md`

**What to build:** The gem5 side of the evaluator handles kernels through plug-ins, with BFS as the only one.

## Acceptance

- [x] The gem5 build adapter's driver and oracle, the verifier binding, the completion witness, and the accelerator cases with their extractors go through a kernel plug-in.
- [x] BFS is the only plug-in; every BFS test and record is unchanged.

## Comments

## Answer

Resolved 2026-10-03 22:40 ET (agent, BC track).

**Built.** The gem5 side of the kernel plug-in seam (`swdb/kernels/__init__.py`,
`swdb/kernels/bfs.py`), BFS still the only plug-in. A plug-in now carries the gem5 ROI
(`bfs.complete_call.v1`), its post-ROI checkers (`dx100.bfs.verifier.v1`/`v2`) and the
witnessed one (`v2`), the selectable entry points, the protected result line and its
record field (`parent_results`), the result-storage marker, the protected-verifier context
key, bounds-check and oracle wording, the trusted v2 runtime files, the frontier print and
the read-only instruction-mix rule. Routed through it:
- the gem5 build adapter's driver and original-graph oracle (`swdb/dx100_candidate.py`);
- verifier binding, post-ROI result parsing, completion and failure identity, the v2 witness
  runtime and validator (`swdb/dx100.py`, `swdb/bfs_protocol.py`, `swdb/library.py`);
- the accelerator cases and their extractors (`swdb/dx100_coverage.py`,
  `bfs_protocol.accelerator_cases`, `swdb/read_only_checks.py`);
- protocol freeze binds `correctness.verifier` to the kernel's plug-in (its native check or
  one of its gem5 checkers).

`swdb/dx100_witness.py`, `scripts/dx100_verify.py` and `scripts/dx100_host_memory.py` are
byte-identical on purpose: frozen gem5 protocols pin their sha256. A second kernel
therefore brings its own driver copy and witness validator (BC: ticket 44).

**Tests.** `tests/test_kernel_plugins.py` gains two cases (freeze verifier binding; BFS gem5
identities and the read-only rule selected by checker): 7 pass. Full suite on this state
(10 workers): 3,672 passed, 35 skipped, 81 failed or errored; 47 of those came from a too strict
first freeze binding (fixed, see Assumption). After the fix, the 12 affected files plus this file
run 253 passed, 1 skipped, 34 failed, and those 34 fail identically on clean `8ad6e8a`.

**Assumption.** Simulated fixture protocols have long frozen the native verifier
`swdb.bfs.structural.v1`; the binding therefore accepts the kernel's native check or any of
its gem5 checkers, in any mode, and refuses another kernel's check.

**Pre-existing failures (not fixed here).** They fail the same way on clean `8ad6e8a`
(repository records changed by later evaluations, or this agent sandbox, which denies
writes to `/private/tmp` and some process-group signals; not diagnosed further):
34 cases in 7 files.
- `tests/test_bfs_acceptance_report.py` (1): `test_native_cells_report_real_ids_outcomes_and_unverified_raw_evidence`
- `tests/test_bfs_workload_driver.py` (2): `test_generator_interrupt_reaps_nested_registration_and_retains_logs`
- `tests/test_dx100_compile_smoke.py` (4): `test_compile_scope_selects_only_permitted_public_builds`, `test_driver_deadline_gracefully_reaps_nested_evaluator_child_and_retains_failure`
- `tests/test_dx100_smoke_cleanup.py` (4): `test_smoke_reaps_nested_evaluator_and_preserves_failure`
- `tests/test_library_submit.py` (1): `test_actual_dx100_submit_reproduces_the_certified_tree`
- `tests/test_typed_certification.py` (2): `test_candidate_scope_cannot_certify_uncontracted_header_edits`, `test_exact_patched_tree_preserves_vendored_identity_and_ships_header`
- `tests/test_typed_gem5_recovery.py` (20): `test_recovery_does_not_run_second_graph_after_public_requalification_failure`, `test_recovery_never_reuses_failed_fixture_or_nested_execution`, `test_recovery_refuses_drift_before_public_calls`, `test_recovery_refuses_existing_new_namespace_or_a_timedout_aggregate_record`, `test_recovery_rejects_consistently_resealed_wrong_planned_cell`, `test_recovery_rejects_record_only_resealed_json_type_drift`, `test_recovery_reuses_exact_uniform_pair_and_qualifies_it_before_two_missing_samples`
