# 32 — BFS contract proof

Created: 2026-10-13 22:17 ET
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 31
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("What a proven verdict asserts" (lifting lemma; harness `assume`s), "Proven once vs per candidate" (contract proof), "Verifier lineup and order", "Bounds", "Records and levels", S1, S2, S5); decisions: [09](../../formal-verification-2026-10-09/issues/09-what-proven-asserts.md), [10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md), [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md)
**Time estimate:** about 1 week

**What to build:** The `bfs_read_offload` contract gets the single-thread parts of its contract proof, each a proof record that every later proof of a BFS candidate artifact reuses. The reference instance is Peter's library code applied to the baseline. Parts: the reference instance meets the unit postcondition; the baseline meets it; two units that meet it satisfy the unit relation; the lifting lemma carries the unit relation to BFS's output relation; every formal-visible single-thread negative control is refuted with the same harness and summaries. Every harness `assume` is proven at real calls, including the widened `parent` precondition. End to end: `swdb candidate-level` reads these records as a contract proof at a recorded level, and a control that proves voids it. Per S5 these records hold for Peter's code as written; ticket 49 re-proves them on the repaired code.

## Acceptance

- [ ] **Reference instance meets the unit postcondition** at threads = 1: a contract-proof record with its level and its value per bound dimension.
- [ ] **The baseline meets the unit postcondition** at threads = 1 (the baseline's meaning is its single-thread run): a proof record.
- [ ] **The unit postcondition gives the unit relation.** Two units that meet it from the same starting state satisfy the unit relation: a proof record.
- [ ] **Lifting lemma for BFS** (map 09 item 6; map 11 item 7). WP on the C lowering of the driver loop, with the proof unit replaced by its contract and induction through a saved `Wp.induction` script replayed on every run, proves: if every call meets the unit relation, the run meets BFS's output relation (same reachable set and depths; parents may differ, each valid). If WP cannot close it, Rocq (in its own opam switch) is the fallback. Until one of them checks it, the lemma is an assumption entry of kind written proof.
- [ ] **Every harness `assume` proven at real calls** (map 09 item 10). In the lifting lemma, each proof-unit precondition is proven at each call: `parent` initialized before the call (L3's premise), the contract's runtime guards, and the `parent` value range widened to include the initializer's negative out-degree values. Negative control: a harness with the old `parent >= -1` assume leaves that call-site goal unproven.
- [ ] **Single-thread controls refuted** (map 10 item 2). Every formal-visible single-thread negative control (by map 19: `dropped_wait`, `read_before_wait`, `index_wrap`, `forged_frontier`, `dropped_continuation`, `chunk_off_by_one`, `skipped_cas_recheck`) is refuted with the same harness and summaries, at the hand-derived minimum bounds, on the C++ and on the C lowering, with agreeing verdicts.
- [ ] **A control that proves voids the contract proof.** Negative control: through `swdb candidate-level`, with a fixture controls record in which one control proves, a fixture candidate artifact that depends on this contract proof reads as certified.
- [ ] **Pinned.** Each record pins the reference instance code, the contract version from ticket 31, the baseline function, the reference semantics, the proof-semantics version, the method version, each summary with its proof record ID, and every build constant. Through `swdb candidate-level`, a changed pin (for example, a new summary version) makes the contract proof stop counting.
- [ ] **Hints on the record.** Any hints used (contract proofs may be human-assisted, map 10 item 8) are hint records with provenance (human or agent), kept inline in the proof record, inside the vocabulary of map 13 item 5.

## Notes

- **Not in this ticket:** 31 — Five-gate drafting and the new bfs_read_offload version (the formal halves and the unit postcondition). 33 — Minimum-bounds script and A2 exit (derives the minimum these controls run at; runs the A2 exit). 39 — BFS unit proven unbounded at one thread; A3 exit (a candidate artifact's own proof through the loop). 44 — Shared-action kinds and commutativity lemmas and 49 — Peter's race repaired; A4 exit (the order-independence lemma, the concurrency parts, and the S5 re-proof on the repaired code). 48 — Concurrency negative controls (`shared_context` and the concurrency controls).
- The known violation this ticket removes: the 08 prototype's harness assumes `parent[v] >= -1`, but the initializer writes the negative out-degree (map 09 item 10).
- Assumption (not decided in the map): the map fixes the tool only for the lifting lemma. The unit-postcondition parts aim for WP (every data dimension unbounded, threads = 1). A part that only the bounded verifier proves caps the contract proof at its bounds (map 10 item 5).
- Assumption (not decided in the map): 35 — Hint records, merger and proof hint check and 36 — Proof setup check and verdict reading do not block this ticket. The hints and setups used here are re-checked by them once they land (both are A3 tickets, so this is not part of ticket 33's A2 exit).
- Assumption (not decided in the map): the controls run at the hand-derived minimum (threads 1, lanes 2, chunk 2, frontier 2, vertices 3, edges 3). Ticket 33's script confirms or corrects it; a correction means a new controls record at the derived minimum (records never change).
- Assumption (not decided in the map): the "baseline meets it" part at threads = 1 is the baseline's whole meaning (map 11 item 10), so its threads = 1 does not cap the contract proof's thread dimension. Otherwise no BFS candidate artifact could reach proven unbounded. Confirm with Yan-Ru.
- Risk: WP's `Wp.induction` tactic left one subgoal unreached in tests (map 11 research), so the Rocq fallback may be needed.
- Risk (S5): Peter's code races at N > 1 as written. These records hold only at threads = 1. The repair changes the content hash, so ticket 49 makes them again.
- Mac: one real verifier job at a time under the ~8 GB RSS watchdog; keep at least 50 GB free. Record each large run's output destination, size budget and readers first (LR-06); post the 30-minute heartbeat for runs past 30 minutes (LR-07).
