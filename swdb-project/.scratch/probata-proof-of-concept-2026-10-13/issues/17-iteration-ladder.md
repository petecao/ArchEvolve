# 17 — Iteration ladder

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 07:46 ET (resolved); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
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

- [x] **Where it appears.** In a new fixture campaign, iteration 1's workspace has no
  `LADDER.json`. Every rewrite workspace from iteration 2 has it. Every repair workspace
  (certification and counterexample) gets the same file as its iteration's rewrite workspace.
  `FEEDBACK.json` is still present. The rewrite prompt names `LADDER.json`.
- [x] **One row per earlier candidate artifact, no gaps.** Rejected candidate artifacts get rows.
  A counterexample-repaired candidate artifact gets its own row with `repair_of` naming the refuted
  one. An
  iteration whose rewrite call returned nothing gets one row with class `-` and reason
  `provider_output_invalid`. Fixture with a rejected, a repaired and an empty iteration: iteration
  numbers run without gaps and the row count matches state. No row cap.
- [x] **Columns (28 item 3).** Iteration, class, contracts, knobs, level, verdict, ratio, lower,
  spread, reason codes, public failed-check names, winner mark. Surviving negative controls appear
  only as one aggregate category.
- [x] **Levels known so far.** Each row's level is one of: rejected, uncertified, certified,
  refuted, proven within bounds at threads = 1, proven within bounds at threads ≤ k. Proven
  unbounded never appears.
- [x] **Winner marks.** `fastest`, `best_proven`, `both` or empty, recomputed each iteration from
  15's winners. Fixture: when the winners change between iterations, the marks move with them.
- [x] **New reason codes.** `refuted` (with its check category only) and `proof_timeout` join the
  feedback reason list; the closed-field check accepts both.
- [x] **Leakage tests, each with its negative control.** Planted in campaign state, each of these
  is kept out of the file by the closed-field check: counterexample text, a raw timing, a patch
  body, a detailed surviving-control name, an unknown field. The workspace record of every provider
  call hashes `LADDER.json`, so what each call saw is auditable.
- [x] **Written by the loop only.** The file is rebuilt whole each iteration from campaign state.
  Control: a `LADDER.json` planted or edited in the campaign folder never reaches a later
  workspace; the next file matches state.
- [x] **Workspace version.** New campaigns record `rewrite_workspace: v2` in state and summary. A
  summary without it reads as `v1`, and old summaries still pass `swdb validate`. The campaign file
  has no iteration-ladder setting: one that names `rewrite_workspace` is refused (it is a record,
  not a setting).
- [x] **Resume.** A resumed `v1` campaign never gains an iteration ladder. A resumed `v2` campaign
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

## Answer

2026-10-14 07:46 ET (agent session, branch `probata-poc/t17`). Every acceptance box is met with contract-fixture
tests (`swdb campaign --fixture`, scripted verifier adapter); no real verifier or provider ran.

**What was built**

- `swdb/iteration_ladder.py`: the versioned renderer (`render`; file format `swdb.iteration-ladder.v1`, written
  into the file), the closed-field check (`check_row`, built on D8's feedback check: closed columns, the
  `_FORBIDDEN_FIELD` pattern, `FEEDBACK_REASONS`, public failed-check names only, ticket 13's counterexample
  detector, no multi-line or diff text), `version_of`/`shown` (v1/v2) and `gate_feedback` (the new reasons).
- `swdb/campaign.py` (small, separate hunks): `Campaign._ladder(iteration)` rebuilds the text from `state.json`
  and the level rule's levels now, and `_workspace` adds `LADDER.json` (so every certification repair workspace
  gets the same bytes); the counterexample repair loop gets it as `ladder=`; the prompt sentence;
  `rewrite_workspace: "v2"` in new state and `rewrite_workspace` in every summary (`v1` when the state names
  none); the rejector keeps `rejection_reason` and `rejection_failed_checks`; the bounded gate adds `refuted` and
  `proof_timeout` feedback. The campaign folder keeps a copy of the latest file; nothing reads it.
- `swdb/counterexample_repair.py` (`loop` and `repair_round` take `ladder=`) and `swdb/provider_workspace.py`
  (the ladder at `.swdb-context/LADDER.json`, byte-identical, hashed as `iteration_ladder` in `workspace.json`,
  listed in the prompt's locations, one conditional prompt sentence).
- `swdb/extensa/search.py`: `refuted` and `proof_timeout` join `FEEDBACK_REASONS`.
- `schemas/campaign_summary.schema.json`: `rewrite_workspace` (`v1` or `v2`). Docs: format-v0.4-extensa.md,
  "The iteration ladder". The campaign-file schema already refuses `rewrite_workspace` (closed top level).
- Tests: `tests/test_iteration_ladder.py` (renderer seam: rows, gaps, no cap, levels, marks, version, the
  campaign-file refusal, reasons, prompt; each leak planted in state with its negative control) and
  `tests/test_iteration_ladder_campaign.py` (seam 3: a gated 4-iteration campaign with a proof timeout, an empty
  iteration, a refuted-and-repaired and a rejected candidate artifact; a v2 resume with a planted and an edited
  file; a v1 resume and an old summary through `swdb validate`). The fixture provider now logs the ladder it sees.

**Assumptions** (not decided in the map)

- Assumption: `repair_of` is the `row` number of the refuted candidate artifact's row, not its candidate ID:
  agent-role JSON inputs may not carry a `candidate` key (`provider_roles.FORBIDDEN_KEYS`), so rows carry a
  `row` number and no record IDs.
- Assumption: the empty iteration's row has level `rejected` (the call's output was rejected).
- Assumption: a refutation's "check category" is the refuting bounded rung, `bounded_threads_1` or
  `bounded_threads_k`, carried in `failed_checks`; `proof_timeout` carries only the class.
- Assumption: winner marks come from the last completed iteration's `winners` rows (ticket 15).
- Assumption: the proven-unbounded case (Notes) shows `proven_within_bounds_threads_k`, since an unbounded proof
  covers every thread count up to k.
- Assumption: a resumed v1 campaign's summary writes `rewrite_workspace: v1`; a summary without the field also
  reads as v1 and validates.
- Kept the ticket's own assumptions: certification repairs stay in their row; iteration 1's repair calls see no
  ladder; the renderer version is in the file.

**For other tickets:** 55 and the evaluation read `summary.rewrite_workspace` through
`swdb.iteration_ladder.version_of` (absent = v1, as for a7). A target adapter that rejects with `failed_checks`
should pass public names (the ladder re-applies `public_checks` anyway). When 16 calls `Campaign.summary` again,
the field is recomputed from state.
