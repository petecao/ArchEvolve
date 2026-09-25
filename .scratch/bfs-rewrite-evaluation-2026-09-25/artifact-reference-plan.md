# BFS artifact reference and matched controls

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)

This is the pre-execution plan for Ticket 16. It is independent of the smaller
candidate-workload pilot. Source facts below were inspected at DX100 revision
`e4fc4afdf894f295442cef3604667a469fab8e62`; none is a claim that reproduction has
completed. Publish concrete content-addressed workload/protocol records before the
measured comparisons, after exact source/binary/model identities are available.

## Artifact facts and retained differences

The README's main pipeline invokes `scripts/benchmark.py`, which dispatches
`scripts/sim.py`. Use that runner as the configuration authority. The older
`configs/run_gem5_all.py` differs in LLC associativity and is not the README's main
artifact pipeline. `scripts/sim.py` selects BFS scale22 and invokes scalar `bfs`
or accelerated `bfs_maa` with `-f serialized_graph_22.sg -l -n 1`.
`benchmarks/gapbs/run_g_gen.sh` generates it with `converter -u 22 -b ...`;
`command_line.h` defaults to degree16, and the pinned generator's seed is27491095.
There is no `-s` symmetrization flag. The actual realized dimensions, directedness,
deduplication, graph bytes and loaded adjacency must still be measured and recorded.

The main runner uses four X86O3CPU cores at3.2GHz, 16GB guest memory, Ramulator2
with its pinned example configuration, two memory channels, 64-byte lines,
32KiB/eight-way L1 data and instruction caches, and 256KiB/four-way L2 caches.
The BASE LLC is10MiB/20-way; the MAA LLC is8MiB/16-way. Preserve every instantiated
cache, prefetch, MSHR, write-buffer, bus, memory, CPU, clock, accelerator and model
setting from the actual gem5 configuration, not just this summary. The MAA build
uses four cores and maximum tile size16384; dynamic smaller tile sizes and scalar
tails are source behavior and require observed execution evidence.

The author's ROI starts after parent/queue/bitmap initialization and ends after
parent normalization. Name this traversal-and-normalization scope explicitly.
It is different from the native evaluator's complete-BFS-call ROI. Preserve the
authors' ROI for this reference pair and use the same semantic scope for its
matched controls; never divide it by native or complete-call timing.

## Inputs, identities, and correctness

Generate the uniform scale22 graph once using the pinned converter under a lane,
with compile180s, generation900s, source selection300s, and registration2400s
budgets, four host threads, and 48GiB address-space bound. Keep SG32 for DX100.
A deterministic SG32-to-SG64 width conversion preserves adjacency bytes and
widened counts/offsets for upstream consumers; register both through exact bounded
streaming CSR validation. The canonical hash must agree across representations.
Keep the converter binary/source hashes and all generator stdout/stderr.

Determine the original first traversal source using the pinned `SourcePicker`
implementation on that exact graph before freezing the protocol. Retain its
nonzero-degree selection evidence. The measured author command may retain default
selection; its reported source must equal the frozen ID. Do not substitute a
convenient source or a smaller graph and call it the prescribed artifact case.

Every primary result needs structural verification of the exact timed parent
array. Seal the completed ROI stats before continuing the same simulator and guest
binary to the protected verifier. Retain failure even if the process exits zero,
and reject absent/duplicate/wrong-source verifier output. Candidate-source
protection and output checking are separate from trusting a printed PASS line.
An observed MAA completion counter/trace must prove accelerator use; `td_maa`
labels are insufficient because that routine can execute scalar fallback.

## Bounded comparisons

Run two independent replays for each of these fixed configurations, on the same
ordered source and exact graph:

| Pair | Scalar configuration | Authors' MAA configuration | Attribution |
|---|---|---|---|
| Artifact | BASE10MiB/20-way | MAA8MiB/16-way | Authors' joint software/hardware/configuration pair |
| Matched control | BASE8MiB/16-way | MAA8MiB/16-way | Matched CPU/cache/memory; explicit software and accelerator differences |

The MAA evidence can serve both pairs only when every shared identity and bound
protocol setting matches. Otherwise run a fresh comparison; do not relabel an
incompatible earlier trial. Baseline/reference neutral or regressing results are
valid outcomes and cannot trigger a search for a favorable result.

At most one checkpoint attempt and one diagnosed corrective retry per binary;
at most two measured replays per configuration plus one diagnosed failed-run
retry. Each checkpoint has a3600s host wall limit. Each restored traversal has
an14400s host wall limit and an independently recorded post-ROI verification tick
allowance. Bound each simulator process group to48GiB sampled RSS and15GiB raw
output. The reference/control batch has a24-hour elapsed cap and60GiB total raw
storage cap. Stop if the raw volume has less than30GiB free or source/build volume
less than10GiB free; recheck before every dispatch. These are execution budgets,
not predictions of how long BFS will take.

Use the two-lane host procedure, never a third measurement process. Record exact
leases, CPU/memory binding, host load, other users' activity, start/end wall time,
model/helper/checkout SHA, commands, actual guest configs, stats hashes, checkpoint
and binary identities. Raw outputs remain on mbit10 and only bounded metadata
returns through Git.

Freeze zero warmups, two actual simulator replays, per-source median ratios,
clock/tick conversion, selected-region correspondence and attribution scope,
diagnostic instrumentation treatment, and explicit profitability thresholds before
comparison dispatch. Report missing/failed/incompatible data as such, never as
speedup1. Region results and memory counts retain their own quantities and scope;
host wall cost cannot substitute for simulated BFS time. Positive gain is not a
Ticket16 acceptance requirement.

A budget expiry leaves the relevant case and Ticket16 incomplete with retained
reason and evidence. It cannot remove the prescribed case from Ticket21, count
reference code as a generated rewrite, or establish either source's candidate
accelerator minimum. Independent implementation work continues.
