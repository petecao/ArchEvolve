# BFS baseline and reference pilot plan

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)

This plan fixes the permitted calibration scope before candidate performance
assessment. It is dependent preparation for Ticket 15; no empirical protocol is
frozen by this document, and no calibration gate is accepted without its evidence.

## Permitted artifacts and questions

Use the unchanged upstream GAPBS `gapbs-bfs-do`, unchanged DX100 scalar
`dx100-bfs-scalar`, and the pinned authors' accelerated BFS at revision
`e4fc4afdf894f295442cef3604667a469fab8e62`. The public `baseline-candidate`
materialization must preserve the exact source snapshot hash; no artificial patch
creates a baseline. Earlier tiny source-changing diagnostics test workflow and
correctness only. Their times cannot select candidate workloads or a gain policy.

The pilot answers whether the two graph families exercise real accelerator work,
whether every timed parent tree passes independent structural verification, which
sizes fit bounded simulation/storage cost, and whether function, loop, and memory
observations have usable source attribution. Native and simulator evidence remain
separate. The authors' uniform-random scale-22, degree-16 input is retained as the
independently frozen Ticket 16 artifact-reference case, regardless of pilot sizes.

## Bounded execution

Use at most the two owned socket lanes on mbit10 and always enter through the
verified current `socket_lane.sh`. Check both socket leases and the legacy lease,
space, available memory, other jobs, exact Git revisions, and affinity before each
dispatch. Record host interference; never modify governor/turbo or other users'
processes. Source/builds remain under `/data1/yanruj`; raw outputs use the recorded
`/data/yanruj/EvolveSWDB_runs` overflow directory while the planned run would take
`/data1` below 20 GiB free. Recheck space before every large build/run.

- Model bring-up: at most two attempts, each 7,200 seconds, eight build jobs,
  48 GiB aggregate process RSS, 10 GiB build tree, and 2 GiB logs. A retry requires
  a diagnosed build/dependency correction and a distinct retained attempt.
- Candidate-size calibration: scale 14 establishes correctness and accelerator
  coverage; scale 18 is the preferred performance pilot, with scale 16 permitted
  only when scale 18 exceeds the declared cost bounds. Use edge factor 16 for both
  Kronecker and uniform-random families. The pinned generator forces
  symmetrization for either synthetic family even without an explicit `-s` flag
  (`command_line.h:76–77`); resulting graphs are undirected. Before deduplication,
  outgoing neighbor entries, 64-bit CSR row pointers, and 32-bit parents total
  approximately 8.75 MiB at scale 16 and 35 MiB at scale 18. These estimates exclude
  queues, bitmaps, and runtime storage; deduplication can reduce the footprint,
  particularly for Kronecker. The scale-16 subset is close to the modeled 8 MiB
  LLC, so its cache behavior must be observed. Retain actual adjacency bytes,
  sources, and memory observations before selecting the size. No arbitrary scale sweep
  follows a negative result. Generate each permitted graph once per pinned
  generator and retain SG32/SG64 representation hashes and canonical loaded
  adjacency identity. Size selection uses unchanged baseline/reference cost and
  coverage, never candidate gains; the 12-hour pilot cap remains unchanged.
  The pinned builder sets the realized vertex count to `FindMaxNodeID(el) + 1`
  (`builder.h:313–321,339–354`), so it can be below `2**scale`. The retained
  Kronecker-18 graph has 262143 vertices, 7610898 directed adjacency entries, and
  88159 isolates; uniform-18 has 262144 vertices, 8388040 entries, and no isolates.
  Preserve all realized vertices and isolates. Version-2 registration corrects
  the first records' erroneous `symmetrize: false` to the effective `true`, with
  explicit CLI flag absence recorded separately and the graph files unchanged.
- Ordered diagnostic sources: `[0, 1234, 7777]` for these scales. Retain isolated
  sources and their outcomes. A source replacement requires a versioned workload
  with a coverage-based reason before any candidate assessment.
- Native calibration: four threads, five fresh-process complete-BFS-call trials
  per ordered source and unchanged starting implementation; at most two complete
  repeated calibration blocks per size/family. Build budget 180 seconds, each
  traversal budget 60 seconds, and total per evaluation 1,200 seconds. Repeated
  trials of one graph/source are distinguished from different source vertices.
- Simulator calibration: four guest cores, baseline/reference only, two identical
  replays per graph/source/configuration. Each replay is a new simulator process;
  the second restores the same manifest-verified checkpoint for that exact
  source/binary/configuration. Primary and diagnostic binaries keep separate
  checkpoints. This pre-execution choice avoids redundant guest serialization
  after the tiny checkpoint cost was observed; it does not reuse ROI measurements.
  Each checkpoint or restored traversal
  gets at most 3,600 host seconds, 32 GiB sampled host RSS, and 10 GiB retained output;
  predeclare a bounded post-ROI verification tick allowance separately. At most
  one diagnosed rerun per failed configuration. Total calibration wall budget is
  12 hours across the two lanes, excluding the bounded model build.
- Separately instrumented collector cases get at most 600 seconds each and do not
  replace the primary timing trials. Collector overhead and code/build differences
  are retained. Limit combined raw pilot output to 40 GiB; stop safely if available
  output-volume space falls below 30 GiB or source/build-volume space below 10 GiB.
  The 10 GiB source/build reserve is a deliberate calibration choice: the observed
  22 GiB free before bring-up must accommodate its separately capped 10 GiB build;
  the repository host rule moves raw output to the overflow volume at 20 GiB and
  does not prohibit source/build storage below that threshold.

A timeout, insufficient accelerator coverage, failed verifier, missing region or
memory evidence, excessive resource cost, or unusable attribution retains a
failed/incomplete observation. It does not authorize removing a graph family,
relabeling scalar fallback as acceleration, choosing by a candidate's speedup, or
continuing until a favorable number appears. Independent implementation work may
continue while an empirical gate remains unresolved.

## Settings selected after baseline observations

Select scale 18 for performance when it satisfies the declared cost bounds,
full-block and tail execution, competing parent updates, both families, and exact
timed-binary correctness. A cost-bounded fallback to scale 16 must retain the
scale-18 failure and explicitly qualify any cache-resident workload limitation.
Scale 14 remains a correctness and coverage diagnostic. The
selected-region mapping must come from automatic source discovery. Record whether
measurements are inclusive or exclusive and per invocation or accumulated. Freeze
actual source/binary/model identities, source list, graph identity, CPU/cache/memory
and clock settings, build flags/compiler version, ROI semantics, instrumentation,
region correspondence, and actual lane before candidate dispatch.

Native primary ROI is the complete BFS call including its initialization. Freeze
zero untimed warmups and at least five repetitions. Use a geometric mean of the
per-source median baseline/candidate ratios, paired by exact graph/source. Record
within-source relative timing spread from actual baseline trials; reject a gain
assessment with excessive interference instead of assigning a neutral ratio.
The initial policy floor is a 1.05 speedup and a 95% bootstrap lower bound above
1.05, with 2,000 resamples and a fixed recorded seed. The allowable relative spread
must be justified by the unchanged-baseline pilot before freezing. If the bounded
pilot cannot meet it, record the limitation rather than weakening the policy to
admit a candidate. Confidence intervals describe the observed repeated workloads,
not an unmeasured population of graphs.

Simulation timing uses actual ROI ticks and the recorded tick/clock conversion;
simulator-host wall time is cost only. Two identical replays must establish their
observed repeatability; guest trial counts do not substitute for completed runs.
The authors' BASE 10 MiB/20-way LLC and MAA 8 MiB/16-way LLC remain distinct in the
artifact pair. Additional controlled pairs match CPU/cache/memory/clock settings
and explicitly enumerate software and accelerator differences. No joint pair is
called an isolated software-only gain.

## Freeze and handoff

Publish content-addressed workload and protocol records with retained pilot
records before candidate assessment. A later setting change creates a superseding
version and requires fresh compatible comparisons. All eight source/route/family
cells, both sources' accelerated minimum on both families, the independent authors'
artifact/reference and matched controls, and a correctness- and policy-qualified
improvement remain separate acceptance obligations. This pilot cannot satisfy
those obligations by itself.
