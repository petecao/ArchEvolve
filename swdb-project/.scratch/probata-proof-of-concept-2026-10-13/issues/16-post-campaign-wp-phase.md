# 16 — Post-campaign WP phase and budgets

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 11, 15
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) (sections "Extensa mode" (WP phase, budgets), "Records and levels" (campaign summary), "Proof-hint loop" (budget), "Verifier lineup and order" (order per candidate artifact, failure classes), "Testing Decisions" seams 1, 3 and 4; choices S1, S6; open point O7); decisions: [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) items 3, 10, 11 and its Later changes, [25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md) items 1, 2, 4, [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) items 6, 10
**Time estimate:** about 2 days

**What to build:** When an Extensa campaign stops, a **WP phase** begins. Per workload class it
takes the `gain` candidate artifacts, fastest first, and runs the unbounded rung on each through
`swdb prove`: WP alone, then seeds, then proof-hint rounds. A class is done when one candidate
artifact is proven unbounded or the proof budget ends. No proof job overlaps a timing step or a gem5
simulation. Proof-hint calls draw on their own cap, `provider_calls_proof` (default 30), and never
on the rewriting total. Proof lane-hours come out of the campaign's lane-hours and are reported on
their own line. Caps rise only through the campaign's approval entry. When the phase ends, the
campaign summary is rewritten once and the best-proven winner is recomputed. Built and tested with
the scripted verifier adapter through `swdb campaign --fixture`.

## Acceptance

- [ ] **Starts after the stop, never overlaps.** The WP phase starts only after the campaign has
  stopped and its first summary is written. The recorded start and end times of every proof job,
  timing step and gem5 simulation show no overlap. Control: with a scripted timing step still open,
  no proof job starts until it closes.
- [ ] **Order and stop per class.** Only `gain` candidate artifacts that are certified and not
  refuted are scheduled, fastest first. Fixture with three in one class: the fastest ends "not
  proven, hint budget spent", the second is proven unbounded, the third is never scheduled. A second
  class runs its own order.
- [ ] **What may run (S6, O7).** A skip skips only the steps that need the missing piece.
  - A `gain` candidate artifact whose bounded job timed out, or whose contract has no minimum
    bounds, is still scheduled.
  - Skip reason "no contract proof": no contract seeds. When its proof unit has a unit
    postcondition, route-1 WP still runs without them and writes its proof record. With no unit
    postcondition, it is skipped with that reason.
  - Skip reason "outside the C++ subset": skipped with that reason (13 item 2: no C lowering, no
    hint loop).
  - A skipped candidate artifact keeps its level, and the next one is tried. Fixture: one case
    each.
- [ ] **One proof record per WP job.** Each run is one `swdb prove` job that writes one proof record,
  accepted by `swdb validate` and `swdb build`. Per-candidate budgets (hint rounds, loop wall time,
  WP time per solver) come from the method-version file, not the campaign file. Not proven after
  the budget: the candidate artifact keeps its prior level, with failure class "hint budget spent"
  from the failure-class list.
- [ ] **`provider_calls_proof` in budget validation.** A value up to 30 validates with no approval
  entry. Above 30 is refused unless the approval entry names it (negative control), and accepted
  with it. Each hint round charges one call to this cap and to the call ledger, never to the
  rewriting total.
- [ ] **The two call budgets stay apart.** Control 1: a campaign that stopped because its rewriting
  total was spent still runs its WP phase's hint calls. Control 2: once `provider_calls_proof` is
  spent, the remaining WP runs use seeds and WP alone, then end "not proven, hint budget spent".
- [ ] **Lane-hours shared, reported apart.** Every proof job (the in-loop bounded gate's and the WP
  phase's) counts in the campaign's lane-hours used and also in its own proof lane-hours line. The
  phase ends when lane-hours run out. Raising lane-hours still needs the approval entry (existing
  check, unchanged).
- [ ] **Summary rewritten exactly once.** When every scheduled proof job has ended, or its budget
  has, the summary is rewritten once (the fixture asserts exactly two writes). It recomputes the
  best-proven winner: a candidate artifact proven unbounded in the phase now beats a threads ≤ k
  one. Its level snapshots are dated at the phase end and name the level-rule version.
  `budgets.used` adds proof lane-hours, proof-hint calls and repair calls (certification and
  counterexample; 26 item 6). No level reads as pending.
- [ ] Fixture records carry `contract_fixture` evidence.

## Notes

- **Not in this ticket:**
  - 14 — Bounded gate in the campaign: the in-loop bounded rungs.
  - 15 — Two winners: in-loop tracking and the first summary.
  - 13 — Counterexample-guided repair: repair calls, which stay in the rewriting total.
  - 37 — The proof-hint loop: the real seeds, rounds, three checks, smoke tests and minimization.
  - The per-candidate budget values: 39 — BFS unit proven unbounded at one thread; A3 exit (the
    calibrated Mac proposal); 58 — Mac verdicts reproduced on mbit10 (the mbit10 recalibration);
    59 — Method-version review and freeze (the frozen values).
  - 57 — Proof workers in a socket lane: proof jobs inside a socket lane on mbit10.
  - 55 — End-to-end fixture campaign with real verifiers: this phase with real WP.
  - 18 — ArchEvolve mode level and handoff block: the same proofs in ArchEvolve mode.
  - 62 — Route choice and predecessor proofs in the campaign: the proof of an earlier rewrite that a
    final candidate artifact depends on (25 item 1), run when that candidate artifact reaches WP,
    once per content hash. This ticket schedules final candidate artifacts only.
  - 53 — Chained vs direct vs bundled; A5 exit: route-1 proofs of derived implementations outside a
    campaign.
- Why no overlap (25 item 1): a loaded lane can push a gem5 evaluation past its timeout, and proofs
  run during the loop are wasted when the leader changes.
- Assumption (not decided in the map): "default 30" works like the other campaign budgets' spec
  defaults: the limit validation enforces without an approval entry. An omitted field follows the
  existing budgets' rule (budgets come from the campaign file; the loop never defaults them).
- Assumption (not decided in the map): a campaign that stopped because its lane-hours ran out has no
  lane-hours left for the WP phase. The phase ends at once, and the summary records why.
- Assumption (not decided in the map): an interrupted WP phase continues on resume from where it
  stopped. A campaign whose WP phase has ended is refused on resume, as a stopped campaign is today.
- Assumption (not decided in the map): the rewritten summary replaces the first one wherever the
  first went (the campaign's store and the team store). Git history keeps the stop-time version.
- Assumption (not decided in the map): the campaign records start and end times for proof jobs,
  timing steps and gem5 simulations, so overlap can be checked from campaign state.
- Skip reasons follow the design spec's O7 default (applies until Yan-Ru rules): 25 item 1 says
  only that such a candidate artifact "skips what it cannot run and keeps its level", and O7 reads
  that as skipping only the steps that need the missing piece. "Outside the C++ subset" skips WP by
  decision (13 item 2).
- Rough cost (25 item 2, not measured): campaign a7 would have spent about 1.75 lane-hours on
  proofs, about 21%.
- Tests use the scripted adapter; no real verifier job runs. Full-suite runs on the Mac use at most 2
  test workers. Contract fixtures only; no held-out kernel (BC, PR, SSSP).
