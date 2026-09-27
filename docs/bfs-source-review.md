# DX100 artifact BFS — source review

Reviewed the source supplied by Josh, at DX100 commit `e4fc4afdf894f295442cef3604667a469fab8e62`. The full modified `bfs.cc` is available locally, with the surrounding GAPBS headers and DX100 API headers. No benchmark has been built or run.

## Two paths in the same file

| Function | Source behavior | Proposed use |
|---|---|---|
| `TDStep` | Explicit frontier/CSR-index loops with CPU reads, compare-and-swap, and queue insertion | First candidate region for Peter's feature extraction; confirm with Peter/Yan-Ru |
| `TDStepMAA` | Tile/register setup, DX100 API operations, synchronization, and CPU handling/fallback | Existing accelerated reference to study after the workload features are identified |
| `DOBFS` / `DOBFSMAA` | Drivers that repeatedly process the frontier | Record the driver/build choice and workload context |

[`TDStep`](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/bfs.cc#L227-L259) is distinct from the iterator-style `TDStep2` retained later in the same file. The `MAA` compile-time flag chooses `DOBFSMAA` instead of `DOBFS` in [`main`](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/bfs.cc#L523-L528).

My recommendation is to use the artifact's CPU `TDStep` statements as the initial feature-extraction target, while keeping `TDStepMAA` as implementation evidence. That is a proposal, not a choice the team has confirmed. Extracting features only from already-offloaded API calls would hide some of the original access-expression structure.

## Concrete statement chain

The CPU loop exposes this sequence in lines 239–249:

```text
frontier index i
  → u = queue.shared[i]
  → row interval [VertexOffsets[u], VertexOffsets[u + 1])
  → v = g.out_neighbors_[j]
  → curr_val = parent[v]
  → if unvisited: compare_and_swap(parent[v], curr_val, u)
  → on success: parent[v] = u; lqueue.push_back(v)
```

This is a source dependency sequence, not a hardware block diagram or a measured execution trace. `parent[v]` is the indirect destination; the update subtype is **compare-and-swap**, rather than the increment in Peter's SPARTA example.

The [source observations](../examples/bfs.source-observations.yaml) record seven proposed statement IDs and exact source locations for discussion. They are manually reviewed facts, **not Peter's feature YAML**, an automated extraction result, or profiling data.

`NodeID` is explicitly `int32_t` in [`benchmark.h`](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/benchmark.h#L28-L34), and `SGOffset` is `int32_t` in [`graph.h`](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/graph.h#L90). The GCC/OpenMP wrapper uses a compiler atomic CAS in [`platform_atomics.h`](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/platform_atomics.h#L18-L32).

Sequential reads within a frontier segment or adjacency row can be identified from source. Their dynamic frequency, cross-row access sequence, reuse distances, active working set, and average irregular stride depend on the graph, frontier, tiling, and execution. Those values remain unmeasured.

## Existing accelerated reference

The [accelerated inner section](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/bfs.cc#L144-L193) contains:

- `maa_stream_load` for the frontier queue.
- `maa_indirect_load` for row starts/ends, neighbor IDs, frontier IDs, and parent values.
- `maa_range_loop` to generate work across variable-length adjacency ranges.
- `maa_alu_scalar` to form the unvisited predicate.
- `maa_indirect_store_vector`, synchronization, and CPU queue insertion in the update path.

The parent read/predicate/store section is enclosed in an OpenMP critical region. Small remaining work can take a CPU fallback path. Treat these as behaviors of this implementation, not proof that any generic gather/scatter component supports the same semantics.

The functional API includes the corresponding declarations in `sources/DX100/benchmarks/API/MAA_functional.hpp`; the gem5 interface is in `MAA_gem5.hpp`. This provides implementation references, but not Eric's current catalog or a complete validated hardware composition for our agent.

## Corrections and comparison limits

**The artifact is not globally free of while loops.** It retains frontier `while` loops in the drivers, an outer work loop in `TDStepMAA`, and a `do/while` around range-loop batches. The useful transformation is the explicit index/range treatment inside the kernel; do not interpret the meeting shorthand as removal of all host control loops.

At the recorded upstream snapshot, `DOBFS` switches between top-down and bottom-up traversal. The artifact drivers shown here repeatedly call top-down steps. The artifact also adds explicit offsets, API calls, and gem5 region/statistics hooks. Consequently, the comparison is broader than a loop-syntax conversion. See [the saved diff](../sources/bfs-upstream-to-dx100.diff).

The artifact [`Makefile`](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/Makefile) distinguishes baseline and `_maa` binaries, compile-time tile/core variants, and functional versus gem5 interfaces. Record these build choices alongside profiling. Existing artifact defaults are reference configurations, not values the Arch Evolve selector must freeze.

`BFSVerifier` checks source/reachability, parent edges, and BFS levels. It does not compare against one canonical parent array. Any future correctness contract must agree with the intended BFS semantics; the presence of a verifier is not evidence that we have executed it.

## Still needed

- Peter's statement-level feature YAML, tied to this revision and a confirmed function/build path.
- Yan-Ru's annotations and the dataset/profiling setup.
- Measured reuse, stride summaries, scoped working set, frequencies, and baseline evidence.
- Eric's current machine-readable hardware catalog.

The source dependency is now available. The other pipeline inputs should remain explicitly pending.
