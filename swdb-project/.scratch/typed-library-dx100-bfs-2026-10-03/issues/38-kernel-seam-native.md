# 38 — Prefactor: kernel plug-in seam, native side

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

**What to build:** The native side of the evaluator handles kernels through plug-ins, with BFS as the only one.

## Acceptance

- [x] Workload registration and protocol-freeze identity checks, native evaluation, the native build adapter (source path, protected verifier, trusted driver and its oracle), native pairs, region discovery, profiling trial parsing and profile packages go through a kernel plug-in.
- [x] BFS is the only plug-in; every BFS test and record is unchanged.

## Comments

## Answer

Resolved 2026-10-03 21:00 ET (agent, BC track).

**Built.** A kernel plug-in registry, `swdb/kernels/__init__.py` (`KernelPlugin`, `register`,
`get`, `require`, `by_native_verifier`, `by_native_roi`, `native_rois`), with BFS as the only
plug-in, `swdb/kernels/bfs.py`. The BFS plug-in holds exactly the constants the evaluator used
before: entry point `DOBFS`, ROI `bfs.complete_call.v1`, trial format
`swdb.bfs.native.trial.v1`, verifier `swdb.bfs.structural.v1` (its `verifier_sha256` is still the
hash of `swdb/bfs_native.py`, where `verify_parents` stays), trusted driver
`tools/bfs_native/driver.cc.in` (byte-identical, so frozen `template_sha256` values hold), binary
`bfs-native`, driver call anchor `auto parent =`, translation units per application,
`BFSVerifier`, and `TDStep` for per-line profiling.

Routed through the plug-in:
- workload registration and protocol validation (`swdb/bfs_protocol.py`: `kernels.require`
  replaces the hard-coded `gapbs-bfs` check; the evaluation ROI default comes from the plug-in);
- native evaluation and the native build adapter (`swdb/bfs_native.py`: entry point, ROI,
  driver, macro protection, trial format, output bound, independent result check);
- native pairs (`swdb/bfs_native_pair.py`: raw recheck selected by the retained verifier);
- region discovery and profiling (`swdb/bfs_discovery.py` scope label, `swdb/bfs_profiling.py`
  trial parsing, wrappers, per-line function, build-artifact names),
  `swdb/bfs_region_comparison.py` (raw recheck), and profile packages
  (`swdb/profile_package.py` requires a plug-in for the implementation's kernel).

**Tests.** New `tests/test_kernel_plugins.py` (CLI): BFS evaluation keeps every former identity
(function, ROI, verifier, verifier hash, driver template hash, binary name); registration,
protocol freeze and native evaluation refuse a kernel without a plug-in; an ROI no plug-in owns
is refused. BFS regression over the touched modules (`test_bfs_native`, `_native_pair`,
`_protocol`, `_profiling`, `_region_comparison`, `_native_region_comparison`,
`test_profile_packages`, `_shared_protocol`, `test_statement_annotation`, `_native_execution`,
`_native_runtime`, `test_provider_pins`, plus the new file): 350 passed, 3 skipped. One error
in that run came from a concurrently edited, temporarily invalid record of ticket 40 copied by
`copy_repo`; it was fixed and does not involve this seam.

**Assumptions.** Messages that named BFS now name the plug-in (`BFS` for BFS, so BFS text is
unchanged except the registration/freeze refusal, which now lists the plug-ins). Records written
before the seam carry only BFS identities, so an absent verifier selects BFS; an unknown one is
refused. Pre-existing, unrelated failure: `test_bfs_acceptance_report.py::
test_native_cells_report_real_ids_outcomes_and_unverified_raw_evidence` (repository records
gained aggregate evaluations); it fails identically at HEAD.
