# SW Database: Record Format Proposal

Navigation updated: 2026-09-28 (Eastern Time).

- Version: 0.1 draft, 2026-09-22
- Author: Yan-Ru Jhou
- Reviewers: Peter Cao (SW agent), Joshveer Grewal (HW agent)
- Status: proposal only. No records, schema files, or tools exist yet.

## 1. Purpose

The Software Database is one box in the ArchEvolve framework (Fig. 1). It has two
jobs for the Controller:

1. **Out: metrics and code patterns.** For a kernel on a given input, what the code
   does, and what profiling measured.
2. **In: SW specs.** For a hardware need, which implementations (code) of the
   kernel exist, and what each one guarantees.

The database holds curated records that can be reproduced. Peter's agent profiles
new kernels and writes its results back as records of the same kinds (Sec. 9).

The pilot data is the upstream GAP Benchmark Suite (gapbs). The real kernels come
from collaborators later, so nothing in the format is specific to gapbs.

## 2. Design rules

These rules let the format change without breaking readers.

- **R1.** One record per YAML file. Every record starts with the same envelope (Sec. 4).
- **R2.** IDs are stable. An ID is never reused or renamed. Records refer to each
  other by ID, never by file path.
- **R3.** Readers ignore keys they do not know. A new field starts under
  `extensions:` and moves into the core format once the readers agree on it.
- **R4.** Term lists (pattern classes, bottleneck classes, and so on) live in
  `vocab/*.yaml`, one file per list, with a one-line meaning for each value. Adding
  a value does not change the format.
- **R5.** Metrics are an open list of `{name, value, unit, ...}` entries, not fixed
  fields. A new metric needs no format change.
- **R6.** Every semantic fact states its basis (Sec. 5). `unknown` is a real value.
  It never means false, zero, or "safe to reorder".
- **R7.** Units are explicit. Every count states its scope: per sweep, per call,
  or per run.
- **R8.** Raw tool output stays in files. Records hold the distilled values and
  point to the raw files.
- **R9.** The files are the only source of truth. Agents may read them directly or
  through a query tool, and the tool only reads the files.

## 3. Record kinds

```
application ──< kernel ──< option (alternative code for the kernel)
                  │
       input ──┐  │
     machine ──┼──< profile  (one kernel × one input × one machine × one build × one thread count)
                  
workload view = generated from kernel + input + profile, in Josh's workload format (Sec. 7)
```

| Kind | Changes when | Holds |
|---|---|---|
| `application` | the source version changes | origin, license, build, parallel model |
| `kernel` | the code changes | hot-loop code, loop structure, access patterns, arrays, semantics |
| `input` | the data changes | generator arguments or file, measured properties |
| `machine` | the host changes | CPU, caches, memory, counter access |
| `profile` | any of the above changes | counts, metrics, bottleneck, raw files |
| `option` | a new implementation is added | code, what it guarantees, what it needs, a correctness check |

**Why kernels and profiles are separate:** the same loop can be memory-bound on one
input and fit in cache on another. Semantics come from the code and do not change
with the input. Metrics do change. (To be confirmed by the pilot, Sec. 10.)

## 4. Envelope (every record)

```yaml
kind: kernel                  # vocab/kinds.yaml
schema_version: "0.1"
id: gapbs.pr.pull_gs_sweep
status: draft                 # draft | reviewed | deprecated
deprecated_by: null           # ID of the replacement, when deprecated
created: 2026-09-22
updated: 2026-09-22
provenance:                   # same shape as `provenance` in Josh's workload file
  - id: src-gapbs-pr
    kind: source_code         # vocab/provenance_kinds.yaml: source_code | measurement | human_report | agent_run | paper
    description: gapbs src/pr.cc, upstream copy
    uri: null
notes: []
extensions: {}
```

## 5. Facts with a basis

Semantic facts, and the bottleneck, use one wrapper:

```yaml
duplicate_target_indices:
  value: true                 # true | false | a vocab value | null
  basis: code_reading         # measured | code_reading | reported | inferred | unknown
  evidence_refs: [src-gapbs-pr]
  note: a vertex v appears in the in-neighbor lists of many vertices u
```

If `basis` is `unknown`, then `value` is `null`.

## 6. Record kinds, with a worked example (gapbs PageRank)

Values marked `<...>` are captured from the host or source at record time. Values
marked `null` with `basis: unknown` still need a measurement. Nothing below has
been measured yet.

### 6.1 application

```yaml
kind: application
id: gapbs
name: GAP Benchmark Suite
source:
  origin: upstream
  uri: https://github.com/sbeamer/gapbs
  commit: <pin>
license: BSD-style, UC Regents (see LICENSE)
language: C++11
parallel_model: OpenMP
build: {command: make, flags: "-std=c++11 -O3 -Wall -fopenmp"}
domain: graph                 # vocab/domains.yaml
kernels: [gapbs.pr.pull_gs_sweep]
```

### 6.2 kernel

The code block is copied from `src/pr.cc` lines 43-59. The `logging_enabled` lines
are omitted.

```yaml
kind: kernel
id: gapbs.pr.pull_gs_sweep
application: gapbs
function: PageRankPullGS
location: {file: src/pr.cc, lines: "43-59"}
code: |
  for (int iter=0; iter < max_iters; iter++) {
    double error = 0;
    #pragma omp parallel for reduction(+ : error) schedule(dynamic, 16384)
    for (NodeID u=0; u < g.num_nodes(); u++) {
      ScoreT incoming_total = 0;
      for (NodeID v : g.in_neigh(u))
        incoming_total += outgoing_contrib[v];
      ScoreT old_score = scores[u];
      scores[u] = base_score + kDamp * incoming_total;
      error += fabs(scores[u] - old_score);
      outgoing_contrib[u] = scores[u] / g.out_degree(u);
    }
    if (error < epsilon)
      break;
  }
loops:
  - {id: iter, trip: "<= max_iters (-i, default 20); stops when error < epsilon (-t, default 1e-4)", parallel: none}
  - {id: u, trip: num_nodes, parallel: "omp for, schedule(dynamic,16384)"}
  - {id: v, trip: "in_degree(u); the sum over all u is num_edges_directed", parallel: none}
patterns:                     # same structure as `patterns` in Josh's workload file
  - id: gather
    expression: "outgoing_contrib[v], v in in_neighbors[in_index[u] .. in_index[u+1])"
    class: range_indirect_gather          # vocab/pattern_classes.yaml
    memory_operation: read
    update: {kind: add_to_register, pseudocode: "incoming_total += outgoing_contrib[v]"}
    arrays:                               # element_count is a formula over input properties
      - {name: in_index,         role: range_index, element_type: "NodeID*", element_bytes: 8, element_count: "num_nodes + 1"}
      - {name: in_neighbors,     role: index,       element_type: int32,     element_bytes: 4, element_count: num_edges_directed}
      - {name: outgoing_contrib, role: target,      element_type: float,     element_bytes: 4, element_count: num_nodes}
    semantics:
      duplicate_target_indices: {value: true, basis: code_reading, evidence_refs: [src-gapbs-pr]}
      index_modified_during_loop: {value: false, basis: code_reading, note: "the graph is passed as const Graph&"}
      loop_carried_dependencies:
        value: true
        basis: code_reading
        note: >-
          Gauss-Seidel style. outgoing_contrib[u] is written in the same sweep that
          reads outgoing_contrib[v]. Under OpenMP, a read can see the old value or
          the new one.
      shared_target_between_threads: {value: read_shared, basis: code_reading}
      atomic_updates_required: {value: false, basis: code_reading}
      ordering: {value: nondeterministic_tolerated, basis: code_reading, note: "PRVerifier checks total error against the tolerance"}
      numerical_requirement: {value: tolerance, basis: code_reading, note: "-t, default 1e-4"}
  - id: owner_writes
    expression: "scores[u], outgoing_contrib[u]"
    class: direct_stream
    memory_operation: write
    arrays:
      - {name: scores,           role: target, element_type: float, element_bytes: 4, element_count: num_nodes}
      - {name: outgoing_contrib, role: target, element_type: float, element_bytes: 4, element_count: num_nodes}
options: [gapbs.pr.pull_jacobi]
```

Types: `NodeID` is `int32_t` (`src/benchmark.h:31`), and `ScoreT` is `float`
(`src/pr.cc:30`).

### 6.3 input

```yaml
kind: input
id: gapbs.kron-s20-k16
generator: {tool: gapbs, args: "-g 20 -k 16"}   # or file: {path, format, checksum}
properties:                                       # the symbols used by kernel formulas
  num_nodes:            {value: 1048576, basis: code_reading, note: "2^scale"}
  avg_degree_requested: {value: 16, basis: reported}
  num_edges_directed:   {value: null, basis: unknown, note: "measure after the graph is built"}
  degree_distribution:  {value: skewed, basis: inferred, note: "Kronecker generator"}
  index_locality:       {value: null, basis: unknown}
  density:              {value: sparse, basis: inferred, note: "density of the data fed in, not the storage format"}
```

The contrast input is `gapbs.urand-s20-k16` (`-u 20 -k 16`), which has the same
size and uniform degrees.

### 6.4 machine

```yaml
kind: machine
id: mbit10
isa: x86_64
cpu: <lscpu model name>
sockets: <n>
cores_per_socket: <n>
caches:
  - {level: L1d, bytes: <n>, shared_by: core}
  - {level: L2,  bytes: <n>, shared_by: core}
  - {level: L3,  bytes: <n>, shared_by: socket}
memory: {bytes: <n>, numa_nodes: <n>}
os: <uname -r>
counter_access: {perf_event_paranoid: <n>, readable_events: [<...>]}
captured: {command: "lscpu; uname -r; cat /proc/sys/kernel/perf_event_paranoid", date: <YYYY-MM-DD>}
```

Any machine can be used. mbit10 is the test host.

### 6.5 profile

```yaml
kind: profile
id: prof.gapbs.pr.pull_gs_sweep.kron-s20-k16.mbit10.t14.20260923a
kernel: gapbs.pr.pull_gs_sweep
input: gapbs.kron-s20-k16
machine: mbit10
build: {compiler: <g++ --version>, flags: "-std=c++11 -O3 -Wall -fopenmp", source_commit: <sha>}
run: {command: "./pr -g 20 -k 16 -n 5", threads: 14, binding: <numactl args>, date: <YYYY-MM-DD>}
counts:
  - {name: inner_iterations, value: null, scope: per_sweep, note: "equals num_edges_directed"}
  - {name: sweeps,           value: null, scope: per_call,  note: "until error < 1e-4, at most 20"}
  - {name: calls,            value: 5,    scope: per_run,   note: "-n trials; each call restarts from the initial scores"}
metrics:                                  # open list; names from vocab/metrics.yaml
  - {name: kernel_time,           value: null, unit: s,              scope: per_call, tool: gapbs_timer}
  - {name: time_share,            value: null, unit: fraction,       scope: per_run,  tool: perf_record}
  - {name: llc_mpki,              value: null, unit: misses_per_kinstr, tool: perf_stat, events: [<...>]}
  - {name: dram_bandwidth,        value: null, unit: GB/s,           tool: <...>}
  - {name: footprint,             array: outgoing_contrib, value: null, unit: bytes}
  - {name: index_duplicate_ratio, array: in_neighbors,     value: null, unit: fraction}
bottleneck:
  value: null                             # vocab/bottlenecks.yaml
  basis: unknown
  evidence: [llc_mpki, dram_bandwidth]    # metric names this verdict rests on
raw_files:
  - {type: stdout,    path: raw/stdout.txt}
  - {type: perf_stat, path: raw/perf_stat.txt}
  # A new file type (for example a memory trace) needs no format change.
```

### 6.6 option (the code itself)

```yaml
kind: option
id: gapbs.pr.pull_jacobi
applies_to:
  kernels: [gapbs.pr.pull_gs_sweep]
  pattern_classes: [range_indirect_gather]
summary: >-
  Jacobi-style PageRank. Each sweep first computes every outgoing_contrib, then
  gathers, so the gather reads only values from the previous sweep.
code:
  origin: {uri: https://github.com/sbeamer/gapbs, file: src/pr_spmv.cc, function: PageRankPull, lines: "35-61", commit: <pin>}
  files: [code/pr_spmv.cc]                 # the code is stored next to this record
  build: make pr_spmv
changes:                                   # the kernel semantics this option changes
  loop_carried_dependencies: {value: false, basis: code_reading, note: "the gather reads values from the previous sweep only"}
  ordering: {value: deterministic_per_sweep, basis: inferred, note: "the reduction order of error can still vary"}
requires:
  - {what: "one extra pass over num_nodes per sweep"}
correctness_check: {command: "./pr_spmv -g 16 -v", criterion: "PRVerifier passes"}
license: BSD-style, UC Regents
```

## 7. Workload view (Josh's format)

The Controller gets a generated view in Josh's workload format
(`HW_ensemble/sparta-sort.input.yaml`). Josh's format needs no change.

| Field in Josh's workload file | Filled from |
|---|---|
| `workload_id` | `<kernel id>@<input id>@<machine id>` |
| `benchmark`, `function` | `application.name`, `kernel.function` |
| `provenance` | the provenance of all joined records |
| `code` | `kernel.code` |
| `environment` | `machine` and `profile.build` / `profile.run` |
| `patterns[].arrays[].element_count` | the kernel formula, evaluated with `input.properties` |
| `patterns[].semantics` | `kernel` semantics (value), with the basis moved to evidence |
| `counts` | `profile.counts` (the scope is always stated) |
| `bottleneck`, `metrics` | `profile.bottleneck`, `profile.metrics` |

## 8. Directory layout

```
SW_Database/
  FORMAT_PROPOSAL.md
  vocab/                            term lists (R4)
  schema/                           one JSON Schema per kind (later)
  applications/<app>.yaml
  kernels/<app>/<kernel>.yaml
  inputs/<input>.yaml
  machines/<machine>.yaml
  profiles/<profile-id>/profile.yaml
  profiles/<profile-id>/raw/        large raw data stays on the measuring host; record its path
  options/<option-id>/option.yaml
  options/<option-id>/code/
  views/                            generated workload views; never edited by hand
```

## 9. Versioning and change process

- `schema_version` is `"MAJOR.MINOR"`.
- **Minor change:** add an optional field, a vocab value, or a record kind. Old
  records stay valid.
- **Major change:** rename or remove a field, or change what a field means. A
  migration script rewrites all records in the same commit.
- New ideas start under `extensions:`. They move into the core format when the
  readers agree.
- Records are deprecated, never deleted: set `status: deprecated` and `deprecated_by`.
- Agent writes (for example Peter's profiling) use the same record kinds, with
  `provenance.kind: agent_run` and `status: draft` until a person reviews them.

## 10. Open items

| # | Item | Owner |
|---|---|---|
| 1 | Pilot: `gapbs.pr.pull_gs_sweep` on the Kronecker and uniform inputs. If the bottleneck differs, the kernel/profile split (Sec. 3) holds. Also confirm one hot loop per kernel record. | Yan-Ru |
| 2 | `HW_ensemble/hardware-agent.md` cites `schemas/workload.schema.json`, which is not in this folder. If that schema differs from `sparta-sort.input.yaml`, the view in Sec. 7 follows the schema. | Josh |
| 3 | Does the Evaluator need memory traces, or only metrics? `profile.raw_files` can carry traces without a format change. | Evaluator owner |
| 4 | Which kernels collaborators will supply, when, and in what form. Which of them covers dense GEMV/GEMM. | Team |
| 5 | Interface of the read-only query tool (R9). | Yan-Ru, Peter |
| 6 | Rules for agent write-back (Sec. 9). | Peter |
