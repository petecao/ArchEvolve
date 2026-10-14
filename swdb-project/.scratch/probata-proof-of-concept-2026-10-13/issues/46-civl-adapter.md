# 46 — CIVL adapter

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 03, 25, 45, 60
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Verifier lineup and order" (threads > 1, failure classes), "Concurrency", "Bounds" (minimum bounds, 15 minutes per job), "Records and levels" (verifier scratch), "Testing Decisions" (seam 1), S1, S3, S6, S8, O4, O6); decisions: [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md), [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (item 10, replay), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) (items 5, 10), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) (item 7, shared `std::vector` growth)
**Time estimate:** about 4 days

**What to build:** CIVL 1.23 fills the bounded-verifier role for threads > 1, behind the verifier
adapter interface of `swdb prove`. The C lowering emits the history-read encoding CIVL needs, since
CIVL interleaves threads under sequential consistency (our reading, confirmed here). CIVL runs with
`-ompLoopDecomp=ALL` and race checking on, at k = 3 threads (minimum k = 2). A clean run gives proven
within bounds, threads ≤ k. A violation gives a refutation with its trace. Every verdict records the
CIVL version, k, input bounds, the encoding and the solver. CIVL also gives the refutation of shared
`std::vector` growth outside `critical` that WP in 45 can only leave not proven.

## Acceptance

- [ ] 07's safe smoke program proves and its seeded bug refutes through `swdb prove` with the CIVL
      adapter.
- [ ] A race-free OpenMP fixture (ticket 45's) is proven within bounds, threads ≤ 3. `swdb candidate-level`
      places it on the threads ≤ k sub-rung, above threads = 1.
- [ ] A fixture with a plain store to a shared-action location is refuted. Its proof record holds CIVL's
      trace inline, naming the racing accesses.
- [ ] The encoding is needed and works (15 item 9 left it "to confirm"): on a fixture whose bug needs a
      relaxed load that returns an older value, CIVL without the history-read encoding finds nothing,
      and with it refutes.
- [ ] Shared `std::vector` growth (16 item 7): with 25's model in the C lowering, a fixture that grows
      a shared vector inside a parallel region, outside `critical`, is refuted at k ≥ 2 (run at k = 2
      and k = 3), with the trace inline naming the racing accesses. The same growth inside
      `critical` is not refuted.
- [ ] Every race refutation here (the plain store, the shared-vector growth) carries ticket 60's label
      "undefined behavior (no strict-layer replay)" (O6): its record marks the violation as a data
      race, the refutation counts and the batch goes on. "Bug" still needs 60's whole-kernel
      reproduction (a real input plus a schedule).
- [ ] Each verdict records the CIVL version, k, input bounds, `-ompLoopDecomp=ALL`, race checking on,
      the memory-model encoding (with its version) and the solver. `swdb validate` and `swdb build`
      accept the records.
- [ ] A run at k = 1, or below the multi-thread minimum input bounds, gives "bounded check below
      minimum" and no level.
- [ ] A run past the 15-minute budget gives "not proven", class timeout. It never retries at smaller
      bounds, and the record carries no refutation, so it does not block WP (S6).
- [ ] **Failure classes.** Every CIVL failure maps to a class on ticket 11's list; an unlisted one
      stops the batch. Each class CIVL can report gets its handler here (11 item 9: extend the
      lowering or the subset; fix the adapter; watchdog and rerun with more memory; minimal
      reproduction) and at least one corpus case: a small input that makes CIVL report that class,
      kept in the adapters' regression corpus. Corpus cases run in the normal test workflow and check
      the recorded class (LR-04). Each diagnosed CIVL failure joins the corpus.
- [ ] CIVL's work folders are deleted when the job ends, and no record names them.
- [ ] Tests that need CIVL skip cleanly when it is missing. On the Mac, one job at a time under the
      ~8 GB RSS watchdog, with the JVM heap set inside that cap.

## Notes

- **Not in this ticket:** 45 — Per-thread lowering (the WP per-thread program); 47 — GenMC adapter and
  agreement; 48 — Concurrency negative controls (the BFS controls, and the multi-thread minimum bounds
  from the script); 14 — Bounded gate in the campaign; 13 — Counterexample-guided repair (consumes the
  trace); 36 — Proof setup check and verdict reading (CIVL's settings join its frozen flags);
  11 — Method-version file and failure classes (holds the CIVL settings and the class list);
  60 — Strict-layer replay and whole-kernel reproduction (builds the replay labels, O6's among them,
  and the reproduction record); 25 — std::vector and std::pair models (the model and its `assigns`
  for growth members).
- Assumption (not decided in the map): the shared-growth fixture is written for this test (threads of
  one region `push_back` onto one shared vector), not taken from GAPBS. CIVL runs the model's C
  functions as the C lowering emits them, so the race shows on the vector struct's fields or buffer.
- Replay labels (O6): a data race is undefined behavior, not a strict-layer rule, so a race
  refutation reads "undefined behavior (no strict-layer replay)" instead of "not reproduced".
- Assumption (not decided in the map): which listed classes CIVL can report is found while building
  the adapter and listed in this ticket's Answer. Expected at least: parse error, unsupported
  construct, timeout, out of memory (the JVM heap), tool crash, below minimum bounds.
- Assumption (not decided in the map): until ticket 48 derives the multi-thread minimum, fixture tests
  use minimum bounds declared by the fixture. A real candidate artifact without one gets the skip
  reason "no minimum bounds".
- k starts at 3 and is calibrated like the hint budgets, then frozen with the method version (15 item 9);
  the method-version file lists it among its budgets (S8).
- A0 risk: CIVL needs a JDK (installed by ticket 03). If CIVL will not run, GenMC alone refutes,
  labeled, and the threads ≤ k rung stays unavailable until CIVL runs (O4).
