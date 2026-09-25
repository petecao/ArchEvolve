# Source contexts and comparisons

Date: 2026-09-25

Format 0.4 adds explicit implementation ownership without renaming existing kernel
IDs or replacing historical records. `gapbs-bfs` remains the shared BFS identity.
An implementation at 0.4 names its `application`, `source_baseline`, source-specific
`evaluator`, and scoped `verification`. `origin.derived_from` remains its source
ancestor. Optional `comparison_baseline` names a separately selected comparator.
An unchecked import is visible as unchecked; membership in a source catalog never
establishes correctness on a new target or workload.

Formats 0.2 and 0.3 retain their historical application and evaluator defaults
from their kernel. Their kernel's `baseline_implementation` remains the historical
catalog baseline. Their `--applies` profile pairing retains ancestry semantics and
is labeled historical pairing, not a performance comparison. A 0.4 implementation
never borrows the shared kernel's executable evaluator or application context.

`Store.source_context(implementation)` and public `implementations` results expose
the application source URI, commit, local source root, implementation code, build,
run, evaluator, verification, source ancestor, source baseline, and selected
comparison baseline. Public queries resolve from the generated index. Deleting and
rebuilding the index preserves these fields because YAML remains authoritative.

`swdb compare IMPLEMENTATION --baseline BASELINE --profile PROFILE
--baseline-profile BASELINE_PROFILE --protocol PROTOCOL` compares an exact pair.
The implementation's explicit `comparison_baseline` can supply `--baseline`; an
argument that conflicts with that record is rejected. Missing references, different
kernels, failed/absent correctness, incomplete profiles, different workloads,
targets, timing scopes, protocols, or thread counts fail without ancestry fallback.
Each profile must also name its owner's exact application revision in its build.

Each profile supplies `extensions.comparison_context` with `protocol`, `roi`,
`target`, `workload`, `threads`, `basis` (measured or simulated), and `evidence_kind`
(fixture or execution). These identities are mandatory for this command; older
profiles remain retrievable but cannot retroactively satisfy a new comparison.
For fixture pairs the result reports only `fixture_ratio`. Execution pairs report
`diagnostic_ratio` with `gain_claim: false` until the evaluation workflow checks the
frozen repetition and profitability policy. This foundation establishes selection
and compatibility, not experimental acceptance or an empirical gain claim.
