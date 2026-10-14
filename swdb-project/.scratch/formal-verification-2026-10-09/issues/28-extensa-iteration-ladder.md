# 28 — How should the Extensa-mode rewrite workspace show earlier candidate artifacts, and what keeps campaigns with and without it comparable?

Created: 2026-10-13 21:00 ET (Yan-Ru's "yes" after ticket 25; opened as typed-library ticket 81, moved
here 21:03 ET at Yan-Ru's request)
**Type:** grilling
**Status:** ready-for-human
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
