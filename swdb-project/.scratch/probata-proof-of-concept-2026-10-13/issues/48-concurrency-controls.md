# 48 — Concurrency negative controls

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 33, 47, 60
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Concurrency" (negative controls), "Bounds" (minimum bounds per rung), "Proven once vs per candidate" ("With the method" row), "Records and levels", "Testing Decisions" (seam 1, method parts), S12, O6); decisions: [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md), [10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md) (item 2)
**Time estimate:** about 4 days

**What to build:** The eight concurrency negative controls run on the BFS read offload through
`swdb prove`. Seven must be refuted by CIVL or GenMC; one must prove. The controls apply to Peter's
code as written, which races, so each counts only the violation its break causes (S12). From them
and the contract's own multi-thread control (`shared_context`), the minimum-bounds script derives the
multi-thread minimum bounds, packed for Yan-Ru's review at ticket 59. A control with the wrong
verdict voids the method version. This is the method's evidence that its concurrency setup sees the
bugs it claims to.

## Acceptance

- [ ] Each must-refute control is refuted by CIVL or GenMC, with the violation at the control's break:
      1. `wait_ready(tile3)` outside `critical`;
      2. `critical` dropped;
      3. one tile shared by all threads;
      4. two chunks overlapping by one;
      5. the barrier before the fallback path dropped;
      6. a plain store to a shared-action location;
      7. thread-dependent worksharing (`accelerate` made thread-dependent, so threads reach different
         `omp for` loops).
- [ ] The must-prove control (read, failed CAS, re-read sees the winner's value) passes: CIVL at
      k = 3 and GenMC report no violation beyond those the base also has (see the assumption below).
- [ ] CIVL and GenMC agree on all eight (ticket 47's rule).
- [ ] Each control's verdict is a method-part proof record. `swdb validate` and `swdb build` accept them.
- [ ] **Base (S12).** The controls apply to Peter's read offload as written, which races (its plain
      store, 15 item 10). A control counts only the violation its break causes (glossary, "negative
      control"). The unmutated base's verdict is recorded beside the controls; a control whose only
      violation is one the base also has does not count as refuted.
- [ ] **Replay (ticket 60).** Every refutation here carries 60's replay label. A data race reads
      "undefined behavior (no strict-layer replay)" and the batch goes on (O6). Any other violation
      reads reproduced, proof semantics only, or not reproduced; "not reproduced" stops the batch.
- [ ] The contract's own multi-thread negative control, `shared_context` (needs threads ≥ 2, 19 item
      1; ticket 32 leaves it here), is refuted by CIVL or GenMC as a contract-proof part. A proving
      `shared_context` voids the contract proof (10 item 2).
- [ ] The script derives the multi-thread minimum bounds (thread count and input bounds) on the
      reference instance, growing one dimension at a time until every multi-thread control is refuted
      (the seven and `shared_context`, the controls labeled for multi-thread runs, 19 item 1).
      By our reading the thread minimum is k = 2 (19 item 6); the result is recorded either way, as a
      contract-proof part.
- [ ] **Review packet for ticket 59.** The multi-thread minimum bounds, the reference instance they
      pin, the record IDs of the control verdicts they rest on, and the base's own verdict. Yan-Ru
      approves the minimum at promotion (19 item 1); 59 carries the packet into the freeze review.
- [ ] The wrong-verdict rule, tested with the scripted adapter: a must-refute control that proves, and
      the must-prove control refuted, each stop the batch and void the method version.

## Notes

- **Not in this ticket:** 33 — Minimum-bounds script and A2 exit (the script and the single-thread
  minimum); 46 — CIVL adapter; 47 — GenMC adapter and agreement; 29 — Proof-semantics checks (the
  semantics negative controls); 32 — BFS contract proof (the single-thread contract controls);
  49 — Peter's race repaired; A4 exit (the A4 exit check, and re-deriving this minimum on the repaired
  code under S5); 60 — Strict-layer replay and whole-kernel reproduction (the replay labels this
  ticket reads).
- Assumption (not decided in the map): "must prove" means neither CIVL nor GenMC finds a violation of
  the control's own, since 15 item 12 names CIVL or GenMC for this check. S12 speaks only of refuted
  controls, but on the racy base no run is clean, so violations the base also has are set aside here
  too. WP on the per-thread program may run and be recorded, but it is not part of the verdict.
- Flag for Yan-Ru. Assumption (not decided in the map): the base's race may hide the must-prove
  control's own property, so a race-free base might be safer for this one control. Not built here:
  all eight controls run on Peter's code as written (S12).
- Assumption (not decided in the map): when 49 re-derives the multi-thread minimum on the repaired
  code (S5), its values replace this packet's in 59's review.
- How a void method version reads: ticket 10's assumption (a method part recorded as failed voids that
  version; every record pinning it stops counting). A control with the wrong verdict is recorded as
  such a failed method part.
- Do not add the two rejected controls, "CAS recheck removed" and "team-size guard removed" (15 item 12).
- Mac: one verifier job at a time under the ~8 GB RSS watchdog. The script's runs can pass 30 minutes:
  post the 30-minute heartbeat (LR-07).
