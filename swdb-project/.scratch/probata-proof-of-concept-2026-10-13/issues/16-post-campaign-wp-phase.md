# 16 — Post-campaign WP phase and budgets

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 07:57 ET (answer, ticket 16); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
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

- [x] **Starts after the stop, never overlaps.** The WP phase starts only after the campaign has
  stopped and its first summary is written. The recorded start and end times of every proof job,
  timing step and gem5 simulation show no overlap. Control: with a scripted timing step still open,
  no proof job starts until it closes.
- [x] **Order and stop per class.** Only `gain` candidate artifacts that are certified and not
  refuted are scheduled, fastest first. Fixture with three in one class: the fastest ends "not
  proven, hint budget spent", the second is proven unbounded, the third is never scheduled. A second
  class runs its own order.
- [x] **What may run (S6, O7).** A skip skips only the steps that need the missing piece.
  - A `gain` candidate artifact whose bounded job timed out, or whose contract has no minimum
    bounds, is still scheduled.
  - Skip reason "no contract proof": no contract seeds. When its proof unit has a unit
    postcondition, route-1 WP still runs without them and writes its proof record. With no unit
    postcondition, it is skipped with that reason.
  - Skip reason "outside the C++ subset": skipped with that reason (13 item 2: no C lowering, no
    hint loop).
  - A skipped candidate artifact keeps its level, and the next one is tried. Fixture: one case
    each.
- [x] **One proof record per WP job.** Each run is one `swdb prove` job that writes one proof record,
  accepted by `swdb validate` and `swdb build`. Per-candidate budgets (hint rounds, loop wall time,
  WP time per solver) come from the method-version file, not the campaign file. Not proven after
  the budget: the candidate artifact keeps its prior level, with failure class "hint budget spent"
  from the failure-class list.
- [x] **`provider_calls_proof` in budget validation.** A value up to 30 validates with no approval
  entry. Above 30 is refused unless the approval entry names it (negative control), and accepted
  with it. Each hint round charges one call to this cap and to the call ledger, never to the
  rewriting total.
- [x] **The two call budgets stay apart.** Control 1: a campaign that stopped because its rewriting
  total was spent still runs its WP phase's hint calls. Control 2: once `provider_calls_proof` is
  spent, the remaining WP runs use seeds and WP alone, then end "not proven, hint budget spent".
- [x] **Lane-hours shared, reported apart.** Every proof job (the in-loop bounded gate's and the WP
  phase's) counts in the campaign's lane-hours used and also in its own proof lane-hours line. The
  phase ends when lane-hours run out. Raising lane-hours still needs the approval entry (existing
  check, unchanged).
- [x] **Summary rewritten exactly once.** When every scheduled proof job has ended, or its budget
  has, the summary is rewritten once (the fixture asserts exactly two writes). It recomputes the
  best-proven winner: a candidate artifact proven unbounded in the phase now beats a threads ≤ k
  one. Its level snapshots are dated at the phase end and name the level-rule version.
  `budgets.used` adds proof lane-hours, proof-hint calls and repair calls (certification and
  counterexample; 26 item 6). No level reads as pending.
- [x] Fixture records carry `contract_fixture` evidence.

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

## Answer

2026-10-14 08:32 ET. Built test-first; every acceptance box is met. Branch `probata-poc/t16`. Interface:
[`format-v0.4-extensa.md`](../../../docs/reference/format-v0.4-extensa.md) "The WP phase"; schemas
`schemas/campaign_summary.schema.json` (`wp_phase`) and `schemas/extensa_campaign.schema.json`
(`budgets.provider_calls_proof`). Code `swdb/wp_phase.py` (new), small hooks in `swdb/campaign.py`
(`_finish` -> `_after_stop`, `_resume_wp_phase`, `_spent`, `_gate`, `summary`, budget validation), the call
ledger (`swdb/extensa/search.py`: `PROOF_HINT_ROLE`, `proof_calls`, `open_proof_call`), adapter hooks
(`TargetAdapter.wp_plan`, `wp_job`, `open_timing_steps` in `swdb/campaign_targets.py`; fixture versions in
`swdb/campaign_fixture.py`).

**What exists now:**

- **The phase.** With a bounded gate (a method version), `Campaign._finish` writes the stop summary
  (`wp_phase.state: not_started`), then `wp_phase.Phase.run`: per class, `order` = certified, unrefuted
  `gain` candidate artifacts, fastest first; one `swdb prove` job per proof unit (stages `wp`, `seeds`,
  hint rounds); the class ends when the level rule reads one `proven_unbounded`, or its order is spent.
  Then `summary()` is called again and the record replaced in the campaign store and the team store
  (`state.summary_writes`: `stop`, `wp_phase_end`). Both winners and every `level_snapshot` are recomputed
  then (15's code), so a candidate proven unbounded in the phase becomes the best-proven winner.
- **Skips (O7).** No contract proof: no `seeds` stage; unit postcondition -> route-1 WP runs, none -> skip
  record `no_contract_proof`. Outside the C++ subset -> skip record `outside_cpp_subset`. Timeouts and
  missing minimum bounds in the gate do not keep a candidate out.
- **Budgets.** Method version: `hint_rounds`, `hint_loop_wall_minutes` (job wall budget, and the lane-hours a
  job needs left to start), `wp_seconds_per_solver` (copied into the block; no fallback default). Campaign:
  `provider_calls_proof` (<= 30 free, above only via `approval.raised_budgets`), charged per hint round to
  the ledger as role `proof_hint`, excluded from `provider_calls_counted` and from per-iteration caps, open
  after the stop. `budgets.used` adds `proof_lane_hours`, `provider_calls_proof`,
  `certification_repair_calls`, `counterexample_repair_calls`; `limits` adds `provider_calls_proof`.
- **Lane-hours.** A gate run that ran a verifier and every WP job are charged to `lane_hours` and
  `proof_lane_hours` (the format doc line saying the gate is not charged is updated).
- **No overlap.** `state.timeline` records every evaluation step (`timing_step`, or `gem5_simulation` on a
  shared-baseline target), gate run and WP job (`proof_job`); each WP job first waits until
  `adapter.open_timing_steps()` is empty (`waits`). Real targets report none (the loop is sequential).
- **Resume.** A stopped campaign whose phase is `not_started`/`running` continues on `--resume` (candidates in
  `tried` are skipped); an ended phase is refused ("already stopped").

**Tests:** `tests/test_wp_phase_campaign.py`, 6 tests (seam 3 `swdb campaign --fixture`, seam 1 `swdb prove`
records, seam 4 `swdb validate`/`swdb build` on both stores): tracer (order and stop per class, one record
per job, summary rewritten once, budget lines, snapshots, no pending, resume refused), skips without a
contract proof, timeout/no-minimum still scheduled plus control 2 (cap spent -> WP and seeds only), control 1
(stopped on `provider_calls`, hint calls still run), lane-hours shared/apart/ending the phase plus the
open-timing-step control and the lane-hours approval check, `provider_calls_proof` validation and its
required-at-start rule. Updated: `tests/testkit/extensa.py` (default `provider_calls_proof: 30`),
`tests/test_bounded_gate_campaign.py` (`VOLATILE` lists the WP-phase fields in the gate-off comparison).
Serial, no xdist: new file 6 passed (`/tmp/claude/probata-runs/t16/pytest/b2.jsonl` sha256
`98fd2b555bb8ede020d3b871eec1d004c02a61bba8e6973b33e2566cc7aace4e`, 2 failed there, fixed, rerun
`b3.jsonl` sha256 `cfcf933f1039b81b4850c8b908cd214b0833d53254064456456937b3068dba0f`); regression
`test_bounded_gate_campaign`, `test_two_winners_campaign`, `test_extensa_budgets`,
`test_counterexample_repair`, `test_format_doc`, `test_campaign_structure`, `test_extensa_machinery`,
`test_extensa_campaign`: 139 passed in 35 min (`/tmp/claude/probata-runs/t16/pytest/r1.jsonl` sha256
`b2d81854bfd7487ad9a62472343c4cb9a6cafa5eb9c1f034b7f63d577df4178d`). After merging the integration tip
(f1fdfe6d): `test_wp_phase_campaign`, `test_format_doc`, `test_bounded_gate_campaign`: 21 passed in 17 min
(`/tmp/claude/probata-runs/t16/final.jsonl` sha256
`ab5fcd58861211586fd869b0872489cde2588740d187a8365f4681e68d4f334c`).

**Assumptions** (the ticket's five are implemented as written):

- Assumption: an omitted `provider_calls_proof` is refused when a new campaign starts with a library that
  holds a method version (the schema keeps it optional so the ten historic campaign files still validate).
- Assumption: the hint rounds are scripted (no provider runs); each opens and closes one ledger call
  `proof_hint`, outcome completed. Ticket 37's loop replaces the stage loop and makes the real calls.
- Assumption: a WP job starts only with `hint_loop_wall_minutes` of lane-hours left; a gate run made only of
  skips is not charged; a gate run's lane time is its elapsed time (rungs run in parallel), not the rungs' sum
  (`proof_job_hours` keeps the sum).
- Assumption: hint rounds are per candidate artifact, shared across its proof units.
- Assumption: a target with no WP adapter (the real ones, and a fixture row without `proof.wp`) ends the
  phase with `end_reason: failure`; the summary is still rewritten.
- Assumption: the "scripted timing step still open" control is a fixture timing step open when the phase
  first asks (`open_timing_step: {seconds}`); in the real loop no step can be open after the stop.

**For other tickets:** 37 replaces `Phase._job`'s stage loop (keep `Phase.charge_hint` for every round's call
and `adapter.wp_job` / `swdb prove` for the record; per-goal data belongs in the proof record). 55 implements
`TargetAdapter.wp_plan`/`wp_job` for real WP and runs this phase end to end. 18 can reuse
`wp_phase.Phase` for ArchEvolve mode (it needs a campaign-like object: `state`, `ledger`, `gate`, `adapter`,
`_levels`, `_save`, `_spent`). 62 hooks predecessor proofs into `Phase._candidate` before the candidate's own
jobs. 17's ladder can read `summary.wp_phase` but rows never show proven unbounded (the loop has ended).
Open: the repair-cap question (13) is untouched; repair calls stay in `provider_calls_counted`.
