# 08 — Index-stream features

Created: 2026-09-22
**Type:** slice
**Status:** resolved
**Blocked by:** 07
**Spec:** `../spec.md`

**What to build:** Profiles report exactly how an implementation's indices behave
(repeats, reuse distance, sequential runs, degree skew), computed from the index arrays
in the order the implementation visits them. No counters are needed.

- [x] A small C++ tool, built against gapbs's own graph builder, regenerates the input's graph and walks the index array in visit order. It builds serially on the Mac and on mbit10.
- [x] It reports the duplicate ratio, a log2-bucketed reuse-distance histogram, the fraction of sequential index steps, and the degree skew, all computed exactly.
- [x] A tiny fixture graph with hand-computed values checks every feature.
- [x] `swdb profile` includes these features as metrics, naming the tool, and fills the input's edge count with a measured value.

## Comments

## Answer

Resolved 2026-09-22.

- `tools/index_features/index_features.cc` builds serially with
  `c++ -std=c++11 -O3 -Wall -I apps/gapbs/src ...` on the Mac and with g++ on mbit10,
  regenerates the graph with gapbs's own Builder, and walks the index array in visit order.
- Exact features: duplicate ratio, log2 reuse-distance histogram (elements and 64-byte
  lines), sequential and same-line fractions, degree mean/max/Gini/CV (Fenwick tree,
  O(L log L)); scale 22 Kronecker: L = 128,311,450 in 31 s, 1.2 GB.
- `tests/test_index_features.py`: tiny hand-computed fixture (every feature), a
  brute-force cross-check on `-g 10`, bad-argument cases; 15 tests.
- `swdb profile` records them as `measured` metrics naming the tool, and fills the
  input's measured vertex and edge counts (cross-checked with the benchmark's own
  "Graph has" line).
- Caveat: Kronecker vertex IDs depend on the C++ standard library (`std::shuffle`), so the
  profiler builds the extractor with the kernel's own compiler.
