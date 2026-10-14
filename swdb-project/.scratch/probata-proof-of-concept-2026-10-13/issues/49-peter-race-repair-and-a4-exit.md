# 49 — Peter's race repaired; A4 exit

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 13, 39, 42, 48
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Concurrency" (repair, not hand fixes), "Refutation, repair and bugs", "Records and levels", "Proof-of-concept plan" (A4 exit check, overrun rule), S2, S5, O5, O6); decisions: [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md), [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (item 10), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) (items 3, 6)
**Time estimate:** about 1 week

**What to build:** Peter's read offload races at N > 1 as written. CIVL's race trace goes to
counterexample-guided repair, and the rewriting role produces the next version with 15 item 10's
general fix: a plain read of a shared-action location becomes a relaxed atomic load, and a redundant
plain store is removed. Peter's code races only through its plain store (15 item 10), so the
expected repair removes the store. A hand deletion is allowed only if the loop fails, labeled
hand-made. The bfs_read_offload contract proof is
then completed on the repaired library code, and every part proven earlier on the as-written code is
re-proven (S5). WP proves the repaired unit per thread for symbolic N. CIVL and GenMC also run at
N > 1 on the authors' `TDStepMAA` and Codex's frontier staging: each is refuted and reported as a
finding. The contract proof's review packet goes to ticket 59. This ticket closes stage A4.

## Acceptance

- [ ] Peter's read offload as written: proven at N = 1 (ticket 39's record) and refuted by CIVL at
      N > 1, with the race trace in its proof record. Reported as a finding. Its replay label (ticket
      60) reads "undefined behavior (no strict-layer replay)" and the batch goes on (O6).
- [ ] The authors' `TDStepMAA` and Codex's frontier staging, as written, each run CIVL and GenMC at
      N > 1 (design spec, "Concurrency"; 15 item 10). Each is refuted, with its race trace in its
      proof record and the replay label above, and reported as a finding in this ticket's Answer.
      For frontier staging this is a separate finding run at the BFS read offload's multi-thread
      minimum bounds (assumption below), reported apart. It is not the bounded rung O7 skips (no
      contract proof) and sets no level (flagged note below).
- [ ] Counterexample-guided repair runs on Peter's trace with the rewriting role (Codex), at most 5
      rounds. The repaired proposal carries its repair lineage: the refuted candidate artifact, the
      proof record holding the counterexample, the round, and a reverted-repair flag that reads false
      (it still applies bfs_read_offload).
- [ ] If the loop fails within 5 rounds: a hand deletion of the store, labeled hand-made in its
      provenance, and never counted as a repair by the loop.
- [ ] The repaired candidate artifact certifies. At the minimum bounds no bounded rung refutes it
      (SAW at threads = 1, CIVL at threads ≤ 3, GenMC), and their verdicts agree.
- [ ] The contract proof is completed on the repaired library code (S5). The unit postcondition on the
      reference instance, the lifting lemma, the order-independence lemma, the contract's single- and
      multi-thread negative controls, the concurrency controls, and the single- and multi-thread
      minimum bounds are each re-proven
      or re-derived as new proof records pinning the new hashes. Old records stop counting; none is
      rewritten.
- [ ] WP proves the repaired unit per thread for symbolic N, through the proof-hint loop with no human
      step. Its proof record reads thread count "unbounded".
- [ ] `swdb candidate-level` computes the repaired candidate artifact's level from these records. Its
      assumption set shows the composition theorem as ticket 42 left it: no entry if Rocq-checked, a
      written-proof entry otherwise.
- [ ] **Review packet for ticket 59:** the bfs_read_offload contract proof on the repaired library
      code. Each part's proof record ID and hash (unit postcondition, lifting lemma, order-independence
      lemma, the contract's controls, the concurrency controls), the single- and multi-thread minimum
      bounds with the reference instance they pin, and the repaired code's promotion review. 59 carries
      it into the freeze review.
- [ ] **A4 exit** (design spec, "Proof-of-concept plan"): the seven must-refute concurrency controls
      refuted and the must-prove control proven; CIVL and GenMC agree; Peter's race repaired; WP proves
      the repaired unit per thread for symbolic N; Rocq checked or the written fallback done. This
      ticket's Answer cites the proof record IDs for each item. If it fails: a disagreement stops the
      batch (15 item 9).

## Notes

- **Not in this ticket:** 13 — Counterexample-guided repair (the loop itself); 31 — Five-gate drafting
  and the new bfs_read_offload version (the contract version whose L4 no longer requires the store);
  39 — BFS unit proven unbounded at one thread; A3 exit; 42 — Rocq: composition theorem proof;
  48 — Concurrency negative controls; 52 — Split the bundled read offload and 53 — Chained vs direct vs
  bundled; A5 exit; 58 — Mac verdicts reproduced on mbit10; 60 — Strict-layer replay and whole-kernel
  reproduction (the replay labels and the reproduction record).
- Assumption (not decided in the map; ticket 13 leaves it to this ticket): how the general race fix
  reaches the rewriting role. This ticket states it as one sentence in the repair prompt for race
  counterexamples, a prompt that belongs to the method version (26 item 3). It is not a deterministic
  rewrite: the glossary sends the counterexample to the rewriting role, and 15 item 11 names a hand
  deletion as the only fallback. Yan-Ru confirms before the run.
- Assumption (not decided in the map): the repaired code becomes the library's next version of Peter's
  read offload through the usual promotion review (15 item 11) before the contract proof is re-run, so
  it can serve as the reference instance. That review is a human step recorded in this ticket.
- A unit-level refutation is not a "bug". "Bug" needs a whole-kernel reproduction record (a real input
  plus a schedule; 60 builds it), computed on read.
- `TDStepMAA` and the frontier staging are refuted and reported only; neither is repaired here. The
  design repairs only Peter's read offload in A4, and the authors' code reaches the rewriting role only
  as the refuted candidate artifact under repair in the evaluation (O5).
- Assumption (not decided in the map): both run at the multi-thread minimum bounds of 48 and k = 3,
  as 06 runs `TDStepMAA` at Peter's bounds. Map 19 sets minimum bounds per contract and names none
  for these two.
- **Flag for Yan-Ru: frontier staging at N > 1.** Our reading of O7: its "no contract proof" skip
  covers only the bounded rung at the contract's minimum bounds, so frontier staging gets no
  bounded level (ticket 39). The CIVL/GenMC race check here is a separate finding run at the BFS
  read offload's multi-thread minimum bounds (the assumption above), reported apart in this
  ticket's Answer, and sets no level. Ticket 10 still reads its refuted record: the refuted flag
  (beside the level, not a level) is set and blocks a proven level for that hash, as for Peter's
  code as written.
- Messages about these findings to the DX100 authors or the team are out of scope (design spec, "Out
  of Scope").
- Overrun: A4 stops for a re-plan with Yan-Ru at 1.5x its ~4-week estimate.
- The proof-hint loop can run 60 minutes: post the 30-minute heartbeat (LR-07). Mac: one verifier job at
  a time under the ~8 GB RSS watchdog. Mac numbers are labeled; paper numbers come only from mbit10.
