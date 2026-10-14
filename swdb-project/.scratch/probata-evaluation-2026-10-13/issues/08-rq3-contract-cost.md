# 08 — RQ3: what a contract buys

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 07
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Evaluation design": RQ3, its three-part gap, baselines, ablations, secondary results; "Proof routes"; "Proven once vs per candidate": the 2-lane pass bar; S1); decisions: [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md), [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md), [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md) (item 1)
**Time estimate:** about 4 days

**What to build:** RQ3 asks what a contract proven once buys each candidate artifact, and at what
one-time cost. Per contract, this ticket gathers the one-time cost (agent time and Yan-Ru's review
hours from 02-04, plus the sum library's one-time cost) and the per-candidate cost (median proof time
on mbit10). It runs nothing: it analyzes the arms 07's interleaved batch ran, the no-contract
baseline among them (route 1 for the unbounded half, SAW whole-function equivalence for the bounded
half). It reports the gap in three parts: seeds, route 3 vs route 1 time, and refutations only the
bounded rung gives. It adds the summaries-vs-inlined ablation (BFS's 2-lane bar plus 07's SSSP arm),
chained vs direct vs bundled from proof-of-concept 53 if that ran, the route used per candidate
artifact, and the count that would have needed an alignment.

## Acceptance

- [ ] Per contract (BC, PR, SSSP): agent time and Yan-Ru's review hours from 02-04's records, against
      the bars (at most 3 weeks of agent time and 1 day of review). The sum library's one-time cost
      comes from [proof-of-concept 26 — Logic and sum libraries](../../probata-proof-of-concept-2026-10-13/issues/26-logic-and-sum-libraries.md)'s
      records and is reported once.
- [ ] Median per-candidate proof time on mbit10, per kernel and pooled, from 07's records, against the
      bar (at most 30 minutes, no human step).
- [ ] The no-contract baseline is read from 07's no-contract arm on 05's frozen candidate artifacts
      (unbounded half: route 1 with no formal halves, no seeds, no route 3 and no alignment, 3 runs;
      bounded half: SAW whole-function equivalence against the baseline implementation, 1 run). It
      is compared only against the with-contract arm interleaved in the same batch (map ticket 23
      item 6). This ticket re-runs no arm.
- [ ] The three-part gap is reported: (1) seeds, from 07's seeds on vs off; (2) route 3 vs route 1
      per-candidate time, from 07's route-1 arm on the candidate artifacts 07 proved by route 3; (3)
      refutations the contract's bounded rung gives that the no-contract arm does not. If
      [proof-of-concept 62 — Route choice and predecessor proofs in the campaign](../../probata-proof-of-concept-2026-10-13/issues/62-route-choice-and-predecessor-proofs.md)
      or A5 is cut, 07 runs no route-1 arm, and part (2) reads "not measured (A5 cut)".
- [ ] Summaries vs inlined building blocks: BFS's 2-lane bar (below) and SSSP's arm from 07's batch,
      inlined vs configuration 1 (proof rate and per-candidate time).
- [ ] No claim that contracts make per-candidate proofs faster unless the A3 RQ3 BFS run of
      [proof-of-concept 39 — BFS unit proven unbounded at one thread; A3 exit](../../probata-proof-of-concept-2026-10-13/issues/39-bfs-unit-unbounded-and-a3-exit.md)
      showed a gap. The report cites its mbit10 recomputation from
      [proof-of-concept 58 — Mac verdicts reproduced on mbit10](../../probata-proof-of-concept-2026-10-13/issues/58-reproduce-on-mbit10.md)
      (paper numbers come only from mbit10).
- [ ] Chained (route 3) vs direct (route 1) vs bundled per-candidate proof time from
      [proof-of-concept 53 — Chained vs direct vs bundled; A5 exit](../../probata-proof-of-concept-2026-10-13/issues/53-route-three-and-a5-exit.md),
      against "chained ≤ bundled", read from 58's mbit10 reproduction of the three arms. If 53 was
      cut, the bar is reported as dropped.
- [ ] The 2-lane bar (BFS's safe 2-lane case, with summaries, under 15 minutes) is reported from
      mbit10 records.
- [ ] The route used per candidate artifact, and the count that would have needed an alignment
      (expected 0), with the rule used to count them.

## Notes

- **Not in this ticket:** 02 — BC held-out contract and contract proof, 03 — PR held-out contract and
  contract proof, 04 — SSSP held-out contract and contract proof (they record the one-time costs);
  07 — RQ1 and RQ2 runs (runs every arm analyzed here: with-contract, no-contract, route-1, SSSP
  inlined; its records carry the borrowed-bounds and route-1 assumptions); 09 — RQ4: refutation and
  repair; 12 — Statistics and results report (paired tests, intervals).
- Proof time is a cost metric, never a speed claim.
- **Interleaving (decided, map ticket 23 item 6):** configurations under comparison share one batch,
  so every arm compared here comes from 07's batch. An across-batch comparison would break the
  protocol; only Yan-Ru can accept it, and 12 would then label it.
- Assumption (not decided in the map): the 2-lane bar comes from
  [proof-of-concept 58 — Mac verdicts reproduced on mbit10](../../probata-proof-of-concept-2026-10-13/issues/58-reproduce-on-mbit10.md)'s
  records. If none holds the timing, flag it to Yan-Ru: this ticket runs nothing.
- Assumption (not decided in the map): "would have needed an alignment" counts candidate artifacts
  for which neither route 1 nor route 3 can state part (B) of the proof.
- **Cut order:** if PR is cut, PR's rows go with it (effort spec).
