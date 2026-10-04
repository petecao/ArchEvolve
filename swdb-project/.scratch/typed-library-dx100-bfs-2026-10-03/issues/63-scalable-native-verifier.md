# 63 — Scalable native BFS evaluator (v2) with a compiled structural verifier

Created: 2026-10-04 06:30 ET (by ticket 61's decision)
**Type:** slice
**Status:** claimed
**Blocked by:** —
**Spec:** `../spec.md`; [design decisions](../extensa-design-2026-10-03.md) D3, D4; [61](61-native-scale22-protocol.md)

**What to build:** The native evaluator can time and verify BFS on the scale-22 graphs of D4 without a
Python adjacency or a text graph copy, under new evaluator and verifier versions.

## Acceptance

- [x] A compiled, trusted structural verifier over the registered SG files (mmap), with exactly the
  criterion of `swdb.bfs_native.verify_parents` (parent tree valid, depths consistent, every reachable
  vertex reached), the same check order and the same first-failure reasons.
- [x] New identifiers: evaluator `swdb.native.evaluator.scalable.v2`, verifier
  `swdb.bfs.structural.compiled.v2`. They are pinned together; v1 protocols and records are unchanged.
- [x] Limits sized for scale 22 and stated (below).
- [x] Differential tests: the compiled verifier and `verify_parents` agree on fixtures and on mutated
  parent vectors (wrong parent, unreachable marked reached, cycle, wrong source and more); both reject
  every mutation.
- [x] Built with `-std=c++11 -O2`, no `-ffast-math`; compiles on the Mac (arm64) and on mbit10 (x86_64).

## Comments

- 2026-10-04 06:30 ET: created and claimed by the agent implementing ticket 61's option 1.
