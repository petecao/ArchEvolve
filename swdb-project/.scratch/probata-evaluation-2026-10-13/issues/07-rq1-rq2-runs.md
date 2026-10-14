# 07 — RQ1 and RQ2 runs

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 05, 06
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Evaluation design": RQ1, RQ2, protocol, cost, baselines, ablations, BFS extras; "Verifier lineup and order", including S6; "Proof-hint loop": seeds, budget; "Records and levels"; "Providers and machines"; S1, S2, S3, S10; O6: replay labels; O7: skips); decisions: [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md), [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md) (items 2, 5, 6, 8), [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) (item 3), [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (items 9-11), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md) (item 1), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) (item 6)
**Time estimate:** about 1 week (about 3 days of proof compute on 12 workers)

**What to build:** On two mbit10 socket lanes with 6 proof workers each, one interleaved batch runs
every proof arm the evaluation compares. This ticket owns the populations' bounded rungs: every
frozen LLM candidate artifact gets them once, at its contract's minimum bounds. Then three
configurations: (1) the proof-hint loop with seeds, 3 independent runs at the frozen budget; (2)
without seeds, 3 runs; (3) WP alone at equal wall time, 1 run. The same batch runs 08's arms, so 08
only analyzes: the no-contract arm, the route-1 arm, and the SSSP arm of the summaries-vs-inlined
ablation. It also runs the BFS extras, reported apart from held-out rates. The output is RQ1's proof
rate per level and RQ2's proof-rate difference over WP alone and median provider calls per proven
candidate artifact, seeds on vs off, per kernel and pooled; plus the records 08 and 09 read.

## Acceptance

- [ ] A run plan is committed before the first proof job. It names the frozen budgets from the
      method-version file, the pass bars committed at the freeze, the Codex pin for proof hinting,
      every arm with its run count (configurations 1-3: 3, 3, 1; the arms below), the order of
      candidate artifacts and the interleaving. A pin change is a new run plan.
- [ ] **Bounded rungs (owned here):** every candidate artifact in 05's frozen manifest gets the
      bounded rungs at its contract's minimum bounds, once: the one-thread bounded verifier (SAW, or
      crux-llvm `-f real` for a real-valued unit per proof-of-concept 23) at threads = 1; CIVL at
      threads ≤ k, with GenMC as second refuter. A CIVL–GenMC contradiction stops the batch. Each refuting job
      writes the replay label from
      [proof-of-concept 60 — Strict-layer replay and whole-kernel reproduction](../../probata-proof-of-concept-2026-10-13/issues/60-strict-layer-replay-and-kernel-reproduction.md)
      on its refutation record (same `swdb prove` job). A "not reproduced" label stops the batch until
      root-caused; "undefined behavior (no strict-layer replay)" lets it go on (O6). 09 reads these
      verdicts and labels and runs none of them again.
- [ ] **C++ subset coverage, for 12:** per kernel and pooled, the share of population members
      skipped as "outside the C++ subset", and the unsupported constructs their records name
      (construct and source location).
- [ ] Every non-refuted candidate artifact reaches WP in each configuration, including those whose
      bounded rung timed out or that have no minimum bounds (S6). Refuted ones never reach WP.
- [ ] Jobs run inside mbit10 socket lanes: up to 6 proof workers per lane job, each pinned to its own
      core under an 8 GB RSS cap, at most 2 lanes.
- [ ] Each proof record written by `swdb prove` carries the job block (the fields
      [proof-of-concept 12 — Proposal and promotion fields](../../probata-proof-of-concept-2026-10-13/issues/12-proposal-and-promotion-fields.md)
      lists); on its verdict, the hint-set hash, rounds, provider
      calls, tokens, provider kind and hint provenance (map ticket 13 item 10); and the run index
      (1-3) and provider pin (S10: a proof-hint run has no proposal). `swdb validate` and
      `swdb build` accept them. No per-candidate hint has provenance "human".
- [ ] Every "not proven" carries a listed failure class. An unclassified failure stops the batch and
      is root-caused before any rerun. Rejected hint sets are recorded by rule.
- [ ] RQ1 table, per kernel and pooled: the share of non-refuted LLM candidate artifacts proven
      unbounded and at least proven within bounds, read with `swdb candidate-level` from the
      counting records. Primary = mean over the 3 runs; "proven in any run" is secondary.
- [ ] RQ2 table, per kernel and pooled: the proof-rate difference of the hint loop over WP alone at
      equal wall time, and median provider calls per proven candidate artifact, seeds on vs off. Each
      candidate artifact's time to proof is kept, so proof rate can be drawn as a curve over the
      budget.
- [ ] **No-contract arm (08's baseline), same batch:** on 05's frozen candidate artifacts. Unbounded
      half: route 1, the same proof-hint loop and budget, WP against the kernel's unit
      postcondition, with no formal halves, no seeds, no route 3 and no alignment; 3 runs. Bounded
      half: whole-function equivalence against the baseline implementation on the one-thread bounded
      verifier (SAW, or crux-llvm `-f real` for a real-valued unit per proof-of-concept 23), from
      [proof-of-concept 61 — SAW whole-function equivalence (bounded direct route)](../../probata-proof-of-concept-2026-10-13/issues/61-saw-whole-function-equivalence.md);
      1 run.
- [ ] **Route-1 arm (part (2) of 08's gap), same batch:** each candidate artifact that route choice
      sends to route 3 is also proven by route 1 with its contract, at the same budget and seed
      setting. If
      [proof-of-concept 62 — Route choice and predecessor proofs in the campaign](../../probata-proof-of-concept-2026-10-13/issues/62-route-choice-and-predecessor-proofs.md)
      or A5 is cut, no candidate artifact goes to route 3, and this arm is not run; the run plan says
      so.
- [ ] **SSSP arm of the summaries-vs-inlined ablation, same batch:** SSSP's population proven with
      the building blocks inlined in place of their summaries, compared against configuration 1.
      (The ablation's BFS half is the 2-lane bar, which 08 reads from proof-of-concept 58.)
- [ ] **BFS extras, same batch, reported apart from held-out rates:** Peter's read offload, Codex's
      frontier staging, the upstream demo (only if
      [proof-of-concept 54 — Upstream-GAPBS demo](../../probata-proof-of-concept-2026-10-13/issues/54-upstream-gapbs-demo.md)
      ran) and the 32 team-store candidate artifacts. Each gets the bounded rungs, or the O7 skip it
      qualifies for, then a BFS seeds on/off arm (configurations 1 and 2). Codex's frontier staging
      has no contract proof: it skips contract seeds, minimum bounds and the bounded rung, and runs
      route-1 WP when its proof unit has a unit postcondition (O7; as in proof-of-concept 39). Their
      tables never pool with BC, PR or SSSP.
- [ ] Worker-hours used are recorded per arm against the estimate of at most ~760 worker-hours.

## Notes

- **Not in this ticket:** 08 — RQ3: what a contract buys (analysis only of this batch's arms:
  median proof time, the three-part gap, route used); 09 — RQ4: refutation and repair (refutation
  rates, repair, the small-scope curve above the minimum; it reads this ticket's bounded verdicts and
  replay labels); 11 — Claude sensitivity check; 12 — Statistics and results report (Wilson
  intervals, McNemar, Wilcoxon; it reads the C++ subset coverage recorded here).
- **Why one batch (decided, map ticket 23 item 6):** configurations under comparison are
  interleaved within one batch, so load affects them alike. That is why 08's arms run here.
- Assumption (not decided in the map): seeds from earlier proven candidate artifacts come only from
  the same run and configuration, in the order the run plan fixes. Otherwise the 3 runs would not be
  independent.
- **WP alone (decided, map ticket 23 item 2):** all solvers, the hint loop's full frozen wall budget
  per candidate artifact, no hints.
- Assumption (not decided in the map): the per-run levels behind the 3-run mean come from
  `swdb candidate-level` over one run's proof records plus the shared bounded records. The read
  over all runs gives "proven in any run".
- Assumption (not decided in the map): the no-contract bounded half runs at the same bound values as
  the contract's minimum bounds, labeled as borrowed, since without a contract there are no minimum
  bounds (map ticket 19 item 1).
- Assumption (not decided in the map): the route-1 arm keeps the contract's formal halves and seeds,
  so part (2) of 08's gap isolates the route. The no-contract arm alone would also mix in the seeds
  and the formal halves.
- Assumption (not decided in the map): the SSSP inlined arm uses configuration 1's loop, budget and
  run count (3), with seeds on.
- Assumption (not decided in the map): the BFS extras skip WP alone and the no-contract arm, since
  RQ2's and RQ3's bars are held-out only. Map ticket 23 item 5's estimate (about 95 LLM candidate
  artifacts, which matches 60 held-out plus these 35 BFS ones; an inference) may count them in more
  arms. Yan-Ru may add them.
- Assumption (not decided in the map): the ~760 worker-hour estimate may not cover the arms moved
  here from 08. A projected overrun goes to Yan-Ru before the batch starts.
- **mbit10:** check both socket leases and the legacy lease before dispatch; `df -h /data1 /data`
  first; raw output under `/data1/yanruj/EvolveSWDB_runs/` (or `/data/` when `/data1` has under
  20 GB free). Post a 30-minute status heartbeat while jobs run (LR-07). Only mbit10 numbers enter
  the paper.
- **Cut order:** if PR is cut, PR's share of this ticket goes with it (effort spec).
