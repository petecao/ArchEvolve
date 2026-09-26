# Author BFS reference and matched-control freeze recipe

Updated: 2026-09-26 (Eastern Time)

This is a reviewable operator recipe for Ticket 16. It does not freeze a protocol,
dispatch a simulator, or claim reference acceptance. The prescribed run plan is
[artifact-reference-plan.md](../.scratch/bfs-rewrite-evaluation-2026-09-25/artifact-reference-plan.md).
The concrete version-1 request files are prepared and validated against current
records; neither has been frozen or executed. Returned protocol, replay, aggregate
and package identifiers remain unavailable until their public operations succeed.

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
| Region correspondence | Actual author diagnostic builds select the top-down step and outer frontier traversal loop, as detailed below |
| Protocol IDs and results | **Unresolved:** two independently frozen protocols and their actual replay/aggregate/package IDs |

The registered graph has 4194304 vertices, 134217158 directed adjacency entries,
undirected topology and zero isolates. Its exact hashes and source selection audit
are in [the preparation receipt](../.scratch/bfs-rewrite-evaluation-2026-09-25/observations/uniform22-preparation-a1.json)
and its public workload record. Generation and source selection are complete;
simulator feasibility and the two frozen comparisons remain pending.

A read-only mbit10 check at 23:21:18 ET rehashed the simulator, both original
author binaries, Ramulator shared library and both author diagnostic binaries.
The tracked model checkout was clean at the pinned revision. The
[configuration and hash receipt](../.scratch/bfs-rewrite-evaluation-2026-09-25/observations/author-freeze-inputs-20260925.json)
retains the full adapter configurations and helper identity. Rehash again before
dispatch; this observation does not authorize changing an active checkout. Current scale18 registrations, native pilot
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

The concrete requests are:

- [Author artifact policy](../.scratch/bfs-rewrite-evaluation-2026-09-25/requests/author-reference-freeze-v1.yaml), requested name `bfs-author-reference-20260925`.
- [Matched cache control](../.scratch/bfs-rewrite-evaluation-2026-09-25/requests/author-matched-control-freeze-v1.yaml), requested name `bfs-author-matched-control-20260925`.

Both use maximum relative spread `0.10`, bootstrap seed `20260925`, two replays,
zero warmups, minimum speedup `1.05`, and the existing 95%/2000-resample policy.
These choices precede all reference timing. The requested names are inputs, not
claims of returned protocol IDs. The canonical model-build record digest is
`13d277a961e44fe0ee254b4685126572fb06394fea455e3e1d450626cc535cea`.

The unfrozen requests now prospectively select `dx100.bfs.verifier.v2` and its
separate post-seal `SyscallBase` trace. Both roles bind the exact driver, parser,
and host-memory observer hashes in `instrumentation.verifier_runtime`; each
actual execution retains immutable copies. Their trace instrumentation also
matches the declared formatting flags and one-billion-tick chunk limit. These
edits do not change an existing protocol or promote a v1 result. A successful
bounded v2 author proof and a fresh check of these exact helper hashes are still
required before publishing. If any helper changes before freezing, explicitly
review and regenerate these prospective identities; after freezing, changed
instrumentation requires a superseding protocol.

On 2026-09-26 the unfrozen parser identity was refreshed after the generated
complete-call original-graph verification repair. The unchanged author traversal
remains its separate treatment; these requests still have no frozen or executed
status.

Reuse `bfs-author-scalar-compile-20260925-a1.diagnostic.build` for the baseline
and `bfs-author-maa-compile-20260925-a1.diagnostic.build` for the MAA role through
`--diagnostic-build`. Their binary hashes are respectively
`0b28af6ac6a32c31f38d7b28062f57b7f4db4917aae2a196db117d846d29b47a`
and `c0d2efb85cd1ec490ce38c3d8d69dc6d470bedd590e2189bd62cfd676d490ec5`.
Both retain collector `dx100.m5_rpns.source_scopes.v1`, library SHA256
`27b38bfdb37d164878767c40c8ce9538c96e801a37d2a67234bee043945de139`,
pass SHA256 `9bee90040d1c4defa96793774ca877d2d26c351303d8e1927448ba0ef0d20ffb`,
and runtime SHA256 `618d8e874eccaf2914a87462e46a1d36a42194e98f1bbfde1f91eadd3818c31d`.
A newer discovery pass is a different collector identity; do not silently rebuild
these diagnostics after freezing.

| Semantic correspondence | Scalar region | MAA region | Attribution |
|---|---|---|---|
| Top-down frontier step | `function:bfs.cc:10396:92351720b886b03a` (`TDStep`, lines227–259) | `function:bfs.cc:2157:ba2f8e639d5daef5` (`TDStepMAA`, lines66–225) | Accumulated inclusive |
| Complete frontier traversal loop | `loop:bfs.cc:14239:db5227d6bf4ba808` (`DOBFS`, lines343–352) | `loop:bfs.cc:16664:d6668c43308db1a5` (`DOBFSMAA`, lines418–431) | Accumulated inclusive |

The mapping is a pre-execution source judgment: each step consumes the current
frontier and appends newly discovered vertices; each outer loop repeats that work,
advances the queue and emits step logging until the frontier is empty. Both pinned
implementations use top-down traversal. The loop includes its nested step, so the
two quantities must not be added. Diagnostic guards report accumulated simulated
elapsed intervals, including waiting and nested work, not CPU service or primary
ROI speedup. The enclosing `DOBFS`/`DOBFSMAA` calls begin before author ROI
activation and are deliberately not selected. The OpenMP transformation loop at
line189 remains unresolved; full source coverage is not claimed.

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
All four use `--author-binary --verifier dx100.bfs.verifier.v2`; only MAA uses
`--accelerated`. Pass the actual
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
--memory-gib 48 --storage-gib 15`, with explicit `--verification-ticks 100000000000000` (the existing series default,
selected before timing). This is a raw simulated-tick ceiling; the wall-clock
execution and shared batch deadlines still apply independently.
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
