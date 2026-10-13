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
