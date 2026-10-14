# 81 — Extensa-mode iteration ladder: every earlier candidate artifact as one row in the rewrite workspace

Created: 2026-10-13 21:00 ET (Yan-Ru's "yes" after formal-verification ticket 25)
**Type:** slice
**Status:** needs-triage
**Blocked by:** None — can start immediately
**Spec:** `../spec.md` ("Extensa mode"); [design decisions](../extensa-design-2026-10-03.md) D8; ADR 0009, ADR 0010;
formal-verification [ticket 25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md) item 4

## Why

- **MemAcc's Extensa shows every earlier iteration.** Its launcher writes `ladder.md`, one row per
  completed iteration (transformations cited, ratio, lower bound, verdict, adopted, reason), and
  rewrites it whole each iteration (`MemAcc/AgenticRefiner/refiner/launcher.py:1659`); every
  iteration's prompt says to read it (`refiner/claude_invoke.py:38`). Design: meta-prompting M1-M3,
  `AgenticRefiner/docs/superpowers/specs/2026-04-28-agentic-refiner-design.md` §7. MemAcc's regime
  study found the ladder empty in its first runs and fixed it.
- **SWDB's port shows only the best patch per class and the previous iteration's feedback** (D8;
  `swdb/campaign.py:856-860`; the feedback is overwritten each iteration, `swdb/campaign.py:908`).
  The launcher and prompts were not ported (D1).
- **The paper's system is "Extensa's loop plus the proven levels"** (formal-verification map, Notes),
  so the loop should keep Extensa's history.
- **Yan-Ru's choice (2026-10-13 21:00 ET):** port the ladder only.

## What to build

- **The ladder:** from iteration 2, a file in the rewrite workspace with one row per earlier
  candidate artifact of this campaign, rejected ones included: iteration, class, contracts applied,
  certification level, verdict, ratio, lower bound, feedback reason code. The current winner per class
  is marked (the fastest winner; also the best-proven winner once formal-verification ticket 25's
  levels exist).
- **Written by the loop, never by a provider,** and rewritten whole each iteration, so a provider edit
  never survives (as MemAcc's `render_ladder`).
- **Same leakage rules as D8's feedback:** no raw timings, workload files, evaluator inputs, other
  campaigns' artifacts or the authors' accelerated code; surviving negative controls only as one
  aggregate category (ticket 76); a refutation only as "refuted" plus its check category, never the
  counterexample (that goes only to repair). The text passes the ported leakage check.
- **The prompt names the file** (the history list in `rewrite_prompt`, `swdb/campaign.py:485-512`).
- **D8 and the spec** say the workspace may hold the ladder.

**Out of scope (Yan-Ru):** `lessons.md` (free text the agent writes; leakage risk) and M3 (a system
prompt that evolves during a campaign, against frozen prompts).

## Triage must confirm (agent recommendations)

1. **Format:** a Markdown table like MemAcc's, or JSON. Recommend JSON with a one-line note in the
   prompt: the loop already passes structured feedback as JSON.
2. **Patches in rows:** recommend no. Patches stay only for the winners (`best/`), which bounds the
   workspace and keeps the role from copying old candidates.
3. **Resumed campaigns:** recommend the ladder only for campaigns started after the change; a resumed
   campaign keeps the workspace rules it started with.
4. **Comparability:** the campaign summary records a workspace-rule version, so campaigns with and
   without a ladder are never pooled unlabeled (RQ5 of the formal-verification map compares
   campaigns).

## Acceptance criteria

- [ ] From iteration 2, the workspace holds the ladder with one row per earlier candidate artifact of
      the campaign, rejected ones included.
- [ ] The loop writes it and rewrites it whole each iteration; it passes the leakage check.
- [ ] A test shows no raw timing, workload path, evaluator input, control name or counterexample in the
      ladder.
- [ ] The campaign summary records the workspace-rule version.
- [ ] D8 and the spec state what the workspace may hold.

Mac only, contract-fixture tests; no mbit10 runs (D35 blocks new real-target campaigns anyway).
Implementation waits for triage and Yan-Ru's approval.

## Comments

- 2026-10-13 21:00 ET: opened at Yan-Ru's request. Question asked: "each iteration, we are able to see
  previous candidates from iteration 0 to n-1 during Nth iteration? because we have meta prompting
  stuff." Answer: true in MemAcc's Extensa, not in SWDB's Extensa mode (facts above).
