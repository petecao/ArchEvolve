# 23 — Which baselines, ablations and metrics answer each research question, and how are runs repeated?

Created: 2026-10-13 17:02 ET
**Type:** grilling
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-13 19:51 ET)
**Blocked by:** 18, 22
**Map:** `../map.md`

## Question

For each research question ticket 18 fixes, decide its baselines, ablations, metrics and run
protocol. Inputs already decided:

- **Baselines named so far:** testing-only certification; the verifier without hints at equal wall
  time (13 item 11); hints without contracts; prior repair loops (ticket 22).
- **Ablations:** seeds on and off (13 item 9, a paper feature); chained vs bundled (17 item 9);
  summaries vs inlined building blocks (10 item 9).
- **Metrics:** proof rate as a curve over the budget; time; hint rounds, provider calls and tokens;
  refutations and bugs by 13 item 10's three evidence steps; escape-hatch attempts by rule (13 item
  8); C-lowering subset coverage on campaign candidates, `std::vector` included (13 item 2, 16 item
  6); translator agreement on fixtures (16 item 1); drafts each formal-half gate rejects (16 item 5);
  ghost-capacity failures (16 item 10); bounds reached (ticket 19); human effort per contract (10
  item 8).
- **Method checks reported as evidence:** the semantics negative controls (12 item 9); the eight
  concurrency controls (15 item 12); CIVL and GenMC agreement (15 item 9); strict layer vs proof
  semantics on fixtures (12 item 8).
- **Concurrency:** the ladder per candidate artifact (SAW threads = 1, CIVL threads <= k, WP every
  N; 15 item 9); as written vs repaired at every N with performance compared (11 Q31, 15 item 10).
- **Protocol:** LLM nondeterminism (repeated runs, provider and model versions); budgets frozen
  after calibration (13 item 11); final runs on mbit10 inside socket lanes; Mac results labeled and
  never mixed with mbit10 timings (13 item 13).

## Comments

- 2026-10-13 17:02 ET: graduated from the map's "Evaluation plan" fog (the baselines, metrics and
  per-ticket evaluation items).
- 2026-10-13 17:32 ET: input from 22 (resolved): five baselines that mirror published repair loops and
  the metrics that literature reports (`../research/22-cex-guided-llm-repair.md`, "Suggested
  baselines"); also decide whether a repair that reverts to the baseline implementation counts.
- 2026-10-13 19:48 ET: input from 18 (resolved): the five research questions, their starting pass bars, the population procedure (20 certified
  Codex candidates per contract, at most 60 proposals) and reference instances kept out of rates.
- 2026-10-13 19:53 ET: claimed 19:51 ET. Facts re-checked this session:
  - **Two named baselines have no definition anywhere else:** "testing-only certification" and
    "hints without contracts" appear only in this ticket (grep over `issues/` and `map.md`).
  - **mbit10 lane:** 16 cores, no hyperthreads, at most 16 threads per job; 125 GB RAM for the
    host (`.claude/skills/mbit10-runs/SKILL.md:28-30,90`). LR-07 caps a lane at 6 test workers.
  - **Repair budget:** no ticket fixes one; RQ4's bar says "within the repair budget" (18 item 2).
  - **Rough proof compute** (estimate, not measured): about 95 LLM candidates (60 held-out, 35 BFS)
    x 8 configurations x at most 60 min is at most about 760 worker-hours, about 3 days on 12
    workers (2 lanes x 6).
  Round 1 posted: Q1 primary metric and pass-bar reading; Q2 baselines per RQ; Q3 revert rule;
  Q4 repair budget; Q5 repeats and statistics; Q6 proof workers per lane; Q7 second provider;
  Q8 ablation list.
- 2026-10-13 20:04 ET: round 1 answers (checkpoint; not yet the answer): Q1-Q8 accepted as
  recommended ("ok" each). Q7 addition (Yan-Ru): the second provider uses this project's default
  Claude setting, the adapter pin `claude-sonnet-5-5` at effort `high`
  (`swdb/provider_adapters.py:24-25`; Codex's pin there is `gpt-5.6-sol` at `xhigh`).
- 2026-10-13 20:10 ET: input from 19 (resolved): measure the small-scope hypothesis as a curve: seeded
  faults and LLM-proposed candidates refuted at the minimum bounds, + 1 and + 2 (19 item 9). The
  bounded-job budget (15 min) is calibrated, then frozen in the method version (19 item 8).
- 2026-10-13 20:12 ET: round 2 answers: Q9 accepted (both LLM roles in the sensitivity check).
  Q10 sharpened by Yan-Ru: one provider, Codex, is the default for every agentic task; Claude is
  kept only as the secondary provider for the sensitivity check. Matches ADR 0006
  (`docs/adr/0006-rewrite-providers-work-in-a-guarded-workspace.md:32`) and `swdb/rewrite.py:78`.
  Shared understanding confirmed.

## Answer

2026-10-13 20:12 ET. Decided with Yan-Ru in a grilling session (rounds 1-2 in Comments; shared
understanding confirmed). Facts: re-checked in code this session (paths in the 19:53 and 20:12 ET
comments; 19 and 20 resolved in parallel, their inputs in item 10). Starting values below are calibrated and frozen with the method version (18 item 7).

1. **One primary metric per RQ** (Q1); every other metric listed in the Question goes to secondary
   tables or the appendix.

   | RQ | Primary metric |
   |---|---|
   | RQ1 | Proof rate per level (proven unbounded; at least proven within bounds) |
   | RQ2 | Proof-rate difference over WP alone at equal wall time; median provider calls per proven candidate, seeds on vs off |
   | RQ3 | Median per-candidate proof time; per contract, agent time and Yan-Ru's review hours |
   | RQ4 | Refutation rate of seeded faults and of N > 1 races; repair rate |
   | RQ5 | Speedup gap, best proven vs best certified candidate artifact |

   **Pass-bar reading:** the pooled held-out point estimate (n about 60, about +/-13 points) against
   18's bar, with the 95% Wilson interval always shown. A bar whose interval crosses its threshold
   is reported as "met, not significant". Per-kernel rates are reported beside it.
2. **Baselines** (Q2):
   - **Testing-only certification** (RQ1, RQ4): the same candidate artifacts through certification
     only. Reported: how many it accepts that the bounded verifier refutes (our counterpart to
     T-LLM's 33.8% false acceptance, research 22), and which seeded faults each side catches.
   - **WP alone at equal wall time** (RQ2; 13 item 11): all solvers, the full 60-minute budget, no
     hints.
   - **No contract** (RQ3; was "hints without contracts"): the same proof-hint loop and budget
     proving the whole function against the baseline implementation directly. Bounded half: SAW
     whole-function equivalence (the per-pair mirror of T-LLM and VERT). Unbounded half: direct WP;
     its form is a setting until ticket 24 decides on an alignment hint kind.
   - **Repair mirrors run** (RQ4): safety-only acceptance (ESBMC-AI: accept when the bounded verifier
     finds no safety violation; no unit relation, no re-certification); verdict only and ask again
     (FLOURINE, ESBMC-AI's ablation), both at equal provider calls.
   - **Cited, not run:** LLOR (needs an LLOV install; our race fix is already one fixed rule, 15
     item 10) and DR.FIX (Uber-internal, Go). A ThreadSanitizer-accepted repair baseline (Archer,
     instrumented libomp) runs only if it installs within a one-day time box.
3. **Reverted repairs** (Q3): a repair counts only if the repaired code passes the contract-match
   check for the same rewrite contract. One that drops the offload or normalizes to the baseline's
   content hash is a **reverted repair** (glossary), reported apart. Patch size is reported as tree
   edit distance (Orvalho et al.).
4. **Repair budget** (Q4): 5 rounds, one provider call each, counted in the campaign's provider-call
   budget. Repair rate is reported after round 1 and after round 5.
5. **Repeats and statistics** (Q5): the candidate population is generated once and frozen by content
   hash; only the LLM-driven loops repeat.
   - Configurations with an LLM (proof-hint loop, repair): 3 independent runs. Primary rate = mean
     over runs; "proven in any run" is secondary (sound, but 3x the budget).
   - Configurations without one (WP alone, SAW, CIVL, GenMC): 1 run.
   - Paired per candidate: exact McNemar for proven or not; Wilcoxon signed-rank for provider calls
     and time.
   - Provider kind, model and effort pinned in the run plan; a change is a new run plan and the
     affected runs are redone.
   - Estimate (not measured): at most about 760 worker-hours (about 95 LLM candidates x 8
     configurations x 60 min), about 3 days on 12 workers.
6. **mbit10 placement** (Q6): one lane job runs up to 6 proof workers, each pinned to its own core,
   each under an 8 GB RSS cap (LR-07; at most 2 lanes, per the lane rules). Per unit:
   wall time and CPU time; per batch: host load. The configurations under comparison are interleaved
   within one batch so load affects them alike. Proof time is a cost metric, never a speed claim.
7. **Providers** (Q7, Q9, Q10): **Codex is the one default provider for every agentic task**
   (rewriting, proof hinting, repair, contract drafting, the Rocq theorem), at the adapter pin
   `gpt-5.6-sol`, effort `xhigh` (`swdb/provider_adapters.py:24`; ADR 0006). **Claude is the
   secondary provider**, used only in a sensitivity check: the project's pin `claude-sonnet-5-5`,
   effort `high` (`:25`), in both the proof-hinting and repair roles, on BFS and SSSP, 1 run each.
   Reported, never part of a pass bar; the paper states both pins and calls it a sensitivity
   check, not a model comparison. In the cut order it goes before PR.
8. **Ablations** (Q8): seeds on vs off (every kernel); chained vs bundled (BFS only, 17 item 9);
   summaries vs inlined building blocks (BFS's 2-lane bar plus SSSP). No checker-off run: rejections
   are already recorded by rule (13 item 8) and reported as what the checks blocked. The CIVL bound
   sweep belongs to ticket 19.
9. **Kept as given in the Question:** the method checks reported as evidence, the concurrency
   ladder, as written vs repaired at every N, and the Mac/mbit10 labeling.
10. **Taken from tickets resolved in parallel** (no question asked): the small-scope curve (19 item
    9: seeded faults and LLM candidates refuted at the minimum bounds, +1 and +2) is a secondary
    RQ4 result; each bounded job keeps 19 item 8's 15-minute budget, frozen with the method version.
    PR's correctness check in the evaluation compares per vertex against the baseline at a fixed
    iteration count (20), not GAPBS's `PRVerifier` at the authors' defaults; the authors' PR is an
    RQ4 subject (refute, then repair).

**Changes to earlier tickets:** 18 item 9's cut order becomes: the Claude sensitivity check, RQ5,
then PR.

**Inputs passed on:**
- **Ticket 24:** the no-contract baseline's unbounded half uses whatever direct method 24 decides.
- **Ticket 25:** provider calls of repair (5 rounds) and of the proof-hint loop count in the
  campaign's provider-call budget.
- **Ticket 26:** records must carry run index (1-3), provider pin, worker core, wall and CPU time,
  batch load, and the reverted-repair flag.
- **Ticket 27:** the ThreadSanitizer time box; the 6-worker lane job as a build item.

Glossary: reverted repair added.
