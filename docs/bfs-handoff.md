# BFS workflow handoff

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)

This handoff describes the implemented interfaces and the evidence available during
implementation. Campaign acceptance is still pending. The final coverage query,
current protocols, and linked records determine acceptance; a successful build,
proposal, or package does not establish a performance gain.

## Roles and contracts

SW and HW producers submit their selected strategy and constraints. The rewrite
worker interprets or applies that intent, retains failures, and may perform only
bounded repairs of that application. The evaluator independently owns the graph,
trusted driver, verifier, timing boundary, target configuration, and comparison
policy. The report accounts for all required cases and returns unmet requirements
rather than choosing a new strategy until a favorable result appears.

The current interchange uses `message_version: '1.0'` and additive record format
`schema_version: '0.4'`. Older implementation records remain readable under their
original format. The contracts are:

| Artifact | Contract | Identity and purpose |
|---|---|---|
| Exact source | `schemas/source_snapshot.schema.json` | Buildable file manifest, hashes, application provenance, protected inputs |
| Profile package | `schemas/profile_package.schema.json` and [package contract](bfs-profile-packages.md) | Exact source, graph, sources, target, threads, ROI, function/loop and dynamic-memory evidence |
| Rewrite request | `schemas/messages/rewrite-proposal.schema.json` | Producer, source/package references, chosen intent, region IDs, scope, and one payload form |
| Proposal result | `schemas/proposal.schema.json` | Original payload, interpretation, provider, bounds, attempts, rejection/failure/candidate outcome |
| Candidate | `schemas/candidate.schema.json` | Actual changed artifact or explicitly unchanged source baseline; no implicit correctness |
| Evaluation result | `schemas/evaluation.schema.json` | Exact candidate/binary/workload, stage outcomes, correctness, native/simulated quantities and raw references |
| Workload and protocol | `schemas/workload.schema.json`, `schemas/protocol.schema.json` | Content-addressed registration/freeze with version and supersession links |
| Explicit comparison | `schemas/comparison_result.schema.json` | Compatible baseline/candidate evidence, frozen policy, gain/regression/inconclusive/rejected result |

YAML under `records/` is authoritative. SQLite is a regenerable query index.
Large source snapshots, binaries, graph files, stdout/stderr, checkpoints, traces,
and stats are external artifacts whose content identity is retained in metadata.
On mbit10, future buildable snapshots and generated builds use `/data1/yanruj`;
raw logs and observations use the selected run volume. Historical paths remain
recorded as produced. A raw path names the host that produced it; its presence in metadata is not a claim
that the file exists on another host.

## Public sequence

1. Use `source-snapshot` to identify the exact starting implementation and source.
   An unchanged comparison artifact uses `baseline-candidate`; it has
   `artifact_role: source_baseline` and no fabricated rewrite proposal or diff.
2. Evaluate that artifact with `evaluate` for native CPU execution, or the bounded
   DX100 compile/checkpoint/execute interfaces for simulation. Keep the two timing
   bases distinct. Every timed result needs its associated correctness evidence.
3. Collect automatic source regions and real memory observations using `bfs-profile`
   or `dx100-profile`. A separately instrumented artifact remains diagnostic; its
   runtime never silently replaces the primary BFS ROI timing.
4. Assemble `profile-package` with exact context. Use `profile-strategies` and
   `strategy-regions` to inspect applicability and unknown legality or hardware
   requirements. These queries do not promise a speedup.
5. Submit a versioned selected proposal with `submit`. Supply a unified patch,
   natural-language instructions, structured intent, or annotated source. The
   producer must name valid region IDs from that exact package. For interpreted
   routes, the operator supplies `--provider-config` separately from the proposal.
6. Before candidate performance assessment, register equivalent graph
   representations and freeze the concrete comparison protocol.
7. Evaluate the returned candidate and reprofile its actual current source.
   Use `repair EVALUATION` only for retained build/correctness failures within the
   fixed proposal budget. A valid regression is returned without performance tuning.
8. Use `compare-evaluations` with explicit
   baseline and candidate IDs. Changed policy/workload needs a new version and fresh
   compatible comparisons.
9. Retrieve evidence through `get ID --chain --format json`, or rebuild the index
   with `build` first. `bfs-coverage` reconstructs the required matrix and preserves
   failed, incomplete, superseded, neutral and regressing attempts.

The baseline pilot and author reference/control batch have separate pre-execution
plans under `.scratch/bfs-rewrite-evaluation-2026-09-25/`. Neither plan freezes
unknown quantities or proves that its runs have completed.

## Real linked examples available now

The following records came from actual mbit10 execution. Tiny diagnostic graphs
and fixture profile packages establish workflow/correctness behavior only.

| Example | Master record | Observed result |
|---|---|---|
| Supplied patch, SW test client | `bfs-native-smoke-20260925-a1.proposal` | Removed a redundant scalar post-CAS store; candidate independently passed all three timed native results |
| Natural language, SW test client | `bfs-instruction-smoke-20260925-a1.natural-language.proposal` | Real Claude interpretation produced the selected source change; native correctness passed 3/3 |
| Structured instructions, SW test client | `bfs-instruction-smoke-20260925-a2.evaluator-fixed` | Retained real structured candidate passed 3/3 after the trusted-driver include correction; original failure and refused out-of-scope repair remain linked |
| Annotated source, SW test client | `bfs-instruction-smoke-20260925-a2.annotated-source.evaluation` | Real alpha 15-to-16 rewrite passed 3/3; earlier rejected HTML-escaped diff remains retrievable |

Later campaign examples will be added with their exact current
package/protocol/comparison IDs. The passing rechecks use separate identifiers
after diagnosed infrastructure corrections. Failures are retained instead of replacing
them with the successful rerun. No entry in this table is a gain claim.

All clients here are explicitly labeled representative test clients. No live
Peter/Josh integration has occurred, and no message has been sent to either
collaborator as part of this implementation. A future client can use the same
versioned public request contracts without sharing the worker process. These
retained proposal examples all declare `role: sw` and `test_client: true`.
A real campaign submission labeled as an HW test client remains an acceptance
obligation; the SW examples do not stand in for that role.

## Real profile-package and strategy-query handoff

The following complete packages bind the corrected a4 collection of the DX100
scalar-source diagnostics to the exact earlier primary evaluations. Each contains 18 validated Callgrind event
rows and six independently checked diagnostic executions. They use a ten-vertex
directed graph, sources `[0, 3, 8]`, one thread, and the complete-call primary ROI.
Completeness applies to the supported collection scope; header/member/outlined
code and an unresolved OpenMP loop remain explicit discovery limitations.

| Package | Primary evaluation | Discovered regions | Strategy candidate matches |
|---|---|---:|---:|
| [`bfs-package-smoke-20260925-a1.before.package.v1.1187f3a8ca4968d0`](../records/profile_packages/bfs-package-smoke-20260925-a1.before.package.v1.1187f3a8ca4968d0.yaml) | `bfs-native-smoke-20260925-a1.evaluation` | 31: 11 functions, 20 loops | 155 |
| [`bfs-package-smoke-20260925-a1.after.package.v1.81772095f055cd8b`](../records/profile_packages/bfs-package-smoke-20260925-a1.after.package.v1.81772095f055cd8b.yaml) | `bfs-profile-smoke-20260925-a3.evaluation` | 34: 12 functions, 22 loops | 170 |

The earlier measured candidate already contains a source change; it is not an
unchanged application baseline or calibration pilot. The later source introduces
`SWDBDiscoveredHelper`, which ranks first among measured functions; its two loops
rank first and second among measured loops. These diagnostic rankings use
attributed thread CPU quantities, not primary wall time. All strategy matches
retain unresolved semantic preconditions and `performance_guarantee: false`.

Run these read-only queries from a checkout containing the records:

```sh
python3 -m swdb profile-strategies bfs-package-smoke-20260925-a1.after.package.v1.81772095f055cd8b --format json
python3 -m swdb strategy-regions loop_tiling --package bfs-package-smoke-20260925-a1.after.package.v1.81772095f055cd8b --format json
python3 -m swdb get bfs-package-smoke-20260925-a1.proposal --chain --format json
```

On mbit10, the actual handoff revalidated raw observations, performed both query
directions, rebuilt the index, and retrieved a 14-record chain. The SW test-client
proposal `bfs-package-smoke-20260925-a1.proposal` consumed the real earlier package
and materialized the already measured helper change. Its candidate's complete
source manifest matches the retained later candidate at SHA-256
`e6e789e6942776ad88cbc3ba8377d09be8f8b8eee63e511230d7a9957a2490fd`.
The [package handoff receipt](evidence/bfs-package-handoff-20260925-a1.yaml) records
the public commands and hashes. A query on another host reports inaccessible
remote raw artifacts as unverified; it does not inherit the worker's live checks.
The invalid a3 Callgrind counts and their audit remain retained; these packages
use the corrected a4 observations. This slice establishes real data handoff and
profiling, without a profitability comparison.

## Durable contract fixtures and remaining acceptance

The separate [contract demonstration receipt](evidence/bfs-contract-demonstrations-20260925-a3.yaml)
records three proposal rejection classes, five evaluation failure classes, and a
frozen comparison against a separately registered unchanged source reference.
The compiler stand-in and artificial durations are labeled `contract_fixture`.
The unfavorable ratio of 0.5 demonstrates result handling only; the report lists
it separately from empirical regressions. An independently failed verifier after
process exit zero remains a failure even when stdout prints a misleading pass.
Fresh coverage preserves AC08/AC09/AC14 contract evidence while rejecting these
fixtures for the real matrix, accelerator execution, AC17, or any gain claim.

Only local evidence is archived under
`/Users/yanrujhou/CLionProjects/EvolveSWDB_runs/bfs-contract-fixtures/`:
`bfs-contract-20260925-a3.tar.gz` retains the completed fixture, and
`bfs-contract-20260925-setup-failures.tar.gz` retains its two earlier setup failures.
Their exact hashes, manifests, and safe restoration instructions are in the
receipt. Original `/private/tmp` paths and immutable record identities remain
unchanged. The archive contains no remote raw data and does not turn fixture
timings into empirical evidence.

| Remaining obligation | Required evidence |
|---|---|
| Eight campaign cells | Both graph families for DX100 natural language and patch routes, and upstream structured-instruction and annotated-source routes, under their current frozen protocols |
| Source-specific acceleration | One correct accelerated candidate from each starting source on both families, with observed instruction execution and full/tail/competing-parent coverage |
| Reference comparisons | The pinned author scalar/MAA artifact pair and separately controlled scalar/accelerated comparisons, with actual workload/configuration/ROI/correctness identities |
| Candidate gain | At least one correct generated candidate passes the frozen policy against its appropriate unaccelerated baseline; a win over author MAA is not required |
| Final handoff and review | Real SW/HW test-client examples, complete fresh coverage with available artifact verification, remaining ticket updates, and final code review |

These obligations remain open. Neither the diagnostic package slice nor the
durable fixtures complete Ticket 21 or substitute for the pilot/empirical batches.
Use `bfs-coverage` with explicitly selected current candidate protocols and
artifact/control comparison IDs to obtain the current assessment; missing
evidence stays visible rather than being filled with earlier diagnostic runs.

## Extending hardware/software co-design

A new operation first needs a versioned operation/interface/model contract covering
semantics, masks/tails, ordering, resource requirements, and support evidence. A
wrapper decomposes into checked leaf operations; a new name does not create an
instruction or executable backend. `capabilities TARGET` distinguishes pinned
source support from successful executable readiness.

A new target or backend must retain build/model/runtime identities, actual target
configuration, independently checked timed output, a defined timing quantity,
source attribution, and supported dynamic observations. Native hardware counters,
modeled Callgrind events, and simulator memory packets are different observations.
Missing quantities or unknown legality remain explicit. Producer intent cannot
supply an invented hardware capability or override evaluator-owned protections.
