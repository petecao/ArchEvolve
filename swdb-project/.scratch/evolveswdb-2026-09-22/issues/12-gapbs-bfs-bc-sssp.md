# 12 — gapbs bfs, bc, sssp

Created: 2026-09-22
**Type:** slice
**Status:** resolved
**Blocked by:** 11
**Spec:** `../spec.md`

**What to build:** The database covers the gapbs traversal kernels, exercising the
compare-and-swap and add-update kinds.

- [x] For each of bfs, bc, and sssp: a kernel record whose correctness check uses the gapbs verifier, and a baseline implementation record with access-pattern chains and semantics with basis.
- [x] The compare-and-swap updates (`parent`, `depths`, `dist`) and bc's floating-point accumulation are recorded with the right update kinds.
- [x] Profiles on mbit10 for the four pilot inputs (with a timeout per run) validate, and a view is generated for each pair.

## Comments

## Answer

Resolved 2026-09-22.

- Kernel records `gapbs-bfs`, `gapbs-bc`, `gapbs-sssp` with verifier-based correctness checks
  (BFSVerifier, BCVerifier with tolerance float epsilon per vertex, SSSPVerifier exact), and
  baseline implementations `gapbs-bfs-do`, `gapbs-bc-brandes`, `gapbs-sssp-delta` with chains
  and semantics with basis.
- Update kinds: `parent` claim (bfs), `depths` claim (bc), and the `dist` relax (sssp, an
  atomic min implemented with a CAS retry loop) are `compare_and_swap`; bc's `path_counts`
  accumulation is `add_update` with `atomic_updates_required: true`, and its floating-point
  back-propagation is `fp_reassociation_allowed`.
- Profiles on mbit10 (node1 lane) for all four pilot inputs: 12 profiles, all complete,
  all validate, `swdb view` succeeds for each pair. Inferred bottlenecks: scale 16 bfs
  parallelism_bound, bc compute_bound, sssp unknown (kron: its footprint is only a lower
  bound because the bins are data-dependent) / parallelism_bound (urand); scale 22 all
  memory_bound (latency).
- Records written by an agent following docs/adding-an-application.md (ticket 11 check);
  vocabulary addition: `index_transforms: divide` (bitmap word = v // 64).
