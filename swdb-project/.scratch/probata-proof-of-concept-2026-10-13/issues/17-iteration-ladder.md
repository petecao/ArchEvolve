# 17 — Iteration ladder

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
**Blocked by:** 15
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) (sections "Extensa mode" (iteration ladder), "Loop, modes and guards", "Testing Decisions" seams 3 and 4 and the leakage-check negative controls); decisions: [28](../../formal-verification-2026-10-09/issues/28-extensa-iteration-ladder.md) items 1-10 and its build items, [25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md) item 4 and its Later changes
**Time estimate:** about 2 days

**What to build:** Every new Extensa campaign shows the rewrite provider its own history, as
Extensa does. From iteration 2, and in repair workspaces, the loop writes `LADDER.json` from
campaign state: one row per earlier candidate artifact, with its contracts, knobs, level known so
far, verdict, numbers, reason codes and winner mark. Rows never carry patches, counterexamples or
raw timings. `FEEDBACK.json` stays. The rewrite prompt names the new file. The campaign records
`rewrite_workspace: v2`; older campaigns read as `v1` and never gain an iteration ladder. The whole
path runs in `swdb campaign --fixture` with the scripted verifier adapter.

## Acceptance

- [ ] **Where it appears.** In a new fixture campaign, iteration 1's workspace has no
  `LADDER.json`. Every rewrite workspace from iteration 2 has it. Every repair workspace
  (certification and counterexample) gets the same file as its iteration's rewrite workspace.
  `FEEDBACK.json` is still present. The rewrite prompt names `LADDER.json`.
- [ ] **One row per earlier candidate artifact, no gaps.** Rejected candidate artifacts get rows.
  A counterexample-repaired candidate artifact gets its own row with `repair_of` naming the refuted
  one. An
  iteration whose rewrite call returned nothing gets one row with class `-` and reason
  `provider_output_invalid`. Fixture with a rejected, a repaired and an empty iteration: iteration
  numbers run without gaps and the row count matches state. No row cap.
- [ ] **Columns (28 item 3).** Iteration, class, contracts, knobs, level, verdict, ratio, lower,
  spread, reason codes, public failed-check names, winner mark. Surviving negative controls appear
  only as one aggregate category.
- [ ] **Levels known so far.** Each row's level is one of: rejected, uncertified, certified,
  refuted, proven within bounds at threads = 1, proven within bounds at threads ≤ k. Proven
  unbounded never appears.
- [ ] **Winner marks.** `fastest`, `best_proven`, `both` or empty, recomputed each iteration from
  15's winners. Fixture: when the winners change between iterations, the marks move with them.
- [ ] **New reason codes.** `refuted` (with its check category only) and `proof_timeout` join the
  feedback reason list; the closed-field check accepts both.
- [ ] **Leakage tests, each with its negative control.** Planted in campaign state, each of these
  is kept out of the file by the closed-field check: counterexample text, a raw timing, a patch
  body, a detailed surviving-control name, an unknown field. The workspace record of every provider
  call hashes `LADDER.json`, so what each call saw is auditable.
- [ ] **Written by the loop only.** The file is rebuilt whole each iteration from campaign state.
  Control: a `LADDER.json` planted or edited in the campaign folder never reaches a later
  workspace; the next file matches state.
- [ ] **Workspace version.** New campaigns record `rewrite_workspace: v2` in state and summary. A
  summary without it reads as `v1`, and old summaries still pass `swdb validate`. The campaign file
  has no iteration-ladder setting: one that names `rewrite_workspace` is refused (it is a record,
  not a setting).
- [ ] **Resume.** A resumed `v1` campaign never gains an iteration ladder. A resumed `v2` campaign
  rebuilds the file from state, never from an old file.

## Notes

- **Not in this ticket:**
  - 15 — Two winners: computing the winners; `best/`'s two patches.
  - 14 — Bounded gate in the campaign: the gate outcomes behind `refuted` and `proof_timeout`.
  - 13 — Counterexample-guided repair: each counterexample repair as a new candidate artifact.
  - 12 — Proposal and promotion fields: repair lineage on proposals.
  - 16 — Post-campaign WP phase and budgets: proven unbounded, which arrives after the loop.
  - 34 — proof_hinting role and workspace: hint records never enter a rewriting workspace.
  - 18 — ArchEvolve mode level and handoff block: ArchEvolve mode has no iterations, so no
    iteration ladder.
  - evaluation 05 — LLM candidate populations: population calls see no iteration ladder.
  - evaluation 10 — RQ5: end-to-end BFS campaigns: campaign a7 labeled "no ladder (v1)"; the paper's
    limit sentence (the iteration ladder's effect on the speed gap is not measured).
- On by default, no off switch (28 item 1). No iteration-ladder ablation is run.
- Leakage rules are D8's: never raw timings, workload files, evaluator inputs, other campaigns'
  artifacts or the authors' accelerated code. A refutation shows only "refuted" and its check
  category; the counterexample goes only to repair.
- Assumption (not decided in the map): "repaired ones with `repair_of`" means counterexample-guided
  repairs, which are new candidate artifacts (25 item 3). A certification repair (D7) stays inside
  its candidate artifact's row, as today.
- Assumption (not decided in the map): if a candidate artifact's computed level is proven unbounded
  during the loop (for example from a record made outside this campaign), its row shows the highest
  bounded rung its records support. Raise with Yan-Ru if this case ever occurs.
- Assumption (not decided in the map): 28's build items call for a versioned iteration-ladder
  renderer. The renderer version is written into `LADDER.json` itself, and the file's top-level
  shape is an object holding that version and the rows.
- Assumption (not decided in the map): rows cover earlier iterations only, and a repair call in
  iteration 1 sees no iteration ladder. Reading: repair calls get their iteration's workspace (28
  item 8), and the file is rebuilt once per iteration from iteration 2 (28 item 2, build items).
  28's build items also say "in repair workspaces" without an iteration limit; confirm with Yan-Ru
  if a refuted iteration-1 candidate artifact's repair should see a one-row file.
- Generality: per kernel, contract, workload class and hardware target. Contract fixtures only; no
  held-out kernel (BC, PR, SSSP).
- Tests use the scripted adapter; no real verifier job runs. Full-suite runs on the Mac use at most 2
  test workers.
