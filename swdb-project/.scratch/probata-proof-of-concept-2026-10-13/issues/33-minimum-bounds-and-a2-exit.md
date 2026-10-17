# 33 — Minimum-bounds script and A2 exit

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 29, 32
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Bounds", "Proof-of-concept plan" (A2 exit check), "Modules" (minimum-bounds script and shape-split enumerator), "Further Notes" (risks), S1, S2, S4); decisions: [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md), [10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md)
**Time estimate:** about 3 days

**What to build:** Stage A2 closes. A script derives the `bfs_read_offload` contract's single-thread minimum bounds on the reference instance: it grows the bounds one dimension at a time until every formal-visible control is refuted, and it must land on the hand minimum. The minimum-bounds record joins the contract proof's content-hash set, so a changed control, harness or summary re-derives it. Then the A2 exit check runs on generated artifacts only. The shape-split enumerator is built only if lever 1 (per-call summaries) misses the 2-lane bar. Last, it prepares the single-thread minimum bounds' review packet for Yan-Ru's review at the freeze (59). Ticket 37 and the A3 tickets after it wait on this ticket, and they start only after every mismatch has a named cause.

## Acceptance

- [ ] **The script reproduces the hand minimum.** On the reference instance, with the contract proof's own harness, summaries and scaffold, the script returns threads 1, lanes 2, chunk 2, frontier 2, vertices 3, edges 3. It writes a contract-proof record (subject: minimum-bounds derivation). A different result is a mismatch to root-cause, never accepted as is.
- [ ] **Script negative controls.** At lanes 1, `skipped_cas_recheck` stays unrefuted (at one lane the hint is gathered again after the first claim, so the CAS never fails). With `skipped_cas_recheck` left out of the control set, the script's lanes value drops to 1.
- [ ] **Below the minimum, no level.** Through `swdb prove`, a bounded run below the minimum is recorded as "bounded check below minimum" (failure class below minimum bounds). Through `swdb candidate-level`, the candidate artifact stays certified.
- [ ] **Pinned.** The minimum-bounds record is in the contract proof's content-hash set. Through `swdb candidate-level`, changing a control, the harness or a summary makes the minimum and the contract proof stop counting until re-derived.
- [ ] **A2 exit: spike verdicts reproduced.** Generated artifacts only (SAWScript specs and C stubs made by our translators from the ACSL source; the generated C lowering; generated summaries; no hand stubs) reproduce every verdict of spikes (a)-(d): SAW reads clang 22 bitcode and keeps ghost state; 2 lanes at threads = 1 on Peter's read offload and the authors' `TDStepMAA`, every single-thread control refuted at the minimum; WP proves one read-offload unit at threads = 1 against its unit postcondition within 60 minutes; the sum lemmas and one unit of the synthetic CSR pull-sum fixture over reals.
- [ ] **A2 exit: summary forms agree (a re-check, not a new check).** The exit reads the three-form records of ticket 23 (fixture scenarios), ticket 29 (proof-semantics scenarios) and ticket 30 (each per-call `dxc_*` summary) for the current translator and proof-semantics versions, and each shows agreement of SAWScript, C stubs and ACSL. It runs no form check of its own.
- [ ] **A2 exit: controls refuted.** Every formal-visible single-thread control is refuted at the derived minimum.
- [ ] **A2 exit: 2 lanes under 15 minutes.** The safe 2-lane case (a build with tile capacity 2), on the subjects of spike (b), proves in under 15 minutes per bounded job on the Mac with generated summaries. If lever 1 meets the bar, the shape-split enumerator stays unbuilt. If not, lever 2: shape splitting, with its enumerator (a trusted-tool entry) and a count check against the closed-form count of shapes; a missing or failed job leaves the whole verdict "not proven". If that fails too, candidate artifacts stay certified and Yan-Ru re-plans.
- [ ] **A2 exit: semantics controls.** Every semantics negative control has its required verdict (S4; ticket 29's records for the current proof-semantics version).
- [ ] **A2 exit: every mismatch root-caused.** Each mismatch found above has a named cause, a fix or a failure class, and a regression-corpus entry. All are listed in the ticket's answer before 37 (and the A3 tickets after it) start.
- [ ] **Review packet for the freeze** (59). The derived single-thread minimum per bound dimension, the minimum-bounds record ID, the round order, the lower-by-one checks, the control set, and every mismatch with its cause. The agent hands it over; the review is Yan-Ru's, at the freeze.

## Notes

- **Not in this ticket:** 32 — BFS contract proof (the contract-proof parts). 23 — C-stub translator, fallbacks and check mode, 29 — Proof-semantics checks and 30 — Reference definitions, per-call summaries and new intrinsic versions (the three-form and semantics-control records this exit re-checks). 09 — Spike verdict (the verdicts reproduced here). 37 — The proof-hint loop and 39 — BFS unit proven unbounded at one thread; A3 exit (stage A3: 37 is blocked by this ticket, and 38-40 come after 37; 34-36 do not wait on it). 60 — Strict-layer replay and whole-kernel reproduction and 61 — SAW whole-function equivalence (bounded direct route): A2 tickets outside this exit check. 47 — GenMC adapter and agreement and 48 — Concurrency negative controls (the multi-thread rung's minimum: k = 2 by map 19 item 6, input bounds from the concurrency controls). 58 — Mac verdicts reproduced on mbit10.
- Yan-Ru approves the minimum at promotion (map 19 item 1), not in this ticket; this ticket prepares its review packet for his review at the freeze (59).
- Assumption (not decided in the map): the script starts every dimension at 1 and grows one dimension per round in a fixed order, recorded in the record. To show the result is a minimum, it also checks that lowering any one dimension by one leaves some control unrefuted.
- Assumption (not decided in the map): a timeout during derivation stops the derivation with failure class timeout. It never skips ahead or falls back to smaller bounds (map 19 item 8).
- Assumption (not decided in the map): spike (c)'s verdict is reproduced by replaying the spike's hint set as hint records on the generated C lowering, re-anchored, with no new provider run. The proof-hint loop is A3.
- Assumption (not decided in the map): if ticket 09 moved a role to its fallback tool, this exit uses that tool.
- Risk: the 2-lane bar is the scaling hypothesis Extensa's gates failed (map 10 item 9). There is no 1-lane fallback: one lane cannot see `skipped_cas_recheck`.
- Overrun rule: A2 is about 6 weeks. At 1.5 times that, stop for a re-plan with Yan-Ru.
- Mac: one real verifier job at a time under the ~8 GB RSS watchdog; keep at least 50 GB free; check that LLVM 22 still works after any Homebrew change. Record each large run's output destination, size budget and readers first (LR-06); post the 30-minute heartbeat for runs past 30 minutes (LR-07).
- Assumption (not decided in the map): 35 (the hint merger) is not upstream. For the A2 exit, the spike's hints are placed at 21's anchors by hand, kept as hint records with provenance, and re-checked by 35's proof hint check once it lands (not part of the A2 exit).

## Later changes
- 2026-10-14 13:19 ET (Yan-Ru accepted ticket 09's A2 changes): the A2 exit reproduces the 14 CBMC verdicts of the 06 continuation (2 units + 12 controls) with generated stubs and lowering.
