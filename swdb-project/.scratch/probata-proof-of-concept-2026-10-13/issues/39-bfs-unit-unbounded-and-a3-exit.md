# 39 — BFS unit proven unbounded at one thread; A3 exit

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 33, 37, 38, 40
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-of-concept plan": A3 row and exit check; "Evaluation design": RQ3, baselines, BFS extras; "Proof-hint loop"; "Solution": thread count is always a bound dimension; "Refutation, repair and bugs": the authors' code; O1; S5; S13; O7); decisions: [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (items 9, 10, 11), [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md) (items 6, 7), [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md) (item 2 and Later changes), [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) (item 5 and Later changes, as O1 decides), [25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md) (item 1, skip rule), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) (items 5, 6)
**Time estimate:** about 1 week

**What to build:** The proof-hint loop proves the BFS read-offload proof unit unbounded at
threads = 1, with no human step. The other BFS candidate artifacts go through the same loop:
Codex's frontier staging, and the authors' `TDStepMAA` as a direct proof (spec O1). The RQ3
both-ways BFS run is recorded: each candidate artifact with and without the contract, at equal
budget. The three checks reject every planted bad hint on the BFS unit. This ticket owns the
calibrated Mac budget proposal, from 38's curve and the BFS results. Then the A3 exit check runs,
reading 38 and 40. If it fails, Yan-Ru re-plans.

## Acceptance

- [ ] **BFS unit proven.** `swdb prove` on Peter's read-offload candidate artifact (contract
      `bfs_read_offload`) gives a proof record with WP's verdict proven, thread count 1 and every
      other bound dimension unbounded. Seeds come from the contract proof (ticket 32).
- [ ] **No human step.** The record's hint provenance holds only "seed" (with source) and "agent".
      Seeds from the human-assisted contract proof keep provenance "seed", and the step still counts
      as automatic (design S13). No hand edit, hand hint or manual rerun happens in the job.
- [ ] **Level on read.** `swdb candidate-level` shows Peter's candidate artifact at proven within
      bounds, threads = 1 (thread count is always a dimension), with the proof record ID.
- [ ] **Other BFS candidate artifacts.** Codex's frontier staging and the authors' `TDStepMAA` each
      leave a proof record. Codex's frontier staging has no contract proof, so it skips only what
      needs one (contract seeds, the contract's minimum bounds, the bounded rung at those bounds) and
      runs route-1 WP when its proof unit has a unit postcondition (design O7). It gets no bounded
      level. Ticket 49's CIVL/GenMC race check on it at N > 1 is a separate finding, not this
      skipped rung (flagged note below). `TDStepMAA`'s record reads "direct proof, no
      matching contract: <verdict>"; its level stays what certification gives; it is reported apart
      and never competes.
- [ ] **RQ3 both-ways run.** For each BFS candidate artifact: one arm with the contract (formal
      halves, contract-proof seeds) and one without (the design's no-contract baseline: same loop,
      same budget, route 1 against the unit postcondition, no formal halves, no seeds). Codex's
      frontier staging has no contract-proof seeds in either arm (O7). `TDStepMAA` matches no
      contract (assumption below), so it has only the no-contract arm. Per arm: verdict, rounds,
      provider calls, tokens, wall time.
- [ ] **Planted bad hints.** A scripted provider feeds ticket 35's planted bad hints into the loop on
      the BFS unit. Each is stopped by its check (proof hint check, proof setup check or verdict
      reading) and recorded by rule. None yields a proven record.
- [ ] **Calibrated Mac budget proposal (owned here).** From 38's suite curve and escape-hatch report
      plus the BFS loop results: one set of proposed values (rounds, loop wall time, per-solver
      timeout), each with the part of the curve that supports it, labeled Mac and recorded as
      "calibrated, not frozen". 59 freezes them; 58 recalibrates on mbit10.
- [ ] **A3 exit check** (design spec): the loop proves the BFS read-offload unit unbounded at
      threads = 1 with no human step; it proves the bucketed-relaxation fixture with seeds (40's
      record); the three checks reject every planted bad hint; budgets calibrated (38's curve and
      the proposal above); the RQ3 BFS numbers recorded. Pass is written in this ticket's answer; a
      fail is a re-plan with Yan-Ru.
- [ ] **Mac rules held.** Output destination, size budget and readers recorded before the first run
      (LR-06). One real verifier job at a time under the ~8 GB RSS watchdog. At least 50 GB free
      throughout.

## Notes

- **Not in this ticket:** 33 — Minimum-bounds script and A2 exit; 32 — BFS contract proof (source of
  the seeds); 38 — Calibration on the public C suites (the curve and escape-hatch report the
  budget proposal reads); 40 — Bucketed-relaxation fixture (the fixture verdict this exit check
  reads); 13 — Counterexample-guided repair; 49 — Peter's race
  repaired; A4 exit (threads > 1); 53 — Chained vs direct vs bundled; A5 exit (route 3); 58 — Mac
  verdicts reproduced on mbit10; evaluation 08 — RQ3: what a contract buys (the held-out RQ3).
- **Blockers:** 38 and 40 block this ticket, so the budget proposal and the A3 exit check read their
  finished results.
- **No speed claim** that contracts make per-candidate proofs faster unless this run shows a gap
  (map 27 item 6).
- **Three-part RQ3 gap** (map 23 Later changes): seeds; route 3 vs route 1 time; refutations only
  the bounded rung gives. Route 3 waits for 53. Assumption (not decided in the map): this run
  reports the parts it can measure and labels route 3 "not measured in A3".
- **S5:** these records pin Peter's library code as written. The contract proof is completed in A4
  on the repaired code, so they stop counting then and are re-proven there.
- **Codex's frontier staging (design O7):** it applies another contract
  (`bfs_tdstep_frontier_staging`, a performance contract outside the initial catalog, map 17 item
  11) whose contract proof this effort does not build. Skip reason "no contract proof" skips only
  the steps that need it: contract seeds, its minimum bounds and the bounded rung at those bounds.
  Route-1 WP still runs when its proof unit has a unit postcondition. O7 settles the reading for
  16 — Post-campaign WP phase and budgets too.
- **Flag for Yan-Ru: frontier staging at N > 1.** Our reading of O7: the skip covers only the
  bounded rung at the contract's minimum bounds, the run that would give a bounded level. Frontier
  staging has no contract proof, so it gets no bounded level. Ticket 49's CIVL/GenMC race check on
  it at N > 1 is a separate finding run, reported apart in 49, and sets no level. Assumption (not
  decided in the map): that check runs at the BFS read offload's multi-thread minimum bounds
  (ticket 48), since frontier staging has no minimum bounds of its own.
- Assumption (not decided in the map): that unit postcondition is the BFS unit postcondition. If it
  does not apply to frontier staging, record the skip and ask Yan-Ru.
- Assumption (not decided in the map): the authors' `TDStepMAA` matches no BFS rewrite contract (it
  bundles six reshapes before its offload, map 17), so O1 applies. If the contract-match check
  accepts it for `bfs_read_offload`, it is a candidate artifact like any other (design
  "Concurrency") and also gets the with-contract arm and a level.
- Assumption (not decided in the map): the no-contract arm's bounded half (SAW whole-function
  equivalence) is not part of this A3 run; record it as not run. 61 — SAW whole-function
  equivalence (bounded direct route) builds it, and this ticket does not wait for it.
- Peter's read offload may be the contract's own reference instance, so contract-proof seeds may
  prove it at round 0. The no-contract arm has no seeds and shows what the agent's rounds do alone.
- Assumption (not decided in the map): the rule that picks calibrated values from the curve is not
  set. Propose values and the reason; Yan-Ru confirms at 59.
- **Long job:** expected past 30 minutes. Schedule the 30-minute status heartbeat first (LR-07).
- **Overrun rule:** A3 is about 4 weeks. At 1.5× (about 6 weeks) the stage stops for a re-plan with
  Yan-Ru (design spec, "Proof-of-concept plan").
