// ArchEvolve / October 8, 2026 / proposal.bfs-maple-dx100-outer-inner.v0
// DESIGN SKETCH: helper operations and descriptor types are semantic placeholders.
// SKETCH_* marks proposed boundary operations; descriptor methods are conceptual too.
// They are NOT available intrinsics, a compilable implementation, or a catalog entry.
// Source anchor: arkhadem/DX100 e4fc4af, benchmarks/gapbs/src/bfs.cc:227-259.
// See README.md and partition.yaml for ownership, evidence and unresolved bindings.
#error "Design sketch only: SKETCH_* APIs require a reviewed implementation contract."

// Per admitted worker:
//   MAPLE: exclusively bound q_begin and q_end, no rebinding during a TDStep.
//   Host: two Metadata buffers; each holds (batch_id, vertices[], begin[], end[]).
//   DX100: private handles for begin/end/row_slot/edge_index/neighbor tiles and
//          last_i/last_j/stride registers. Handles are NOT immediate scalar values.
//   CPU: one thread-local QueueBuffer for successful discoveries.
// B = frontier vertices per metadata batch; T = maximum neighbor results per chunk.
// B <= both MAPLE queues' capacity in DECODED LOGICAL OFFSET VALUES and DX row tiles.
// T is the bound range producer's actual chunk limit (or a proved bounded lowering),
// not an arbitrary sub-tile cap. It fits index arithmetic and size bookkeeping.
// No concrete B, T, worker count, queue packing, MMIO layout or address width chosen.

MetadataTicket SKETCH_issue_bounds(Worker& w, Metadata& slot, Offsets& VertexOffsets,
                                   FrontierSlice vertices, BatchID id) {
    // [H1 / CPU, added work] Own an unused host slot and bind vertex identities.
    // Previous batch on these queues was fully consumed; at most one batch pending.
    SKETCH_require(slot.state == FREE && w.metadata_ticket == NONE);
    slot.batch_id = id;
    slot.vertices = vertices; // read-only view into F, alive until this batch retires
    slot.n = vertices.size();
    SKETCH_require(slot.n <= w.q_begin.logical_capacity);
    SKETCH_require(slot.n <= w.q_end.logical_capacity);
    // This capacity restriction lets the entire future batch finish while the
    // CPU is busy with DX100. It does not require a background consumer thread.

    // [M1 / MAPLE submission] Source role: bfs-td-row-bounds, line 241.
    // Two independent FIFO streams, one value each per vertex, same vertex order.
    // Pointer requests avoid assuming two simultaneously rebound LIMA base contexts.
    for (int r = 0; r < slot.n; ++r) {
        NodeID u = slot.vertices[r];
        SKETCH_maple_produce_pointer(w.q_begin, &VertexOffsets[u]);
        SKETCH_maple_produce_pointer(w.q_end,   &VertexOffsets[u + 1]);
        // Return from each produce means request acceptance, NOT data readiness.
        // CPU computes these addresses; MAPLE owns the asynchronous memory fetch.
    }
    slot.state = MAPLE_PENDING;
    return SKETCH_ticket(id, slot.n, w.q_begin, w.q_end, slot);
}

void SKETCH_collect_bounds(Worker& w, MetadataTicket& ticket, Count directed_edges) {
    Metadata& slot = ticket.host_slot;
    SKETCH_require(ticket.batch_id == slot.batch_id);
    // [H2 / CPU consumption + transfer] Receive exactly n decoded values per FIFO.
    // Packed transport words must be decoded by a future typed adapter; one MMIO
    // consume instruction is NOT assumed to equal one logical offset value.
    for (int r = 0; r < ticket.n; ++r) {
        slot.begin[r] = SKETCH_maple_consume_offset(w.q_begin); // blocks for data
        slot.end[r]   = SKETCH_maple_consume_offset(w.q_end);   // blocks for data
        // FIFO order plus one batch per queue pair binds both bounds to vertices[r].
        SKETCH_require(0 <= slot.begin[r] && slot.begin[r] <= slot.end[r]);
        SKETCH_require(slot.end[r] <= directed_edges);
    }
    SKETCH_finish_exact_count_ticket(ticket); // all consumes delivered to this CPU
    w.metadata_ticket = NONE;
    slot.state = HOST_READY;
    // Normal queue reuse keeps bindings fixed. Queue space being freed does not
    // itself establish CPU completion, global drain, or permission to rebind/reset.
}

void SKETCH_process_neighbors(Worker& w, Metadata& current,
                              const Graph& g, Parent& parent, QueueBuffer& lqueue) {
    SKETCH_require(current.state == HOST_READY);

    // [X1 / CPU -> DX100 transfer, added work]
    // Copy begin/end into owned DX source tiles, set valid counts to current.n,
    // and establish publication/visibility to DX100. This is a REQUIRED adapter
    // contract, not an assumed memcpy or an existing cross-accelerator intrinsic.
    SKETCH_dx_publish_rows(w.dx, current.begin, current.end, current.n);
    current.state = DX_IN_USE;

    // [D1 / CPU control] Initialize values through allocated REGISTER HANDLES.
    SKETCH_dx_const_i32( 0, w.dx.last_i_reg);
    SKETCH_dx_const_i32(-1, w.dx.last_j_reg);
    SKETCH_dx_const_i32( 1, w.dx.stride_reg);
    Count emitted = 0;

    while (true) {
        // [D2 / DX100] Continuation of the inner CSR traversal, line 241.
        // row_slot[k] is an ordinal in this metadata batch, NOT a vertex ID.
        // edge_index[k] is the corresponding absolute CSR neighbor-array index.
        SKETCH_dx_range_continue(w.dx.last_i_reg, w.dx.last_j_reg,
                                 w.dx.begin_tile, w.dx.end_tile,
                                 w.dx.stride_reg,
                                 w.dx.row_slot_tile, w.dx.edge_index_tile);
        SKETCH_dx_wait_range_outputs(w.dx); // both outputs and their sizes usable
        Count p = SKETCH_dx_range_result_count(w.dx);
        SKETCH_require(p <= w.dx.admitted_chunk_capacity);
        if (p == 0) {
            // A completed empty range result must mean exhaustion, not temporary
            // producer unavailability. The backend must establish this contract.
            SKETCH_require_range_exhausted(w.dx);
            break;
        }

        // [D3 / DX100] Original bfs-td-neighbor, line 242.
        // Bulk neighbor gather; physical requests may group/interleave/reorder.
        // Results must retain the original logical edge_index/row_slot association.
        SKETCH_dx_gather(g.out_neighbors_, w.dx.edge_index_tile,
                         w.dx.neighbor_tile, p);
        SKETCH_dx_wait_cpu_readable(w.dx.row_slot_tile, w.dx.neighbor_tile, p);
        // Wait above includes required CPU observer visibility, not just acceptance.

        // [C1 / CPU] Retain the original parent-read/CAS/store/append statements.
        for (int k = 0; k < p; ++k) {
            int r = SKETCH_dx_read_row_slot(w.dx, k);
            SKETCH_require(0 <= r && r < current.n);
            NodeID u = current.vertices[r];
            NodeID v = SKETCH_dx_read_neighbor(w.dx, k);
            NodeID curr_val = parent[v];                    // bfs-td-parent-read:243
            if (curr_val < 0) {
                if (compare_and_swap(parent[v], curr_val, u)) { // bfs-td-parent-cas:247
                    parent[v] = u;                         // bfs-td-parent-store:248
                    lqueue.push_back(v);                   // bfs-td-queue-append:249
                }
            }
        }
        emitted += p;
        // [H3 / CPU/DX completion] Cover all tile consumers AND host reads before
        // overwriting row_slot/edge_index/neighbor tiles in the next chunk.
        SKETCH_dx_release_chunk_after_all_consumers(w.dx);
        // Keep last_i/last_j values across chunks. A short chunk is not an exit test.
    }

    SKETCH_require(emitted == SUM(r in [0,current.n): current.end[r] - current.begin[r]));
    // Count equality is an accounting invariant, not a proof of pair identity.
    SKETCH_dx_finish_batch_and_cover_source_reuse(w.dx);
    SKETCH_require_CPU_effects_complete_for_this_batch();
    current.state = FREE;
}

void TDStep_MapleDx100_SKETCH(const Graph& g, Offsets& VertexOffsets,
                             Parent& parent, SlidingQueue& queue,
                             int num_nodes, int num_edges) {
    // One invocation processes exactly ONE existing BFS frontier/level.
    // Original source loop: TDStep, e4fc4af bfs.cc:227-259.
    if (queue.shared_out_start == queue.shared_out_end) return;

    // [H0 / CPU setup] BEFORE any parent/next-frontier mutation:
    // validate CSR/node/index domains and stable graph epoch; select a common
    // deployment/typed ABI; admit 2 MAPLE queues + a DX context per worker;
    // validate positive B/T/worker count, capacities and publication/visibility/waits.
    // Queue pairs start exclusively owned, empty and quiescent; each worker's
    // metadata_ticket starts at NONE. OPEN alone is not evidence of an empty queue.
    // Setup encompasses actual allocation, register/tile allocation, region binding
    // and MMU/driver initialization. These are not hidden assumed-success APIs.
    // Admission covers every planned batch size, including final tails and any
    // packed-consume alignment. No speculative padding reads are assumed.
    Admission a = SKETCH_admit_composition(g, VertexOffsets, queue, num_nodes, num_edges);
    if (!a.accepted) {
        // Only pre-effect whole-step fallback is part of this sketch.
        SKETCH_release_unissued_resources(a);
        TDStep(g, VertexOffsets, parent, queue, num_nodes, num_edges);
        return;
    }

    // [H0 / CPU, added traffic] Copy the frozen current-frontier IDs into immutable F.
    // Next-frontier pushes may use the original queue storage; no accelerator reads
    // that mutating buffer. Account for this snapshot cost rather than hiding it.
    ImmutableFrontier F = SKETCH_snapshot_current_frontier(queue);
    SKETCH_publish_stable_graph_and_frontier_epoch(a, g, VertexOffsets, F);

    parallel_for_each_admitted_worker(a, [&](Worker& w) {
        // Disjoint static spans cover F exactly once. Resources are worker-private;
        // reference per-core tile counts do not prove arbitrary worker scalability.
        FrontierSpan span = SKETCH_partition(F, w.id, a.worker_count);
        QueueBuffer<NodeID> lqueue(queue);
        if (!span.empty()) {
            Metadata slots[2] = {FREE, FREE};
            int cur = 0;
            FrontierBatch first = span.take_next(a.B);
            MetadataTicket pending = SKETCH_issue_bounds(w, slots[cur], VertexOffsets,
                                                         first.vertices, first.id);
            w.metadata_ticket = pending;
            while (true) {
                // Prologue/steady state: current row bounds become host-ready.
                SKETCH_collect_bounds(w, pending, num_edges);
                bool has_next = !span.empty();
                MetadataTicket next = NONE;
                if (has_next) {
                    // Start MAPLE for n+1 BEFORE running DX100/CPU for n.
                    // These queues were emptied by collecting n. Buffer 1-cur
                    // cannot alias the current metadata or current DX source tiles.
                    FrontierBatch following = span.take_next(a.B);
                    next = SKETCH_issue_bounds(w, slots[1-cur], VertexOffsets,
                                               following.vertices, following.id);
                    w.metadata_ticket = next;
                }
                SKETCH_process_neighbors(w, slots[cur], g, parent, lqueue);
                // Intended overlap: MAPLE(n+1) with DX100 + CPU(n).
                // Overlap is possible, not guaranteed by the pseudocode.
                if (!has_next) break; // epilogue: no speculative extra batch issued
                cur = 1 - cur;
                pending = next;
            }
        }
        // [H4 / drain] Known requested counts must be fully consumed; then establish
        // deployment quiescence and DX source/destination reuse. CLOSE alone is not
        // a universal drain. No orphan metadata ticket or result may survive.
        SKETCH_finish_worker_requests_and_consumers(w);
        lqueue.flush(); // original CPU thread-local queue effect
    }); // join all workers; required next-frontier visibility/level barrier

    SKETCH_finish_step_and_release_epoch(a, F);
    // The original BFS driver advances to the next frontier only after this return.
    // A fault after effects begin aborts this candidate run; do not replay TDStep
    // over already-mutated parent/queue state without a separate recovery contract.
}
