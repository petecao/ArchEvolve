# BFS workloads and frozen comparisons

Date: 2026-09-25

This contract implements Ticket 11 using Ticket 03's durable evaluations.
The public operations are `register-workload`, `freeze-protocol`,
and `compare-evaluations`, each taking a version 1.0 YAML request file. Records use
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
also enables streaming for small graphs. Inputs exceeding the native parser's
2,000,000 vertices, 5,000,000 edges, or 512 MiB require it. The canonical hash is
identical across parsers and offset widths. The representation retains parser
source identity and verification method. Native inline graph materialization
retains its size limit; simulator dispatch can use `workload_representation` to
select and rehash the verified external SG file for its application.

A protocol freezes explicit workloads and their fingerprints, per-role build and
target definitions, threads, semantic ROI, correctness coverage, instrumentation,
sampling, and profitability policy. Native, artifact-reference, and controlled
simulator comparisons are separate modes. Controlled comparisons require matched
CPU/cache/memory configurations; artifact-reference comparisons retain disclosed
differences. Software and accelerator changes are enumerated without claiming an
isolated software cause when target configurations differ.

Frozen records are content-addressed: their identifier contains the freeze hash,
and readers recompute the hash. Evaluations retain the exact frozen hash at dispatch;
later record edits invalidate that binding. The public operations never overwrite
a workload, protocol, or comparison result. A changed version links its predecessor
and names existing comparisons that need new evidence. These checks protect the
workflow's history; they are not a signature against a maintainer rewriting all
authoritative records and evidence.
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
