---
name: extract-kernel-features
description: >-
  Extracts memory access features, runs hardware profiling (perf stat + perf record + perf annotate),
  classifies microarchitectural bottlenecks (atomic CAS stalls, gather cache misses, branch divergence),
  and generates validated workload feature YAML files (e.g., bfs-sparse.features.vX.Y.yaml)
  aligned with ArchEvolve schemas.
---

# Extract Kernel Features Skill

This skill guides the automated extraction of memory features, loop control structures, hardware performance counter (PMU) metrics, and assembly-level hotspot attribution from benchmark source code and execution.

## Core Responsibilities

1. **Static AST & Type Inspection**:
   - Inspect source headers (`benchmark.h`, `graph.h`) to verify element bit-widths (`int32_t` vs `int64_t`).
   - Extract access expressions ($A[B[k]]$) and map statement IDs.
2. **Dynamic Locality & Stride Profiling**:
   - Compute mean element jump $|\Delta b| = |b_{k+1} - b_k|$ and byte stride $\Delta \text{bytes} = |\Delta b| \times \text{sizeof}(T)$.
   - Measure spatial locality distribution:
     - Same 64B cache line ($\le 64 / \text{sizeof}(T)$ elements).
     - Same 4KB virtual page ($\le 4096 / \text{sizeof}(T)$ elements).
     - Cross-page jumps ($> 4096 / \text{sizeof}(T)$ elements).
3. **Automated PMU Profiling**:
   - Run `parse_perf_profile.py` with standard PMU counter suite:
     - IPC, branch miss rate, L1 D-cache miss rate, LLC miss rate, CAS stall overhead.
4. **Disassembly Hotspot Attribution (`perf annotate`)**:
   - Attribute sampled cycles down to individual assembly instructions and source lines.
   - Classify bottlenecks into canonical hardware categories:
     - `ATOMIC_CAS_CONTENTION`: `lock cmpxchg` (cache-line bouncing on shared hub nodes).
     - `INDIRECT_LOAD_MISS`: `mov (%base, %idx, scale)` (pointer chasing / gather misses).
     - `BRANCH_DIVERGENCE`: Conditional jumps (`j*`).
     - `SERIALIZING_FENCE`: `mfence`, `sfence`.
5. **Output Generation**:
   - Emit `examples/received/<kernel>.features.vX.Y.yaml`.
   - Validate against `schemas/workload.schema.json`.

## Helper Scripts

Located in `scripts/`:
- `parse_perf_profile.py`: Runs `perf stat` and `perf record` + `perf annotate`, outputs JSON with cycle percentages and bottleneck taxonomy.
- `calc_stride_locality.py`: Takes an index trace and computes stride distributions and cache/page proximities.

## Execution Example

```bash
# 1. Profile and annotate target kernel
python3 .agents/skills/extract-kernel-features/scripts/parse_perf_profile.py \
  --symbol=TDStep \
  --output=kernel_hotspots.json \
  -- ./bfs -g 18 -k 16 -n 5

# 2. Review classified bottlenecks
cat kernel_hotspots.json | grep -E "sample_pct|bottleneck_type|instruction"
```
