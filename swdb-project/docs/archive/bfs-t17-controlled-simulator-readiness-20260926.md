# T17 controlled-simulator freeze and execution readiness

Navigation updated: 2026-09-28 (Eastern Time).

Prepared: 2026-09-26 (Eastern Time). **Prospective, local source audit only.**
No protocol, campaign clock, host work, provider call or transfer is created here.
This narrows the [candidate next steps](bfs-candidate-simulator-next-steps-20260926.md)
to the data and orchestration still needed after T15 qualifies its workloads and
T17's diagnostic build exists. Historical failures remain failed.

The remaining preparation is one exact freeze request, a four-row role/family
manifest and a bounded recipe invoking the existing series client. The fixed
author batch cannot serve unchanged: its
[builder](../../scripts/bfs_simulator_batch.py#L662) selects `--author-binary`.

## Reopen these actual dependencies

| Role | Candidate | Retained primary / diagnostic builds |
|---|---|---|
| Baseline | `bfs-dx100-compile-20260925-a1.candidate` | `bfs-scalar-v2-preparation-20260926-a1.dx100.primary.build` / `.dx100.diagnostic.build` |
| T17 candidate | `bfs-campaign-preparation-20260925-a1.dx100-instructions.candidate-1` | `bfs-t17-build-only-20260926-a1` / `bfs-t17-diagnostic-build-only-20260926-a1` |

Reopen both scalar records/binaries individually; their enclosing preparation
remains failed. Preserve the original T17 proposal/package/source/primary chain
and same-host Git materialization provenance. The diagnostic is still pending;
no provider/repair/recompile is implied. Also require model
`bfs-dx100-build-20260925-a2`, target `dx100-e4fc4af-4c`, T15's accepted graph/source identities,
actual repeatability/coverage packages and size-selection reasons. Native
qualification and T16's author protocols do not replace this freeze.

## Assemble the freeze from identities, not an author-protocol copy

Use public `freeze-protocol` with `message_version: "1.0"`, a fresh request ID,
`version: 1`, and the following settings. Preserve the returned content-addressed
ID and query it freshly with `get --chain`
([freeze](../../swdb/bfs_protocol.py#L558), [ID construction](../../swdb/bfs_protocol.py#L227)).

| Setting | Exact derivation |
|---|---|
| Mode/kernel/ROI/threads | `controlled_simulator`, `gapbs-bfs`, `bfs.complete_call.v1`, four guest cores. Both primary adapters must be `dx100.complete_call.v2`. |
| Workloads/sampling/profitability | T15's actual selected graph identities and ordered sources; two replays, zero warmups, `geomean_source_median_ratio`, unchanged accepted spread/floor/confidence/resamples/seed. No native paired collection fields. |
| `simulation_identity` | Version `1.0`; model build evaluation ID plus canonical record digest; the exact `gem5.opt` path/hash from that model's binary inventory. Preserve Ramulator identity. |
| `targets[role]` | Actual target ID and the complete expanded configuration returned by `dx100._configuration`, including command arguments and Ramulator-file hash. The four-field input is BASE versus MAA with matched 8-MiB/16-way LLC and the same 16,384-element tile; revalidate against the chosen pilot treatment. CPU/cache/memory/clock/model must match. |
| `builds[role]` | Copy `compiler`, `compiler_version`, ordered `flags`, and `adapter` from that role's retained **primary** build. Keep full record/binary/source/compiler/driver/m5ops references in the execution manifest. |
| `instrumentation[role]` | Reproduce the exact primary map constructed at `dx100.py:715–741`: complete-call ROI, retained suppressed internal events, same-guest post-ROI verification, original-adjacency contract, exact verifier/parser/observer hashes from the final runtime, and exact v2 `SyscallBase` post-seal map. Scalar coverage uses `MAATrace`; accelerated coverage uses all three required MAA flags. Gzip encoding stays outside this semantic map. |
| Correctness/differences | v2 checker, every timed trial, explicit software/accelerator/configuration differences. Baseline accelerator cases are empty; candidate requires actual `executed`. Additional relevant cases must follow pilot applicability and be demonstrated by the candidate; unchanged-author A2 does not certify it. |

The [configuration constructor](../../swdb/dx100.py#L321) reads metadata without
executing a guest. Before public freeze, run existing `_validate_settings` and
retained-build validators against the completed records/artifacts. After freeze,
[simulation binding](../../swdb/bfs_protocol.py#L667) requires canonical equality of
the complete build/configuration/instrumentation maps. Do **not** copy T16's
`reference_artifacts`: it requires unchanged catalog sources for both roles.
This controlled protocol permits binaries under its declared build treatment;
the manifest must bind the particular T17 candidate and four retained builds.

Choose region IDs/extents from both diagnostic builds' `context.diagnostic.regions`.
Each pair needs inspected semantic correspondence, baseline/candidate IDs,
`scope`, `attribution`, `evidence: simulated_diagnostic_profile`, and matching
discovery backend/collector/library/pass hashes plus diagnostic runtime hash.
A split rewrite cannot inherit a guessed helper correspondence. Existing
[build checks](../../scripts/bfs_simulator_series.py#L58) and the
[region reader](../../swdb/bfs_region_comparison.py#L60) enforce these bindings; reported
diagnostic intervals include instrumentation/waiting/overlap and never replace
primary ROI timing.

## Seal four series and one enclosing finite allowance

Seal four ordered rows: baseline/candidate for each accepted family. Each binds
fresh series ID, candidate and primary/diagnostic canonical hashes, returned
protocol ID/role, workload/source identities, configuration-file hash and CLI
options. The enclosing manifest retains runtime/Python/environment, Linux proof,
original finite outer clock, shared cleanup binding, lane, exact raw/`.dispatch`
roots, external cache/sidecars and new canonical output inventory.

Invoke `scripts/bfs_simulator_series.py` with `--primary-build` and
`--diagnostic-build`, `--protocol`, `--protocol-role`, exact configuration,
`--build-evaluation`, workload/candidate, `--require-capacity`, and the original
shared `--owned-cleanup-ledger`/`--owned-cleanup-binding`. Candidate rows add
`--accelerated`; baseline rows omit it. Both omit `--author-binary`; use the
reviewed lossless transport explicitly. The public cache already resides in each
series' counted driver directory
([reuse checks](../../scripts/bfs_simulator_series.py#L85),
[public orchestration](../../scripts/bfs_simulator_series.py#L310)).

Select finite aggregate/per-series/per-stage bounds from actual T15 cost and
storage plus remaining campaign authority; CLI maxima do not create an allowance.
Charge wrapper/preflight, artifact reopening, execution, profiling, comparison,
retrieval and finalization. Admit only a complete next series under the original
outer deadline/shared cleanup; stop on failure. Existing Owned primitives supply
supervision. This fixed manifest/recipe, not another evaluator, remains missing.

The client performs six primary and six diagnostic cells per series, creates
six packages and one primary aggregate, reuses only the same source/binary/config
checkpoint for its second replay, and reopens the primary build at completion.
Across four series that is 24 primary + 24 diagnostic executions, 24 packages,
four aggregates and two final comparisons. No new compilation is requested.
For each family, submit public `compare-evaluations` with the returned protocol ID, the two aggregate IDs,
`comparison_baseline: dx100-bfs-scalar`, and `region_packages` mapping **exactly**
its twelve primary component IDs to their returned package IDs. Fresh
`get --chain` must reconstruct the original proposal through both comparisons
([aggregation](../../scripts/bfs_simulator_series.py#L449),
[package coverage](../../swdb/bfs_region_comparison.py#L285)). Correct accelerator
execution on both families is required; a T17 gain is not.

The only additional readiness defect found in this audit was the shared
four-case proof reader rejecting the approved fifth SQLite case. Its separately
reviewed narrow repair is documented in the existing
[T17 diagnostic contract](bfs-t17-diagnostic-build-20260926.md). No other concrete
API defect was reproduced in this read-only freeze/series audit; actual build
collector IDs, T15 feasibility and host artifact availability remain unverified
until those empirical prerequisites are supplied.
