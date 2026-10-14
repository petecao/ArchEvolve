# 45 — Per-thread lowering

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 24, 44
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Concurrency" (one thread at a time, memory model, OpenMP), "Formal-half language and the C++ subset" (sharing classes per candidate, OpenMP constructs, standard-library model), "Modules" (C lowering tool), "Verifier lineup and order", "Testing Decisions" (seam 1), S1); decisions: [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md)
**Time estimate:** about 1 week

**What to build:** For a proof unit with an OpenMP parallel region, the C lowering emits the program of
one symbolic thread t of N, and WP proves it through `swdb prove`. The build sets `NUM_CORES` = N, and
team size = N is proven against the run-time guard. The lowering proposes a sharing class per array
per barrier interval; WP proves each. A plain access to a shared-action location becomes a race
obligation. Reads that race by design are history reads. Uniform control is proven by a two-copy
product, and chunk splits computed from the thread id are proven to cover the frontier exactly once.
The OpenMP runtime is one trusted-tool entry. An OpenMP fixture shows the whole path: proven when
correct, not proven for each planted break. Growing a shared `std::vector` outside `critical` is a
WP obligation that reads not proven; WP never refutes, so its refutation is 46's.

## Acceptance

- [ ] On the OpenMP fixture, `swdb prove` with WP proves the per-thread program for symbolic N. The
      proof record reads thread count "unbounded" (symbolic N, `NUM_CORES` = N). `swdb validate` and
      `swdb build` accept it; fixture records carry `contract_fixture` evidence.
- [ ] The team-size obligation (team size = N) is discharged from the run-time guard and named in the
      record.
- [ ] The lowering proposes one sharing class per array per barrier interval (memory allocated inside
      the region is thread-owned), and WP proves each one. A fixture variant with a wrong proposal
      leaves that obligation not proven; it never passes.
- [ ] Thread-owned memory includes ranges, tiles and registers: WP proves them disjoint for t != t'.
      A variant where two threads share one tile leaves that obligation not proven.
- [ ] Each atomic block or `critical` section is proven to implement one shared action of a kind its
      contract allows. A plain access to a shared-action location becomes a race obligation; a variant
      with a plain store there leaves it not proven (WP never refutes; the race's refutation is
      ticket 46's).
- [ ] Reads the contract marks as history reads are modeled as history reads; a CAS is a sequentially
      consistent read-modify-write (15 item 3). Shown both ways: a re-read after a failed claim CAS
      proves it sees the winner's value; a variant whose postcondition needs a history read to
      return the newest value anywhere leaves that goal not proven.
- [ ] Uniform control: a two-copy product proves that any two threads evaluate every condition guarding
      a barrier or worksharing construct equally. A variant with a thread-dependent guard leaves it not
      proven.
- [ ] Chunk splits computed from the thread id are proven to cover the frontier exactly once. A variant
      with two chunks overlapping by one leaves it not proven.
- [ ] Each per-candidate obligation is named after the composition-theorem hypothesis it discharges
      (16 item 4). Every hypothesis that ticket 41's table maps to a per-candidate obligation is
      emitted.
- [ ] Shared `std::vector` growth (16 item 7; the WP side, from 25): on a fixture that grows a
      shared vector inside a parallel region, outside `critical`, the growth is a write to the vector
      under its sharing class (25's `assigns`), and WP leaves that obligation not proven. The record
      names it as the obligation not proven. WP never refutes; the refutation is ticket 46's (CIVL,
      k ≥ 2).
- [ ] The record's assumption set lists the OpenMP runtime (trusted tool, OpenMP 5.2), RC11 (platform
      choice, 26 item 4) and the composition theorem (kind written proof), each with one plain
      sentence.

## Notes

- **Not in this ticket:** 21 — C lowering and WP adapter (A2 tracer); 24 — C++ subset widening (the
  OpenMP constructs themselves); 44 — Shared-action kinds and commutativity lemmas; 46 — CIVL adapter
  (the history-read encoding for CIVL, and refutations, including shared `std::vector` growth);
  47 — GenMC adapter and agreement (the pthreads harness); 48 — Concurrency negative controls (the
  BFS controls); 37 — The proof-hint loop;
  49 — Peter's race repaired; A4 exit (the repaired BFS unit through the loop); 25 — std::vector and
  std::pair models (the model itself); 42 — Rocq: composition theorem proof (`swdb candidate-level`
  dropping the theorem's entry once the Rocq-checked record counts; this record is never rewritten).
- 25 (the model) is upstream through 44, 31 and 30, so the shared-growth obligation runs here.
- "Team-size guard removed" is not a control: it changes no verdict, since team size = `NUM_CORES` is a
  precondition (15 item 12).
- The lowering stays our deterministic tool, never an LLM, and a trusted-tool entry; its naming rules
  are versioned ([11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) item 3; 16 item 3).
- Assumption (not decided in the map): the fixture is written for this test, not taken from GAPBS. It
  holds a parallel region with static and dynamic `omp for`, `critical`, a barrier, a claim CAS, a
  relaxed atomic load, a chunk split from the thread id and the run-time team-size guard.
- Assumption (not decided in the map): the fixture is proven with WP alone, or with hints of provenance
  "human" (it is a fixture, not a candidate artifact). The per-thread program first runs through the
  proof-hint loop in ticket 49.
- Mac: one WP job at a time under the ~8 GB RSS watchdog.
