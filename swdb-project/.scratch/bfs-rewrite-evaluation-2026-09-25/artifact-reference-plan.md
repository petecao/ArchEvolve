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
artifact pipeline. `scripts/sim.py` selects BFS scale 22 and invokes scalar `bfs`
or accelerated `bfs_maa` with `-f serialized_graph_22.sg -l -n 1`.
`benchmarks/gapbs/run_g_gen.sh` generates it with `converter -u 22 -b ...`;
`command_line.h` defaults to degree 16, and the pinned generator's seed is 27491095.
There is no explicit `-s` flag, but this does **not** make the generated graph
directed: pinned `command_line.h:76–77` forces `symmetrize_ = true` whenever a
synthetic scale is supplied (`-u` or `-g`). `builder.h:332–333` then constructs an
undirected CSR graph. The first scale-18 registrations incorrectly recorded the
effective generator parameter as `parameters.symmetrize: false`. Retain those
immutable records and supersede them through public version-2 registration with
`symmetrize: true`, `explicit_symmetrize_flag: false`, and the retained generator
command. This is a metadata correction using the same graph files and hashes;
it does not authorize regeneration.
Realized dimensions, deduplication, graph bytes, directedness, and loaded adjacency
remain independently checked from the generated serialization. Uniform-18 already
realized 262144 vertices and 8388040 directed adjacency entries with `directed: false`;
this smaller observation does not substitute for generation of the prescribed scale 22.
Kronecker-18 realized 262143 vertices, 7610898 directed adjacency entries, and
88159 isolated vertices. The builder derives its vertex count from
`FindMaxNodeID(el) + 1` (`builder.h:313–321`); the synthetic path does not override
that count with `2**scale` (`builder.h:339–354`). An absent highest vertex therefore
reduces the realized range, while isolated vertices below that maximum remain.
Preserve these actual counts and all isolates in the workload identity.

The main runner uses four X86O3CPU cores at 3.2 GHz, 16GB guest memory, Ramulator2
with its pinned example configuration, two memory channels, 64-byte lines,
32KiB/eight-way L1 data and instruction caches, and 256KiB/four-way L2 caches.
The BASE LLC is 10 MiB/20-way; the MAA LLC is 8 MiB/16-way. Preserve every instantiated
cache, prefetch, MSHR, write-buffer, bus, memory, CPU, clock, accelerator and model
setting from the actual gem5 configuration, not just this summary. The MAA build
uses four cores and maximum tile size 16384; dynamic smaller tile sizes and scalar
tails are source behavior and require observed execution evidence.

The author's ROI starts after parent/queue/bitmap initialization and ends after
parent normalization. Name this traversal-and-normalization scope explicitly.
It is different from the native evaluator's complete-BFS-call ROI. Preserve the
authors' ROI for this reference pair and use the same semantic scope for its
matched controls; never divide it by native or complete-call timing.

## Inputs, identities, and correctness

Generate the uniform scale 22 graph once using the pinned converter under a lane,
with compile 180s, generation 900s, source selection 300s, and registration 2400s
budgets, four host threads, and 48GiB address-space bound. Keep SG32 for DX100.
A 3600-second outer driver ceiling, matching prior workload preparation,
reserves 30 seconds for cleanup. Individual phase budgets are ceilings within
that total. Interrupted public registration receives TERM so it can reap its
separately grouped streaming parser; the driver waits at most 20 seconds before
forcing remaining owned processes to exit. Preserve partial logs and their
hashes even when generation, compilation, or registration is interrupted.
A deterministic SG32-to-SG64 width conversion preserves adjacency bytes and
widened counts/offsets for upstream consumers; register both through exact bounded
streaming CSR validation. The canonical hash must agree across representations.
Keep the converter binary/source hashes and all generator stdout/stderr.
New generator outputs are named `graph-dx100.sg` and `graph-upstream.sg`: both
pinned Builders dispatch serialized loading by the `.sg` suffix, while the record's
`format` carries the 32-bit versus 64-bit offset width. The original SourcePicker
must load the SG32 file through that actual Builder path. Existing scale-14/18
records and bytes retain their identities; an evaluator-owned, hash-verified loader
alias supplies a compatible suffix when an older representation name needs one.

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
| Artifact | BASE 10 MiB/20-way | MAA 8 MiB/16-way | Authors' joint software/hardware/configuration pair |
| Matched control | BASE 8 MiB/16-way | MAA 8 MiB/16-way | Matched CPU/cache/memory; explicit software and accelerator differences |

The MAA evidence can serve both pairs only when every shared identity and bound
protocol setting matches. Otherwise run a fresh comparison; do not relabel an
incompatible earlier trial. Baseline/reference neutral or regressing results are
valid outcomes and cannot trigger a search for a favorable result.

At most one checkpoint attempt and one diagnosed corrective retry per binary;
at most two measured replays per configuration plus one diagnosed failed-run
retry. Each checkpoint has a 3600s host wall limit. Each restored traversal has
a 14400s host wall limit and an independently recorded post-ROI verification tick
allowance. Bound each simulator process group to 48 GiB sampled RSS and 15 GiB raw
output. The reference/control batch has a 24-hour elapsed cap and 60 GiB total raw
storage cap. Stop if the raw volume has less than 30 GiB free or source/build volume
less than 10 GiB free; recheck before every dispatch. These are execution budgets,
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
speedup 1. Region results and memory counts retain their own quantities and scope;
host wall cost cannot substitute for simulated BFS time. Positive gain is not a
Ticket 16 acceptance requirement.

A budget expiry leaves the relevant case and Ticket 16 incomplete with retained
reason and evidence. It cannot remove the prescribed case from Ticket 21, count
reference code as a generated rewrite, or establish either source's candidate
accelerator minimum. Independent implementation work continues.
