# 37 — The proof-hint loop

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 12, 33, 34, 35, 36
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-hint loop": Seeds, Budget, Three checks; "Solution": one candidate artifact's path, step 4; "Verifier lineup and order": solver portfolio, failure classes, order per candidate; "Records and levels": where things live; "Testing Decisions", seams 1 and 2; user stories 19, 21, 32, 33, 34, 58; S1, S3, S6, S10, S13, O7); decisions: [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (items 3, 8, 9, 10, 11), [25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md) (items 1, 2), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) (item 5, where evidence lives)
**Time estimate:** about 1 week

**What to build:** `swdb prove` runs the proof-hint loop on one proof unit and writes one proof
record. Order: WP with no hints; then seeds as round 0; then hint rounds, each one provider call to
the `proof_hinting` role, with rejection reasons and failing goals fed back. Seeds come from the
contract proof and from earlier proven candidate artifacts of the same contract; failing seeds are
dropped Houdini-style, and seeds alone may prove the unit with no provider call. The budget is a set
of run-plan parameters (start: 10 rounds, 60 minutes, 30 s per solver; tokens recorded, not capped).
**Proven:** smoke tests, one greedy minimization pass, then the full record. **Not proven:** the
candidate artifact keeps its prior level, with failure class "hint budget spent", the unproven
goals and the last hint set; it is retried only when a pinned hash changes. The loop never changes
the candidate artifact's code.

## Acceptance

- [ ] **WP alone first.** A fixture unit WP proves with no hints is recorded proven with zero seeds
      and zero provider calls.
- [ ] **Trigger.** Only goals with failure class timeout or unknown enter seeds and hint rounds.
      Controls: a parse error, an unsupported construct and out of memory each go to their fixed
      handler, with no hint round. An unclassified failure stops the batch.
- [ ] **Seeds alone.** A fixture unit that seeds prove is recorded proven with zero provider calls.
      Each hint's provenance reads "seed" with its source. Control: seeds from a human-assisted
      contract proof also read "seed", and the step still counts as automatic (design S13).
- [ ] **Houdini drop.** In a seed set with one failing seed, that seed is dropped and the rest are
      kept. A seed whose anchor does not exist is not placed; it is shown to the agent as an
      example.
- [ ] **Rejected round.** A scripted provider returns a hint set the proof hint check rejects. The
      set uses up its round, never reaches WP, and the next workspace shows the rejection by rule.
      The record counts every rejection by rule.
- [ ] **Budget spent.** With a scripted provider that never proves, the loop stops at the run plan's
      round or wall-time limit. The record says not proven, failure class "hint budget spent", with
      the unproven goals and the last hint set. `swdb candidate-level` shows the prior level
      unchanged.
- [ ] **Retry rule.** With the same pins, a second request starts no new hint loop. After one pinned
      hash changes, it runs.
- [ ] **Smoke tests.** Smoke tests run on the final hinted unit before proven is recorded. Control
      on real WP: a fixture unit whose goals all prove but whose smoke test fails (contradictory
      preconditions, research 13 Q6) is never recorded proven. With the scripted adapter, a failed
      smoke goal on a round's hint set feeds "vacuous pass" back (assumption below).
- [ ] **Minimization.** On real WP, one greedy pass drops a redundant hint and keeps a proving
      subset. If the budget ends mid-pass, the record keeps the unminimized set.
- [ ] **Full record.** A proven record holds: per goal, the solver that proved it (Alt-Ergo, Z3 or
      CVC5) and its time; the hint-set hash, rounds, provider calls, tokens, wall time, provider kind
      and per-hint provenance; the run index and provider pin (ticket 12's run fields; design S10: a
      proof-hint run has no proposal to carry them). The final hint set is inline; earlier rounds' sets, logs and per-goal
      reports are named by path and sha256; verifier scratch is deleted. It passes `swdb validate`
      and `swdb build`. The candidate artifact's tree hash is the same before and after the job.

## Notes

- **Not in this ticket:** 12 — Proposal and promotion fields (the run fields and job block this
  record carries); 33 — Minimum-bounds script and A2 exit (A3 starts only after A2's exit
  check names a cause for every mismatch); 34 — proof_hinting role and workspace; 35 — Hint records,
  merger and proof hint check; 36 — Proof setup check and verdict reading (this loop calls all
  three); 16 — Post-campaign WP phase and budgets (fastest gain candidate artifact first,
  `provider_calls_proof`, seeds and WP alone once that cap is spent); 18 — ArchEvolve mode level
  and handoff block; 13 — Counterexample-guided repair (a refutation's counterexample never reaches this loop); 10 — Level
  rule; 38 — Calibration on the public C suites; 39 — BFS unit proven unbounded at one thread; A3
  exit; 40 — Bucketed-relaxation fixture; 45 — Per-thread lowering (its program for symbolic N runs
  through this loop later).
- **When WP runs** (S6): whenever the bounded rung did not refute. A bounded timeout or missing
  minimum bounds does not block it. A candidate artifact outside the C++ subset gets no hint loop
  (skip reason "outside the C++ subset"). With no contract proof, the loop has no contract seeds and
  still runs when the proof unit has a unit postcondition (design O7: a skip skips only the steps
  that need the missing piece).
- Round 0 makes no provider call; the 10 rounds are provider calls (map 13 item 11). The 60 minutes
  are loop wall time, verifier time included.
- Budget values are starting values. 38 measures the curve on the public C suites; 39 proposes the
  calibrated Mac values; the freeze is 59 — Method-version review and freeze. A changed value is a
  new run plan.
- **Seeds from a human-assisted contract proof (design S13, map 13 item 9):** they belong to the
  contract (reviewed at promotion) and keep provenance "seed" (with source) in a candidate
  artifact's record; the per-candidate step still counts as automatic. In the contract proof's own
  record those hints read "human" (map 13 item 12).
- Assumption (not decided in the map): seeds come only from records that still count (every pin
  matches) of the same contract, plus the contract proof's final hint set.
- Assumption (not decided in the map): a failed smoke test on a round's hint set counts as a
  failed round, with failure class "vacuous pass" fed back, and the loop goes on while budget
  remains.
- Assumption (not decided in the map): when the retry rule declines, `swdb prove` names the existing
  record and writes no new one, since no proof job ran.
- Mac: one real verifier job at a time under the ~8 GB RSS watchdog, the agent's wrapper runs
  included. Tests that need real WP skip cleanly when it is missing.
