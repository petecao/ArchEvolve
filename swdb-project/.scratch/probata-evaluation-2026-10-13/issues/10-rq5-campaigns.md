# 10 — RQ5: end-to-end BFS campaigns

Created: 2026-10-13 22:17 ET
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** proof-of-concept 55, proof-of-concept 59
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Evaluation design": RQ5, cut order; "Extensa mode": bounded gate, WP phase, two winners, budgets, iteration ladder, start gate; "Records and levels": campaign summary; "Further Notes": paper framing); decisions: [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md), [25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md), [28](../../formal-verification-2026-10-09/issues/28-extensa-iteration-ladder.md), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) (item 6, campaign summary); ADR 0010 (D35 start gate note)
**Time estimate:** about 2 weeks of campaigns
**Cut order:** 2

**What to build:** Only once D35 has lifted, Yan-Ru gets new BFS Extensa campaigns, all with the
iteration ladder, run with the frozen method. Per workload class, each campaign reports the speedup
gap between its fastest winner and its best-proven winner, and its proof lane-hours as a share of the
campaign's. The bars: the best-proven winner within 5% of the best certified candidate artifact's
speedup, and proofs at most 25% of lane-hours. Campaign a7 is reported as a labeled worked example
("no ladder (v1)"), not a result. The paper gets its ladder limit sentence.

## Acceptance

- [ ] No campaign starts while D35 refuses new real-target campaigns. Each campaign file names its
      numeric pairing check, and that check passes. If D35 still blocks when time runs out, this
      ticket is cut and a7 stays a worked example.
- [ ] A run plan Yan-Ru approves names the campaigns (hardware targets, workload classes, rewrite
      contracts), the budgets (`provider_calls_proof` default 30, lane-hours default 24) and the
      provider pin. Any budget raise appears in the campaign file's approval entry.
- [ ] Each campaign records `rewrite_workspace: v2` in its state and summary, writes `LADDER.json`
      from iteration 2, and passes the ladder leakage check (no patches, no counterexamples, no raw
      timings).
- [ ] Each campaign runs the bounded gate at minimum bounds before evaluation and never evaluates
      refuted code. Refutations get at most 5 repair rounds, apart from D7's 2 certification repairs.
- [ ] The WP phase starts only after the campaign stops: gain candidate artifacts, fastest first,
      until one is proven unbounded or the budget ends. No proof job overlaps a timing step or a gem5
      simulation.
- [ ] Each campaign summary lists, per workload class, the fastest winner and the best-proven winner
      with dated level snapshots naming the level-rule version, and `budgets.used` with proof
      lane-hours, proof-hint calls and repair calls. It is rewritten once when the WP phase ends.
- [ ] RQ5 table, per class: the speedup gap between the two winners against the 5% bar, and proof
      lane-hours as a share of the campaign's against the 25% bar. Threads > 1 refutations and the
      repair calls they used are reported beside.
- [ ] Campaign a7 appears as a labeled worked example, "no ladder (v1)", outside the RQ5 result.
- [ ] The results draft carries the limit sentence: RQ5 does not measure whether the iteration
      ladder, or its level column, changes the speed gap.

## Notes

- **Not in this ticket:** [proof-of-concept 55 — End-to-end fixture campaign with real verifiers](../../probata-proof-of-concept-2026-10-13/issues/55-end-to-end-fixture-campaign.md)
  (the fixture campaign); 09 — RQ4: refutation and repair (refutations outside campaigns); 12 —
  Statistics and results report.
- **Why only new campaigns:** the 15 old BFS campaigns hold 3 certified candidate artifacts, all in
  a7, so they cannot answer RQ5 (map ticket 25 item 6). No ladder ablation runs (map ticket 28 item
  9).
- **Paper check:** before writing "Extensa's ladder", confirm Extensa's published runs postdate MemAcc
  commit `bc92c2eec` (2026-08-25); the ladder was empty before it.
- Assumption (not decided in the map): the number of campaigns, their hardware targets and workload
  classes are set in the run plan above.
- Assumption (not decided in the map): this ticket promotes nothing. Choosing which winner to promote
  stays Yan-Ru's, outside RQ5.
- **mbit10:** campaigns run inside socket lanes under the lease rules; `df -h /data1 /data` before
  each; a 30-minute status heartbeat while they run (LR-07).
- **Cut order:** second in the evaluation (after 11). RQ5 is BFS only, so cutting it never touches the
  held-out floor.
