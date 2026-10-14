# 09 — RQ4: refutation and repair

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 05, 06, 07
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Evaluation design": RQ4, baselines, secondary results, performance; "Refutation, repair and bugs"; "Bounds": minimum bounds; "Verifier lineup and order"; S1; open point O1; O5: repairing the authors' code; O6: replay labels); decisions: [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md), [22](../../formal-verification-2026-10-09/issues/22-cex-guided-llm-repair-research.md), [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md), [25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md), [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (item 10), [28](../../formal-verification-2026-10-09/issues/28-extensa-iteration-ladder.md) (item 9)
**Time estimate:** about 1 week

**What to build:** RQ4 asks whether seeded faults and threads > 1 races are refuted, and whether
counterexample-guided repair yields candidate artifacts proven at every thread count. This ticket
measures refutation rates for the seeded faults and the races. For the populations it reads 07's
bounded verdicts at minimum bounds, with their replay labels, instead of running them. It runs the
testing-only certification baseline and counts its false acceptances. It runs
counterexample-guided repair (5 rounds, 3 runs) against three mirrors at equal provider calls, plus
the ThreadSanitizer repair baseline if proof-of-concept 50 installed it. It reports reverted repairs
apart, patch size as tree edit distance, the small-scope curve, and repaired vs as-written performance on mbit10. It also reports
the threads > 1 refutation rate and repair calls per refuted candidate artifact on the populations.
It owns the authors' row, built from 06's results (PageRank's refutation and repair among them).

## Acceptance

- [ ] Every formal-visible seeded fault in 06's manifest runs the bounded rungs at minimum bounds
      through `swdb prove`. The refutation rate is reported per kernel and pooled. Runtime-only
      controls are listed by label, outside the rate.
- [ ] Every refutation this ticket's jobs make is replayed on the strict layer in the same
      `swdb prove` job and labeled: reproduced, proof semantics only, not reproduced, or (O6)
      undefined behavior (no strict-layer replay). The populations' refutations already carry their
      labels on 07's refutation records; this ticket reads them and replays none again. "Not
      reproduced" stops the batch until root-caused, and so does a CIVL–GenMC contradiction. An
      "undefined behavior" refutation, such as a data race, counts, and the batch goes on. "Bug"
      still needs a whole-kernel reproduction: a real input, plus a schedule for a race. Replay and
      reproduction come from
      [proof-of-concept 60 — Strict-layer replay and whole-kernel reproduction](../../probata-proof-of-concept-2026-10-13/issues/60-strict-layer-replay-and-kernel-reproduction.md).
- [ ] The threads > 1 refutation rate on the as-written populations (05) is read from 07's verdicts at
      threads ≤ k, per kernel and pooled, against the bar "every racing candidate artifact refuted".
      This ticket runs no bounded rung at minimum bounds on a population member.
- [ ] Testing-only certification baseline, per kernel: how many candidate artifacts and seeded faults
      certification accepts that the bounded verifier refutes (false acceptances), and which seeded
      faults each side catches. Population verdicts come from 07.
- [ ] Every refuted population candidate artifact goes through counterexample-guided repair: the
      counterexample goes to the rewriting role (Codex), at most 5 rounds of one provider call each,
      3 independent runs, no iteration ladder. Each repaired candidate artifact is certified, gated and
      proven again. Reported: the repair rate (refuted races repaired into candidate artifacts proven
      at every thread count, that is proven unbounded) after round 1 and after round 5, and repair
      calls per refuted candidate artifact.
- [ ] The three mirrors run on the same refuted candidate artifacts at equal provider calls, 3 runs
      each, interleaved with the repair runs within one batch: safety-only acceptance (accept when
      the bounded verifier finds no safety violation; no unit relation, no re-certification),
      verdict only, and ask again.
- [ ] **ThreadSanitizer repair baseline, only if
      [proof-of-concept 50 — ThreadSanitizer one-day box](../../probata-proof-of-concept-2026-10-13/issues/50-threadsanitizer-box.md)
      installed it:** a repair counts as accepted when ThreadSanitizer (Archer) reports no race. It
      runs on the same refuted candidate artifacts as the mirrors. If 50's Answer says "not run", the
      report cites the baseline only, with 50's reason. LLOR and DR.FIX are cited, not run.
- [ ] Reverted repairs are flagged by the deterministic check (the repaired code fails the
      contract-match check for the same contract, drops the offload, or normalizes to the baseline's
      content hash; map ticket 23 item 3), reported apart and never counted. Each repaired proposal
      carries its repair lineage (refuted candidate artifact, counterexample record, round, reverted
      flag), run index and provider pin. Patch size is reported as tree edit distance.
- [ ] The small-scope curve: seeded faults and LLM candidate artifacts refuted at the minimum bounds,
      at +1 and at +2. The populations' minimum-bounds points come from 07; +1 and +2 run here.
- [ ] Each repaired candidate artifact is timed against its as-written version on mbit10 with
      Extensa's evaluator (gem5 for DX100), same evaluator and machine, against the bar "within the
      evaluator's noise band".
- [ ] **The authors' row (owned here):** 06 hands over its results on the authors' code, PageRank's
      refutation and repair among them; any authors' refutations and repairs run here join them. The
      row stays outside the repair rate (spec O1). The authors' PageRank counts as caught when it
      fails certification or is refuted (O5).

## Notes

- **Not in this ticket:** 06 — Authors' code and seeded faults (the seeded-fault manifest; the
  authors' PR refuted and repaired, results handed here); 07 — RQ1 and RQ2 runs (the populations'
  bounded rungs at minimum bounds and their replay labels, read here); 08 — RQ3: what a contract
  buys; 11 — Claude sensitivity check (Claude in the repair role); 12 — Statistics and results
  report (paired tests, intervals).
- These repairs run outside Extensa campaigns and see no iteration ladder (map ticket 28 item 9).
  Campaign refutation counts come with RQ5 (10).
- Assumption (not decided in the map): "+1 and +2" raises every size dimension of a rung by 1, then by
  2, together; the thread count stays the rung's own.
- Assumption (not decided in the map): repairs of the authors' BC and SSSP refutations, if any, run
  here under the same protocol, reported in the authors' row.
- **Repairing the authors' code (O5, default until Yan-Ru rules):** the rewriting role may see the
  authors' code only when it is the refuted candidate artifact under repair, in the evaluation,
  never in a campaign. Keep these calls apart from the population repairs.
- Assumption (not decided in the map): timing runs never overlap proof jobs in the same lane. The
  design states this only for Extensa mode.
- Assumption (not decided in the map): the ThreadSanitizer baseline runs like the mirrors: equal
  provider calls, 3 runs, interleaved in the same batch. Map ticket 23 item 2 says only that it runs
  if it installs within one day.
- **mbit10:** lane leases, `df -h /data1 /data`, output under `/data1/yanruj/EvolveSWDB_runs/`, and a
  30-minute status heartbeat while jobs run (LR-07).
- **Cut order:** if PR is cut, PR's share of this ticket goes with it (effort spec).
- Internal findings about the authors' code are never sent to the authors or the team without
  Yan-Ru.
