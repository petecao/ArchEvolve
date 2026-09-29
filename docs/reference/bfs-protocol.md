# BFS workloads and frozen comparisons

Navigation updated: 2026-09-28 (Eastern Time).

Updated: 2026-09-29 ET (baseline-not-invoked simulated region rule)

This contract implements Ticket 11 using Ticket 03's durable evaluations.
The public operations are `register-workload`, `freeze-protocol`,
`aggregate-evaluations`, and `compare-evaluations`, each taking a version 1.0 YAML request file. Records use
format 0.4 and remain retrievable through `get`. Rejected comparisons are retained.

Workload registration reads actual JSON/edge-list and GAPBS little-endian SG
representations with 32-bit or 64-bit offsets. It checks file hashes, CSR offsets,
vertex bounds, directed inverse adjacency, and the loaded outgoing adjacency.
Canonical identity uses the native evaluator's `swdb.bfs.adjacency.v1` format:
sorted neighbors, removed self loops/duplicates, and symmetric adjacency for an
undirected graph. Serialized representations must already have that normalized
adjacency; registration does not silently repair an invalid serialized graph.
Graph family and generator metadata are operator declarations; realized counts
and adjacency hashes are computed. Ordered sources are retained separately from
repetitions. Different representation hashes can identify one verified graph.

Artifact-size SG registration uses a bounded C++ CSR reader that maps the input
read-only, checks every outgoing/inverse edge by exact sorted-row membership, and
streams canonical JSON into SHA256. It does not construct Python adjacency lists.
The request's `parser` mapping supplies an external `work_dir`, plus optional
`compile_timeout_s` (default 60, maximum 600) and `timeout_s` (default 900, maximum
7200). On mbit10 that directory belongs under `/data1/yanruj/`. Supplying this mapping
also enables streaming for small graphs. Registration inputs exceeding
2,000,000 vertices, 5,000,000 adjacency entries, or 512 MiB require it. The canonical hash is
identical across parsers and offset widths. The representation retains parser
source identity and verification method. Native registered-SG materialization has
its separate evaluator bounds of 2,000,000 vertices, 32,000,000 directed adjacency
entries, and 512 MiB. It rehashes the serialized bytes and canonical adjacency and
passes strict adjacency rows directly, preserving isolates and avoiding temporary
edge-pair expansion. The registration streaming threshold is not a native size
limit. Simulator dispatch can use `workload_representation` to
select and rehash the verified external SG file for its application.

A protocol freezes explicit workloads and their fingerprints, per-role build and
target definitions, threads, semantic ROI, correctness coverage, instrumentation,
sampling, and profitability policy. Native, artifact-reference, and controlled
simulator comparisons are separate modes. Controlled comparisons require matched
CPU/cache/memory configurations; artifact-reference comparisons retain disclosed
differences. Software and accelerator changes are enumerated without claiming an
isolated software cause when target configurations differ.
For a lane-managed native machine the target freezes the socket lane ID. Dispatch
and comparison accept the exact recorded host lane verifier receipt for that ID,
including matching NUMA binding and lease generation; an unverified bare label,
arbitrary suffix, or another socket is incompatible. Each run retains its full
receipt even though the frozen lane identity excludes the changing generation.

New native freezes also require `settings.native_runtime`, a version 1 map of
the exact eight requested OpenMP/libgomp environment inputs described in
[the native runtime contract](../archive/bfs-native-runtime-20260926.md). Evaluation dispatch
constructs that environment, including removing explicitly unset variables;
comparison reopens the recorded `build.native_runtime` and requires equality.
Historical records without the map remain readable. Their missing inputs cannot
authorize empirical native dispatch or comparison; explicit fixture-only flows
remain available and cannot claim gain. This map is not worker-placement or
actual-team telemetry.

Frozen records are content-addressed: their identifier contains the freeze hash,
and readers recompute the hash. Evaluations retain the exact frozen hash at dispatch;
later record edits invalidate that binding. The public operations never overwrite
a workload, protocol, or comparison result. A changed version links its predecessor
and names existing comparisons that need new evidence. These checks protect the
workflow's history; they are not a signature against a maintainer rewriting all
authoritative records and evidence.
The locked writer also rejects two workload or protocol records with the same
kind, requested name and version, even if their content-addressed IDs differ.
Concurrent creators cannot replace an existing immutable result or fork one
logical version silently.
Baseline-role dispatch and comparison also resolve the explicitly selected
implementation's application source and full manifest. The candidate and source
snapshot must match those bytes and their application, function, and revision.
An ancestry ID or rematerializing rewritten code with `baseline-candidate` does
not establish that identity. A separately registered implementation can still be
selected when its own source context matches. Ordinary historical `get` retrieval
does not require remote source files or rewrite recorded comparison outcomes.
The public `add` operation rejects these two sealed kinds: workload registration
must parse the real representations, and protocol creation must run the freeze
checks. The normal writer still persists both operations as authoritative YAML.

Comparison requires complete correctness for every timed graph/source/repetition,
the actual timed binary, compatible quantities and scope, and a protocol frozen
before dispatch. Whole-process diagnostics and simulator host time cannot stand in
for BFS ROI duration. Region ratios additionally require declared correspondence,
per-invocation or accumulated duration, and matching inclusive/exclusive attribution.

Native profitability uses a predeclared repetition count of at least five per
source, a declared maximum relative spread, and a deterministic bootstrap confidence
interval over independently resampled per-source durations. The primary aggregate
is the geometric mean of per-source median ratios. The lower confidence bound must
exceed the predeclared minimum speedup; excessive spread yields an inconclusive
outcome. These are an admissibility floor and an explicit algorithm, not empirical
calibration: Ticket 15 must choose actual counts and thresholds from baseline pilots.
Fixture evidence always yields fixture outcomes and `gain_claim: false`.

A simulator dispatch binds an explicit `protocol_trial` containing
`source_position` and `repetition` before execution. The adapter supplies the
actual target configuration, guest compiler/version/flags/adapter, instrumentation,
thread count, ROI, and verifier to `validate_protocol_for_simulation`; any mismatch
rejects the binding. The source and registered SG file must match the frozen
loaded-adjacency identity. Diagnostic requests without a protocol remain diagnostic.

New simulated freezes also require `simulation_identity.version: "1.0"`, an exact
`model_build` evaluation ID and record `sha256`, and the `simulator` path and SHA256
listed in that completed build receipt. The complete build record binds the source,
compiler receipt and recorded dependencies. Frozen dispatch rehashes the simulator,
receipt and runtime shared libraries, including `libramulator.so`; comparison checks
the selected model and simulator against the evaluation and component bindings.
The build's recorded system package versions are evidence, not invented file hashes.
An `artifact_reference` protocol, or a protocol whose two guest adapters are
`dx100.author_artifact.v1`, additionally requires `reference_artifacts` for both
roles: `candidate`, `candidate_sha256` (record digest), `source_snapshot`,
`source_snapshot_sha256`, `source_artifact_sha256`, and `binary: {path, sha256}`.
Those candidates must match their unchanged catalog sources, and their binaries
must belong to the frozen model receipt. Future rewrite protocols pin the model
without requiring an unknown future candidate binary. Native freezes are unchanged.
Legacy simulated protocol records remain readable, but missing bindings cannot
authorize a new simulator dispatch or comparison gain. Publish a superseding
protocol and collect fresh evidence; never retrofit a prior freeze.
`correctness.required_accelerator_cases` is an optional per-role mapping of lists
using only `executed`, `full_tiles`, `tail_tiles`, and `competing_parent_updates`.
New author/reference protocols require `baseline: []` and candidate `executed`.
Every required timed replay must contain matching typed observations: positive
instruction counts and completed S/I/R/A traces for execution, plus positive
observed case counts when a particular case is requested. Scalar fallback, labels,
missing cells and context strings cannot satisfy those requirements. Fixture
counter shapes exercise this contract without becoming execution evidence.

`aggregate-evaluations` takes an `id`, `protocol`, `protocol_role`, and an
`evaluations` list of distinct execution IDs. Each component must retain exactly
one timed traversal and its matching structural check. The completed grid must
cover every frozen source position and repetition, with identical candidate,
binary, build, model, target configuration, instrumentation, and ROI. Guest trial
arguments do not stand in for completed executions. The result retains
`component_evaluations` with content hashes, each original execution binding and
context, raw artifacts, and stages. Comparisons revalidate those component hashes
and observations. Missing cells, failed components, duplicate cells, and identity
mismatches produce a retained incompatible aggregation with no gain claim.

For simulator region pairs, freeze `evidence: simulated_diagnostic_profile` and
`collector` with `backend: libclang-cindex`,
`collector: dx100.m5_rpns.source_scopes.v1`, `library_sha256`, `pass_sha256`, and
`runtime_sha256`. The comparison request's `region_packages` maps every primary
component evaluation ID in both grids to its exact sealed package. The comparator
checks current package/profile/compile identities, independently passed diagnostic
correctness, source/repetition coverage, the separate diagnostic binary, and the
collector's actual source extent and timing scope. Local diagnostic raw reports
are parsed and hashed from the same byte stream; stale values are rejected even
after a package is reassembled. Remote raw bytes remain unverified during local
metadata retrieval. Region results retain each package, collector, compilation,
binary, raw-report reference, invocation count and source cell. They compute a
geometric mean of per-source median diagnostic duration ratios; `per_invocation`
divides each diagnostic duration by its own invocation count first. These are
simulated elapsed intervals summed across executing threads, including waiting and
overlap. They always retain `primary_bfs_roi: false` and `gain_claim: false` and
cannot substitute for primary BFS ROI timing.

Baseline-not-invoked rule (added 2026-09-29 ET). A frozen simulated pair may name
a region that the baseline binary never executes (the T17 scalar baseline never
calls `TDStepMAA`). When the baseline region's raw-verified invocation count and
both inclusive and exclusive seconds are exactly zero in every replay cell, the
comparison is not rejected. The pair is reported with `state:
baseline_not_invoked`, `duration_ratio: null`, `baseline_invocations: 0`, the
candidate's per-cell invocations and per-source median durations, and
`gain_claim: false`. The primary BFS ROI decision and every other region pair are
computed normally. These remain rejections: a zero-invocation candidate region,
zero baseline invocations with nonzero time, a baseline that is zero in only some
cells, and any other invalid count or duration. Native pairs keep strict rejection
(see [native selected-region comparisons](bfs-native-region-comparison.md)).

Native region pairs can select the versioned
[`native_diagnostic_profile.v1` treatment](bfs-native-region-comparison.md).
It reads the separate native profile package and verified per-trial raw CPU
counters, with explicit frozen collector identity and diagnostic repetition
count. It retains diagnostic CPU ratios separately from the primary BFS wall-time
decision; primary `profiling.regions` is not populated or fabricated for it.

The workload `definition` contains the kernel, family, generator, normalization,
ordered sources, representation references, computed canonical hash, and realized
graph properties. Both workloads and protocols retain `requested_id`, `version`,
`supersedes`, `identity_sha256`, and `invalidated_comparisons`. The returned `id`
appends the first 16 hexadecimal characters of the identity hash. A protocol also
retains `settings`, `workload_identities`, `frozen_at`, and `state: frozen`.

The comparison request explicitly provides `protocol`, `baseline_evaluation`,
`candidate_evaluation`, and `comparison_baseline`. The durable result retains
those references, `source_ancestor`, `protocol_sha256`, `evaluation_identities`,
`decision` (state and reasons), `metrics`, `region_comparisons`, `evidence_kind`,
`gain_claim`, and `finished_at`. Rejected results have empty metrics. Fixture
results use `fixture_ratio`; execution results separately report the primary ROI
ratio, confidence interval, measured spread, and limits on causal attribution.
