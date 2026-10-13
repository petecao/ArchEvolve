# 15 — How do proofs cover concurrency for any thread count?

Created: 2026-10-13
**Type:** grilling
**Status:** ready-for-human
**Blocked by:** 11, 12
**Map:** `../map.md`

## Question

How do a contract proof and each candidate artifact's proof cover concurrency for any thread
count? Decide:

- what is proven once per rewrite contract (the order-independence lemma: every serial order of
  atomic blocks meets the unit relation; soundness of the reduction to a thread-indexed
  sequential program) and what per candidate artifact (tile and buffer ownership, race freedom,
  barrier alignment, exact chunk cover);
- how the C lowering emits the thread-indexed sequential program for a symbolic thread count N,
  and how relaxed atomic reads and the CAS are modeled in it;
- what the hand-written VerCors PVL model covers and how it is kept faithful to the code;
- how CIVL's bounds (team sizes 1..k) and GenMC's memory model are recorded in a verdict.

The method must be general: GAPBS `bc.cc:106-107` and `sssp.cc:157-160` use the same
"plain read, then CAS" pattern as BFS.

## Comments

- 2026-10-13: input from 11 (graduated from the map's "Concurrency phase" fog). Settled there:
  - **Claim** for every thread count N: race freedom outside atomics and critical sections;
    atomic critical sections, so a run equals some serial order of atomic blocks; every serial
    order meets the unit relation; per-thread tile ownership with no DX100 hazard; exact chunk
    cover.
  - **Thread count** = every N, built with `NUM_CORES` = N and run with N threads
    (`apps/dx100/benchmarks/gapbs/src/bfs.cc:62-63,142,195`); a contract precondition with a
    run-time guard.
  - **Methods:** (A) reduction proven in WP for symbolic N, the only one that sets the level;
    (C) CIVL 1.23 as refuter, GenMC second; (B) VerCors on a hand PVL model, BFS read offload
    only, sets no level, dropped first.
  - **Negative controls:** wait moved outside `critical`; `critical` dropped; one shared tile;
    overlapping chunks; barrier dropped.
  - **Baseline** = its single-thread run. Undefined behavior is a proof obligation; a racy
    candidate is refuted (provisional). The authors' `TDStepMAA` is refuted at threads > 1 (its
    fallback path races, `bfs.cc:205-210`).
  - Facts: [`../research/11-concurrency-verification.md`](../research/11-concurrency-verification.md).
- 2026-10-13: blocked by 12 because the proof needs the DX100 store inside `critical` to be
  complete and visible to other cores before the lock is released; ticket 12 decides that
  semantics.
- 2026-10-13 14:19 ET: input from 12 (now resolved, so this ticket is unblocked):
  - **Overlap rule** (12, item 4): a CPU access by another thread that overlaps an unfinished DX100
    command's footprint is allowed when DX100 only reads; the read returns some value the location
    held while the command ran, never older than the stores made before the command was issued.
    The contract must tolerate it (BFS read offload: the CAS recheck, L4); prove it here. When
    DX100 writes, the overlap is a hazard. Same-thread overlaps with a write are hazards.
  - **Tile ownership** is a proof obligation: the device does not enforce it (research 12).
  - **Store inside `critical`:** finishing before the lock is released is proven by the wait rule;
    the next thread's DX100 load seeing it is a cited rule plus two gem5-corner assumption entries;
    the CPU reads after `omp barrier` rest on the entry "no stale CPU copy survives a DX100 store"
    (owner Eric). One DX100 instance is an assumption entry. Details: 12, item 7.
  - **Peter's read offload races too:** it keeps the plain store `parent[v]=u` after a successful
    CAS (`library/dx100/bfs_read_offload.inc:53,63`) beside other threads' CAS and relaxed loads
    of the same `parent[v]`, the race class 11 found in the authors' fallback path
    (`apps/dx100/benchmarks/gapbs/src/bfs.cc:205-210`). Decide here what 01 decision 9.2
    ("should be proven") means at threads > 1.
