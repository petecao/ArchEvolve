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
| Supplied patch | `bfs-native-smoke-20260925-a1.proposal` | Removed a redundant scalar post-CAS store; candidate independently passed all three timed native results |
| Natural language, SW test client | `bfs-instruction-smoke-20260925-a1.natural-language.proposal` | Real Claude interpretation produced the selected source change; native correctness passed 3/3 |
| Structured instructions | `bfs-instruction-smoke-20260925-a2.evaluator-fixed` | Retained real structured candidate passed 3/3 after the trusted-driver include correction; original failure and refused out-of-scope repair remain linked |
| Annotated source | `bfs-instruction-smoke-20260925-a2.annotated-source.evaluation` | Real alpha 15-to-16 rewrite passed 3/3; earlier rejected HTML-escaped diff remains retrievable |

Later campaign examples will be added with their exact current
package/protocol/comparison IDs. The passing rechecks use separate identifiers
after diagnosed infrastructure corrections. Failures are retained instead of replacing
them with the successful rerun. No entry in this table is a gain claim.

All clients here are explicitly labeled representative test clients. No live
Peter/Josh integration has occurred, and no message has been sent to either
collaborator as part of this implementation. A future client can use the same
versioned public request contracts without sharing the worker process.

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
