# 15 — Two winners

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 06:50 ET (resolved); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
**Blocked by:** 14
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) (sections "Extensa mode", "Records and levels" (campaign summary), "Solution" (levels), "Testing Decisions" seams 2, 3 and 4; choice S2); decisions: [25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md) item 4, [28](../../formal-verification-2026-10-09/issues/28-extensa-iteration-ladder.md) items 4-5, [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) items 2, 6, 9, [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md) item 7
**Time estimate:** about 2 days

**What to build:** An Extensa campaign names two winners per workload class instead of one. The
**fastest winner** is what selection picks today: certified beats uncertified, then speed. The
**best-proven winner** is the `gain` candidate artifact at the highest proven certification level,
then the fastest. The loop recomputes both every iteration from the levels known so far: the bounded gate
gives the proven-within-bounds levels; proven unbounded waits for the WP phase. The rewrite
workspace's `best/` (name decided in map 25) shows both patches when they differ. An iteration improves when either winner
improves, so the plateau stop cannot end a campaign that is still finding better-proven
candidate artifacts. The campaign summary records both winners per class, each with a dated level
snapshot. Yan-Ru chooses which to promote. The whole path runs in `swdb campaign --fixture` with the scripted
verifier adapter.

## Acceptance

- [x] **Fastest winner, unchanged rule.** Per class: the fastest `gain` candidate artifact that is
  not refuted; certified beats uncertified; the faster-uncertified list stays. A fixture campaign
  with only certified and uncertified levels picks the same winner as before this ticket.
- [x] **Best-proven winner.** Among `gain` candidate artifacts at a proven level: highest level
  first, then the fastest. Order: proven unbounded; proven within bounds, threads ≤ k; proven within
  bounds, threads = 1. Fixture: a slower candidate artifact at threads ≤ k beats a faster one at
  threads = 1; at the same rung, the faster one wins. A class with no proven `gain` candidate
  artifact has no best-proven winner, and its summary says so.
- [x] **Negative controls** (one fixture campaign each): (a) an uncertified candidate artifact given
  a scripted proven record never becomes best-proven (proven requires certified); (b) a candidate
  artifact with a counting refutation wins neither, whatever its level or speed; (c) two candidate
  artifacts at threads = 1 whose bounds differ above the minimum rank by speed only (bounds above
  the minimum are never ranked); (d) a candidate artifact whose proof record's pin changed
  mid-campaign reads certified through `swdb candidate-level` and drops out of best-proven.
- [x] **Tracked inside the loop.** Both winners are recomputed every iteration. After each
  iteration they match what `swdb candidate-level` reports for each candidate artifact at that point
  (levels known so far; never proven unbounded). The next rewrite workspace's `best/` (name decided in map 25) holds the
  fastest winner's patch and, when the best-proven winner differs, its patch too. When one candidate
  artifact wins both, `best/` holds one patch for that class.
- [x] **Plateau uses both winners.** Fixture: the fastest winner stays put while the best-proven
  winner improves each iteration, for longer than `plateau_iterations`; the campaign does not stop
  on plateau. Control: when neither winner improves for `plateau_iterations` iterations, it stops on
  plateau as today.
- [x] **Campaign summary.** Per class: both winners, each with a level snapshot that is dated and
  names the level-rule version. One candidate artifact winning both is reported once. Every candidate
  artifact stays in the summary with its level and speed. `swdb validate` and `swdb build` accept
  the new fields; a snapshot missing its date or level-rule version is refused.
- [x] **Yan-Ru chooses.** The summary marks neither winner as "the" one to promote. The existing
  promotion command accepts either winner of a class.

## Notes

- **Not in this ticket:**
  - 14 — Bounded gate in the campaign: the bounded levels; refuted code is never evaluated.
  - 10 — Level rule: computing levels and the two sub-rungs.
  - 16 — Post-campaign WP phase and budgets: proven unbounded, the summary rewrite after WP, final
    winners.
  - 17 — Iteration ladder: winner marks in `LADDER.json`.
  - 12 — Proposal and promotion fields: the promotion review's proof record IDs and level pin.
  - 13 — Counterexample-guided repair: repaired candidate artifacts entering selection; the
    reverted-repair flag.
  - evaluation 10 — RQ5: end-to-end BFS campaigns: the speedup gap between the two winners.
- Assumption (not decided in the map): the second patch's file name under `best/`, and the prompt
  sentence that says which patch is which. Proposed: `best/<class>.patch` (name decided in map 25) stays the fastest
  winner's; the best-proven winner's gets a distinct name beside it.
- Assumption (not decided in the map): the summary's existing per-class best fields keep meaning
  "fastest winner", so summaries written before this ticket still read the same; the best-proven
  winner gets new fields.
- Assumption (not decided in the map): "fastest" for both winners uses the speed key selection
  uses today (25 item 4: "as today"). A winner improves when its key rises: fastest winner by
  (certified over uncertified, speed); best-proven winner by (proven level, speed).
- Inside the loop the winners differ mainly when the fastest candidate artifact's bounded job times out
  (25 item 4).
- Generality: per contract, kernel and workload class; nothing BFS-specific. Contract fixtures only;
  no held-out kernel (BC, PR, SSSP) is touched before 59 — Method-version review and freeze.
- Tests use the scripted adapter; no real verifier job runs. Full-suite runs on the Mac use at most 2
  test workers.

## Answer

2026-10-14 06:50 ET. Built test-first; every acceptance box is met. Branch `probata-poc/t15`. Interface:
[`format-v0.4-extensa.md`](../../../docs/reference/format-v0.4-extensa.md) "Two winners per workload class";
schema `schemas/campaign_summary.schema.json` (`$defs.level_snapshot`, `$defs.winner_row`). Code `swdb/campaign.py`.

**What exists now:**

- **Selection.** `select(pool, refuted)` is today's fastest-winner rule with the level rule's refuted set
  removed. `best_proven(pool, levels)`: certified `gain` entries at a proven level, key (level rank, lower
  bound). `winner_rows` gives one row per distinct winner (`fastest`, `best_proven`, `both`), each with its
  dated `level_snapshot` (`swdb.level_rule.snapshot` via `Rule.candidate`), `ratio` and `lower`.
- **Inside the loop.** `Campaign._winners` recomputes both winners of every class after each iteration by
  reading the level rule over the campaign store and library (never stored). The iteration row gets `winners`
  and `improved_winners`; `improved_classes` lists their classes; the iteration improves (plateau) when either
  winner's key rises. `state.json`: `bests` (fastest), `best_proven`, `patches` (every `gain` candidate
  artifact's patch, since a winner can come from any earlier iteration; a state from before this ticket is
  seeded from its `bests`).
- **`best/`.** `best/<class>.patch` stays the fastest winner's; `best/<class>.best_proven.patch` holds the
  best-proven winner's when it is another candidate artifact; the prompt gets one sentence saying which is which
  (unchanged prompt when no best-proven file exists).
- **Summary.** Per class: `winners`, `best_proven` (ID or null), `best_proven_note` when null; the `best*`
  fields keep meaning the fastest winner. Every candidate entry with an ID gets `level_snapshot` (its level when
  the summary is written). The schema refuses a snapshot without `at` or `level_rule`. No field marks a winner to
  promote; `swdb promote` accepts either winner (it never checked which candidate won).

**Tests:** `tests/test_two_winners_campaign.py`, 9 tests (seam 3 `swdb campaign --fixture` with the scripted
adapter; seam 2 `swdb candidate-level`; seam 4 `swdb validate`, `swdb build`, `swdb promote`): tracer
(tracking, `best/` contents, summary), summary validation and promotion, plateau and its control, unchanged
fastest rule (ungated), negative controls (a)-(d). The fixture provider now logs the text of each `best/` file
(`tests/testkit/extensa.py`). Mutation check: with best-proven improvements ignored, the plateau test fails.
Run logs and hashes: see the final report line below.

**Assumptions** (the ticket's three are implemented as written: `best/<class>.patch` stays the fastest
winner's, the `best*` summary fields keep meaning fastest, both winners use today's speed key):

- Assumption: the best-proven patch's name is `best/<class>.best_proven.patch` (the winner-mark spelling of
  map 28 item 4).
- Assumption: winners are recomputed from scratch each iteration (not kept monotonically), so a winner that
  is refuted later or whose proof records stop counting drops out; a drop is not an improvement. Without
  refutations the fastest winner is the same as before (the pool only grows; ties keep the earlier one).
- Assumption: a refutation written after a candidate artifact was evaluated (fixture (b); in practice a later
  proof job) removes it from both winners but does not send it to counterexample-guided repair; only the
  bounded gate's refutations enter 13's loop.
- Assumption: negative control (d) changes the content of both minimum-bounds derivation records during a
  pause (a re-derivation), the one pin the gate's proof records carry that certification does not share
  (proof semantics is `not_applicable` before ticket 27; a method-version change is refused on resume).
- Assumption: promotion evidence is a certification under a named command version (spec review C3), which
  fixture campaign certifications are not, so the promotion test adds one per winner before `swdb promote`.

**For other tickets:** 16 rewrites the summary after WP by calling `Campaign.summary` again (it recomputes
`winners`, `best_proven` and every `level_snapshot`); `levels` come from `Campaign._levels`. 17 reads each
iteration's `winners` rows (`class`, `candidate`, `winner`, `level_snapshot`) for ladder winner marks. 18 can
use `level_rule.snapshot` the same way. Evaluation 10 (RQ5) reads `per_class[].winners` `ratio`/`lower`.

**Side finding (for the main session):** `swdb.estimate_protocol.estimator_identity` hashes every
`swdb/**/*.py`, so editing any swdb module while a `swdb campaign` test runs makes it stop with
`infrastructure_failure` ("paired estimate implementation/configuration changed after freeze"). Do not merge
or edit swdb code while campaign tests run in the same checkout.
