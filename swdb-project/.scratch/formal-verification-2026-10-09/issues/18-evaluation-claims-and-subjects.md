# 18 — What does the evaluation set out to show, and on which kernels and candidate artifacts?

Created: 2026-10-13 17:02 ET
**Type:** grilling
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-13 17:04 ET)
**Blocked by:** None — can start immediately
**Map:** `../map.md`

## Question

What does the paper's evaluation set out to show, and on which subjects? Decide:

- **Claims as research questions:** each with a hypothesis and the result that would refute it.
  Starting points: 01 decision 2 as reworded by 10 (contract parts proven once, plus one small
  automatic proof per candidate artifact; LLM proof hints; bugs as motivating evidence), 10 item 9
  (the per-candidate proof stays small: a hypothesis with a pass bar), 11's Q31 hypothesis (a
  candidate artifact proven at every thread count where the authors' code is refuted at N > 1,
  performance compared), 13 item 9 (hint seeds, a paper feature), 17 item 9 (chained vs bundled),
  and 01's comment on the strict layer's false alarm (hardware semantics must be explicit and
  checked against the device model).
- **Kernels beyond BFS** (generality note). Each one costs an output relation (09) and, per
  contract, a unit relation, a lifting lemma, a reference instance and a contract proof (10), its
  shared-action kinds (15), formal halves (16) and any catalog templates it needs (17). Weigh the
  set against the cost rule (about one month per piece).
- **Candidate artifacts per kernel:** the authors' DX100 code, Peter's and Josh's code (tentative),
  Extensa-campaign artifacts (LLM-written), counterexample-guided repairs, and the upstream-GAPBS
  "any input" demo (17 item 9b).
- **Calibration vs held-out split:** 13 item 11 calibrates on public C suites plus the BFS proof of
  concept and holds out BC, PR, SSSP and BFS bottom-up. Confirm or change.

Not in this ticket: baselines, ablations, metrics and the run protocol (ticket 23).

## Comments

- 2026-10-13 17:02 ET: graduated from the map's "Evaluation plan" fog after all 17 tickets
  resolved. Facts re-checked in code (counts of `maa_` calls per file in
  `apps/dx100/benchmarks/gapbs/src/`):
  - **Authors' DX100 code exists for** BFS top-down (`bfs.cc`, 15 calls), BFS bottom-up
    (`bfs_bu.cc`, 22; `BUStep`), BC in three variants (`bc.cc` 31, `bc_maa_full.cc` 27,
    `bc_new.cc` 77), PR (`pr.cc`, 13) and SSSP (`sssp.cc`, 22). `sssp_maa.cc` has `MAA` ifdefs but
    no `maa_` calls.
  - **None for** CC (`cc.cc`, `cc_sv.cc`), TC (`tc.cc`) and `pr_spmv.cc`.
  - **Library contracts today:** `bfs_read_offload`, `bc_read_offload` (derived), and the native
    `bfs_tdstep_frontier_staging` (`library/rewrite_contracts/`).
  - **Extensa campaigns so far:** BFS only (`records/campaign_summaries/`: seven gem5 and eight
    native BFS campaigns, 2026-10-04 and -05).
  - **Possible PR defect:** ticket 20 checks it by a run; a confirmed defect could be a subject.
- 2026-10-13 17:09 ET: claimed 17:04 ET. More facts, re-checked in code:
  - **Built vs side files:** the authors' Makefile builds `KERNELS = bc bfs cc cc_sv pr pr_spmv
    sssp tc` (`apps/dx100/benchmarks/gapbs/Makefile:24`), so their DX100 kernels are `bfs.cc`
    (`TDStepMAA`, `DOBFSMAA`), `bc.cc` (`PBFSMAA`, `:130`), `pr.cc` (`PageRankPullMAA`, `:127`) and
    `sssp.cc` (`DeltaStepMAA`, `:82`). `bfs_bu.cc` is an unbuilt fragment (no includes; the built
    `bfs` calls only `TDStep` and `TDStepMAA`); `bc_new.cc`, `bc_maa_full.cc` and `sssp_maa.cc` are
    also unbuilt.
  - **Start gate:** D35 refuses every new real-target Extensa campaign today; no paired estimate
    can pass yet (`swdb/campaign.py:1367-1389`). Proposals and certification outside a campaign
    are not gated.
  - **Contamination guard gap:** agent-role inputs must not contain the authors' accelerated code,
    enforced by a name regex (`swdb/provider_roles.py:26,145`) that lists `TDStepMAA`, `DOBFSMAA`,
    and two names that exist nowhere in the authors' code (`TDStepMAA2`, `BCMAA`). It misses
    `PBFSMAA`, `PageRankPullMAA` and `DeltaStepMAA`, so held-out kernels are unguarded today.
  - **Team-store candidates:** 32 candidate records, all BFS.
  Round 1 posted: Q1 research questions; Q2 kernels; Q3 who writes held-out contracts and output
  relations; Q4 candidate sources; Q5 calibration, held-out split and freeze; Q6 the role of
  performance. Held for round 2: numeric pass bars per hypothesis; population size per contract;
  the cut order if time runs short.
- 2026-10-13 19:43 ET: round 1 answers (checkpoint; not yet the answer): Q1-Q6 accepted as
  recommended ("ok" each). Q1: five research questions (RQ1 automation, RQ2 hints and seeds, RQ3
  once vs per candidate, RQ4 refutation and repair, RQ5 end to end for BFS, retrospective if D35
  still blocks); real defects and the false alarm in the motivation; hypotheses with numeric pass
  bars committed before held-out runs. Q2: BFS top-down calibrates; BC, PR, SSSP held out; BFS
  bottom-up, CC and TC dropped. Q3: an agent drafts held-out output relations and contracts after
  the freeze from the baseline and the intrinsic specification, the authors' code hidden; Yan-Ru
  approves at promotion. Q4: authors' code and repairs, an LLM population of k proposals per
  contract, seeded faults, BFS extras; reference instances and BFS out of held-out rates; fix the
  authors'-code guard first. Q5: calibration on public C suites plus BFS; freeze and commit the
  method version before the first held-out run. Q6: performance only in RQ4 and RQ5, with
  Extensa's evaluator on mbit10.
  More facts: the fork's baselines for BC (`PBFS`, `bc.cc:69`), PR (`PageRankPullGS`, `pr.cc:55`)
  and SSSP (`DeltaStep`, `sssp.cc:319`) are hand-reshaped from upstream GAPBS like BFS's (raw
  `VertexOffsets` CSR indexing, absent upstream). "Method version" is used in 15 and 16 but not in
  the glossary. Round 2 posted: Q7 baselines; Q8 LLM population; Q9 starting pass bars; Q10 cut
  order; Q11 the term "method version".
- 2026-10-13 19:46 ET: round 2 answers: Q7-Q11 accepted as recommended ("ok" each). Glossary:
  method version added. Shared-understanding confirmation posted.

## Answer

2026-10-13 19:48 ET. Decided with Yan-Ru in a grilling session (rounds 1-2 in Comments; shared
understanding confirmed "yes"). Facts: the code re-checked in this session (paths in the 17:02 and
17:09 ET comments).

1. **Five research questions** (Q1). Generality is not its own question: every one is reported per
   kernel, held-out kernels apart.
   - **RQ1 Automation:** of the certified candidate artifacts that apply a contract, how many does
     the per-candidate step prove, at which level, with no human step?
   - **RQ2 Hints:** what do LLM proof hints add over WP alone at equal wall time, and what do hint
     seeds add?
   - **RQ3 Once vs per candidate:** what a contract costs once (agent time, Yan-Ru's review) vs each
     candidate (time, rounds, tokens); includes chained vs bundled (17 item 9) and the 2-lane pass
     bar (10 item 9).
   - **RQ4 Refutation and repair:** seeded faults and the N > 1 races in the authors', Peter's and
     Codex's code are refuted; counterexample-guided repair yields candidates proven at every N,
     performance compared (11's Q31).
   - **RQ5 End to end (BFS only):** does ranking by proven level change which candidate wins, at
     what cost? New campaigns if D35 has lifted by then, else a labeled retrospective over the 15
     existing BFS campaigns.

   Real defects and the strict layer's wrong-tile false alarm go to the motivation (01 decision 2c).
2. **Hypotheses with pass bars** (Q9). Starting values; final values set at the freeze, after
   calibration, committed to git before the first held-out run. A miss is reported as a refuted
   hypothesis.

   | RQ | Hypothesis (held-out kernels) |
   |---|---|
   | RQ1 | Of non-refuted LLM candidates, >= 50% proven unbounded and >= 80% at least proven within bounds, inside the frozen budget |
   | RQ2 | At equal wall time, hints add >= 20 points of proof rate over WP alone; seeds cut median provider calls per proven candidate by >= 30% |
   | RQ3 | Median per-candidate proof <= 30 min on mbit10, no human step; each held-out contract <= 3 weeks of agent time and <= 1 day of Yan-Ru's review; chained per-candidate proof time <= bundled; 2 lanes under 15 min with summaries |
   | RQ4 | Every seeded fault a formal check can see is refuted; every as-written candidate racing at N > 1 is refuted; >= 80% of refuted races repaired into candidates proven at every N within the repair budget; repaired performance within the evaluator's noise band of as written |
   | RQ5 | The best proven candidate within 5% of the best certified candidate's speedup; proofs use <= 25% of the campaign's lane-hours |

3. **Kernels** (Q2): BFS top-down calibrates; BC, PR and SSSP are held out: every GAPBS kernel the
   DX100 authors built accelerator code for (`apps/dx100/benchmarks/gapbs/Makefile:24`). Together
   they cover both proof routes and all five shared-action kinds. BFS bottom-up is dropped
   (`bfs_bu.cc` is an unbuilt fragment), as are CC and TC (no DX100 code). Rough cost: 2-3 weeks of
   agent work per held-out kernel, in parallel, plus Yan-Ru's review at promotion.
4. **Baselines** (Q7): each held-out kernel's baseline implementation is the fork's non-DX100
   function as found (`PBFS`, `bc.cc:69`; `PageRankPullGS`, `pr.cc:55`; `DeltaStep`, `sssp.cc:319`),
   though, like BFS's, they are hand-reshaped from upstream GAPBS. The upstream "any input" demo
   stays BFS only (17 item 9b).
5. **Held-out contracts and output relations** (Q3): after the freeze, an agent drafts each
   kernel's output relation and one offload-only contract per kernel (16's five gates; catalog
   reshapes as needed), from the baseline and the intrinsic specification only. The authors' DX100
   code stays hidden, as from the rewriting role. Yan-Ru approves each at promotion. The authors'
   code is then checked as an ordinary candidate; if it does not match the contract it gets only
   the direct bounded check (17 item 4.4). Soundness does not depend on who writes a contract: one
   too weak to lift fails its lifting lemma.
6. **Candidate artifacts per kernel** (Q4, Q8):
   - the authors' DX100 code as written, and its counterexample-guided repairs;
   - an LLM population: rewrite proposals from the rewriting role (Codex, model version pinned in
     the run plan), deduplicated by normalized content hash, until 20 distinct candidates certify
     or 60 proposals are made; the certification rate is reported (about +/-22 points per kernel,
     +/-13 pooled; about 90 mbit10 lane-hours for the held-out set);
   - seeded faults: each contract's negative controls plus the semantics (12) and concurrency (15)
     controls, all to be refuted;
   - BFS only: Peter's read offload, Codex's frontier staging, the upstream demo, and the 32 BFS
     candidates in the team store.

   Reference instances (proven inside their contract proofs) and BFS stay out of held-out rates.
   **Build item first:** the guard that keeps the authors' code out of agent-role inputs
   (`swdb/provider_roles.py:26`) must name `PBFSMAA`, `PageRankPullMAA` and `DeltaStepMAA`, and drop
   the two names that exist nowhere (`TDStepMAA2`, `BCMAA`), before any held-out proposal.
7. **Calibration, held out, freeze** (Q5): calibrate on Code2Inv, X509-parser and
   Frama-C-problems plus everything BFS. Before the first held-out proof run, freeze and commit the
   **method version** (glossary). Per-kernel contract work comes after the freeze and counts in
   RQ3. A later method change makes a new method version, re-runs every held-out kernel, and both
   runs are reported.
8. **Performance** (Q6): the proven level makes no speed claim (01 decision 10). Performance
   appears only in RQ4 (repaired vs as written, same evaluator and machine) and RQ5 (selection,
   ADR 0010), measured with Extensa's evaluator on mbit10, gem5 included for DX100. "gem5 out of
   scope" means proofs never verify or trust gem5.
9. **Cut order** (Q10): RQ5, then PR. BFS, BC and SSSP are the floor; BC is never cut. If SSSP
   cannot finish either, the submission waits rather than claim generality from one held-out
   kernel.

**Changes to earlier tickets:** 13 item 11's held-out list loses BFS bottom-up (now BC, PR, SSSP).

**Inputs passed on:**
- **Ticket 23:** the five research questions and their pass bars; the population procedure;
  certification rate as a reported number; reference instances out of the rates.
- **Ticket 25:** RQ5's form (new campaigns or a retrospective; the 5% and 25% bars).
- **Ticket 27:** the guard fix as the first build item; the cut order; per-kernel contract work
  after the freeze; the method-version freeze as a stage gate.
- **Ticket 20:** if the PR defect is real, the authors' PR fails certification or is refuted, and
  goes to the motivation.

Glossary: method version added.

## Later changes

- 2026-10-13 20:41 ET, from [24](24-alignment-hint-kind.md) (items 3, 5): item 5's authors' code that matches no contract may reach
  proven unbounded by route 1 (unit postcondition plus hazard freedom), recorded as "direct, no
  matching contract", reported apart from RQ1's rates. RQ3's "chained per-candidate proof time <=
  bundled" compares chained (route 3), direct (route 1) and bundled; RQ3 also counts the sum
  library's one-time cost.
- 2026-10-13 20:43 ET, from [25](25-extensa-loop-proofs-and-ranking.md) (items 4, 6): RQ5 runs only on
  new campaigns, once D35 has lifted; item 1's fallback retrospective becomes a labeled worked example
  (the 15 BFS campaigns hold 3 certified candidate artifacts, all in a7). RQ5 compares each class's
  fastest winner with its best-proven winner.
