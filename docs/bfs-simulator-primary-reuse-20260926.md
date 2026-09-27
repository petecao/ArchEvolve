# Retained primary build in a frozen simulator series

Prepared: 2026-09-26 (Eastern Time). Local implementation; no guest dispatch.

`bfs_simulator_series.py --primary-build ID` reuses a completed public candidate
build in a frozen complete-call series. It requires `--protocol` and
`--protocol-role`, rejects `--author-binary`, and never issues `dx100-compile`
for that primary. The existing `--diagnostic-build` independently reuses a
separate diagnostic. Omitting the new option preserves the old compilation
path and author/pilot behavior. No consumed compilation budget is replenished.

The reader checks the exact candidate artifact, function, model, target, ROI,
acceleration setting and non-diagnostic treatment. The adapter must match the
selected frozen verifier, and compiler/flags/adapter must match the frozen role.
It reopens source bytes, primary binary, compiler and generated driver/m5ops
hashes before execution and again before marking the series complete. Public
execution still verifies each candidate-build binding and frozen instrumentation.
The driver records the reused evaluation's canonical hash and binary reference;
its `compile_calls: 0` refers only to this primary. A separately requested
missing diagnostic may still compile under the existing series rules.

This option supplies a missing operation for T17/T20 orchestration. It does not
create a candidate protocol, authorize a new campaign clock, or turn a successful
build into correctness/performance evidence. Actual host input sealing, resource
admission and the complete source-specific grid remain required. The existing
T15 and T16 batch plans do not select the option; their pinned running code is
unchanged. A future bounded manifest must select the exact retained build IDs
and account for all new output in its original allowance.

Verification uses identity rejection cases with real temporary files and a
synthetic public-command grid that reaches aggregation and final readback. The
grid confirms that the primary is fetched, never rebuilt, and that every primary
execution names the retained build. It establishes orchestration behavior only;
no local test is a gem5 run or Linux ownership proof.
