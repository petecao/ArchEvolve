# Finite DX100 full/tail/competing-update correctness case

Navigation updated: 2026-09-28 (Eastern Time).

Created: 2026-09-26 (Eastern Time).
Updated: 2026-09-26 (Eastern Time).
Status: preparation and independent review; no graph preparation or simulator
execution on mbit10 has occurred under this plan.

Ticket 13 needs an actual accelerated structural check, including full and tail
tiles and competing parent updates. The tiny uniform64 proof selects scalar
fallback. This separate correctness-only case is chosen from the pinned author
source before observing its execution. It cannot replace either required graph
family, the uniform22 artifact reference, a calibration sample, or a gain.

## Source-grounded graph choice

The source is `benchmarks/gapbs/src/bfs.cc`, SHA-256
`6835fc42dfadcb60c1c3fae543f736903977f135fd7c55cd495c0e481b572465`,
retained in the unchanged author source snapshot. `TDStepMAA` chooses a
1,024-frontier chunk per core when the remaining frontier is strictly greater
than `NUM_CORES * 1024` and no larger branch applies. With four guest cores,
4,097 frontier vertices select four such chunks and one scalar remainder.
The inner range operation expands adjacency into the physical 16,384-element
tile; full range output does not require a 16,384-vertex frontier chunk.

The deterministic undirected simple graph has:

- Source vertex 0 and first-level vertices 1 through 4,097.
- One private successor for each first-level vertex, numbered 4,098–8,194.
- Sixteen shared successors, 8,195–8,210, each adjacent to every first-level vertex.
- One isolated vertex, 8,211.

Each first-level vertex has degree 18: the source, its private successor, and
the sixteen shared successors. Expected BFS level sizes are 1, 4,097, 4,113,
with one unreachable vertex. There are **8,212 vertices, 73,746 undirected edges,
and 147,492 directed adjacency entries**. No parallel edge or self-loop is used.

For a 1,024-vertex chunk, 18,432 adjacency entries motivate one full range tile
of 16,384 and a tail of 2,048. Shared successors supply many valid predecessor
choices at the same preceding depth, motivating competing updates. The actual
queue order and instruction trace remain execution-dependent. These arithmetic
facts are preparation evidence only; no counter or coverage result is inferred.
In particular, the collector must observe distinct parent-store values at the
same physical word from instructions bound to the returned parent array.

## Generator and check boundary

[The fixed generator](../../scripts/bfs_dx100_coverage_graph.py) writes one new
SG32 artifact and a manifest. It reopens the bytes through the existing SG
parser and preserves the canonical adjacency digest. It never overwrites an
existing directory. Actual invocation requires mbit10, a verified socket lane,
and a fresh path under the authorized raw-output volumes. Graph generation is
not a simulation or a performance measurement.

Local contract tests independently traverse the serialized graph, check the
exact BFS levels and isolated vertex, verify symmetric simple adjacency and
shared predecessor choices, exercise the public generator entry, and retain
the non-execution/non-coverage flags. Their fixture graph bytes are not an
mbit10 run artifact or acceptance evidence.

The intended timed artifact is a fresh public compile of the unchanged
`bfs-author-maa-compile-20260925-a1.candidate` using the trusted
`dx100.complete_call.v2` wrapper, four guest cores and 16,384-element MAA tiles.
This gives the returned-parent binding, original-adjacency structural oracle,
and complete-call ROI. It is distinct from the original author's traversal-only
primary binary. No original-ROI reference timing is claimed by this treatment.
Use `verification.coverage: true` and the v2 post-seal completion witness.

## Prospective resource envelope

Before dispatch, record a new case ID, exact request, graph/build/runtime hashes,
absolute latest start/end, and terminal prerequisite receipts. The corrected
tiny a3 witness must first pass its actual independent audit. The paired native
pilot and provider batch must have terminated; no heavy simulation overlaps
native measurement. All three leases, current helper, owners, capacity, and
disk gates remain mandatory. Use one named tmux session and `socket_lane.sh`.

The proposed single-attempt envelope is 3,600 seconds outside, with 30 seconds
reserved for cleanup; compile at most 240 seconds; checkpoint at most 300;
simulation at most 2,700; and public execution at most 3,100. Generation and
registration have a combined 120-second cap. The wrapper enforces one
cumulative deadline, so individual caps cannot extend the total. Sampled RSS
is capped at 48 GiB and raw output at 4 GiB; require at least 52 GiB estimated
available memory on the chosen node, 64 GiB global, 10 GiB build-volume free,
and 30 GiB raw-volume free. These are proposed caps, not observed feasibility.

No automatic retry, tile-size reduction, graph alteration, new optimization,
or trace-based tuning is authorized by this plan. A timeout, missing coverage,
failed check or resource limit is retained as the finite attempt's outcome.
No simulator dispatch is ready until the missing exact runtime/request and
absolute schedule are prospectively recorded and independently reviewed.

## Admission

Reopen the actual sealed interval and protected completion witness. Require
structural PASS against original adjacency, explicit accelerator execution,
observed full and tail range tiles, and observed competing parent updates.
Preserve the exact graph/source/binary/configuration/ROI identities, all raw
artifact references, correctness outside the ROI, and the finite-case limit.
Fresh public retrieval must reconstruct the outcome. Success resolves only the
specified correctness coverage; it supplies no frozen comparison or gain.


## Preparation review — 2026-09-26

Three local topology/format/public-entry/no-overwrite tests passed in 1.47
seconds. An independent reviewer reopened the exact pinned author source,
checked the strict four-core branch and range expansion, and checked the pinned
SG reader's field layout against the generated bytes. It found no preparation
blocker. Shared parent destinations motivate the intended test; their actual
updates remain unobserved. No mbit10 graph or simulated result is included in
this review.
