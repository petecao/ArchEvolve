# 15 — Two winners

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
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

- [ ] **Fastest winner, unchanged rule.** Per class: the fastest `gain` candidate artifact that is
  not refuted; certified beats uncertified; the faster-uncertified list stays. A fixture campaign
  with only certified and uncertified levels picks the same winner as before this ticket.
- [ ] **Best-proven winner.** Among `gain` candidate artifacts at a proven level: highest level
  first, then the fastest. Order: proven unbounded; proven within bounds, threads ≤ k; proven within
  bounds, threads = 1. Fixture: a slower candidate artifact at threads ≤ k beats a faster one at
  threads = 1; at the same rung, the faster one wins. A class with no proven `gain` candidate
  artifact has no best-proven winner, and its summary says so.
- [ ] **Negative controls** (one fixture campaign each): (a) an uncertified candidate artifact given
  a scripted proven record never becomes best-proven (proven requires certified); (b) a candidate
  artifact with a counting refutation wins neither, whatever its level or speed; (c) two candidate
  artifacts at threads = 1 whose bounds differ above the minimum rank by speed only (bounds above
  the minimum are never ranked); (d) a candidate artifact whose proof record's pin changed
  mid-campaign reads certified through `swdb candidate-level` and drops out of best-proven.
- [ ] **Tracked inside the loop.** Both winners are recomputed every iteration. After each
  iteration they match what `swdb candidate-level` reports for each candidate artifact at that point
  (levels known so far; never proven unbounded). The next rewrite workspace's `best/` (name decided in map 25) holds the
  fastest winner's patch and, when the best-proven winner differs, its patch too. When one candidate
  artifact wins both, `best/` holds one patch for that class.
- [ ] **Plateau uses both winners.** Fixture: the fastest winner stays put while the best-proven
  winner improves each iteration, for longer than `plateau_iterations`; the campaign does not stop
  on plateau. Control: when neither winner improves for `plateau_iterations` iterations, it stops on
  plateau as today.
- [ ] **Campaign summary.** Per class: both winners, each with a level snapshot that is dated and
  names the level-rule version. One candidate artifact winning both is reported once. Every candidate
  artifact stays in the summary with its level and speed. `swdb validate` and `swdb build` accept
  the new fields; a snapshot missing its date or level-rule version is refused.
- [ ] **Yan-Ru chooses.** The summary marks neither winner as "the" one to promote. The existing
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
