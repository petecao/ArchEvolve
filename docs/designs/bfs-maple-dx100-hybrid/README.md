# BFS hybrid: MAPLE row bounds, DX100 neighbors, CPU discovery

**October 8 design thought experiment — proposal.bfs-maple-dx100-outer-inner.v0.** This sketches one top-down BFS step on the pinned DX100 source. The `SKETCH_*` operations name desired behavior; they have no implementation or approved ABI. This is a new composition proposal, not an executable intrinsic contract or a measured speedup.

Start with the [annotated code](bfs_hybrid.pseudo.cpp). The [partition and obligations](partition.yaml) give stable region IDs for Peter/Eric/Yan-Ru to discuss. The [pipeline diagram](pipeline.svg) and [batch schedule](schedule.svg) visualize the proposed overlap.

**The proposed overlap is MAPLE fetching batch n+1's row bounds while DX100 and the CPU process batch n.** The CPU explicitly transfers MAPLE results into DX100 source tiles. No direct device-to-device path is assumed.

| Work | Actor | Data |
|---|---|---|
| Snapshot current frontier and associate vertices with batches | CPU | Immutable `F`, containing vertex IDs `u` |
| Fetch metadata for the next batch | MAPLE | `VertexOffsets[u]` and `VertexOffsets[u+1]` |
| Consume bounds and stage them into row tiles | CPU | `begin[r]`, `end[r]`, valid count; retain `F` association |
| Expand current row ranges and bulk-fetch neighbors | DX100 | `(row_slot, edge_index)` pairs and `g.out_neighbors_[edge_index]` |
| Read parent, claim discoveries, retain store and queue push | CPU | `parent[v]`, CAS success and thread-local next-frontier entries |

## Precise partition of the original code

Source: [`TDStep`, DX100 e4fc4af, bfs.cc:227–259](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/bfs.cc#L227).

| Source statement | Existing ID | Proposed responsibility |
|---|---|---|
| Line 240: `u = queue.shared[i]` | `bfs-td-frontier` | CPU snapshots the frozen frontier, partitions it and retains each `u`. |
| Line 241: `VertexOffsets[u]`, `VertexOffsets[u+1]` | `bfs-td-row-bounds` | MAPLE fetches the two bounds; CPU receives and publishes them to DX100. |
| Line 241: enumeration of `j` in the row interval | Context of `bfs-td-row-bounds` | DX100 range expansion with persistent continuation; host controls chunk submission. |
| Line 242: `v = g.out_neighbors_[j]` | `bfs-td-neighbor` | DX100 gathers neighbor IDs and retains the corresponding row ordinal. |
| Line 243: `curr_val = parent[v]` | `bfs-td-parent-read` | CPU loads current parent; there is no accelerator parent hint in this proposal. |
| Line 247: CAS | `bfs-td-parent-cas` | Original CPU comparison/update and success test. |
| Line 248: `parent[v] = u` | `bfs-td-parent-store` | Retained CPU store inside the successful branch. |
| Line 249: `lqueue.push_back(v)` | `bfs-td-queue-append` | Retained CPU queue effect, followed by the original per-worker flush. |

This differs from Peter/Yan-Ru's existing DX100 parent-gather proposal. It needs its own contract if implemented. It does not resolve that proposal's L3 assumption by renaming it; it removes accelerator parent reads from this new partition. Initialization visibility, aliases, CPU/DX tile publication and synchronization still need proof.

## MAPLE submission choice

The first sketch uses **two FIFO queues per admitted worker**, one for row starts and one for row ends. The host issues pointer fetches for `&VertexOffsets[u]` and `&VertexOffsets[u+1]` in the same vertex order. Consuming ordinal `r` from each queue supplies the two bounds for that worker's `vertices[r]`.

This uses the documented `PRODUCE_PTR`/`CONSUME` behavior as a reference. It avoids assuming independent, simultaneously rebound LIMA base contexts. A LIMA version is a later alternative: it would need separate proof of queue/configuration ownership, output counts, tails and index types. The pointer version explicitly pays CPU pointer-formation and two-command-per-vertex submission overhead.

The queues start exclusively owned, empty and quiescent, and remain bound for the whole step. `OPEN` alone does not establish that initial state. There is at most one pending metadata batch per worker's queue pair. Before submitting the next batch, all values from the preceding batch have been delivered to the CPU. FIFO identity is local to each queue, not a global ordering promise across workers.

## Bounded resources and buffer ownership

- `B`: number of frontier vertices in one metadata batch, not the number of edges.
- `T`: actual chunk limit of the bound DX100 range producer (or a proved bounded lowering), respecting tile and size bookkeeping. It is not an arbitrary sub-tile cap.
- `W`: admitted worker count. Each worker has its own two MAPLE queues, two host metadata buffers, DX100 tile/register context and CPU queue buffer.
- B, T and W must be positive for an admitted nonempty step.
- The pictured DX context needs five logical tiles (begin, end, row ordinal, edge index, neighbor) and three logical scalar registers (two continuation values and stride), before any additional adapter state. These are ownership demands, not a new area estimate or proof of physical allocation.
- `B <= min(Q_begin, Q_end, DX_row_tile_capacity)`, where queue capacities are in **decoded logical offset values**, after resolving packing and legal tail sizes. At most `2B` metadata values are outstanding per worker. Every planned batch, including tails, must be admissible.
- `T` does not have to equal `B`. A few high-degree vertices can generate many neighbor chunks.

Metadata slots progress through `FREE -> MAPLE_PENDING -> HOST_READY -> DX_IN_USE -> FREE`. While slot n is in DX/CPU use, slot n+1 identifies the future batch, whose payload remains in the MAPLE FIFOs until the host consumes it. The second host buffer does not imply MAPLE DMA writes directly into host storage.

The immutable frontier snapshot and CSR arrays remain valid throughout the step. Next-frontier insertion may write the original queue storage because neither accelerator reads that growing output buffer. The snapshot copy is additional CPU traffic and must be accounted for.

DX100 row-bound source tiles are published once per batch with the actual valid count. Continuation registers are initialized once per batch and persist across its chunks. Both range output sizes and original row association must be established before neighbor consumption. All users of source, index and result tiles must finish before those tiles are overwritten. Workers never use shared fixed `DXC_TILE0..7` identifiers.

**A design tension:** small MAPLE queues limit B and may leave DX100 tiles underfilled. The first sketch deliberately exposes that cost. Collecting several bounded metadata waves into a larger batch would require a different schedule/progress argument; it is not silently assumed here.

## Prologue, steady state and drain

1. Admit the combined deployment, all resource/width/bounds/packing requirements and batch sizes before any parent or next-frontier mutation. If admission fails, release unissued resources and run the scalar step.
2. Snapshot the current frontier, establish its visibility and partition it into disjoint worker spans.
3. Each worker submits and consumes its first metadata batch. This startup latency cannot be hidden by earlier work.
4. Submit metadata for the next batch into the now-empty queue pair. Its complete result fits without host consumption, so the CPU can work on the current DX100 batch.
5. Stage current bounds, run range/gather chunks, and perform CPU discovery effects. Continue through every row; `p < T` alone is not a termination condition.
6. Retire all current tile consumers and CPU effects, exchange metadata slots, and repeat. The final batch submits no extra lookahead request.
7. Consume all requested metadata and establish device/consumer quiescence before teardown or rebind. Queue capacity release and `CLOSE` are not universal drain fences. Flush thread-local output, join workers and establish the level boundary before the original BFS driver advances.

A device fault after effects begin ends the candidate run as incomplete. Whole-step replay over already-mutated parent/queue state is not a recovery strategy in this sketch.

## Hand trace: tail batch, long row and duplicate destinations

This is a symbolic one-step trace with **B=2 and T=2 for illustration only**. It is not a legal hardware sizing recommendation or an execution test.

```text
VertexOffsets = [0, 3, 3, 6, 6, 7, 9]
neighbors     = [2, 5, 1, 3, 4, 0, 2, 3, 4]
current F     = [2, 5, 1]       # reachable as the first frontier from root 0
parent before = [0, 0, 0, -1, -1, 0]
batch 0       = vertices [2,5], starts [3,7], ends [6,9]
batch 1       = vertices [1],   starts [3],   ends [3]
```

| DX100 chunk | Logical `(u, edge_index, v)` tuples | CPU effects in this one-worker trace |
|---|---|---|
| Batch 0 / chunk 0 | `(2,3,3)`, `(2,4,4)` | Claim vertices 3 and 4; retain stores and append each once. |
| Batch 0 / chunk 1 | `(2,5,0)`, `(5,7,3)` | Both already visited; no enqueue. |
| Batch 0 / chunk 2 | `(5,8,4)` | Already visited; no enqueue. A short chunk still requires exhaustion confirmation. |
| Batch 0 / terminal | Empty completed range | Confirms batch exhaustion and permits source reuse. |
| Batch 1 / terminal | Empty completed range | Zero-degree row; its two metadata values were still fetched and consumed. |

MAPLE supplies six logical metadata values over two batches. DX100 delivers five logical neighbor values over three nonempty chunks. These are semantic counts, not physical cache-line transactions or estimated time. Result association must remain correct if physical responses arrive out of order. Other valid thread interleavings can produce different parent choices; the expected next frontier is the set `{3,4}`, with each vertex enqueued once.

## What to compare later

| Variant | Intended work split |
|---|---|
| CPU-only | Original scalar TDStep; common graph/root/correctness oracle. |
| DX100-only | DX100 supplies row bounds and neighbors; CPU parent read/CAS/store/push. This is a separately specified CPU-parent-load variant. |
| MAPLE-only | MAPLE supplies the corresponding read operands; CPU enumerates/consumes them and retains parent effects. It needs its own bounded queue schedule. |
| Hybrid | This sketch: MAPLE bounds for n+1, CPU staging, DX100 neighbors for n, CPU parent effects. |

Use the same BFS direction, graph, root, thread policy, result oracle and accounting boundary. Include all actual setup, staging, waits, snapshot and drain costs. The paper baselines and the older parent-gather implementation are not interchangeable versions of these controls. No control variant is implemented by this document.

Potential gain is overlap of irregular metadata fetches with the current batch's neighbor processing. Potential losses include pointer submissions, CPU queue consumption and tile staging, small batches, cold-start/drain latency, shared memory contention and extra area. A stage timeline can overlap; summing every device duration as if serialized would miscount it. Copying baseline time for retained CPU code remains a prototype accounting assumption, not proof that its memory contention/runtime is unchanged.

## Review questions and evidence

Peter: confirm the source partition and the future abstract-intrinsic/IR region binding. Eric: bind the common deployment, queue packing/capacity/ownership, CPU-to-DX publication, tile consumer coverage and final quiescence. Yan-Ru: review lowered contracts and correctness checks after those bindings exist; this proposal grants no typed-library admission.

Use `BFSVerifier` plus trusted per-level frontier counts and once-enqueue checks for a future implementation, with an execution witness showing both intended offload paths ran. Identical parent arrays are not required. Counts alone do not prove tuple association or memory visibility.

Source anchors: [MAPLE paper §§3.1–3.6](https://jbalkind.github.io/docs/isca2022_maple.pdf#page=4), [DX100 pinned API](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/API/MAA_gem5.hpp), [source observations](../../../examples/bfs.source-observations.yaml), and [the hardware behavior guide](../../hardware-behavior-handoff.md). `manifest.json` records the catalog/source identity used to prepare this sketch. Existing candidate/library artifacts are untouched; the hybrid is not admitted to the hardware catalog.

[Review notes](review.md) record the source/region checks, illustrative trace and remaining implementation obligations.
