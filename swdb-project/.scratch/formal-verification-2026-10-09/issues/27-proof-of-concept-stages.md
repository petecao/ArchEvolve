# 27 — In what order does the proof of concept build its pieces, and what closes each stage?

Created: 2026-10-13 17:02 ET
**Type:** grilling
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-13 21:05 ET)
**Blocked by:** 18, 19, 24
**Map:** `../map.md`

## Question

The Destination says running the proof of concept is the next effort. Its pieces are decided
across tickets but not ordered or costed as a whole. Decide:

- **Stages and order.** Candidates: (1) one thread: C lowering, WP and SAW on Peter's read offload
  and the authors' `TDStepMAA`; (2) the proof-hint loop; (3) concurrency: CIVL and GenMC, WP's
  per-thread proof, the Rocq time-box (15 item 8); (4) rewrite chains: the catalog templates (17
  item 2) and chained vs bundled (17 item 9); (5) the strict layer catching up to the proof
  semantics as a new certify version (12 item 4, 16 item 11).
- **Each stage's pass bar and stop rule.** Already set: 2 lanes under 15 minutes with summaries,
  else the claim drops to 1 lane (10 item 9); SAW reads clang 22 bitcode, else crux-llvm (11 item
  2); Rocq in about 2 weeks, else a written proof (15 item 8); SAW ghost state on clang 22 (16 item
  10); every negative control refuted.
- **Cost:** the total against the cost rule (about one month per piece), and what is cut first if
  time runs short.
- **Split:** which pieces are build tickets of the next effort and which belong to the evaluation
  (ticket 23).

## Comments

- 2026-10-13 17:02 ET: graduated from the map's "Evaluation plan" fog (the proof-of-concept items).
  Build items already listed: 12 item 10 (new intrinsic and contract versions), 15's inputs (new
  `bfs_read_offload` and Peter's code versions; GenMC from source; a JDK for CIVL), 16's inputs
  (schema fields, translators, check mode, `std::vector` model, logic library), 17's inputs
  (contract lineage on implementation records; campaign start from a derived implementation;
  per-rewrite certification links).
- 2026-10-13 17:53 ET: input from 21 (resolved): no known product-program technique proves loop
  flattening as is, and unbounded reordering (fission-, tiling-like) defeats the data-driven
  aligner (`../research/21-relational-alignment.md`, Q4 failure modes 1-2). 17 item 2's catalog
  templates for flattening, phase split and chunking may need loop summaries; test one early.
- 2026-10-13 19:48 ET: input from 18 (resolved): first build item is the authors'-code guard fix (`swdb/provider_roles.py:26`); the
  method-version freeze gates held-out runs; held-out contract work comes after it; cut RQ5, then PR.
- 2026-10-13 20:10 ET: input from 19 (resolved): build item: the minimum-bounds derivation script, run on
  the reference instance to confirm 19's hand derivation (lanes 2, chunk 2, frontier 2, vertices 3,
  edges 3). Lever order: per-call summaries, then shape splitting. 10 item 9's pass bar has no 1-lane
  fallback.
- 2026-10-13 20:41 ET: input from 24 (resolved): (1) WP on real-valued sums is untested at our sizes;
  an early stage proves the sum library's lemmas and one PR unit; (2) SSSP's per-candidate proof needs
  delta-stepping's outer-loop invariant, from contract-proof seeds (risk); (3) build item: the sum
  library (method level, before the freeze); (4) 21's catalog-template risk is gone (no templates
  built); (5) SSSP contract: "delta <= least weight" precondition for the live `assert(false)`
  (`sssp.cc:384-388`).
- 2026-10-13 20:43 ET: input from 25 (resolved): build items: the bounded gate and counterexample
  repair before evaluation (`swdb/campaign.py:938-1003`); the WP phase after the campaign stops; the
  best-proven winner in selection, in the workspace and in the plateau test (`swdb/campaign.py:404-425,
  856-858,893-909`); `provider_calls_proof` in budget validation; iterations from a derived
  implementation (17 item 8). Measure how often campaign candidates are refuted at N > 1 and how many
  repair calls that uses.
- 2026-10-13 20:49 ET: Yan-Ru (after 24): revisit RQ3's contract-vs-no-contract claim while working
  this ticket. Since 24, the no-contract baseline also proves by route 1, so a contract's measured
  advantage is only its formal halves, its hint seeds and route 3 (23, Later changes). Decide whether
  a proof-of-concept stage measures that gap early, and whether RQ3's hypothesis needs rewording.
- 2026-10-13 21:10 ET: input from 26 (resolved): build items: the `proof` record schema and
  `records/proofs/`; `swdb_proof*` tables; the versioned level rule (computed on read, ADR 0016);
  `library/methods/<version>.yaml` and its review at the freeze; `vocab/proof_failure_classes.yaml`;
  the handoff's `certification_level` block and its sentence templates; campaign-summary winner
  snapshots, proof budgets used and the post-WP rewrite; repair lineage and run fields on proposals;
  promotion-review level pins; the adapter returning every certification record ID
  (`swdb/campaign_targets.py:585`). The record pieces precede any proof stage whose results must
  count.
- 2026-10-13 21:12 ET: grilling round 1 (agent's recommendation, then Yan-Ru's answer).
  Facts checked: RQ1-RQ4 populations can use the ArchEvolve-mode rewriting role
  (`swdb/workflow.py:418`, `swdb/provider_roles.py:260`), which D35 does not gate; D35 still refuses
  every new real-target Extensa campaign (`docs/adr/0010-extensa-mode-loop.md:24-31`). Installed on
  the Mac today: CBMC, ESBMC, z3, cvc5, Frama-C (opam switch `framac-33`), crux-llvm; not installed:
  SAW, CIVL, GenMC, Rocq.
  - Q1 split at the freeze: the proof-of-concept effort builds and calibrates (BFS, public suites;
    Mac, then mbit10) and ends at the method-version freeze; a second effort, evaluation, drafts the
    held-out contracts, generates populations and runs RQ1-RQ5. **Yes.**
  - Q2 kill tests before building: a 2-week spike with throwaway agent-written stubs: (a) SAW on
    clang 22 bitcode with ghost state; (b) 2 lanes under 15 min with per-call summaries, threads = 1,
    Peter's read offload and the authors' `TDStepMAA`, every single-thread control refuted at 19's
    hand-derived minimum; (c) WP proves one read-offload unit at threads = 1 with agent hints within
    60 min; (d) WP proves the sum lemmas and one CSR pull-sum unit over reals. Stop and re-plan with
    Yan-Ru if (b) fails after both levers or (c) fails in the box. **Yes.**
  - Q3 no PR unit before the freeze (24's "one PR unit" conflicts with 18 item 5 and 24 item 4):
    a synthetic CSR pull-sum fixture instead. **Yes.**
  - Q4 RQ3: (a) in the hint-loop stage, prove the BFS candidates with and without the contract at
    equal budget; (b) reword RQ3 to "What does a contract proven once buy each candidate, and at what
    one-time cost?", the gap reported in three parts (seeds, route 3 vs route 1, refutations only the
    bounded rung gives); no speed claim unless (a) shows a gap; bars set at the freeze. **Yes.**
  - Q5 Extensa-loop integration (25's loop items, 28's ladder): agent recommended (a) the last stage
    before the freeze. **Yan-Ru: (b), a parallel track from day 1.**
- 2026-10-13 21:15 ET: grilling round 2 (every recommendation accepted, "ok").
  - Q6 main track, in order, one verifier job at a time on the Mac (RAM rule): A0 setup (~3 days:
    guard fix first; SAW, CIVL + JDK, GenMC, Rocq; ADR 0006 Mac exception); A1 kill-test spike (2 wk);
    A2 foundations (~6 wk: YAML frame, translators, check mode; C lowering and `std::vector` model;
    logic and sum libraries; per-`maa_*` proof-semantics contracts and new library versions; new
    `bfs_read_offload` version; minimum-bounds script); A3 proof-hint loop (~4 wk: role, checks,
    seeds; calibration suites and BFS; RQ3 both-ways BFS run); A4 concurrency (~4 wk: per-thread
    lowering, CIVL and GenMC adapters, eight controls, race repair of Peter's code, ThreadSanitizer
    one-day box); A5 rewrite chains (2-3 wk: 17 item 9a; 9b only if 9a passes); A6 mbit10 and freeze
    (~2 wk). About 5 months.
  - Q7 Rocq track (composition theorem, DX100 reduction lemma; 2-week box, written fallback) starts
    with A2, beside A2-A3.
  - Q8 strict-layer catch-up (12 item 4's memory-timing rule, new certify version) is a side track
    beside A3-A4, done before the freeze; the 8-byte tile-pair rule (16 item 11) waits until after
    the evaluation.
  - Q9 Extensa track from day 1: 26's record pieces first (A2 reuses them), then 25's loop items,
    26's campaign-summary and handoff fields, the all-record-IDs adapter fix, start from a derived
    implementation, and 28's ladder once 28 resolves; coded against a stub verifier adapter; the
    real gate plugs in after A2, the WP phase after A3. Exit: one `--fixture` campaign end to end
    with real verifiers.
- 2026-10-13 21:24 ET: grilling round 3 (every recommendation accepted, "ok").
  - Q10 exit checks per stage: A0 guard test plus each new tool proves 07's safe smoke program and
    refutes its seeded bug (2 days, else fallback: SAW to crux-llvm, GenMC to CIVL alone labeled,
    Rocq to the written proof); A1 Q2's checks; A2 generated artifacts reproduce every spike verdict,
    the three summary forms agree on fixtures, the script reproduces 19's hand minimum, every
    single-thread control refuted, 2 lanes under 15 min with generated summaries; A3 the loop proves
    the BFS read-offload unit unbounded at threads = 1 with no human step, the checks reject every
    planted bad hint, budgets calibrated, RQ3 BFS numbers recorded (else re-plan); A4 seven controls
    refuted and one proven, CIVL and GenMC agree, Peter's race repaired, WP proves the repaired unit
    per thread for symbolic N, Rocq checked or written; A5 chained, direct and bundled reach the same
    level with times recorded (= 9a passes); A6 every Mac verdict reproduces on mbit10, budgets
    recalibrated, the method file reviewed and committed.
  - Q11 about 21 weeks on the main track accepted; a stage at 1.5x its estimate stops for a re-plan;
    time-boxed items end on their fallbacks.
  - Q12 cut order inside the proof of concept: 17 item 9b; the strict-layer catch-up; A5; the
    Extensa track's end-to-end exit (moves after the evaluation with RQ5). Never cut: A0-A4, A6,
    records.
  - Q13 the next effort gets its own folder, a spec (destination: the freeze) and about 18 build
    tickets of at most about a month each, created when the map's design spec is written.
  - Q14 the N > 1 refutation rate of campaign candidates is measured in the evaluation (RQ4 on the
    populations; campaign numbers with RQ5), not in a proof-of-concept stage.
- 2026-10-13 21:29 ET: grilling round 4 ("ok"). Q15: SSSP's outer-loop invariant (24's risk 2) is
  tested before the freeze on a synthetic bucketed-relaxation fixture (a bucket worklist with
  min-update CAS on distances, written for the test, not GAPBS SSSP); A3's exit adds that the loop
  proves it unbounded with seeds from a contract-proof-style seed set, else re-plan (SSSP is on the
  floor, 18 item 9). Q16: shared understanding confirmed; write up.

## Answer

2026-10-13 21:29 ET. Decided with Yan-Ru in a grilling session (rounds 1-4 in Comments; every
recommendation accepted except round 1 Q5, where Yan-Ru chose a parallel Extensa track). Facts: the
code and tool installs re-checked in this session (the 21:12 ET comment).

1. **Two efforts, split at the freeze** (Q1). The **proof-of-concept effort** builds the method and
   calibrates it on BFS and the public suites (Code2Inv, X509-parser, Frama-C-problems), on the Mac
   then on mbit10, and ends when the method version is frozen and committed (18 item 7). The
   **evaluation effort** then drafts the held-out contracts blind, generates the populations and
   runs RQ1-RQ5; ticket 23's items are its run plan. Held-out kernels (BC, PR, SSSP) are never touched
   before the freeze.

2. **Main track, in order** (Q6). The Mac runs one verifier job at a time (RAM rule), so proof stages
   run in sequence; work with no verifier load runs beside them. Weeks marked † come from earlier
   tickets; the rest are estimates.

   | Stage | Content | Weeks |
   |---|---|---|
   | A0 Setup | The authors'-code guard fix first (`swdb/provider_roles.py:26`: add `PBFSMAA`, `PageRankPullMAA`, `DeltaStepMAA`; drop `TDStepMAA2`, `BCMAA`); install SAW, CIVL with a JDK, GenMC from source, Rocq; record ADR 0006's scoped exception for proof work on the Mac (13 item 13) | ~0.5 |
   | A1 Kill-test spike | Item 3 | 2 (box) |
   | A2 Foundations | YAML frame, both translators, check mode (3-4†); C lowering and `std::vector` model (1†); logic library and sum library (1-2†); per-`maa_*` proof-semantics contracts and the new library versions (12 item 10, 16); the new `bfs_read_offload` version (formal halves L1-L4 and `once_enqueue`, no redundant store, 15 item 11); the minimum-bounds script (19); reuses the record pieces of item 4 | ~6 |
   | A3 Proof-hint loop | Role, vocabulary, three checks, seeds (13); calibration on the public suites and BFS; the RQ3 both-ways BFS run (item 6); the synthetic bucketed-relaxation fixture (item 3) | ~4 |
   | A4 Concurrency | Per-thread lowering, sharing classes, uniform control (15); CIVL and GenMC adapters; the eight concurrency controls; counterexample-guided repair of Peter's race; the one-day ThreadSanitizer box (23) | ~4 |
   | A5 Rewrite chains | 17 item 9a: chained (route 3) vs direct (route 1) vs bundled on Peter's read offload; 9b (upstream GAPBS) only if 9a passes | 2-3† |
   | A6 mbit10 and freeze | Lineup under `/data1/yanruj/` without sudo; the 6-worker lane job (23 item 6); recalibrate budgets; Yan-Ru's review of the method-version file (26 item 3); freeze | ~2 |

   Each stage needs the one before: A3 proves generated artifacts, A4 runs the per-thread program
   through A3's loop (13 item 12), A5 needs routes 1 and 3.

3. **The kill-test spike comes before any building** (Q2, Q3, Q15). Two weeks, throwaway
   agent-written stubs, testing where Extensa's gates failed:
   - (a) SAW reads clang 22 bitcode and keeps ghost state (else crux-llvm, 11 item 2);
   - (b) 2 lanes under 15 minutes with per-call summaries at threads = 1, on Peter's read offload and
     the authors' `TDStepMAA`; every single-thread negative control refuted at 19's hand-derived
     minimum bounds (else lever 2, shape splitting);
   - (c) WP proves one read-offload unit at threads = 1 against its unit postcondition, with
     agent-written hints, within 60 minutes;
   - (d) WP proves the sum library's three lemmas and one unit of a **synthetic CSR pull-sum
     fixture** over reals. Not a PR unit: 24's "one PR unit" would leak a held-out kernel into
     calibration (18 item 5; 24 item 4).

   **Stop rule:** if (b) fails after both levers, or (c) fails within the box, stop and re-plan with
   Yan-Ru before building anything. SSSP's risk (24 input 2) is handled the same way, in A3: a
   synthetic bucketed-relaxation fixture (bucket worklist, min-update CAS on distances), proven
   unbounded by the loop with seeds from a contract-proof-style seed set.

4. **Side tracks** (Q7, Q8, Q9):
   - **Rocq** (15 item 8: the parallel composition theorem and the DX100 reduction lemma; 2-week box,
     written fallback) starts with A2, beside A2-A3, so the spike's stop rule cannot waste it. A4's
     exit needs its result.
   - **Strict-layer catch-up:** a new certify version with 12 item 4's memory-timing rule, so
     refutations using it can replay (13 item 10); beside A3-A4, done before the freeze. The 8-byte
     tile-pair rule (16 item 11) waits until after the evaluation: no evaluated kernel uses 8-byte
     tile data.
   - **Extensa track, from day 1** (Yan-Ru's choice; the agent had recommended the last stage):
     first 26's record pieces (A2 reuses them; 26 says they precede any proof stage whose results
     count), then 25's loop items (bounded gate and counterexample repair in the pre-evaluation path,
     post-campaign WP phase, the best-proven winner in selection, workspace and plateau test,
     `provider_calls_proof`), 26's campaign-summary and handoff fields, the adapter returning every
     certification record ID (`swdb/campaign_targets.py:585`), start from a derived implementation
     (17 item 8), and 28's ladder once 28 resolves. Coded against a stub verifier adapter with
     scripted verdicts; the real bounded gate plugs in after A2, the WP phase after A3. The RQ1-RQ4
     populations do not need it: they can come from the ArchEvolve-mode rewriting role
     (`swdb/workflow.py:418`), which D35 does not gate.

5. **Exit checks** (Q10, Q15). A stage ends only when its check passes.

   | Stage | Exit check | If it fails |
   |---|---|---|
   | A0 | A test shows the guard blocks the three authors' function names; each new tool proves 07's safe smoke program and refutes its seeded bug | A tool not running after 2 days goes to its fallback: SAW to crux-llvm; GenMC to CIVL alone, labeled; Rocq to the written proof |
   | A1 | Item 3 (a)-(d) | Item 3's stop rule |
   | A2 | Generated artifacts reproduce every spike verdict; the three summary forms (SAWScript, C stubs, ACSL) agree on fixtures; the script reproduces 19's hand minimum (lanes 2, chunk 2, frontier 2, vertices 3, edges 3); every formal-visible single-thread control refuted; 2 lanes under 15 min with generated summaries | Root-cause every mismatch before A3 |
   | A3 | The loop proves the BFS read-offload unit unbounded at threads = 1 with no human step; it proves the bucketed-relaxation fixture with seeds; the three checks reject every planted bad hint; budgets calibrated; the RQ3 BFS numbers recorded | Re-plan with Yan-Ru |
   | A4 | The seven must-refute concurrency controls refuted and the must-prove control proven; CIVL and GenMC agree; Peter's race repaired; WP proves the repaired unit per thread for symbolic N; Rocq checked or the written fallback done | A disagreement stops the batch (15 item 9) |
   | A5 | Chained, direct and bundled reach the same level, times recorded (this is 17 item 9a "passes") | Report; route 1 covers every candidate |
   | A6 | Every Mac verdict reproduces on mbit10; budgets recalibrated; the method-version file reviewed and committed | Root-cause before the freeze |
   | Extensa track | One `--fixture` campaign runs gate, repair, evaluation, WP phase and both winners end to end with real verifiers | Moves after the evaluation (item 7) |

6. **RQ3 revisited** (Q4; Yan-Ru's 20:49 ET request). Since 24 a candidate's (B) proof is route 1 with
   or without a contract, and summaries belong to library entries, so the no-contract baseline has
   them too. A contract still adds hint seeds, route 3, minimum bounds (hence a bounded level and
   refutations at known bounds; without a contract there are none, 19 item 1) and its formal halves.
   - **Measured early:** in A3, the BFS candidates are proven with and without the contract at equal
     budget (BFS is calibration, so this is allowed before the freeze).
   - **Reworded:** RQ3 asks "What does a contract proven once buy each candidate, and at what
     one-time cost?" Primary metric unchanged; the gap is reported in three parts: seeds (from RQ2's
     seeds on/off), route 3 vs route 1 time, and refutations only the bounded rung gives. No claim
     that contracts make per-candidate proofs faster unless the A3 run shows it. Bars set at the
     freeze.

7. **Cost and cut order** (Q11, Q12). The main track is about 21 weeks (about 5 months); side tracks
   add no calendar time unless they slip. Only A2 exceeds the one-month rule, and it is several
   pieces. **Overrun rule:** a stage at 1.5x its estimate stops for a re-plan with Yan-Ru; the
   time-boxed items (spike, Rocq, ThreadSanitizer) end on their fallbacks. **Cut first,** inside the
   proof of concept: (1) 17 item 9b; (2) the strict-layer catch-up (its replays stay "proof semantics
   only", 13 item 10); (3) A5 (route 1 covers every candidate; RQ3 loses its chained arm); (4) the
   Extensa track's end-to-end exit, moved after the evaluation with RQ5. Never cut: A0-A4, A6, the
   record pieces. The evaluation's own cut order stays (Claude check, RQ5, PR; 23).

8. **Build-ticket split** (Q13). The proof-of-concept effort gets its own folder and spec (destination:
   the freeze) and about 18 tickets of at most about a month each: A0 guard fix; A0 tool installs; A1
   spike; A2 frame and translators; A2 C lowering and `std::vector`; A2 logic and sum libraries; A2
   proof semantics and library versions; A2 minimum-bounds script; A3 hint loop; A3 calibration and the
   RQ3 run; A4 concurrency; A5 chains; A6 mbit10 and freeze; Rocq; strict layer; Extensa records; Extensa
   loop items; Extensa ladder. Blocking follows the stage order. The tickets are created when the
   map's design spec is written, not here (plan, then implement in a fresh session).

9. **Measured in the evaluation, not here** (Q14): how often campaign candidates are refuted at N > 1
   and the repair calls that uses (25's input). RQ4 reports both on the RQ1 populations; campaign
   numbers come with RQ5, once D35 lifts.

10. **Generality.** The stages build the method, not BFS: BFS is only the calibration kernel, and the
    two synthetic fixtures stand in for the held-out kernels' riskiest proofs (PR's real-valued sums,
    SSSP's outer-loop invariant) without touching them.

**Changes to earlier tickets** (each noted under its "Later changes"): 16 item 11 (the 8-byte rule's
strict-layer version deferred); 17 item 9 ("9a passes" defined); 18 RQ3 (wording); 23 item 1 (RQ3's
three-part gap); 24 input 1 (a synthetic fixture, not a PR unit); 25's measurement input (to the
evaluation).

**Inputs passed on:**
- **The map's design spec:** the two efforts, the stage table, exit checks, cut order and ticket list.
- **Ticket 28** (claimed in another session): its ladder is a ticket of the Extensa track, cut with
  the track's end-to-end exit.
