# Finite DX100 correctness and simulator calibration sequence

Navigation updated: 2026-09-28 (Eastern Time).

Prepared: 2026-09-26 (Eastern Time).

This is dependent preparation for Tickets 13 and 15, using revision 2 of
[the pilot plan](../../.scratch/bfs-rewrite-evaluation-2026-09-25/pilot-plan.md).
It authorizes no dispatch, freeze, metadata export, or acceptance. All IDs below
marked **planned** are prospective names, not claims that records exist. The
original absolute pilot deadline remains **2026-09-26 05:56:38 ET**, including
engineering and idle time. A partial grid at that deadline remains incomplete.

## Fixed inputs

Use the existing registered representations, without regeneration or source
replacement. All four workloads use ordered sources `[0, 1234, 7777]`, degree
16, seed 27491095, and the pinned generator's effective symmetrization. They are
undirected; the edge counts below are directed adjacency entries. Scale-18 IDs
are the corrected version-2 registrations.

| Purpose | Registered workload | Vertices | Adjacency entries | Isolates |
| --- | --- | ---: | ---: | ---: |
| Coverage, uniform | `bfs-20260925-uniform14.9d0116c0ee015aec` | 16384 | 523720 | 0 |
| Coverage, Kronecker | `bfs-20260925-kronecker14.d03827828666f7dd` | 16381 | 425860 | 3828 |
| Preferred calibration, uniform | `bfs-20260925-uniform18.cd2169a5c421baf7` | 262144 | 8388040 | 0 |
| Preferred calibration, Kronecker | `bfs-20260925-kronecker18.48de8267ac2098d5` | 262143 | 7610898 | 88159 |

Retrieve each immutable workload with public `get --chain --format json` and
resolve the `dx100-gapbs` SG32 representation. The record contains its exact
byte and loaded-adjacency hashes. Existing paths end in `graph.sg32`; the public
adapter must retain the original reference and its verified `.sg` loader alias.
A filename alone does not prove equivalent input.

The actual model-build record is `bfs-dx100-build-20260925-a2`, at pinned model
revision `e4fc4afdf894f295442cef3604667a469fab8e62`. Its model root is
`/data1/yanruj/DX100-bfs-e4fc4af`. Revalidate its receipt and dynamic dependency
identities on the producing host before dispatch.

| Artifact | Existing identity |
| --- | --- |
| Simulator `build/X86/gem5.opt` | `f4038c88318ee09085b6c07f163094a07a31a256f21b652d4f3cfa046feb1f6b` |
| Author `benchmarks/gapbs/bfs_maa` | `6abd8190e4e1daf7c670c214dd0323393e3d29a9a26a3487c21f66e5ef194a5d` |
| `libramulator.so` | `46b5dbd87a77845ebadd1854e990d8e5c04c41253ad76315a766d61b77ca43dd` |
| Unchanged author candidate | `bfs-author-maa-compile-20260925-a1.candidate` |
| Candidate source manifest | `d5ac642dfe1a2ba5ef548f86c5c269ef54164b55985badc55872288f41504e9d` |
| Existing diagnostic compile | `bfs-author-maa-compile-20260925-a1.diagnostic.build` |
| Diagnostic guest binary | `c0d2efb85cd1ec490ce38c3d8d69dc6d470bedd590e2189bd62cfd676d490ec5` |

The diagnostic compilation selects `DOBFSMAA`, g++-13, and
`-std=c++11 -O3 -Wall -g3 -fopenmp -DGEM5 -DNUM_CORES=4 -DTILE_SIZE=16384 -DMAA`.
It retains a separate source-scope wrapper and binary. Primary author execution
uses the unchanged author binary. Both declare `bfs.dx100.traversal.v1`; neither
supplies complete-call candidate performance evidence.

## Order and immutable attempt names

1. Finish the separately reviewed `bfs-dx100-witness-20260926-a1` tiny author
   v2 proof. Require a sealed exact ROI, protected author PASS followed by
   benchmark completion, a separate simulator-origin `exit_group(0)`/zero
   return witness, clean bounded host execution, and fresh raw-aware retrieval.
   Its driver, parser, and host-memory observer must use retained runtime copies
   whose hashes match `instrumentation.verifier_runtime`. Preserve actual
   `normal_exit_observed: false` when applicable. Tiny scalar fallback cannot
   establish accelerated correctness or choose the shared performance size.
2. Exercise unchanged author MAA at scale 14, uniform then Kronecker. Planned
   series prefixes are `bfs-sim-cal-20260926-maa14-u-a1` and
   `bfs-sim-cal-20260926-maa14-k-a1`. Within each family the order is
   source position 0, 1, 2, each with repetitions 0 and 1. A cell prefix is
   `<series>.s<position>.r<repetition>`; public execution IDs end in
   `.primary.evaluation` and `.diagnostic.evaluation`, followed by `.profile`
   and a content-addressed package from the public assembler. Retain every
   attempted cell, including isolates, fallback, failures, and timeouts.
3. After the scale-14 correctness/coverage and actual cost gate, apply the same
   finite grid at preferred scale 18. Planned prefixes are
   `bfs-sim-cal-20260926-maa18-u-a1` and `bfs-sim-cal-20260926-maa18-k-a1`.
   Scale 16 is permitted only after a retained scale-18 resource-cost failure;
   absent coverage is not permission to sweep sizes or replace sources.
4. Only after shared-size feasibility is established, select compatible
   already completed native baseline packages and perform any still-needed
   unchanged scalar/upstream complete-call simulator calibration. Do not rerun
   every baseline before the accelerator size gate. A native repeatability
   failure remains a separate freeze blocker. Artifact-reference scale 22 and
   BASE/MAA controls remain separate Ticket-16 obligations.

The public series client runs the entire six-cell family and stops on a failed
cell. It has no resume or first-cell-only option. If the coordinator instead
dispatches a bounded first cell through `dx100-execute`, continue the remaining
explicit manifest cells through the public API; do not launch a whole series
that repeats that completed cell. One diagnosed distinct rerun is the pilot
limit, not an automatic failure retry.

## Request and resource treatment

Every primary and diagnostic request carries its own explicit `protocol_trial`
with the registered source position and repetition, even before a protocol is
frozen. Diagnostic collection must preserve that execution's actual cell and
require equality with the primary. The calibration reader rejects missing,
duplicated, Boolean, or mismatched cell coordinates. Implementations must not
infer a diagnostic cell from a primary label.

Use exactly `{"mode":"MAA","l3_size_mb":8,"l3_assoc":16,"tile_elements":16384}`,
four guest cores, the existing modeled memory/clock configuration, and checker
`dx100.bfs.verifier.v2`. Set `verification.coverage: true`,
`verification.post_roi_trace: SyscallBase`, and explicitly bound continuation
to `10000000000` ticks in chunks no larger than `1000000000`. Actual ROI ticks,
`simFreq`, and observed clock period remain the conversion evidence. Host wall
time is resource cost only.

For `scripts/bfs_simulator_series.py`, supply `--author-binary --accelerated`,
the candidate/model/workload IDs above, the existing `--diagnostic-build`,
`--verifier dx100.bfs.verifier.v2 --verification-ticks 10000000000`,
`--memory-gib 48 --checkpoint-seconds 3600 --run-seconds 3600`,
`--diagnostic-seconds 600 --storage-gib 10 --batch-storage-gib 40`.
Choose `--total-seconds` from the remaining absolute deadline with cleanup
reserve, never the generic client default. The two families together retain
three sources and two distinct replay processes each: 12 primaries plus 12
separate diagnostics per scale. Checkpoints may be reused only between the two
replays of the exact same source, binary, and configuration. Primary and
diagnostic checkpoints remain distinct.

The coordinator checks both socket leases, legacy lease, current jobs,
affinity, free space, and at least 52 GiB node / 64 GiB global available memory
before starting a 48 GiB request. At most two owned lanes may be used, but the
memory check can require serial execution. Keep raw pilot output at most
40 GiB combined; stop below the existing 30 GiB raw / 10 GiB source-build
reserves. No memory ratchet, model patch, graph regeneration, or deadline reset
is part of this plan.

## Separate diagnostic case evidence

Every primary used for calibration must independently be complete, structurally
passed, and observed accelerated: positive `system.maa.numInst` plus completed
S/I/R/A trace events within its sealed ROI. Supporting diagnostics cannot repair
a primary fallback, failed verifier, missing runtime witness, or missing replay.

Full and tail observations require positive RangeFuser output-tile counts for
size 16384 and size strictly between 0 and 16384, respectively. Competing parent
updates require distinct signed32 values at the same physical word from an
`INDIR_ST_VECTOR` instruction whose virtual base matches the returned parent
storage marker, inside the exact ROI. Graph topology and TD labels are not
substitutes. The unchanged author primary has no parent-storage marker; its
current parser cannot establish that case from the original binary alone.

For calibration only, `bfs_freeze_pilot.py` retains `supporting_case_evidence`
from the separately instrumented author diagnostic when a primary case is
unobserved. Each supporting diagnostic requires its own complete passed v2
check; exact source/candidate/workload/cell/configuration/ROI/model identity;
its own actual compiled binary; package/collector identity; matching verifier
runtime treatment; and available unchanged raw evidence. The reader recomputes
case observations from the sealed statistics and trace. Receipts retain actual
diagnostic evaluation/build/model IDs and digests, binary, checks, cell,
instrumentation differences, and raw validation. They never overwrite primary
coverage or supply primary timing. Cases may be accumulated across the fixed
six cells of a family; every primary still needs its own positive execution.

This implements the spec's finite applicable-case obligation without asserting
that diagnostic observations occurred in the original author primary. Future
generated-candidate qualification remains strict on each timed candidate binary;
the shared comparison and coverage code gains no diagnostic exception. Any
freeze remains nonpublishable until all actual pilot, repeatability, source,
collector, and fixed-grid gates pass. Local test fixtures establish admission
behavior only and resolve neither Ticket 13 nor Ticket 15.
