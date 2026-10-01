# Intrinsic Specification & Rewrite Contract: GAPBS BFS Top-Down Step
**Document Version:** 1.0 (Draft 0.2 aligned)  
**Author:** Peter (Pete Cao)  
**Target Consumer:** Yan-Ru Jhou (Loop Rewrite & Profiling Agent)  
**Upstream Sources:** Joshveer Grewal (`docs/peter-intrinsics-handoff.md`, `runs/bfs-hardware-v0.1/case-01/hardware-request.yaml`), Eric's Hardware Catalog (`catalog/hardware-v0.1.yaml`, revision 0.1.2)  
**Target Kernel:** `gapbs_bfs_top_down_step` (`TDStep` in `benchmarks/gapbs/src/bfs.cc` @ revision `e4fc4afdf894f295442cef3604667a469fab8e62`)  
**Associated Hardware Candidate:** Candidate 2 (`dx100-artifact-e4fc4af:read_execute`)

---

## 1. Architectural Decisions & Scope

### 1.1 Phase 3 (Terminus Memory-Side CAS) is Formally Deferred
As documented in [`docs/peter-intrinsics-handoff.md`](file:///home/petepc/ArchEvolve_petecao/docs/peter-intrinsics-handoff.md) and Candidate 3 (`terminus-micro2024-cas:update_execute`), offloading atomic compare-and-swap directly to memory controllers/L2 slices currently lacks verified evidence for:
1. Address partitioning & single-writer-multiple-reader (SWMR) exclusion boundaries across memory channels.
2. Cross-interconnect synchronization between memory-side atomic response tokens and CPU-side thread-local queue pushes (`lqueue.push_back(v)`).

**Decision:** **Candidate 3 is formally deferred.** No hardware-side CAS intrinsic is permitted for immediate rewrite.

### 1.2 DX100 Hardware CAS Exclusion
In the inspected DX100 benchmark artifact (`bfs.cc` lines 170–187), the parent update was implemented as a masked vector store (`maa_indirect_store_vector`) guarded by a host OpenMP critical section (`#pragma omp critical`). The DX100 hardware contains **no hardware atomic CAS primitive** capable of handling concurrent multi-core discovery conflicts safely without software critical sections.

**Decision:** **Parent atomic claims remain on the host CPU.** The rewrite must retain the architectural `compare_and_swap(parent[v], curr_val, u)` executed by the CPU.

### 1.3 Active Acceleration Target: Candidate 2 (`dx100-artifact-e4fc4af:read_execute`)
The loop rewrite will accelerate **read/gather traversal operations** using DX100 scratchpad tiles and the `RangeFuser` hardware engine, feeding pre-screened candidate vertices to the host CPU for atomic arbitration.

---

## 2. Hardware Resource & State Model

The DX100 coprocessor interface relies on memory-mapped registers and dedicated on-chip scratchpad tiles:

* **Scratchpad Tiles (`tile0` .. `tile7`):**
  * Fixed reference capacity: $C_{\text{tile}} = 16{,}384$ elements of 32-bit words (`int32_t`).
  * Dynamic size bookkeeping: 16-bit unsigned integer (`uint16_t`).
  * Tile allocation mapping for BFS traversal:
    * `tile0`: Loaded frontier vertex IDs ($u \in \text{queue.shared}$) / target neighbor IDs ($v \in \text{g.out\_neighbors\_}$).
    * `tile1`: CSR row start offsets (`VertexOffsets[u]`).
    * `tile2`: CSR row end offsets (`VertexOffsets[u + 1]`).
    * `tile3`: Origin parent vertex IDs ($u$) aligned with expanded neighbor slots.
    * `tile4`: Boolean/predicate mask tile (`parent[v] < 0`).
    * `tile6`: Range generator outer index accumulator ($i$).
    * `tile7`: Range generator inner index accumulator ($j$ in `g.out_neighbors_`) / gathered `parent[v]` values.
* **Scalar / Continuation Registers:**
  * `reg0`, `reg1`, `regOne`, `regZero`: Scalar loop limits and constant values.
  * `last_i_reg`, `last_j_reg`: Continuation state for chunked CSR row expansion across tile boundaries.

---

## 3. Concrete Intrinsic Function Specifications

The following C/C++ pseudo-intrinsics reflect the source-observed DX100 API in `MAA_gem5.hpp` and `IndirectAccess.cc`.

### 3.1 `__dxc_stream_load`
Sequential stream read from memory into a designated scratchpad tile.
```c
void __dxc_stream_load(
    const int32_t* base_addr,
    int32_t start_idx,
    int32_t end_idx,
    int32_t stride,
    dxc_tile_t dst_tile
);
```
* **Hardware Realization:** Native primitive (`STREAM_LD`).
* **Workload Binding:** `access-01-read` (Statement: `u = queue.shared[i]`).
* **Preconditions:**
  * `start_idx < end_idx`.
  * Count $(end\_idx - start\_idx) \le C_{\text{tile}}$ (16,384 elements).
  * `base_addr` points to contiguous memory (`queue.shared`).
* **Postconditions:** `dst_tile` contains the sequence `base_addr[start_idx .. end_idx - 1]`.

---

### 3.2 `__dxc_gather`
Indirect load using index offsets supplied in an index tile.
```c
void __dxc_gather(
    const int32_t* base_addr,
    dxc_tile_t idx_tile,
    dxc_tile_t dst_tile,
    dxc_tile_t mask_tile = DXC_NO_MASK
);
```
* **Hardware Realization:** Native primitive (`INDIR_LD`).
* **Workload Binding:**
  * `access-02-read` (Statements: `VertexOffsets[u]` and `VertexOffsets[u + 1]`).
  * `access-04-read` (Statement: `parent[v]`).
* **Preconditions:**
  * `idx_tile` must have valid elements generated from a prior operation.
  * **Critical 32-bit Arithmetic Bound:** For all active entries $k$ in `idx_tile`, the product $\text{Index}[k] \times \text{sizeof(int32\_t)}$ must evaluate without wrapping in unsigned 32-bit arithmetic:
    $$\text{Index}[k] \le \left\lfloor \frac{2^{32} - 1}{4} \right\rfloor = 1{,}073{,}741{,}823 \quad (\approx 1.07\text{B vertices})$$
* **Postconditions:** `dst_tile[k] = base_addr[idx_tile[k]]` for all unmasked lanes.

---

### 3.3 `__dxc_range_loop`
Hardware-assisted segmented index expansion (`RangeFuser`).
```c
void __dxc_range_loop(
    dxc_reg_t last_i_reg,
    dxc_reg_t last_j_reg,
    dxc_tile_t row_start_tile,
    dxc_tile_t row_end_tile,
    int32_t stride,
    dxc_tile_t out_outer_idx_tile,
    dxc_tile_t out_inner_idx_tile
);
```
* **Hardware Realization:** Documented hardware sequence (`RangeFuser`).
* **Workload Binding:** Segmented CSR expansion for $[VertexOffsets[u], VertexOffsets[u + 1])$.
* **Preconditions:**
  * `last_i_reg` initialized to `0` and `last_j_reg` initialized to `-1` at start of batch.
  * `row_start_tile` and `row_end_tile` populated via `__dxc_gather`.
* **Postconditions:**
  * Populates `out_outer_idx_tile` with parent index $i$ and `out_inner_idx_tile` with neighbor index $j \in [row\_start, row\_end)$.
  * Caps output when either tile reaches $C_{\text{tile}}$, writing continuation state back to `last_i_reg` and `last_j_reg`.

---

### 3.4 `__dxc_alu_scalar`
Element-wise SIMD comparison against a scalar threshold.
```c
void __dxc_alu_scalar(
    dxc_tile_t src_tile,
    int32_t scalar_imm,
    dxc_tile_t dst_mask_tile,
    dxc_op_t op // e.g., DXC_OP_LT
);
```
* **Workload Binding:** Pre-screen unvisited vertices (`curr_val < 0` where `scalar_imm = 0`).
* **Postconditions:** `dst_mask_tile[k] = (src_tile[k] < scalar_imm) ? 1 : 0`.

---

### 3.5 Synchronization & Status Intrinsics
Explicit completion barrier between coprocessor scratchpad and host CPU access.
```c
void __dxc_wait_ready(dxc_tile_t tile);
uint16_t __dxc_get_tile_size(dxc_tile_t tile);
const int32_t* __dxc_get_tile_ptr(dxc_tile_t tile);
```
* **Hardware Semantics:**
  * `__dxc_wait_ready(tile)`: Polls the memory-mapped tile status register until pending memory requests clear, followed by an architectural `mfence`.
  * `__dxc_get_tile_ptr(tile)`: Returns direct host CPU memory-mapped pointer to read scratchpad entries.

---

## 4. Legality, Numerical & Ordering Constraints

1. **32-Bit Index Overflow Restriction:**
   * GAPBS compiled with 32-bit offsets (`SGOffset` = `int32_t`) and node IDs (`NodeID` = `int32_t`).
   * The effective address is computed as $\text{Base} + (\text{Index} \times 4)$. Yan-Ru's guard checks must ensure $|V| \le 1{,}073{,}741{,}823$ and $|E| \le 1{,}073{,}741{,}823$.
2. **Dynamic Degree Imbalance & Chunking:**
   * High-degree hub nodes ($degree(u) > 16{,}384$) cannot fit inside a single scratchpad tile.
   * `__dxc_range_loop` must be invoked inside a `do { ... } while (tile_size > 0)` loop using `last_i_reg` and `last_j_reg` to resume expansion without dropping neighbor edges.
3. **Short Frontier Fallback:**
   * When frontier size $|F| < \text{THRESHOLD}$ (e.g., $< 64$ vertices in Kronecker levels 1, 2, and 7 where frontier sizes are 1, 3, and 6), dispatching DX100 tile instructions introduces net overhead due to MMIO latency.
   * Yan-Ru must emit a scalar CPU loop fallback for small frontiers.
4. **Visibility & Freshness on `parent`:**
   * The `parent` array is concurrently read by DX100 (`dxc-gather`) and updated by the CPU (`CAS`).
   * DX100's gathered `parent[v]` is purely a **filtering hint** (`parent[v] < 0`).
   * The host CPU **must re-verify** the current value inside the atomic CAS:
     ```cpp
     if (curr_val < 0) {
         if (compare_and_swap(parent[v], curr_val, u)) {
             parent[v] = u;
             lqueue.push_back(v);
         }
     }
     ```

---

## 5. Loop Rewrite Template for Yan-Ru

Yan-Ru's AST/rewrite agent can transform `TDStep` in `benchmarks/gapbs/src/bfs.cc` using the following guarded pattern:

```cpp
void TDStep_Accelerated(
    const Graph &g,
    pvector<SGOffset> &VertexOffsets,
    pvector<NodeID> &parent,
    SlidingQueue<NodeID> &queue,
    int num_nodes,
    int num_edges
) {
    const size_t frontier_len = queue.shared_out_end - queue.shared_out_start;
    const size_t TILE_CAPACITY = 16384;
    const size_t MIN_ACCEL_FRONTIER = 64;

    // Guard 1: Fall back to CPU baseline if frontier is too small or exceeds 32-bit index limit
    if (frontier_len < MIN_ACCEL_FRONTIER || num_nodes >= 1073741823 || num_edges >= 1073741823) {
        // Original CPU reference loop
        #pragma omp parallel
        {
            QueueBuffer<NodeID> lqueue(queue);
            #pragma omp for nowait
            for (size_t i = queue.shared_out_start; i < queue.shared_out_end; i++) {
                NodeID u = queue.shared[i];
                for (int j = VertexOffsets[u]; j < VertexOffsets[u + 1]; j++) {
                    NodeID v = g.out_neighbors_[j];
                    NodeID curr_val = parent[v];
                    if (curr_val < 0) {
                        if (compare_and_swap(parent[v], curr_val, u)) {
                            parent[v] = u;
                            lqueue.push_back(v);
                        }
                    }
                }
            }
            lqueue.flush();
        }
        return;
    }

    // Accelerated Path: Chunked execution across threads
    #pragma omp parallel
    {
        QueueBuffer<NodeID> lqueue(queue);
        int tid = omp_get_thread_num();
        int nthreads = omp_get_num_threads();

        #pragma omp for schedule(dynamic, 1)
        for (size_t chunk_start = queue.shared_out_start; 
             chunk_start < queue.shared_out_end; 
             chunk_start += TILE_CAPACITY) 
        {
            size_t chunk_end = std::min(chunk_start + TILE_CAPACITY, (size_t)queue.shared_out_end);
            int count = chunk_end - chunk_start;

            // Step 1: Stream-load frontier chunk into tile0
            __dxc_stream_load(queue.shared, chunk_start, chunk_end, 1, DXC_TILE0);
            __dxc_wait_ready(DXC_TILE0);

            // Step 2: Indirect load CSR offsets for vertices u in tile0
            __dxc_gather(VertexOffsets.data(), DXC_TILE0, DXC_TILE1);
            __dxc_gather(VertexOffsets.data() + 1, DXC_TILE0, DXC_TILE2);
            __dxc_wait_ready(DXC_TILE1);
            __dxc_wait_ready(DXC_TILE2);

            // Step 3: Segmented traversal of neighbor ranges
            dxc_reg_t last_i = 0;
            dxc_reg_t last_j = -1;
            uint16_t produced_neighbors = 0;

            do {
                // Generate chunk of (u, v) neighbor indices
                __dxc_range_loop(last_i, last_j, DXC_TILE1, DXC_TILE2, 1, DXC_TILE6, DXC_TILE7);
                __dxc_wait_ready(DXC_TILE7);
                produced_neighbors = __dxc_get_tile_size(DXC_TILE7);
                if (produced_neighbors == 0) break;

                // Load neighbor IDs v into DXC_TILE0
                __dxc_gather(g.out_neighbors_, DXC_TILE7, DXC_TILE0);
                // Load corresponding parent IDs u into DXC_TILE3
                __dxc_gather(queue.shared + chunk_start, DXC_TILE6, DXC_TILE3);
                __dxc_wait_ready(DXC_TILE0);
                __dxc_wait_ready(DXC_TILE3);

                // Step 4: Screen parent[v] in DXC_TILE4
                __dxc_gather(parent.data(), DXC_TILE0, DXC_TILE4);
                __dxc_wait_ready(DXC_TILE4);

                const int32_t* v_ptr = __dxc_get_tile_ptr(DXC_TILE0);
                const int32_t* u_ptr = __dxc_get_tile_ptr(DXC_TILE3);
                const int32_t* p_ptr = __dxc_get_tile_ptr(DXC_TILE4);

                // Step 5: CPU Arbitration & Queue Insert (atomic compare-and-swap)
                for (uint16_t k = 0; k < produced_neighbors; k++) {
                    NodeID v = v_ptr[k];
                    NodeID u = u_ptr[k];
                    NodeID curr_val = p_ptr[k];

                    if (curr_val < 0) {
                        if (compare_and_swap(parent[v], curr_val, u)) {
                            parent[v] = u;
                            lqueue.push_back(v);
                        }
                    }
                }
            } while (produced_neighbors > 0);
        }
        lqueue.flush();
    }
}
```

---

## 6. Actionable Handoff Summary for Yan-Ru

1. **Intrinsics to provide:** Include headers for `__dxc_stream_load`, `__dxc_gather`, `__dxc_range_loop`, `__dxc_wait_ready`, `__dxc_get_tile_size`, and `__dxc_get_tile_ptr`.
2. **Loop structure:** Preserve CPU atomic `compare_and_swap`. Do not attempt to offload CAS to hardware.
3. **Guards:** Check `|V| < 1.07B`, `|E| < 1.07B`, and $|F| \ge 64$.
4. **Verification:** Validate against `BFSVerifier` to guarantee identical BFS tree depth and edge reachability.
