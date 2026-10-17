# 28 — How should the Extensa-mode rewrite workspace show earlier candidate artifacts, and what keeps campaigns with and without it comparable?

Created: 2026-10-13 21:00 ET (Yan-Ru's "yes" after ticket 25; opened as typed-library ticket 81, moved
here 21:03 ET at Yan-Ru's request)
**Type:** grilling
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-13 21:10 ET)
**Blocked by:** 25
**Map:** `../map.md`

## Question

Extensa's loop lets each iteration see every earlier one; SWDB's Extensa mode does not. Yan-Ru chose
to port the ladder only (2026-10-13 21:00 ET). Decide the ladder's design so a build ticket can be
cut:

1. **Format:** a Markdown table like MemAcc's, or JSON.
2. **Patches in rows:** whether rows carry patches, or only the winners keep theirs (`best/`).
3. **Resumed campaigns:** whether a campaign started before the change gains a ladder on resume.
4. **Comparability:** how campaigns with and without a ladder stay apart in records and in RQ5 (18,
   25 item 6).
5. **Proof levels in rows:** how a row shows the levels of 25 item 4 (bounded levels known in the loop;
   proven unbounded only after WP) and marks both winners.
6. Whether D8 and ADR 0010 need a note.

## Inputs already decided

- **Ladder only (Yan-Ru):** `lessons.md` (free text the agent writes; leakage risk) and M3 (a system
  prompt that evolves during a campaign, against frozen prompts) stay out.
- **Proposed shape (agent):** from iteration 2, one row per earlier candidate artifact of the
  campaign, rejected ones included: iteration, class, contracts applied, certification level, verdict,
  ratio, lower bound, feedback reason code. Written by the loop, never by a provider, and rewritten
  whole each iteration (as MemAcc's `render_ladder`). Same leakage rules as D8's feedback: no raw
  timings, workload files, evaluator inputs, other campaigns' artifacts or the authors' accelerated
  code; surviving negative controls only as one aggregate category (typed-library ticket 76); a
  refutation only as "refuted" plus its check category, never the counterexample (repair only). The
  prompt names the file (`rewrite_prompt`, `swdb/campaign.py:485-512`).
- **Planning only (map Notes):** this ticket decides; the build is a later ticket in the
  proof-of-concept effort (Mac only, contract-fixture tests).

## Facts

- **MemAcc's Extensa shows every earlier iteration.** Its launcher writes `ladder.md`, one row per
  completed iteration (transformations cited, ratio, lower bound, verdict, adopted, reason), and
  rewrites it whole each iteration (`MemAcc/AgenticRefiner/refiner/launcher.py:1659`); every
  iteration's prompt says to read it (`refiner/claude_invoke.py:38`). Design: meta-prompting M1-M3,
  `AgenticRefiner/docs/superpowers/specs/2026-04-28-agentic-refiner-design.md` §7. MemAcc's regime
  study found the ladder empty in its first runs and fixed it.
- **SWDB's port shows only the best patch per class and the previous iteration's feedback**
  ([D8](../../typed-library-dx100-bfs-2026-10-03/extensa-design-2026-10-03.md);
  `swdb/campaign.py:856-860`; the feedback is overwritten each iteration, `swdb/campaign.py:908`). The
  launcher and prompts were not ported (D1).
- **The paper's system is "Extensa's loop plus the proven levels"** (map Notes), so the loop should
  keep Extensa's history.

## Comments

- 2026-10-13 21:00 ET: opened at Yan-Ru's request as typed-library ticket 81 (`needs-triage`, slice).
  Question asked: "each iteration, we are able to see previous candidates from iteration 0 to n-1
  during Nth iteration? because we have meta prompting stuff." Answer: true in MemAcc's Extensa, not in
  SWDB's Extensa mode (facts above).
- 2026-10-13 21:03 ET: moved into this map at Yan-Ru's request ("put the ticket in this plan path").
  Recast as a grilling ticket because the map is planning only; the triage questions became the
  Question.
- 2026-10-13 21:13 ET: claimed 21:10 ET. Facts checked in code this session: every materialized candidate's diff is
  already in its candidate record (`swdb/campaign_targets.py:540-545`), rejected-before-build ones have
  only a patch hash (`swdb/campaign.py:912-922`); feedback fields are a closed set with leakage checks
  (`swdb/extensa/search.py:322-341`); each provider call's `workspace.json` already hashes every
  visible file (`swdb/provider_roles.py:181-187`); all 15 BFS campaigns are stopped (summaries in
  `records/campaign_summaries/`) and resume refuses a stopped campaign (`swdb/campaign.py:1148-1149`);
  a7 ran with `max_iterations: 8`; ADR 0009 hides "other candidate artifacts", which D8 reads as
  outside the campaign's own lineage. MemAcc ladder facts requested from a sub-agent. Round 1 posted
  (format, rows, levels, FEEDBACK.json, resume, marker, RQ5, LLM population); patches in rows and the
  D8/ADR notes wait for round 2.
- 2026-10-13 21:15 ET: MemAcc ladder facts (sub-agent, read-only; paths under `MemAcc/AgenticRefiner/`):
  rows carry no patch (patches stay in `history/iter_NNN.patch` and `best_candidate.patch`); one row per
  iteration whose self-report was read, so a no-report or attribution-rejected iteration leaves a gap
  (`refiner/launcher.py:3479-3506,3573-3574`); a scope-rejected row keeps its place with numbers blanked
  (`:4795-4804`); no row cap (`:1677-1680`); rebuilt from memory, never read back, and no record of what it
  held per iteration (`:2628`); no on/off flag, pre/post-fix runs told apart only by `tool_revision`.
  Design §7 had the agent edit the ladder (M2); the code made it a launcher-written results table, which
  is our proposed shape. Correction to Facts: `refiner/claude_invoke.py:38` is the legacy wrapper; the
  production prompt is `refiner/launcher.py:2340-2345`. Round 1 addendum posted: Q9 patches, Q10 no gaps.
- 2026-10-13 21:23 ET: round 1: Q1-Q6 and Q8 accepted by Yan-Ru. Q7 "are you sure?" plus: what are the ladder and
  FEEDBACK.json, should the ladder be the default, how should it be treated, does Extensa use it by
  default. Re-checked: RQ5 is within one campaign (the gap between its two winners, 25 item 4; 23 item 1)
  and runs only on new campaigns (25 item 6), so "never pool" holds by construction; no RQ in 18 is about
  the ladder. Refinement: the paper may not claim the ladder or its level column causes RQ5's gap. MemAcc
  writes the ladder with no off switch (`refiner/launcher.py:4812`), empty before `bc92c2eec`
  (2026-08-25). Follow-ups posted: Q6b (marker recorded by the loop, no off switch), Q11 (glossary term
  "iteration ladder"; "rung" already names a level step in 15, 19, 25). Q9, Q10 still open.
- 2026-10-13 21:28 ET: Q6b, Q9, Q10, Q11 accepted by Yan-Ru; glossary "iteration ladder" added. Yan-Ru asked to confirm
  the ladder is on by default and for one Q7 recommendation. Round 2 posted: Q12 D8 note, Q13 no ADR,
  Q14 repair calls see the ladder.
- 2026-10-13 21:32 ET: round 2: Q7 (one recommendation), Q12, Q13, Q14 accepted by Yan-Ru. Frontier empty.

## Answer

2026-10-13 21:32 ET. Decided with Yan-Ru in a grilling session (rounds 1-2 in Comments; every recommendation
accepted, Q7 after an "are you sure?" re-check, Q6 revised by Q6b). Facts: SWDB code re-checked this
session (21:13 ET comment); MemAcc's ladder read by a sub-agent (21:15 ET comment).

1. **On by default, no off switch** (Q6b; Yan-Ru's question). Every new Extensa campaign has the
   iteration ladder, as Extensa does: MemAcc writes `ladder.md` after every verdict with no flag
   (`MemAcc/AgenticRefiner/refiner/launcher.py:4812`). The loop records `rewrite_workspace: v2` in the
   campaign state and summary; a summary without it reads as `v1` (today's D8 shape; the 15 BFS
   campaigns). The campaign file has no such field, so it is a record, not a setting; a future
   ablation would add a new version. Caveat for the paper: MemAcc's ladder stayed empty until commit
   `bc92c2eec` (2026-08-25); check that Extensa's published runs postdate it before writing
   "Extensa's ladder".
2. **Format** (Q1): `LADDER.json` in the rewrite workspace, beside `FEEDBACK.json` and `REGIONS.json`.
   The loop builds every row through the closed-field check feedback uses
   (`swdb/extensa/search.py:322-341`) and rewrites the file whole each iteration from `state.json`;
   no provider writes it. The rewrite prompt names it (`swdb/campaign.py:485-512`).
3. **Rows** (Q2, Q10). One row per earlier candidate artifact of the campaign, rejected ones included;
   a repaired candidate gets its own row with `repair_of` (25 item 3). An iteration whose rewrite call
   returned nothing gets one row (class `-`, reason `provider_output_invalid`), so iteration numbers
   have no gaps (MemAcc skips such iterations). Columns: iteration, class, contracts, knobs, level,
   verdict, ratio, lower, spread, reason codes, public failed-check names (surviving negative controls
   as one aggregate category, typed-library ticket 76), winner mark. Never raw timings, workload files,
   evaluator inputs, other campaigns' artifacts or the authors' accelerated code (D8). No row cap
   (a7 ran 8 iterations).
4. **Levels and winners** (Q3). Each row shows the level known when the ladder is written: rejected,
   uncertified, certified, refuted, proven within bounds at threads = 1, or at threads <= k. Proven
   unbounded never appears (WP runs after the campaign stops, 25 item 1). Two new reason codes:
   `refuted` (check category only; the counterexample goes only to repair, 13 item 10) and
   `proof_timeout`. `winner` is `fastest`, `best_proven`, `both` or empty, recomputed each iteration
   (25 item 4).
5. **No patches in rows** (Q9). `best/` keeps the fastest winner's patch and, when it differs, the
   best-proven winner's, per class (25 item 4). MemAcc's rows carry no patch either.
6. **`FEEDBACK.json` stays** (Q4): the last iteration's explanations; the ladder gives every
   iteration's outcome.
7. **Resume** (Q5). A campaign's workspace shape is fixed when it starts: a `v1` campaign never gains a
   ladder on resume; a `v2` campaign rebuilds it from `state.json`, never from an old file. No campaign
   is affected today: all 15 have stopped and resume refuses a stopped one
   (`swdb/campaign.py:1148-1149`).
8. **Repair calls** (Q14). Certification and counterexample repair calls inside a campaign see the
   ladder; they get the same workspace (`swdb/campaign.py:973`).
9. **Comparability** (Q7, Q8).
   - RQ5 uses only new campaigns (25 item 6), so all have the ladder; the a7 worked example is labeled
     "no ladder (v1)". No ladder ablation: it would double RQ5's lane-hours, and RQ5 is cut first.
   - The paper reports RQ5 for Probata as built and states one limit: it does not measure whether the
     iteration ladder, or its level column, changes the speed gap. The useful ablation (levels shown vs
     hidden) is future work.
   - 18 item 6's LLM population comes from independent calls with no ladder (27 item 4: the
     ArchEvolve-mode rewriting role), so its certification rate stays a rate over independent
     proposals. RQ4's repairs run outside campaigns and see none.
10. **What each call saw is auditable.** Each provider call's `workspace.json` already hashes every
    visible file (`swdb/provider_roles.py:181-187`); MemAcc keeps no record of what its ladder held.
11. **D8 note, no ADR** (Q12, Q13). D8 gets a dated note (the ladder; `best/` up to two patches per
    class). ADR 0009 and ADR 0010 stay unchanged: the ladder is easy to reverse (a new workspace
    version), and its rows describe the campaign's own candidates without code, inside D8's reading of
    ADR 0009's "other candidate artifacts".
12. **Generality.** Per kernel, contract, workload class and hardware target; nothing BFS-specific.
    ArchEvolve mode has no iterations and so no ladder (ADR 0010: one proposal attempt plus bounded
    repair).

**Build items** (27's "Extensa ladder" ticket on the Extensa track, cut with the track's end-to-end
exit; Mac, contract-fixture tests): a versioned ladder renderer from `state.json`; `LADDER.json` in
`_workspace` from iteration 2 and in repair workspaces; the prompt sentence; `refuted` and
`proof_timeout` in `FEEDBACK_REASONS`; `rewrite_workspace` in state and summary; the row for an
empty iteration; leakage tests (no counterexample, no raw timing, surviving controls aggregated).

**Changes to earlier tickets:** 18 item 6 and RQ5 (population calls see no ladder; the RQ5 limit
sentence); 25 item 4 (ladder rows carry levels and both winner marks); D8 (note). Glossary: iteration
ladder added.
