# 63 — Scalable native BFS evaluator (v2) with a compiled structural verifier

Created: 2026-10-04 06:30 ET (by ticket 61's decision)
Updated: 2026-10-05 17:20 ET (tracker hygiene, code review: Blocked by line); 2026-10-04 08:15 ET (resolved)
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
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

## Answer

Resolved 2026-10-04 08:15 ET by the agent (commit 36e7544, branch `worktree-agent-afdaa95806fe8434d`, not pushed).

**Design.**
- `tools/bfs_native/bfs_verify.cc` (`swdb.bfs.structural.compiled.v2`): maps the registered SG file and an
  int32 little-endian parent file read-only; same checks, order and reason strings as `verify_parents`;
  prints the same verdict mapping; exit 3 (no verdict) on malformed input. The evaluator compiles it per
  evaluation from repository source with the host C++ compiler and `-std=c++11 -O2`, records source and
  binary SHA-256, and runs it as a separate process on every timed trial.
- `tools/bfs_native/driver_scalable.cc.in`: same ROI and timed `DOBFS` call as `driver.cc.in`; outside the
  ROI it maps the registered SG file (bounds-checked CSR copy) and writes `swdb.bfs.native.trial.v2` plus
  the parent file.
- `swdb/bfs_native_scalable.py`, branches in `swdb/bfs_native.py`, `bfs_protocol.py`, `bfs_native_pair.py`:
  evaluator `swdb.native.evaluator.scalable.v2` is selected only by a protocol pinning
  `settings.evaluator` (both identifiers pinned together) or an unprotocoled request naming it. The SG file
  is bound to its registration by SHA-256 before each execution and each check (registration already proved
  canonical equivalence with `sg_identity.cc`). Passed parent files are kept gzip-compressed (raw SHA-256
  retained); paired receipts re-run the evaluation's own compiled verifier on them.
- v1 is unchanged; existing protocols and records keep their meaning (no frozen protocol changed).
- Campaign files may set `protocol.evaluator`; `NativeAdapter` then freezes v2 protocols (driver hash,
  verifier v2) and plans 2 GiB per block.

**Limits.** At most 2^23 = 8,388,608 vertices, 2^28 = 268,435,456 directed edges, 3 GiB SG file. Driver heap
outside BFS: (n+1)*8 + m*4 bytes (about 0.55 GB at scale 22); verifier heap about 9 bytes per vertex.

**Tests.** `tests/test_bfs_native_scalable.py` (19 tests, Mac): differential verdict equality on five fixture
graphs (path, star, random undirected, random directed, two components), both SG widths, three sources each,
two distinct valid trees, named mutations (wrong parent, unreachable marked reached, cycle, source not its own
parent, wrong source, missing parent, wrong depth, out of range, below -1, short and long vectors) and random
single-entry corruption: every mutation is rejected by both, with identical reasons. Malformed SG files give no
verdict. The driver builds against the upstream and DX100 BFS sources (GCC, `-fopenmp`). An end-to-end
`evaluate-pair` and `compare-evaluations` under a v2 protocol passes; a changed retained parent file and an
incorrect candidate are rejected; mixed version pins are refused. `tests/test_extensa_targets.py` adds a v2
campaign freeze test. Related suites: 173 passed. Pre-existing failure, also on `yanrujhou_main`:
`test_bfs_acceptance_report.py::test_native_cells_report_real_ids_outcomes_and_unverified_raw_evidence`.

**x86_64 (mbit10, node 1 lease generations 514-515, 2026-10-04 08:06 ET, load1 1.41, commit 36e7544).** The
verifier and both baseline drivers build with g++ 13.3 (`-O3 -fopenmp` for drivers, `-O2` for the verifier).
Differential check: 492 verdicts agree with `verify_parents`, 470 of them rejections. Scale-22 source 0 (not
timing evidence): both baselines pass on both graphs (Kronecker 2,394,645 reachable; uniform 4,194,304); a
mutated vector is rejected; the verifier takes 2.5-3.6 s per trial. Output under
`/data/yanruj/EvolveSWDB_runs/t63-x86-check/` (mbit10).
