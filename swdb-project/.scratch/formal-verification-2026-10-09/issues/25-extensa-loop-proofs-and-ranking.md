# 25 — How does the Extensa-mode loop budget proofs and rank candidate artifacts by certification level?

Created: 2026-10-13 17:02 ET
**Type:** grilling
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-13 20:12 ET)
**Blocked by:** 19
**Map:** `../map.md`

## Question

ADR 0010: a campaign bounds iterations, lane-hours, provider calls and disk; selection ranks
certification first, performance second, per workload class. Proofs add cost and new levels.
Decide:

- **When proofs run:** for every certified final candidate artifact, for the top few by
  performance, or after the campaign; and the proof budget per campaign (mbit10 lane-hours, proof
  jobs inside a socket lane; 13 item 13).
- **Repair budget:** counterexample-guided repair rounds per refuted candidate artifact (13), and
  whether a repaired candidate re-enters selection.
- **Ranking:** proven unbounded > proven within bounds (verdicts with different bounds compared per
  ticket 19) > certified; a candidate whose proof is still running; a refuted candidate leaves
  selection (13 item 10).
- **Rewrite chains in the loop:** an iteration may start from a certified derived implementation;
  only final candidate artifacts are ranked and use lane-hours (17 item 8).
- **ArchEvolve mode:** whether and when proofs run there (one proposal attempt, ADR 0010).
- Whether ADR 0010 needs an amendment.

## Comments

- 2026-10-13 17:02 ET: graduated from the map's "Extensa-mode loop" fog. The glossary's
  "Certification level" already ranks proven unbounded, proven within bounds, certified,
  uncertified in Extensa-mode selection.
- 2026-10-13 17:32 ET: input from 22 (resolved): a counterexample-guided repair may just revert to
  the baseline implementation (Orvalho et al. saw models copy the reference); decide whether such a
  repair re-enters selection.
- 2026-10-13 19:48 ET: input from 18 (resolved): RQ5 is BFS-only end to end: new campaigns if D35 has lifted, else a labeled
  retrospective; pass bars 5% of best certified speedup and <= 25% of lane-hours for proofs.
- 2026-10-13 20:10 ET: input from 19 (resolved): proven within bounds at or above the minimum bounds is one
  level with two sub-rungs, threads <= k (CIVL) above threads = 1 (SAW); bounds above the minimum are
  never ranked (19 item 7). Extensa mode proves at the minimum only (19 item 3): one 15-minute job per
  rung plus WP per candidate.
- 2026-10-13 20:20 ET: claimed 20:12 ET. Facts re-checked in code this session:
  - **Selection today** is lexicographic: level first (`certified` 2 > `uncertified` 1), then the
    lower bound; only `gain` candidates can win; faster uncertified ones are listed
    (`swdb/campaign.py:404-425`). The level is derived from records, never stored
    (`swdb/extensa_boundary.py:99-118`).
  - **A repair loop already exists before evaluation:** a failed certification goes to a `repair`
    call, at most `max_repairs` = 2 (D7), and the repaired patch is certified again; only then is
    the candidate evaluated (`swdb/campaign.py:938-1003`).
  - **Provider calls:** one shared total, 1 setup + 3 per iteration x 8 = 25; repair calls count
    in it; when it is spent the campaign stops (`swdb/campaign.py:116-118,646-651`).
  - **The 15 BFS campaigns** (`records/campaign_summaries/`): 3 certified candidate artifacts in
    all, every one in `extensa-gem5-bfs-20261004-a7` (2 of them class winners); most lane-hours
    used 6.7 of 24; most provider calls 20 of 25. The 7 native-campaign candidates that were not
    rejected are uncertified (no contract).
  - **From 23 (resolved 20:12 ET):** counterexample-guided repair gets 5 rounds; repair and hint
    calls count in the campaign's provider-call budget; one lane job runs up to 6 proof workers.
  Round 1 posted: Q1 when proofs run; Q2 proof budget; Q3 repair in the loop; Q4 ranking; Q5
  ArchEvolve mode; Q6 RQ5's retrospective.
- 2026-10-13 20:27 ET: round 1 answers (checkpoint; not yet the answer): Q3, Q5, Q6 accepted. Q2
  accepted, plus Yan-Ru: reserve the right to raise budgets as campaigns show what they need. Q1:
  "are you sure? which one is better?" Re-check against the a7 records: an iteration with a certified
  candidate took 2.5-4 h wall (gem5 evaluation, `it4` 14:42-17:18, `it8` 17:51-21:59 UTC) against
  15-20 min without one; all 3 certified candidates gained; gem5 `evaluate-pair` has a 7500 s
  timeout (`swdb/campaign_targets.py:800`). So bounded rungs before evaluation stay (about 10% of one
  evaluation, and a refutation saves the whole evaluation); the WP part is revised to run after the
  campaign stops, with no overlap with gem5 (a loaded lane could push a simulation past its timeout,
  and during the loop a leader change wastes proofs). Q4: Yan-Ru asks to track two winners, the best
  proven and the best speedup. Round 2 posted: Q1 revised, Q4 two winners, Q7 ADR 0010 note.
- 2026-10-13 20:37 ET: round 2 answers (checkpoint): Q1 revised accepted; Q7 accepted; Q4 two winners
  accepted, but "the fastest winner drives the loop because WP arrives only after the campaign" drew
  "are you sure?". Re-check: the reason is wrong. The bounded gate runs before evaluation, so both
  proven-within-bounds rungs are known inside the loop; only proven unbounded waits for WP. Today the
  loop keeps one best per class by (level, lower bound); its patch is shown as `best/<class>.patch`
  (a reference: every iteration still patches the base snapshot), and an iteration counts as improving
  only when that key rises (`swdb/campaign.py:856-858,893-909`; plateau rule
  `swdb/extensa/search.py:13-15`). Round 3 posted: Q4b both winners tracked inside the loop.

## Answer

2026-10-13 20:40 ET. Decided with Yan-Ru in a grilling session (rounds 1-3 in Comments; shared
understanding confirmed "ok"). Facts: re-checked in code this session (paths in the 20:20, 20:27 and
20:37 ET comments).

1. **When proofs run** (Q1, revised after "are you sure?").
   - **Bounded gate before evaluation:** each certified final candidate artifact runs the bounded
     rungs at its contract's minimum bounds (SAW at one thread; CIVL and GenMC at threads <= k), in
     parallel, 15 minutes each (19 item 8), right after certification and before speed evaluation,
     where today's certification repair sits (`swdb/campaign.py:938-1003`). A refuted candidate is
     never evaluated and goes to repair (item 3). Reason: in campaign a7 an iteration with a certified
     candidate took 2.5-4 h of gem5 wall time, against about 15 minutes for the gate.
   - **Unbounded proofs after the campaign stops:** WP and the proof-hint loop run only for
     candidates that pass `gain` in their class, fastest first, until one is proven unbounded (no
     slower candidate can then become best-proven winner) or the proof budget ends. No proof job
     overlaps a timing step or a gem5 simulation: a loaded lane can push `evaluate-pair` past its
     7500 s timeout (`swdb/campaign_targets.py:800`), and proofs run during the loop are wasted when
     the leader changes.
   - **Rewrite chains:** the gate and WP run on final candidate artifacts. A proof of an earlier
     rewrite that a final candidate depends on (17 item 4, as revised by 24) runs when that final
     candidate reaches WP, once per content hash. A candidate with no contract proof, no minimum bounds, or code outside the C++ subset skips
     what it cannot run and keeps its level.
   - Rejected: every proof step for every certified candidate (WP spent on candidates that cannot
     win); all proofs after the campaign (a refutation could not feed repair, and refuted code would
     be evaluated).
2. **Budget per campaign** (Q2).
   - **Hint calls** get their own cap, `provider_calls_proof`, default 30 (three full hint loops).
     They are counted in the campaign's call ledger (23) but never use the rewriting total: a7 used 20
     of its 25 calls, and a spent total stops the campaign (`swdb/campaign.py:646-651`). When the cap is
     spent, the remaining WP runs use seeds and WP alone, then end as "not proven, hint budget spent"
     (13 item 10).
   - **Repair calls** (certification and counterexample) stay in the rewriting total, as today.
   - **Lane-hours:** proof jobs share the campaign's lane-hours (default 24) with no separate cap,
     reported as their own line for RQ5's 25% bar; up to 6 proof workers per lane job (23 item 6).
     Rough estimate (not measured): a7 would spend about 1.75 lane-hours on proofs, about 21%.
   - **Raising budgets (Yan-Ru: reserve the right):** campaign caps rise per campaign through the
     existing approval entry (`swdb/campaign.py:114-117,190-201`); the new caps join that list.
     Per-candidate budgets (10 hint rounds, 60 min, 15 min per bounded job, 5 repair rounds) belong to
     the method version: raised freely before the freeze, after it only as a new method version (18
     item 7).
3. **Repair inside the loop** (Q3). A refutation enters the existing pre-evaluation repair loop, its
   counterexample as feedback (13 item 10): at most 5 rounds (23 item 4), counted apart from the 2
   certification repairs (D7). A repaired candidate is a new candidate artifact: certified, gated,
   evaluated and ranked like any other. A reverted repair may compete in selection, flagged, and never
   counts as a repair (23 item 3).
4. **Two winners per workload class** (Q4, Yan-Ru's proposal; Q4b after "are you sure?"; glossary).
   - **Fastest winner:** the fastest `gain` candidate artifact that is not refuted; certified beats
     uncertified, as today (`swdb/campaign.py:404-425`; the faster-uncertified list stays).
   - **Best-proven winner:** among `gain` candidates at a proven level, the highest level first, then
     the fastest. Levels, top first: proven unbounded; proven within bounds, threads <= k; proven
     within bounds, threads = 1 (19 item 7). None when no candidate reached a proven level.
   - One candidate winning both is reported once. Every candidate artifact stays in the campaign
     summary with its level and speed (records: 26). Refuted candidates leave selection (13 item 10).
   - **Inside the loop:** both winners are tracked from the levels known so far. The gate gives the
     bounded levels before evaluation; only proven unbounded waits for WP. The workspace shows the
     fastest winner's patch and, when it differs, the best-proven winner's (`best/<class>.patch` today,
     `swdb/campaign.py:856-858`); an iteration improves when either winner improves, so the plateau
     stop cannot end a campaign that is still finding better-proven candidates. The two differ inside
     the loop mainly when the fastest candidate's bounded job times out.
   - **After WP:** the summary recomputes the best-proven winner. No pending level: final winners are
     set once every scheduled proof job has ended or its budget has.
   - **Promotion:** Yan-Ru chooses which winner to promote.
   - RQ5's metric is the speedup gap between the two winners (23 item 1).
   - Rejected: one level-first ranking (a proven 1.06x beats a certified 2.0x and hides the trade-off);
     a speed band (blurs RQ5).
5. **ArchEvolve mode** (Q5). Its one final candidate artifact runs the same gate and unbounded proofs
   with the same budgets. A refutation gets counterexample-guided repair within the 5 rounds, as its
   allowed bounded correctness repair. The level is reported, never ranked; what ArchEvolve mode shows
   is ticket 26's. The method stays the same in both modes (ADR 0009).
6. **RQ5 only on new campaigns** (Q6). The 15 BFS campaigns hold 3 certified candidate artifacts, all
   in a7, so at most 2 class winners could change. RQ5 runs only once D35 has lifted; the retrospective
   becomes a labeled 3-candidate worked example, not a result. RQ5 is already early in the cut order
   (23), so the floor does not move.
7. **ADR 0010** (Q7): a dated "Proof note" added now (proposed); implemented in the proof-of-concept
   effort.
8. **Generality.** Nothing here is BFS-specific: the gate, the WP order, the budgets, the two winners
   and repair apply per contract, kernel and workload class.

**Changes to earlier tickets:** 13 item 11 (proof-hint calls get their own cap,
`provider_calls_proof`, still counted in the campaign's ledger); 18 item 1 (RQ5's fallback
retrospective becomes a worked example); ADR 0010's "certification first, performance second" becomes
two winners for the proven levels (certified still beats uncertified).

**Inputs passed on:**
- **Ticket 26:** per candidate artifact: gate result per bounded level, refutation and repair lineage
  (reverted-repair flag), WP verdict; per class: both winners, recomputed after WP; per campaign: proof
  lane-hours, proof and repair call counts, and any approval entry that raised a budget.
- **Ticket 27:** build items: the bounded gate and counterexample repair in the pre-evaluation path;
  the post-campaign WP phase; the second winner in selection and in the plateau test;
  `provider_calls_proof` in budget validation; iterations from a derived implementation (17 item 8).
  Measure how often campaign candidates are refuted at N > 1 and how many repair calls that uses.

Glossary: certification level and Extensa mode sharpened; fastest winner and best-proven winner added.
ADR 0010: proof note.
