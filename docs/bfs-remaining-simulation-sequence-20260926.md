# Remaining BFS simulator calibration and reference sequence

Created: 2026-09-26 (Eastern Time).
Updated: 2026-09-26 (Eastern Time).
Status: local, read-only planning audit; no new dispatch, protocol, or measurement.

The practical sequence is: independently accept the fresh tiny a3 witness; run
and audit the separately planned accelerated correctness case; then admit a new
finite simulator-calibration plan and the independent author-reference batch.
Neither small case substitutes for performance-workload evidence. This document
does not start a budget clock or select an execution window.

## Boundaries that remain in force

- The original pilot expired at **2026-09-26 05:56:38 ET**. Its two serial native
  blocks, high spreads, false-positive unchanged-code control, and simulator
  failures remain evidence. No command below runs under that expired window.
- Witness a1 remains failed; a2 expired unused. The selected a3 window remains
  latest launch **15:20 ET**, hard end **15:40 ET**, one attempt and unchanged
  caps. It waits for both scheduled batches' terminal cleanup barriers. A
  read-only a1 reparse does not become an execution or a passed evaluation.
- The native paired study has its own fixed four cells, 240 observations,
  15:00 ET end, 0.10 spread gate, both-direction A/A veto, and unchanged
  1.05/95%/2,000-resample/seed-20260925 policy. This audit does not assume it
  succeeds or authorize more native samples.
- T14's complete collection package retains **unverified** primary/diagnostic
  correctness and `missing_observation` outcomes. It establishes actual
  collection, not a qualified timing or simulator-calibration input.

These boundaries follow [T15](../.scratch/bfs-rewrite-evaluation-2026-09-25/issues/15-baseline-pilot-and-protocol-freeze.md),
[the a3 plan](bfs-dx100-witness-continuation-20260926.md),
[the paired plan](bfs-native-paired-pilot-20260926.md), and the retained
`bfs-dx100-profile-20260926-a1.{primary,diagnostic}` records. No real frozen
simulator protocol was present in the local catalog inspected for this audit.
Remote artifact availability must be freshly verified on mbit10.

## Reuse and fresh-build decisions

| Artifact | Permitted reuse and limit |
|---|---|
| Model build `bfs-dx100-build-20260925-a2` | Reuse after rehashing its complete receipt, pinned model, simulator, library, and configuration. This build ID is unrelated to expired witness a2. No model rebuild is justified by this audit. |
| Original author `bfs` / `bfs_maa` | Reuse scalar SHA `70301ad2e587c2dd55a730da5e0135337cb6b46ddd72999a843f86fd4b070dd1` and MAA SHA `6abd8190e4e1daf7c670c214dd0323393e3d29a9a26a3487c21f66e5ef194a5d`. Their adapter stays `dx100.author_artifact.v1`; fresh execution uses the v2 completion verifier. Verifier version does not rename or rebuild these original binaries. |
| Unchanged source candidates | Reuse `bfs-author-scalar-compile-20260925-a1.candidate`, `bfs-author-maa-compile-20260925-a1.candidate`, and the existing upstream/DX100 scalar baseline candidates only after snapshot/manifests, protections, implementation, and function agree. No artificial rewrite is needed. |
| Author traversal diagnostics | The retained `bfs-author-{scalar,maa}-compile-20260925-a1.diagnostic.build` artifacts use `dx100.author_roi_diagnostic.v1`; they may be reused with their exact source/ROI/model and frozen collector identities. Fresh v2-verifier executions are required. Their current compilation records are not correctness evidence. |
| Existing complete-call builds | `bfs-dx100-compile-20260925-a1.{primary,diagnostic}.build` and `bfs-upstream-compile-20260925-a1.{primary,diagnostic}.build` use `dx100.complete_call.v1`. They cannot qualify v2 complete-call evidence. Compile fresh primary and diagnostic `dx100.complete_call.v2` artifacts when that treatment is needed; retain old builds unchanged. |
| Graph registrations and bytes | Reuse exact registered SG32/SG64 representations after immutable-record and adjacency/hash checks; no regeneration. Use corrected version-2 scale-18 records below, retaining version 1 as history. |
| Checkpoints | Reuse only an exact manifest-bound source/binary/graph/configuration/ROI checkpoint. A new v2 complete-call binary needs a new checkpoint. The tiny a4/a3 checkpoint cannot serve scale 18, the coverage graph, or scale 22. The series driver restores the same checkpoint for repetition 1 after repetition 0, with primary and diagnostic checkpoints separate. |

The model revision is `e4fc4afdf894f295442cef3604667a469fab8e62`, target
`dx100-e4fc4af-4c`, simulator SHA
`f4038c88318ee09085b6c07f163094a07a31a256f21b652d4f3cfa046feb1f6b`.
The concrete reuse checks are in
[`validate_diagnostic_build` and `validate_selection`](../scripts/bfs_simulator_series.py).
The v2 complete-call requirement is explicit in
[`validate_completed_witness`](../swdb/dx100_witness.py): the protected wrapper
must verify against original adjacency, and its adapter must be
`dx100.complete_call.v2`. Author traversal remains a distinct treatment.

## T15: minimum shared simulator gate

The current native publisher's `accelerator_gate` requires the **same workloads
as the native packages**, not a smaller graph with similar topology:

| Family | Registered workload | Ordered sources |
|---|---|---|
| Uniform random, scale 18 | `bfs-20260925-uniform18.cd2169a5c421baf7` | `[0, 1234, 7777]` |
| Kronecker, scale 18 | `bfs-20260925-kronecker18.48de8267ac2098d5` | `[0, 1234, 7777]` |

Use unchanged `dx100-bfs-maa-reference` / `DOBFSMAA`, four guest cores,
MAA mode, and a prospectively fixed full configuration. The direct reusable path
uses `--author-binary --accelerated --verifier dx100.bfs.verifier.v2`, the
original `bfs.dx100.traversal.v1` primary ROI, and the retained author diagnostic
build. A complete-call author-reference treatment is also supported but requires
fresh v2 primary/diagnostic builds; choosing it changes the treatment and must
precede collection. Do not combine those ROIs in one replay signature.

The reader minimum is **12 distinct primary replays**: two per source per family.
The existing public series supplies **12 separately executed diagnostics,
12 region profiles, and 12 complete sealed packages** alongside them. Each
primary must have real, passed exact timed-binary correctness, positive observed
MAA execution, finite simulated ROI timing, and distinct output identity.
Both replays per source must use the same primary binary/build/configuration/
instrumentation. Compare their actual spread to the fixed supplied ceiling;
guest `-n` counts are not repetitions.

Each graph must also show full tiles, tail tiles, and competing parent updates.
For unchanged author-traversal calibration only, the reader permits a separately
passed v2 diagnostic to support a case absent from the primary trace. It must
match the primary candidate, source, workload, source/repetition cell, target,
model and ROI, and have its own checked binary, sealed statistics, trace and
package binding. It cannot supply primary accelerator execution or correctness,
and its flags are not copied into primary evidence. The proposed 8,212-vertex
coverage graph cannot supply this graph-specific gate.

This is the minimum for the existing **shared gate**, not all of T15. Its
`packet` reader also requires usable automatically discovered function and loop
timing and actual memory observations; inclusive simulated elapsed scopes and
whole-ROI memory counters remain explicitly scoped. Reuse neither T14's tiny
unverified package nor native thread-CPU timings for these quantities.

After actual packages and the entire paired study qualify, use
`scripts/bfs_freeze_pilot.py prepare` separately for each unchanged native
implementation, review the retained historical controls and new evidence, then
`publish`. The publisher only freezes **native** policies. Source-specific
controlled-simulator policies for later DX100/upstream candidates still need
their own complete-call v2 baseline/build/collector identities and pre-timing
region correspondence through public `freeze-protocol`. The paired native
bootstrap policy is not a simulator collection policy. No extra arbitrary
simulator sweep or per-source baseline grid is added by this blueprint.

Sources: [`accelerator_gate`, `supporting_case_evidence`, and `packet`](../scripts/bfs_freeze_pilot.py),
[publication contract](bfs-pilot-freeze.md), and
[specification D10–D13](../.scratch/bfs-rewrite-evaluation-2026-09-25/spec.md).

## T16: two independent frozen reference comparisons

T16 is independent of T15's acceptance. It retains the prescribed
`bfs-20260925-uniform22.f23b09bb0c0601b5`, source **2,796,003**, 4,194,304 vertices,
134,217,158 adjacency entries, and the actual pinned SourcePicker evidence.
Scale 18 or the coverage graph cannot replace it. Keep the original author
`bfs.dx100.traversal.v1` scope: traversal, queue advancement, and parent
normalization; initialization outside that author ROI remains outside it.

| Frozen policy | Scalar role | MAA role |
|---|---|---|
| `artifact_reference` | BASE, LLC 10 MiB / 20-way | MAA, LLC 8 MiB / 16-way |
| `controlled_simulator` | BASE, LLC 8 MiB / 16-way | MAA, LLC 8 MiB / 16-way |

Both retain four cores, tile capacity 16,384, and the full actual CPU/cache/
memory/clock configuration, not only this abbreviated table. Rehash and review
the existing prospective
[artifact request](../.scratch/bfs-rewrite-evaluation-2026-09-25/requests/author-reference-freeze-v1.yaml)
and [control request](../.scratch/bfs-rewrite-evaluation-2026-09-25/requests/author-matched-control-freeze-v1.yaml).
Neither is already frozen. They bind the original source/binaries, simulator,
current v2 parser/driver/observer, selected diagnostic regions and collector.
Retain two replays, zero warmups, 0.10 spread, 1.05 floor, 95% interval,
2,000 resamples and seed 20260925. Their per-replay MAA requirement is
`executed`; do not claim their empty generic `required_cases` fulfills T13's
additional case coverage.

Freeze both policies before measured comparisons. The current series path runs
four role/policy series: **8 fresh primary executions, 8 diagnostic executions,
8 profiles/packages, 4 aggregates, and 2 comparisons**. Supply the retained
scalar/MAA diagnostics through `--diagnostic-build`; do not silently rebuild a
different collector after freezing. Despite identical MAA configuration, the
two policy IDs require separately bound fresh primary replays; the current
recipe cannot relabel one evaluation under both policies. Every comparison's
`region_packages` maps every primary component to its own sealed package.

Report simulated ROI ratios separately from accumulated inclusive diagnostic
region elapsed times and whole-ROI memory observations. Preserve diagnostic
cost/treatment differences. A neutral or regressing comparison is retained;
there is no requirement to keep running until it improves. Neither author pair
qualifies a generated rewrite or either source's candidate accelerator minimum.
See [T16](../.scratch/bfs-rewrite-evaluation-2026-09-25/issues/16-artifact-reference-and-controls.md)
and the [exact author recipe](bfs-artifact-freeze-recipe-20260925.md).

## Prospective decisions still needed before any larger dispatch

1. **Complete the preceding gates.** Audit a3's new witness and the separate
   coverage execution. Neither authorizes a larger replay, a retry, or a4.
   Preserve failures and all old records. T15 publication also waits for actual
   paired admission; T16 does not inherit that dependency.
2. **Choose an explicit new T15 simulator window.** Record a new plan ID,
   earliest/latest launch and absolute end, shared elapsed/storage ledger,
   exact two-family grid, treatment, runtime hashes and post-ROI tick limit.
   The old 12-hour/40-GiB pilot budget is expired, not replenished. Its existing
   per-phase ceilings provide a conservative starting proposal: 3,600 seconds
   each for checkpoint/restored primary, 600 total for each diagnostic,
   48-GiB sampled RSS, 10-GiB per execution. A fresh finite batch cap still
   needs a prospective decision; individual ceilings do not prove the complete
   grid fits it. Scale 16 would require a retained scale-18 cost failure and its
   own compatible native controls; it is not a shortcut around the present gate.
3. **Instantiate T16's clock and common budget.** Its existing plan caps the
   entire four-series batch at 24 elapsed hours / 60 GiB, with checkpoint
   3,600 seconds, primary restoration 14,400 seconds, diagnostic 600 seconds,
   48-GiB sampled RSS and 15-GiB per execution. Set the absolute start/end and
   account for any already charged preparation; do not grant each series a
   fresh 24 hours or 60 GiB. Preserve its explicit `10^14` verification-tick
   ceiling. A diagnosed retry needs its own retained authorization within that
   batch; `bfs_simulator_series.py` itself performs no retries.
4. **Retain one common supervisor per selected batch.** The series enforces
   `--total-seconds` and storage only for its dedicated child folder, reserves
   30 seconds for cleanup, and stops on an unsuccessful sample. A coordinator
   must subtract all prior series' time/storage and enforce the batch's absolute
   deadline externally. The native freeze helper publishes native policies;
   simulated policies use public `freeze-protocol`. Prepare exact commands/IDs
   and a bounded wrapper or equivalent retained multi-series supervision before
   launch; no new evaluator backend is required.
5. **Recheck physical feasibility and retrieval.** Use current socket helper,
   all three lease/owner checks, fresh lane/capacity observations, at least
   52 GiB estimated node availability / 64 GiB global, and 30-GiB raw / 10-GiB
   build reserves. No heavy simulation overlaps native measurement. Do not
   infer safe parallel 48-GiB jobs from two free leases. Rehash all artifacts on
   mbit10, retain actual configs, sample bounds and stage costs, and finish with
   fresh public retrieval plus raw witness/profile audits. Metadata visible on
   the Mac cannot establish current remote hashes or resource availability.

The current diagnostic ceiling is a concrete feasibility risk, not a reason to
raise it silently: the series splits its 600 seconds into 300 for checkpoint and
270 for restored execution, reserving 30. A failure on a larger graph leaves the
package and relevant ticket incomplete. Any future budget or treatment change
requires a separately recorded prospective decision before fresh execution.
