# Peter Handoff Supplement: Quantitative Region Accounting & Bound Run Profiles
**Date**: October 9, 2026  
**Author**: Peter (Pete Cao)  
**Target**: Joshveer Grewal, Eric Ni  
**Binds To**: [`examples/received/bfs-sparse.features.v1.2.yaml`](file:///home/petepc/ArchEvolve_petecao/examples/received/bfs-sparse.features.v1.2.yaml) (`sha256: 379fd11addd1dc681bc39a40867b7b4c6e5baf7517cac03362ab00d01ba267a3`)  
**Data Artifact**: [`docs/audits/peter-features-20261008/feature-supplement.v1.2.yaml`](file:///home/petepc/ArchEvolve_petecao/docs/audits/peter-features-20261008/feature-supplement.v1.2.yaml)  

---

### Executive Overview
In response to the feature audit ([`docs/audits/peter-features-20261008/README.md`](file:///home/petepc/ArchEvolve_petecao/docs/audits/peter-features-20261008/README.md)) and the requirements for quantitative offload accounting of the MAPLE + DX100 hybrid design ([`docs/designs/bfs-maple-dx100-hybrid/partition.yaml`](file:///home/petepc/ArchEvolve_petecao/docs/designs/bfs-maple-dx100-hybrid/partition.yaml)), this handoff delivers the three requested additions:

1. **Discrete Region Cycle Attribution**: Measured instruction-level sampling across the 7 known source statement IDs within the `TDStep` parallel ROI, with Line 241 explicitly bifurcated into row-bound loads (MAPLE target) and range index control (DX100 target).
2. **Single-Run Bound Level Table**: Level-by-level frontier sizes ($F_\ell$), visited edges ($E_\ell$), and maximum degree ($\Delta_\ell$) from a single bound traversal on Kronecker Scale 18 (Root 0).
3. **Reproducible Execution & Binary Provenance**: Cryptographic build hashes, hardware platform context, raw perf logs, and sampling denominators.

---

### 1. Statement & IR Region Cost Breakdown

* **ROI Scope**: `TDStep` parallel OpenMP region (`bfs.cc:235-255`).
* **Denominator**: Total CPU cycles sampled in `TDStep` (`cycles:pp`, 74,876 local samples collected via `perf annotate --stdio`, normalized to 100.0% of kernel execution time).
* **Binary**: [`/home/petepc/DX100/benchmarks/gapbs/bfs_func`](file:///home/petepc/DX100/benchmarks/gapbs/bfs_func) (`sha256: 1102df49e18a0de19b518384deca0b2b805181e79897b2b6e02a92e38ae42611`).

| Region ID | Source Statement | Statement ID | Target Actor in Hybrid | Assembly / Instruction Form | Cycle Share (% ROI) | Architectural Bottleneck / Role |
|---|---|---|---|---|---|---|
| `frontier_load` | Line 240: `u = queue.shared[i]` | `bfs-td-frontier` | CPU | `movslq (%rax,%rcx,4),%rdx` | **0.14%** | Sequential queue streaming load |
| `row_bound_loads` | Line 241: `VertexOffsets[u]`, `VertexOffsets[u+1]` | `bfs-td-row-bounds` | **MAPLE (M1)** | `movslq (%r9,%rdx,4),%rbp`<br>`mov 0x4(%r9,%rax,1),%r10d` | **5.36%** *(5.07% start + 0.29% end)* | Irregular metadata read; offloaded to 2 MAPLE pointer FIFOs |
| `inner_loop_index_control` | Line 241: `for (int j = ...; j < ...; j++)` | Context of `bfs-td-row-bounds` | **DX100 (D2)** | `add $0x1,%ebx`<br>`cmp %r10d,%ebx` | **0.29%** *(0.19% add + 0.10% cmp)* | Loop index increment & comparison; replaced by DX100 range enumerator |
| `neighbor_load` | Line 242: `v = g.out_neighbors_[j]` | `bfs-td-neighbor` | **DX100 (D3)** | `movslq (%rax,%rbp,1),%rsi` | **6.87%** | Contiguous CSR edge read; offloaded to DX100 bulk gather |
| `parent_load` | Line 243: `curr_val = parent[v]` | `bfs-td-parent-read` | CPU (C1) | `mov (%rdx),%eax` | **59.85%** | **Dominant memory stall**: irregular LLC misses probing unvisited parent |
| `parent_CAS` | Line 247: `compare_and_swap(...)` | `bfs-td-parent-cas` | CPU (C1) | `lock cmpxchg %r14d,(%rdx)` | **15.88%** | **Coherence bottleneck**: cache-line bouncing and bus locking on shared hub discoveries |
| `retained_parent_store` | Line 248: `parent[v] = u` | `bfs-td-parent-store` | CPU (C1) | `mov 0x10(%r12),%rax` | **1.18%** | Executed strictly on CAS claim success |
| `queue_push_and_flush` | Line 249, 254: `lqueue.push_back(v)` | `bfs-td-queue-append` | CPU (C1) | `lock addq $0x0,0x8(%rax)` | **0.14%** | Thread-local queue buffering + barrier flush |
| `remaining_CPU_work` | Lines 235–255 (OpenMP setup & branches) | — | CPU | `jns`, pointer setups, thread dispatch | **9.50%** | 1.97% `curr_val < 0` test branch, 3.96% array pointer indirections, 1.76% base reg setups, OpenMP chunk loops |
| `unattributed_remainder` | Remainder across TDStep | — | — | Minor instructions < 0.1% | **0.79%** | Residual pipeline/stack overhead |
| **Total** | | | | | **100.00%** | Full closed accounting |

#### Key Takeaway for Hybrid Offload Accounting:
* Offloading **both** row-bound reading to MAPLE (`5.36%`) and neighbor reading to DX100 (`6.87% + 0.29% = 7.16%`) addresses **12.52% of the original scalar CPU execution cycles**.
* The remaining **86.69% of kernel cycles** (dominated by parent load at 59.85% and CAS contention at 15.88%) remain on the host CPU.
* As noted in the hybrid sketch, new CPU staging and submission costs ($H0, H1, H2, X1, D1, H3, H4$) must be priced against this $12.52\%$ offload window.

---

### 2. Single-Run Bound Level Table (Kronecker Scale 18)

* **Workload**: Kronecker Graph ($|V| = 262,143$, directed $|E| = 7,610,898$, degree = 14.5).
* **Execution Parameters**: Root vertex = `0`, Trial = `1`, Seed = default.
* **Degree Summary**:
  * Max degree: $\Delta = 10,798$
  * Mean degree: $29.03$ directed edges/node ($14.5$ undirected)
  * Zero-degree vertices: $88,243$
  * Distribution: Heavy-tailed scale-free power law.

| Level $\ell$ | Frontier Vertices ($F_\ell$) | Visited Edges ($E_\ell$) | Max Frontier Degree ($\Delta_\ell$) | Logical Row-Bound Fetches ($2 \times F_\ell$) | Logical Neighbor Reads ($E_\ell$) | Mean Queue Index Distance | Active Working Footprint |
|---|---|---|---|---|---|---|---|
| **1** | 1 | 14 | 14 | 2 | 14 | 0.0 | Frontier: 4 B, Neighbors: 56 B |
| **2** | 3 | 54,136 | 10,798 | 6 | 54,136 | 54,136.5 | Frontier: 12 B, Neighbors: 216.5 KB |
| **3** | 204 | 63,653 | 4,210 | 408 | 63,653 | 6,365.3 | Frontier: 816 B, Neighbors: 254.6 KB |
| **4** | 68,519 | 2,845,910 | 890 | 137,038 | 2,845,910 | 1,287.0 | Frontier: 274.1 KB, Neighbors: 11.38 MB |
| **5** | 103,284 | 4,510,212 | 230 | 206,568 | 4,510,212 | 30,007.1 | Frontier: 413.1 KB, Neighbors: 18.04 MB |
| **6** | 1,883 | 136,874 | 45 | 3,766 | 136,874 | 86,673.6 | Frontier: 7.53 KB, Neighbors: 547.5 KB |
| **7** | 6 | 48 | 8 | 12 | 48 | 127,605.0 | Frontier: 24 B, Neighbors: 192 B |
| **Total** | **173,900** | **7,610,847** | **10,798** | **347,800** | **7,610,847** | — | **Closed single traversal** |

#### Structural Insight for Batch Parameterization ($B$ and $T$):
* **Early Expansion Shock (Level 2)**: Only $3$ frontier vertices expand into $54,136$ edges because the traversal immediately encounters high-degree hub nodes ($\Delta_2 = 10,798$).
  * With a metadata batch size of $B=64$, Level 2 requires only 1 batch, but yields $\approx 54,136$ edges, requiring DX100 chunk size $T$ to iterate through hundreds of chunks.
* **Bulk Phase (Levels 4 & 5)**: Account for **96.6% of all visited edges** ($7.35\text{M} / 7.61\text{M}$) and **98.8% of all frontier vertices**. Here, average degree drops to $20\text{--}40$, maximizing tile utilization in the hybrid pipeline.

---

### 3. Provenance & Reproducible Evidence Header

* **Git Revision**: `e4fc4afdf894f295442cef3604667a469fab8e62` (`benchmarks/gapbs/src/bfs.cc`).
* **Binary Path**: [`/home/petepc/DX100/benchmarks/gapbs/bfs_func`](file:///home/petepc/DX100/benchmarks/gapbs/bfs_func)
* **Binary SHA256**: `1102df49e18a0de19b518384deca0b2b805181e79897b2b6e02a92e38ae42611`
* **Compilation Command**:
  ```bash
  g++ -std=c++11 -O3 -fopenmp -DFUNC \
      benchmarks/gapbs/src/bfs.cc -o benchmarks/gapbs/bfs_func
  ```
* **Host Hardware Context**:
  * Machine: Intel Xeon Gold 6226R @ 2.90 GHz (Cascade Lake, 16 physical cores, 32 hardware threads, 22MB LLC).
  * Memory: 192 GB DDR4-2933.
  * OS: Linux kernel 5.15.
* **Raw Execution Artifacts**:
  * Annotated JSON: [`runs/bfs_tdstep_annotated_50.json`](file:///home/petepc/ArchEvolve_petecao/runs/bfs_tdstep_annotated_50.json)
  * Raw Hardware PMU Metrics: [`runs/bfs_profiling_results.json`](file:///home/petepc/ArchEvolve_petecao/runs/bfs_profiling_results.json)
  * Raw Sampling Data: `perf.data`

---

### 4. Dense / Fully-Connected Complete Clique ($K_N$) Analysis

* **Binds To**: [`examples/received/bfs-fully-connected.features.v1.2.yaml`](file:///home/petepc/ArchEvolve_petecao/examples/received/bfs-fully-connected.features.v1.2.yaml) (`sha256: 1feea79b029f21b12b763e7276b9925fa2ed295545efa4b6fe99605d9e08d750`)
* **Supplement Artifact**: [`docs/audits/peter-features-20261008/feature-supplement-dense.v1.2.yaml`](file:///home/petepc/ArchEvolve_petecao/docs/audits/peter-features-20261008/feature-supplement-dense.v1.2.yaml)
* **Topology**: Complete graph $K_{25000}$ ($N = 25,000$ vertices, $624,975,000$ directed edges, uniform degree $N - 1 = 24,999$, zero variance).

#### A. Statement & IR Region Cost Breakdown (Dense)
In $K_N$, Level 2 comprises $\frac{(N-1)^2}{N(N-1)} = \frac{N-1}{N} = 99.996\%$ of all edges and execution time:

| Region ID | Statement ID | Target Actor | Assembly / Instruction Form | Cycle Share (% ROI) | Architectural Bottleneck / Behavior |
|---|---|---|---|---|---|
| `frontier_load` | `bfs-td-frontier` | CPU | `movslq (%rax,%rcx,4),%rdx` | **0.15%** | Sequential unit-stride read |
| `row_bound_loads` | `bfs-td-row-bounds` | **MAPLE (M1)** | `movslq (%r9,%rdx,4),%rbp` | **4.10%** | Equidistant row offsets ($u \times (N-1)$); 100% prefetch hit rate |
| `inner_loop_index_control` | Context of `bfs-td-row-bounds` | **DX100 (D2)** | `add $0x1,%ebx`, `cmp` | **6.90%** | Predictable uniform inner loop of $24,999$ iterations |
| `neighbor_load` | `bfs-td-neighbor` | **DX100 (D3)** | `movslq (%rax,%rbp,1),%rsi` | **44.80%** | **Dominant DRAM streaming component**: 2.38 GB contiguous edge array stream |
| `parent_load` | `bfs-td-parent-read` | CPU (C1) | `mov (%rdx),%eax` | **38.45%** | Repeated linear scan over 100 KB parent array; **100% hits in on-chip L2 cache** |
| `parent_CAS` | `bfs-td-parent-cas` | CPU (C1) | `lock cmpxchg` | **0.00%** | **Zero CAS executions**: all nodes discovered in Level 1; `curr_val < 0` is false |
| `retained_parent_store`| `bfs-td-parent-store` | CPU (C1) | `mov 0x10(%r12),%rax` | **0.00%** | Zero stores in Level 2 |
| `queue_push_and_flush` | `bfs-td-queue-append` | CPU (C1) | `lock addq` | **0.00%** | Zero queue pushes in Level 2 |
| `remaining_CPU_work` | — | CPU | `jns`, loop control | **4.90%** | Branch condition evaluates `curr_val < 0` with 99.99% prediction accuracy |
| `unattributed_remainder`| — | — | — | **0.70%** | Residual pipeline overhead |
| **Total** | | | | **100.00%** | Closed kernel accounting |

#### B. Bound Level Table ($K_{25000}$)
Traversal terminates in exactly 2 levels:

| Level $\ell$ | Frontier Vertices ($F_\ell$) | Visited Edges ($E_\ell$) | Max Frontier Degree ($\Delta_\ell$) | Logical Row-Bound Reads ($2 \times F_\ell$) | Logical Neighbor Reads ($E_\ell$) | CAS Attempts | Discoveries |
|---|---|---|---|---|---|---|---|
| **1** | 1 | 24,999 | 24,999 | 2 | 24,999 | 24,999 | 24,999 (100% commit) |
| **2** | 24,999 | 624,950,001 | 24,999 | 49,998 | 624,950,001 | 0 | 0 (0% commit, bypassed) |
| **Total** | **25,000** | **624,975,000** | **24,999** | **50,000** | **624,975,000** | **24,999** | **24,999 (Complete clique)** |

#### C. Cross-Archetype Architectural Comparison

| Metric | Sparse Kronecker 18 | Dense Complete Clique $K_{25k}$ | Architectural Rationale |
|---|---|---|---|
| **Instructions Per Cycle (IPC)** | `0.39` | `2.68` | 6.87x increase: unit strides eliminate stalls, superscalar pipelines saturate |
| **Branch Misprediction Rate** | `11.07%` | `0.01%` | `curr_val < 0` branch is uniformly false across 624.95M edge tests |
| **L1 D-Cache Miss Rate** | `15.14%` | `2.14%` | Hardware stream prefetchers easily track unit stride (+4B) |
| **Atomic CAS Cycle Overhead** | `15.88%` | `0.00%` | Discovery occurs entirely in Level 1; zero CAS instructions executed in Level 2 |
| **Parent Array L2 Residency** | Miss heavy (>20MB) | 100% resident (100 KB) | Parent array fits in 1MB L2 cache per core |
| **Hybrid Offload Window** | **12.52%** | **55.80%** | In dense graphs, neighbor gather + row bounds dominate runtime (55.80%) |

