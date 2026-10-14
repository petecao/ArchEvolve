# 41 — Rocq: composition theorem statement and definitions

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
**Blocked by:** 09
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Concurrency" (composition theorem, shared-action kinds, memory model, OpenMP), "Formal-half language and the C++ subset" (sharing classes, YAML frame), "DX100 proof semantics" (reduction lemma, hazards), "Modules" (Rocq development), "What a proven verdict asserts" (assumption set, seven kinds), "Proof-of-concept plan" (Rocq side track), S9); decisions: [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md), [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md)
**Time estimate:** about 4 days plus Yan-Ru's review

**What to build:** Codex writes, in Rocq, two statements and the definitions they need: the parallel
composition theorem and the DX100 reduction lemma. Yan-Ru then reviews and approves only these, in
one review before the shared Rocq box (S9), a human step recorded in this ticket. The theorem says:
if each thread of a parallel region is proven alone, and touches shared memory only through shared
actions within their sharing classes, then every run ends as some serial order of those shared
actions would. Shared-action kinds and sharing classes are closed constructors. Each hypothesis is
exactly one per-candidate WP obligation or one assumption entry. The lemma says: if the code is
hazard-free, every timing gem5 allows gives the same values as finish-at-issue (12 item 2). The
theorem fits on about 1-2 pages, so the review is short. The proofs are tickets 42 and 43.

## Acceptance

- [ ] Both statements and their definitions type-check under the Rocq version ticket 03 installed
      (version recorded). Both proofs are left open and visibly marked open. Nothing else is
      admitted, and no axiom is declared.
- [ ] Shared-action kinds are a closed enumeration with exactly five constructors: claim (write-once
      CAS), min-update, atomic add or OR, OpenMP reduction, queue reserve.
- [ ] Sharing classes are a closed enumeration with exactly four constructors: read-only,
      thread-owned, changed only through shared actions, lock-protected. A class is assigned per array
      per barrier interval.
- [ ] The definitions state 15 item 3's memory model: a history read returns a value the location
      already held, never older than the newest write the reading thread has seen (its own accesses,
      and writes ordered before it by a barrier, `critical` or a CAS); a CAS is a sequentially
      consistent read-modify-write; a plain access to a location changed only through shared actions
      is a race. Other threads' DX100 commands (15 item 7): their reads meet thread t as history
      reads; their writes are allowed only inside `critical` or into the issuing thread's own memory.
- [ ] The conclusion holds for a symbolic thread count N with distinct thread ids 0 to N-1: every run
      ends as some serial order of the shared actions would.
- [ ] A hypothesis table beside the Rocq files maps every hypothesis to exactly one per-candidate WP
      obligation or exactly one assumption entry (kind and plain sentence). No hypothesis maps to both
      or to neither. The table covers at least:
      - the per-candidate obligations of 15 items 2 and 4: accesses fit their sharing classes; each
        atomic block or `critical` section implements one shared action; owned ranges, tiles and
        registers are disjoint for t != t'; chunk splits cover the frontier exactly once; uniform
        control; team size = N;
      - the OpenMP runtime entry (trusted tool, citing OpenMP 5.2);
      - the RC11 entry (platform choice, per 26 item 4).
- [ ] Each hypothesis has a stable name, so each per-candidate WP obligation can be named after the
      hypothesis it discharges (16 item 4).
- [ ] **DX100 reduction lemma statement (S9).** The lemma is stated in the same development. Its
      definitions model what 12 item 2 names: one core's commands dispatch in program order but may finish out
      of order; the tile dispatch stall; the memory-region stall (across all cores of one instance,
      12 item 4); each command finishes at some point before its covering wait. Each definition
      cites the proof-semantics rule it models and that rule's gem5 citation.
- [ ] "Hazard-free" is the proof semantics' own hazard definition (12 items 3-5): no unready read,
      and no CPU write to a tile an unfinished command reads; no same-thread overlap with an
      unfinished command's footprint where either side writes; no other-thread overlap with an
      unfinished DX100 write; no use of a tile or register the thread does not own. Device against
      device is not a hazard: the region stall orders it, and the definitions model that stall.
- [ ] The theorem's statement plus definitions fit in about 2 printed pages.
- [ ] Yan-Ru's approval of both statements is recorded in this ticket's Answer: date and time ET, and
      the content hash of each statement's reviewed files. Codex's provider pin is recorded with the
      draft.

## Notes

- **Not in this ticket:** 42 — Rocq: composition theorem proof (the proof and its proof record);
  43 — Rocq: DX100 reduction lemma (the lemma's proof and proof record; its statement is written and
  reviewed here); 44 — Shared-action kinds and
  commutativity lemmas (the WP lemmas, and the script that checks the YAML kinds, sharing classes and
  Rocq constructors agree); 45 — Per-thread lowering (emits the obligations named after these
  hypotheses); 11 — Method-version file and failure classes.
- The commutativity lemmas are not hypotheses of this theorem. They feed each contract's
  order-independence lemma, which turns "some serial order" into the unit relation (15 item 2).
- Assumption (not decided in the map): the Rocq statement ends at "some serial order of the shared
  actions". It is joined with a contract's order-independence lemma (a WP proof) through the proof
  records' dependencies, not inside Rocq. Yan-Ru may ask for a Rocq corollary at review.
- The method-version file lists the Rocq development (S8). Assumption (not decided in the map): it is
  versioned library content, pinned there by content hash.
- Yan-Ru's one review, of both statements, comes before the box: one 2-week box then covers 42 and 43
  together (S9).
- Assumption (not decided in the map): any change to an approved statement or its definitions needs
  a new approval. Tickets 42 and 43 each check that they prove the approved hash.
- Assumption (not decided in the map): this ticket waits only on 09, so the lemma's statement is
  written from 12 items 2-5, not from a built proof-semantics version. 43's rule-coverage assumption
  checks it against the version 43 pins.
- Assumption (not decided in the map): 15 item 7 calls other threads' DX100 commands shared actions,
  but item 5's closed list has no DX100 kind. This ticket models them through history reads and the
  thread-owned and lock-protected classes, not as a sixth constructor. Yan-Ru confirms at review.
- Provider: Codex, pin `gpt-5.6-sol`, effort `xhigh` ([23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md) item 7). Yan-Ru reviews only the statements and definitions,
  never the proofs (15 item 8; S9).
- The Rocq track starts after the spike verdict, so the spike's stop rule cannot waste it
  ([27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) item 4).
- Mac: Rocq runs as one job at a time under the ~8 GB RSS watchdog.
