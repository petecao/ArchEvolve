# Author BFS reference and matched-control freeze recipe

Date: 2026-09-25 (Eastern Time)

This is a reviewable operator recipe for Ticket 16. It does not freeze a protocol,
dispatch a simulator, or claim reference acceptance. The prescribed run plan is
[artifact-reference-plan.md](../.scratch/bfs-rewrite-evaluation-2026-09-25/artifact-reference-plan.md).
Use public records and commands below; replace every angle-bracket input with an
actual returned identifier or observed value before execution.

| Input | Current evidence or unresolved value |
|---|---|
| Pinned source | DX100 `e4fc4afdf894f295442cef3604667a469fab8e62` |
| Model build | `bfs-dx100-build-20260925-a2`; recompute its complete record digest at freeze |
| Simulator | `build/X86/gem5.opt`, SHA256 `f4038c88318ee09085b6c07f163094a07a31a256f21b652d4f3cfa046feb1f6b` |
| Author scalar | `benchmarks/gapbs/bfs`, SHA256 `70301ad2e587c2dd55a730da5e0135337cb6b46ddd72999a843f86fd4b070dd1` |
| Author MAA | `benchmarks/gapbs/bfs_maa`, SHA256 `6abd8190e4e1daf7c670c214dd0323393e3d29a9a26a3487c21f66e5ef194a5d` |
| Model root | `/data1/yanruj/DX100-bfs-e4fc4af` |
| Runtime shared library | `ext/ramulator2/ramulator2/libramulator.so`, SHA256 `46b5dbd87a77845ebadd1854e990d8e5c04c41253ad76315a766d61b77ca43dd` |
| Runtime package receipt | Recorded JSON SHA256 `ae7389a0b6848fa21eae7c527211948a88e3010f9a5135754a2241dc6f5542c4`; system package versions do not establish unrecorded file hashes |
| Workload and source | `bfs-20260925-uniform22.f23b09bb0c0601b5`; actual pinned SourcePicker source2796003, degree40; uniform scale22/degree16/seed27491095 with effective symmetrization |
| Fixed reference candidates | `bfs-author-scalar-compile-20260925-a1.candidate` and `bfs-author-maa-compile-20260925-a1.candidate`; unchanged public source candidates audited in `observations/dx100-compile-extension-a1.json` |
| Region correspondence | **Unresolved:** compiler-discovered scalar/MAA region IDs, actual diagnostic library/pass/runtime hashes and explicit semantic mapping |
| Protocol IDs and results | **Unresolved:** two independently frozen protocols and their actual replay/aggregate/package IDs |

The registered graph has 4194304 vertices, 134217158 directed adjacency entries,
undirected topology and zero isolates. Its exact hashes and source selection audit
are in [the preparation receipt](../.scratch/bfs-rewrite-evaluation-2026-09-25/observations/uniform22-preparation-a1.json)
and its public workload record. Generation and source selection are complete;
simulator feasibility and the two frozen comparisons remain pending.

The listed hashes are retained build metadata, not a fresh remote file check.
Rehash them on mbit10 before dispatch. Current scale18 registrations, native pilot
durations and fixture comparisons do not fill any unresolved author scale22 input.

## Prepare actual inputs

Run inside a verified owned socket lane using the current host procedure. Check
both socket leases and the legacy lease, current disk reserves and other users'
load; use a fresh checkout at an explicitly recorded Git commit. Keep raw data on
mbit10 outside Git. The existing public dispatch operations, with the identity and
regional comparison fixes described below, provide this sequence without another
evaluation backend.

1. Retrieve the existing registered graph and retain its audit. The completed
   preparation used
   `scripts/bfs_generate_workload.py --family uniform_random --scale 22
   --artifact-default-source`, with explicit `--id`, `--runs-dir`, `--build-dir`,
   `--records`, and `--lane`. Retain its converter source/binary/command, SG32 and
   widened SG64 hashes, canonical adjacency hash, realized vertices/arcs,
   `directed: false`, `symmetrize: true`, and `explicit_symmetrize_flag: false`.
   Preserve the original SourcePicker command, source and output evidence. Use
   the returned workload ID and its ordered `definition.sources`; do not regenerate
   it or type an
   assumed source ID. The driver calls public `register-workload` with streaming
   validation. New representations use the loader-compatible `.sg` suffix.
2. Use `swdb source-snapshot dx100-bfs-scalar --id <scalar-snapshot> --runs-dir
   <external-sources> --format json`, then `swdb baseline-candidate
   <scalar-snapshot> --id <scalar-candidate> --runs-dir <external-sources>
   --format json`. Repeat for `dx100-bfs-maa-reference`. Retrieve both with
   `swdb get <id> --chain --format json`. The first selects `DOBFS`; the second
   selects `DOBFSMAA`. Both must retain the pinned complete application manifest.
3. Retrieve `bfs-dx100-build-20260925-a2` and rehash its receipt, simulator, author
   guests and runtime library on mbit10. Preserve recorded dependency revision
   and package evidence. Build diagnostic source scopes through public
   `dx100-compile` with those candidates, `diagnostic_regions: true`, the author
   ROI, explicit `function`, `accelerated` and the selected `build_evaluation`.
   The resulting compilation receipts supply the real region IDs and collector
   hashes before freezing. Compilation alone is not timing or correctness evidence.

## Freeze two exact policies

Create separate version1 request files for these pairs:

| Policy mode | Baseline request configuration | Candidate request configuration |
|---|---|---|
| `artifact_reference` | `BASE`, LLC10MiB/20-way, tile16384 | `MAA`, LLC8MiB/16-way, tile16384 |
| `controlled_simulator` | `BASE`, LLC8MiB/16-way, tile16384 | `MAA`, LLC8MiB/16-way, tile16384 |

Each `settings.targets.<role>.configuration` must be the **full** mapping returned
by `swdb.dx100._configuration` for that four-field request and actual pinned model
root/target. This read-only adapter helper includes the complete command argument
list, CPU/cache/memory parameters, Ramulator configuration hash, clocks and model
revision. Do not reconstruct it from the four-field summary or copy a differently
configured smoke run. Retain the actual instantiated gem5 config after execution
and verify it agrees. Use target `dx100-e4fc4af-4c`, four threads and
`roi: bfs.dx100.traversal.v1` throughout.

Both requests have this shape; values marked `<...>` are unresolved inputs:

```yaml
message_version: '1.0'
id: <new-requested-protocol-name>
version: 1
settings:
  mode: <artifact_reference-or-controlled_simulator>
  kernel: gapbs-bfs
  workloads: [bfs-20260925-uniform22.f23b09bb0c0601b5]
  targets:
    baseline: {id: dx100-e4fc4af-4c, configuration: <full-BASE-mapping>}
    candidate: {id: dx100-e4fc4af-4c, configuration: <full-MAA-mapping>}
  simulation_identity:
    version: '1.0'
    model_build: {evaluation: bfs-dx100-build-20260925-a2, sha256: <whole-record-digest>}
    simulator: {path: <absolute-gem5.opt>, sha256: <receipt-simulator-hash>}
  reference_artifacts:
    baseline: <fixed-scalar-source-and-binary-identity>
    candidate: <fixed-MAA-source-and-binary-identity>
  builds:
    baseline: <author-scalar-compiler-version-flags-adapter>
    candidate: <author-MAA-compiler-version-flags-adapter>
  instrumentation:
    baseline: {treatment: primary, roi: bfs.dx100.traversal.v1, suppressed_internal_events: [], verification: same_guest_post_roi, debug_flags: MAATrace}
    candidate: {treatment: primary, roi: bfs.dx100.traversal.v1, suppressed_internal_events: [], verification: same_guest_post_roi, debug_flags: 'MAATrace,MAARangeFuser,MAAIndirect'}
  threads: 4
  roi: bfs.dx100.traversal.v1
  correctness:
    coverage: every_timed_trial
    verifier: dx100.bfs.verifier.v1
    required_cases: []
    required_accelerator_cases: {baseline: [], candidate: [executed]}
  sampling: {repetitions: 2, warmups: 0, aggregation: geomean_source_median_ratio}
  profitability: {minimum_speedup: 1.05, maximum_relative_spread: <reviewed-explicit-limit>, confidence: 0.95, bootstrap_resamples: 2000, bootstrap_seed: <fixed-seed>}
  differences:
    software: [Pinned scalar DOBFS versus pinned author DOBFSMAA.]
    accelerator: [MAA enabled only for the candidate role.]
    configuration: [<actual-LLC-difference-or-explicit-matched-settings>]
  region_pairs:
    - semantic_region: <reviewed-correspondence>
      baseline: <scalar-discovered-region-id>
      candidate: <MAA-discovered-region-id>
      scope: accumulated
      attribution: <inclusive-or-exclusive>
      evidence: simulated_diagnostic_profile
      collector: {backend: libclang-cindex, collector: dx100.m5_rpns.source_scopes.v1, library_sha256: <actual>, pass_sha256: <actual>, runtime_sha256: <actual>}
```

Every fixed-source identity mapping contains `candidate`, `candidate_sha256`
(digest of that record), `source_snapshot`, `source_snapshot_sha256`,
`source_artifact_sha256`, and `binary: {path, sha256}`. Compute record digests with
the repository's canonical `artifacts.digest`, not a YAML or pretty-JSON file hash.
Use `compiler: g++-13`, the exact first two compiler version lines in the retained
build receipt, and `adapter: dx100.author_artifact.v1`. Scalar flags are
`[-std=c++11, -O3, -Wall, -g3, -fopenmp, -DGEM5]`; MAA adds
`[-DMAA, -DNUM_CORES=4, -DTILE_SIZE=16384]` in that order. Diagnostic flags and
instrumented binaries are different artifacts and remain in their own receipts.

`required_cases` is the adapter's named correctness-case coverage mechanism, not
a place to invent fulfilled labels. The frozen per-role accelerator mapping checks
typed positive instruction counters and completed S/I/R/A traces for every MAA
replay. Add `full_tiles`, `tail_tiles`, or `competing_parent_updates` when that
protocol requires each case on every replay; a requested case needs a positive
observed count, not a context string. Scalar correctness and MAA exact timed-parent
correctness remain required independently. Explicitly choose the spread limit and seed
before publishing; neither missing measurements nor a regression authorizes relaxing
them. Positive gain is not needed for Ticket16 acceptance.

Publish only after review of concrete inputs:

```sh
python3 -m swdb freeze-protocol <artifact-request.yaml> --records <records> --format json
python3 -m swdb freeze-protocol <control-request.yaml> --records <records> --format json
python3 -m swdb get <returned-protocol-id> --chain --records <records> --format json
```

## Execute, collect and compare

Invoke `scripts/bfs_simulator_series.py` four times: baseline and candidate for
each frozen policy. Supply actual `--id`, `--candidate`, `--workload`,
`--build-evaluation`, four-field `--configuration` JSON, `--protocol`,
`--protocol-role`, dedicated empty `--runs-dir`, `--records`, and owned `--lane`.
All four use `--author-binary`; only MAA uses `--accelerated`. Pass the actual
`--diagnostic-build bfs-author-scalar-compile-20260925-a1.diagnostic.build` or
`--diagnostic-build bfs-author-maa-compile-20260925-a1.diagnostic.build` selected
for that frozen collector identity. This reuses the exact audited diagnostic
artifact; later collector changes cannot silently replace it. Both reused and
newly compiled diagnostics must match the frozen selected regions and collector
before any primary execution. Execution still rehashes the source and binary.
The driver preserves
two separate source/repetition replays, independent diagnostics, public profiles,
sealed packages and a public aggregate. It cannot reuse one MAA evaluation under
two different frozen protocol IDs; use fresh MAA replays for the second policy.

Explicit author bounds are `--checkpoint-seconds 3600 --run-seconds 14400
--memory-gib 48 --storage-gib 15`, with a reviewed `--verification-ticks` allowance.
Diagnostic executions currently have their separate bounded 600-second maximum;
failure to finish is retained and leaves regional evidence incomplete. Do not
silently raise this or substitute primary wall time. The outer operator must share
one 24-hour/60GiB batch budget across the four series, subtracting already spent
time/storage before each invocation and supervising the remaining batch deadline.
Each series' own `--total-seconds`/`--batch-storage-gib` applies only to its dedicated
child folder, with 30 seconds reserved inside the elapsed budget for process
cleanup. Storage/reserve checks continue while public subprocesses run; an
interruption preserves stage output hashes and reaps owned child groups. Preserve 30GiB raw and 10GiB build reserves. No automatic regression
retry or unbounded search is authorized by this recipe.

For each policy, create a public `compare-evaluations` request with the returned
baseline/candidate aggregate IDs, `comparison_baseline: dx100-bfs-scalar`, and
`region_packages` mapping **every primary component evaluation ID** in both grids
to its returned sealed package ID. The primary result is the simulated ROI ratio;
each selected region reports its separate diagnostic elapsed quantity and
`gain_claim: false`. Retrieve the comparison with `get --chain` in a fresh process,
verify every primary and diagnostic check, accelerator-use evidence, package/raw
identity, observed config and timing scope, and retain all rejected/failed records.
Update the coverage report with actual comparison IDs only after these checks.

The two contract gaps found while preparing this recipe were reproduced using
explicit synthetic records: ignored simulator/build hashes and missing aggregated
region evidence. Their regression tests establish API enforcement only. They do
not establish scale22 feasibility, author reproduction, matched-control performance,
generated-candidate acceptance, or any gain.

For later generated candidates, compiler-discovered region IDs do not exist before
proposal materialization. Discover the actual candidate before freezing its region
correspondence and before collecting the timing to be compared. If an earlier
protocol already exists, publish a superseding pre-execution protocol and retain
the earlier version. Do not invent future IDs, omit required selected-region
evidence, or attach a post-timing correspondence to an earlier freeze.
