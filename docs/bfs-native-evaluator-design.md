# Native BFS evaluator design

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
Status: Ticket 03 implemented; real native correctness diagnostic passed on mbit10.

Real mbit10 primary runs automatically retain a separate
`swdb.host-observation.v1` receipt after lane verification. Its identified raw file
records load, users, disk/memory, CPU/NUMA, available governor/turbo controls,
kernel, and running SWDB revision through bounded read-only commands. Missing
controls remain explicit, and collection time counts against the run budget.

This design binds the native evaluator to the candidate artifact produced by
Ticket 02. It supports DX100 scalar top-down BFS first and upstream GAPBS
direction-optimizing BFS second. The evaluator owns source protection, invocation,
timing boundaries, result capture, and the structural correctness check. The
candidate supplies the BFS computation and its permitted supporting code.

## Verified source facts

The inspected upstream source is `apps/gapbs`, revision
`2972aeb2703165bafd921222f4ed7196f542d3a8`. The inspected DX100 source is
`/private/tmp/codex-dx100-bfs-inspect-20260925`, revision
`e4fc4afdf894f295442cef3604667a469fab8e62`; implementation must resolve the durable
source context recorded by Ticket 01 rather than depend on this temporary path.

| Fact | Pinned source evidence | Consequence |
|---|---|---|
| Both sources expose `DOBFS(const Graph&, NodeID, bool, int, int)` returning `pvector<NodeID>`. | Upstream `src/bfs.cc`; DX100 `benchmarks/gapbs/src/bfs.cc`. | One evaluator-owned wrapper can call each source-specific entry point. |
| Upstream's timer surrounds `auto result = kernel(g)` and stops before verification and destruction of the result. | Upstream `src/benchmark.h`, `BenchmarkKernel`. | Preserve that result-lifetime boundary for `bfs.complete_call.v1`. |
| DX100 `DOBFS` calls only `TDStep` in its traversal loop; its descriptive header still discusses direction optimization. | DX100 `benchmarks/gapbs/src/bfs.cc`, `DOBFS`. | Identify this source as scalar top-down from executed code. |
| DX100 `DOBFS` constructs offsets, calls `alloc_MAA()` and `init_MAA()`, initializes parent/frontier state, and prints frontier sizes. | DX100 `benchmarks/gapbs/src/bfs.cc`, `DOBFS`; `benchmarks/API/MAA_functional.hpp`. | Those calls remain inside complete-call timing. A rewrite cannot move required work into untimed setup. |
| `FUNC` selects the authors' CPU functional API; `MAA` selects `DOBFSMAA` in their `main`. | DX100 BFS includes and `main`. | Native scalar build uses `-DFUNC` without `-DMAA`; accelerated functional execution cannot become DX100 performance evidence. |
| DX100's Makefile depends on `m5op.o` even for its `FUNC` targets. | DX100 `benchmarks/gapbs/Makefile`. | Compile the evaluator wrapper directly for native work; no simulator or m5 assembly dependency is needed. |
| Upstream `SGOffset` is `int64_t`; DX100 `SGOffset` is `int32_t`. Both serialized headers use that type for vertex and edge counts as well as CSR offsets. | Both sources' `src/graph.h`, `src/reader.h`, `src/writer.h`. | The `.sg` extension does not establish serialization compatibility. |
| The regular benchmark can print `Verification: FAIL` and still return zero. | Both sources' `BenchmarkKernel` and `main`. | Exit status alone never establishes correctness. |

## Public request and module boundary

Use the versioned workflow record and persistence helpers established by Ticket 02.
The implemented Python entry point is:

```python
swdb.bfs_native.run(args) -> dict
```

The public CLI is `swdb evaluate REQUEST.yaml --runs-dir EXTERNAL_DIRECTORY` and
accepts `--records`, `--db`, `--format`, and optional `--lane`. It returns the durable
evaluation record; success exits zero and retained non-success exits one. Retrieval
uses the evaluation ID and the generated query index, including after a failed run.
The request has these required meanings:

```json
{
  "message_version": "1.0",
  "id": "bfs-native-diagnostic",
  "candidate": "candidate-id",
  "comparison_baseline": "explicit-implementation-id",
  "workload": {
    "family": "diagnostic",
    "graph": {"num_vertices": 5, "directed": true,
              "edges": [[0, 1], [0, 2], [1, 3], [2, 3]]}
  },
  "machine": "machine-record-id",
  "sources": [0, 4],
  "threads": 1,
  "roi": "bfs.complete_call.v1",
  "repetitions": 1,
  "protocol": null,
  "budget": {"build_seconds": 600, "run_seconds": 120, "total_seconds": 900}
}
```

These numbers illustrate explicit bounded diagnostic settings, not the later
performance protocol. A protocol-less evaluation always has `gain_claim: false`.
Optional `build_directory` selects a unique absolute directory outside the repository
and records. On mbit10 it must be under `/data1/yanruj` and defaults to
`/data1/yanruj/EvolveSWDB_builds/<evaluation-id>`. Generated wrappers and binaries live
there; graph inputs, logs, and result files remain in `--runs-dir`.
The host, lane, source, binary, and executable capabilities are verified rather
than accepted from request labels. Timeout values must be positive and finite;
repetitions and thread count must be positive integers, excluding booleans. Instead
of inline `graph`, `workload` may name an absolute JSON `graph_file` plus its
`graph_sha256`; that file contains the same vertex/edge mapping. A graph can instead
provide `adjacency`, with exactly one sorted, distinct, in-range neighbor list per
vertex, no self loops, and exact symmetry when undirected. It cannot also provide
`edges`. Both forms have the same canonical identity. Registered workloads use
`workload: {id: ...}`; SG materialization verifies the retained serialized hash and
canonical identity, then carries adjacency directly under the native limits of
2,000,000 vertices, 32,000,000 directed adjacency entries, and 512 MiB of input.
The evaluation retains the original serialized representation identity. Diagnostic
reloads read the evaluator's sorted adjacency file incrementally under the same
vertex/edge bounds. Neither path expands CSR into millions of temporary edge pairs.
`build` optionally overrides `compiler` and a bounded `flags` argument list.
`fixture: true` labels external benchmark/compiler fixtures explicitly; their
durations are contract evidence and cannot establish native BFS performance.

The authoritative `evaluation` record stores `request`, `outcome`, `stages`,
`timing`, `correctness`, `profiling`, `raw_artifacts`, `evidence_kind`, and
`gain_claim`. Resolved links name `candidate`, `proposal`, `source_snapshot`,
`profile_package`, `implementation`, `machine`, and the independently chosen
`comparison_baseline`. `context` holds exact source, target, workload, requested
thread/source/repetition settings, protected ROI, and verifier identities. `build`
records actual compiler arguments and hashes. `summary` appears only after every
requested trial completes and passes the structural check.

Each entry in `stages` has its `stage`, `state`, `started` timestamp, and eventually
`finished`; child-stage `host_wall_s` is execution cost outside the primary ROI
metric. Each `timing` entry names `source`, `source_position`, `repetition`,
`duration_s`, `roi`, `basis`, `quantity`, `binary_sha256`, `output`,
`output_sha256`, `verified`, and `evidence_kind`. `source_position` preserves
ordered-source identity even when the same source appears repeatedly. The
`quantity` is `native_roi_wall_seconds` for this backend. The `checks` array under `correctness`
contains the verdict and graph/binary/result identity for every checked trial;
its overall `state` remains unverified when later trials are interrupted.

Keep implementation narrow: `swdb/bfs_native.py` orchestrates stages;
`tools/bfs_native/driver.cc.in` holds the protected wrapper; and a verifier helper
checks exported arrays independently. Do not grow the legacy `profile.py` into
the durable proposal worker. Reuse its verified-lane logic and bounded process
group execution where doing so preserves failures and signal cleanup.

## Protected wrapper and complete-call ROI

Generate a wrapper in the external run directory. Include the exact candidate BFS
translation unit with its `main` renamed, then define an evaluator-owned `main`:

```cpp
#define main swdb_unused_application_main
#include "ABSOLUTE_CANDIDATE_BFS_SOURCE"
#undef main

// Parse only evaluator arguments here; graph-builder arguments are a separate list.
// Materialize and validate the graph before the timed operation.
const NodeID source = explicitly_requested_source;
const auto begin = std::chrono::steady_clock::now();
auto parent = DOBFS(graph, source, false);
const auto end = std::chrono::steady_clock::now();
// Persist the complete returned parent array and duration after the timer stops.
```

The actual wrapper also supplies includes, checked argument parsing, graph
construction, exact-length binary result capture, and explicit error outcomes.
The snippet specifies the boundary; it is not standalone implementation code.
The candidate's ordinary `main`, `BFSVerifier`, `PrintBFSStats`, and
`BenchmarkKernel` are not called. No candidate output string grants a pass.

Use one process per requested source/repetition initially. This makes each
completed parent artifact recoverable and bounds the DX100 functional API's
allocation lifetime: its `alloc_MAA()` allocates storage without a matching cleanup
in the inspected call path. Repeating processes is a repetition policy, not
additional source coverage. Graph construction stays outside the complete-call
ROI, and its cache effects are part of the declared process-start treatment.

Compile directly with a controlled argument vector, not a candidate-supplied shell
command. Upstream needs its source include root and the declared compiler/OpenMP
flags. DX100 additionally needs the API include root and `-DFUNC`; record the
effective `NUM_CORES` and `TILE_SIZE` definitions. The native scalar evaluator
rejects `-DMAA`, `-DGEM5`, and a request for accelerator timing. The pinned DX100
API currently defaults to `NUM_CORES=4` and `TILE_SIZE=16384`.

Record the compiler executable/version, complete argument vector, relevant
environment, wrapper hash, input hash, candidate manifest, binary hash, and source
adapter identity. Rehash protected inputs immediately before dispatch and retain
the compiled dependency manifest. Existing assertions remain enabled for the
diagnostic build; a separate sanitizer build, if used, has its own artifact and
cannot certify an otherwise untested timing binary.

Protect the evaluator template, canonical workload, verifier module, result
schema, and evaluator-owned ROI definitions outside the candidate snapshot.
Ticket 02 must also reject changes to protected source definitions already named
by the source adapter, including embedded verifier and ROI controls. Permitted
helper/header edits are retained, but cannot alter trusted build flags or replace
the evaluator template through include search paths. Reject stale content,
symlink substitution, paths outside the declared snapshot, duplicate protected
definitions, and unsupported callable signatures before running.

The implementation rejects candidate preprocessor definitions or undefinitions
of identifiers used in the trusted driver suffix. The scan removes line
continuations and comments before checking directives and includes extensionless
and `.inc` inputs. It also rejects inputs that shadow trusted standard headers
or `omp.h`. This prevents a permitted source edit from turning the wrapper's
clock or parent-serialization expressions into macro substitutions.

This is a reproducible compiler-research boundary for authorized candidate code,
not a security sandbox for actively malicious C++ programs. A crashed or malformed
candidate output is a failed evaluation and cannot produce a verified result.

## Independent structural correctness

The trusted verifier consumes the original canonical adjacency, explicit source,
and the parent vector exported by the same binary invocation whose duration is
recorded. It does not consume the candidate's printed verdict. Its algorithm is:

1. Validate the input graph representation before constructing adjacency: finite
   nonnegative vertex/edge counts, bounded allocation, monotone CSR offsets,
   `offsets[0] == 0`, `offsets[n] == m`, and every neighbor in `[0, n)`.
2. Require a nonempty graph, `0 <= source < n`, exactly `n` parent entries, and
   each parent to be an integer in `[-1, n)`. Reject truncated/trailing data and
   inconsistent count fields before allocating from them or indexing arrays.
3. Compute shortest unweighted depths from the explicit source using a trusted
   queue over outgoing adjacency; use a wide enough depth/index type.
4. Require `parent[source] == source`. For every other reachable vertex `v`,
   require `parent[v] >= 0`, the edge `parent[v] -> v`, and
   `depth[parent[v]] + 1 == depth[v]`. For every unreachable vertex require `-1`.
5. Persist pass/fail, source, graph identity, returned-array identity, binary
   identity, verifier version/hash, and the first bounded diagnostic reason.

Check ranges before indexing with any parent value. Any valid predecessor at the
previous BFS depth is accepted; there is no bitwise comparison against one parent
tree. Competing parent updates, isolated vertices, directed reachability, and
disconnected components are valid correctness cases. A source with zero outgoing
degree is valid when explicitly requested. Never invoke `SourcePicker` on an
edgeless graph: its random nonzero-degree search cannot terminate there.

For the first implementation, the Python verifier can operate on small diagnostic
graphs. Large-graph acceptance may use a separately built trusted C++ verifier
over the same canonical binary format to bound Python memory overhead. Such a
change needs equivalence tests and a recorded verifier identity; it must not
silently replace the checked criterion.

Keep each exact result file until its verification result is durably written.
Only a trial with a finite positive ROI duration, complete output, matching
identities, successful process completion, and an explicit structural pass is
eligible timing evidence. Retain durations observed before later failure as
unverified diagnostics; do not quietly drop a failing repetition and aggregate
the survivors into a successful result.

## Graph identity and source sequence

Use a canonical adjacency stream with explicit version, directedness, vertex
count, neighbor counts, and fixed-width little-endian vertex IDs. Sort neighbors
for semantic identity and record the normalization/duplicate policy. Separately
retain each loaded adjacency-order hash: equal edge sets do not imply equal
traversal order or equal performance. Isolated vertices are represented by the
declared vertex count, not inferred from the largest ID appearing in an edge list.

For small integration cases, use one canonical edge-list input where appropriate,
then dump the graph actually loaded by each source adapter and compare it with
the canonical graph. A plain edge list alone cannot represent trailing isolated
vertices reliably; use a representation with explicit vertex count for those
cases. A graph/source workload binds an ordered, explicit source list. A new
process restarting the source picker's deterministic seed is not a new workload.

For serialized graphs, record a source-specific format identifier, native ABI
assumptions, and content hash. Produce upstream and DX100 representations
separately. Validate their loaded outgoing adjacency and inverse adjacency where
present; reject a 64-bit-offset file passed to the 32-bit reader before execution.
Do not rely on the readers' unchecked raw `file.read` calls for input validation.
DX100's 32-bit offsets require the directed edge count to fit the signed 32-bit
range. A format conversion must preserve vertex IDs, normalization, and ordered
sources and retain both representation identities.

Ticket 03 can accept and bind explicit diagnostic workload identities. Ticket 11
owns authoritative registration/versioning and comparison enforcement; Ticket 03
must not fabricate canonical equivalence from matching filenames while waiting
for that interface.

## Durable stages and interruption

Persist the request before processing, then write each stage transition atomically
through the workflow store. Stages are `source_resolution`, `protection`, `build`,
`workload_resolution`, per-trial `execution`/`correctness`, `aggregation`, and
`persistence`. Pending/running stages are distinguishable from complete ones.
Each stage names its command, time budget, timestamps, return code or signal,
artifact paths/hashes, and reason. Use unique run IDs; never overwrite an earlier
run's directory.

Each child process runs in its own process group. Timeout, interrupt, or signal
kills and reaps the complete group before releasing the lane. The supervisor
retains earlier completed stage records and marks the current stage interrupted
or timed out. A fresh process can identify an abandoned running stage without
claiming that it completed. Raw output remains outside Git and on its producing
host, following the mbit10 disk/lane rules.

Ticket 03 returns `profiling.status: unavailable` with specific missing function,
loop, and dynamic-memory capabilities until later tickets provide real evidence.
Successful correctness may produce workload/target-scoped verification; it is
not general certification over all graphs. The explicit comparison baseline is
retained independently of source ancestry. No protocol-less ratio is a gain.

## Extension to diagnostic profiling

Tickets 06–08 reuse the exact invocation context with distinct diagnostic artifact
identities. Compiler AST discovery inspects current candidate function and loop
definitions, including eligible new helpers, without a fixed symbol whitelist.
Nested timing uses per-thread scope stacks and reports accumulated inclusive and
exclusive durations plus invocation counts. A sum across threads is not BFS wall
duration. Unsupported macro/OpenMP/source mappings remain explicit attribution
gaps, and instrumentation overhead is retained as a limitation.

Callgrind can supply executed memory read/write counts and modeled cache misses
inside an evaluator-owned collection boundary. Keep instruction counts separate
from durations and simulated cache results separate from native hardware facts.
Its collection controls and thread-dump behavior require testing on the actual
installed version. See the [Callgrind manual](https://valgrind.org/docs/manual/cl-manual.html)
and [Clang AST matching documentation](https://clang.llvm.org/docs/LibASTMatchers.html).
No source-order CSR traversal substitutes for the candidate's executed frontier.

## Acceptance checks for Ticket 03

Exercise the public proposal/evaluation/retrieval workflow, not only private
helpers. Contract cases cover build failure, timeout, interruption after a
completed trial, malformed output, exit-zero verifier failure, wrong sources,
invalid parent ranges, and missing ROI output. Structural cases accept distinct
valid BFS trees and reject wrong depth, predecessor, source, or reachability.
Fixture timings remain labeled fixtures and cannot establish native execution.

Run a real small DX100 scalar candidate first, then upstream, under the verified
mbit10 lane wrapper. Retain exact source/binary/input identities and parent-array
evidence. These runs establish diagnostic integration and correctness, not a
candidate gain. Later pilot and protocol tickets determine performance workloads
and their repetition policy before candidate assessment.
