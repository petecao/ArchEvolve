# 68 — knob_range and schedule_range: make the contracts' named checks enforceable

Created: 2026-10-04 21:35 ET (by the final code review, 2026-10-04, requested known issue 3)
Updated: 2026-10-04 21:35 ET (resolved)
**Type:** slice
**Status:** resolved
**Blocked by:** —
**Spec:** `../spec.md`; [code review](../code-review-2026-10-04.md), [17](17-bfs-read-offload-contract.md), [42](42-bc-certification-and-derived-contract.md), [43](43-promote-bc-contract.md)

**What to build:** `swdb certify` reports the two checks that both promoted contracts name but that no
run reported before:
- `knob_range`, named by clause `frontier_threshold`;
- `schedule_range`, named by clause `schedule`.

Each check gets a negative control that only that check rejects. The contract text and the shared
entries' normative content are unchanged.

## Acceptance

- [x] `knob_range`: every tunable knob value lies in the contract's declared range.
- [x] `schedule_range`: the schedule parameters lie in their declared ranges.
- [x] One negative control per check (an out-of-range knob, an out-of-range schedule), rejected by
  its named check.
- [x] Ticket 20 (BFS) and ticket 42 (BC) re-certify, and the record says the clauses are now enforced.
- [x] No shared entry's normative content changes.

## Answer

Resolved 2026-10-04 21:35 ET by the agent. Agent-decided under Yan-Ru's 2026-10-04 delegation; revisable.

**Design** (new module `swdb/certification_legality.py`).

Both checks are evaluator-owned. They run on the preprocessed private build copy of every matrix and
control build: `g++ -E` with the build's flags, run from a probe copy outside the tree, so the tree
identity is unchanged.
- **`knob_range`** checks every knob in the contract's `knobs`:
  - Its value comes from the candidate's knob assignment `SWDB_KNOB_<NAME>`, the interface that
    Extensa campaigns define. The macro is expanded at the end of the translation unit and at the
    build's tile size.
  - The value must be an integer constant inside `min`/`max` (with `upper_bound: build.tile_size`),
    or one of `choices`. Non-constant expressions are refused.
  - A knob that is not assigned keeps the contract default and is recorded as `contract_default`.
- **`schedule_range`** is structural, matching the clause's discharge mode. Every OpenMP
  worksharing-loop `schedule` clause in the candidate's own translation unit is checked after
  preprocessing (macros and `_Pragma` resolved, inactive code removed):
  - its kind must be one of the `schedule` knob's choices (dynamic or static); `monotonic` and
    `nonmonotonic` modifiers are allowed;
  - any chunk must be an integer constant inside the `schedule_granularity` range;
  - a loop without a `schedule` clause uses the default (static), which is in range.
- **Failures.** A matrix cell that fails either check is `failed`, and its reason is the check name.
  Campaign feedback has a fixed message for both checks.
- **Controls.** The certifier owns two controls, run beside the plug-in's at each tile size:
  - `knob_out_of_range` sets the assignment of the knob whose clause names `knob_range`
    (`frontier_threshold`) to its minimum minus one. It edits the campaign knob block if there is
    one, otherwise it adds a block.
  - `schedule_out_of_range` puts `schedule(guided)` on every `#pragma omp ... for` line. Guided is
    valid OpenMP, so the runs still pass and only `schedule_range` can reject the control.
  - A build failure still never rejects a control. A candidate's own `static_assert` on the knob
    stops the control's build (a7's best patch does), but `knob_range` has already named it. Such a
    control is `rejected` with reason `knob_range`, and the failed build is recorded.
- **Clause controls.** The contract pairs `frontier_threshold` with control `chunk_off_by_one` and
  `schedule` with `shared_context`. Neither control changes a knob assignment or a schedule clause,
  so neither pair can ever match.
  - Those rows stay in `clause_controls`, marked not enforceable with reason
    `control_cannot_exercise_check`.
  - A `certifier` row (`knob_out_of_range` → `knob_range`, `schedule_out_of_range` →
    `schedule_range`) is enforceable, and a mismatch on it fails the verdict.
  - Changing the contract's control IDs is a wording change for Yan-Ru. It was not made, and no
    contract or library entry changed.
- **Records.**
  - `schemas/certification.schema.json`: `clause_controls[].source` gains `certifier`, and rows gain
    `reason`.
  - Matrix cells and controls carry `legality_checks` (resolved knob values and the schedule rows
    found).
  - Certification command `1.2`. Records before `1.2` report neither check.
  - `source_digest` now covers `certification_legality.py`.

**Re-certification (Mac, g++-16, scratch records copy, not committed)**:
[`evaluation/legality-checks-recertification-2026-10-04.json`](../evaluation/legality-checks-recertification-2026-10-04.json).

| Input | Certification | Tree | Matrix | Controls | `frontier_threshold` / `schedule` |
|---|---|---|---|---|---|
| Ticket 20 BFS patch (`contract.bfs_read_offload` `867fac18…`) | `certification.028d19d09b9a4b509c816fefebbedd9e` | `991de652…` | 10/10 | 20/20 | enforced, matched |
| Ticket 42 BC patch (`contract.bc_read_offload` `96927643…`) | `certification.032979943b5640d7a99e2caca3e9b489` | `d6f86eb6…` | 10/10 | 28/28 | enforced, matched |
| a7 best `it4.kronecker.a2` | `certification.e45ee7ed74ce43cd9e2e0ccd17c9d996` | `c8f4bf16…` | 10/10 | 20/20 | enforced, matched |
| a7 best `it8.uniform_random.a1` | `certification.fb19e082ea3a4fdbbf1a4dda63a76fbb` | `d63c714a…` | 10/10 | 20/20 | enforced, matched |

- The tree hashes equal the ticket 20 and ticket 42/43 pins and the a7 candidate records.
- Ticket 20 and BC keep the contract defaults (64, tile size, dynamic, 1). Both a7 bests assign
  `frontier_threshold` 1 and `chunk_size` 16384. All schedule clauses are `dynamic` (1 or 64) or the
  default.
- Clauses `frontier_threshold` and `schedule` of both promoted contracts are now enforced by
  `knob_range` and `schedule_range` on every certification.

**Tests.**
- `tests/test_certification_legality.py`, 22 cases:
  - constant evaluation and refusals;
  - assignments, defaults and out-of-range values;
  - the schedule scan (main file only, modifiers, refused kinds and chunks);
  - both control mutations;
  - clause rows;
  - a full `certify()` of a candidate on the knob interface with a `static_assert` (certified, 20/20,
    knob control rejected by `knob_range` despite the failed build);
  - a full `certify()` of a `schedule(guided)` candidate, refused on every cell by `schedule_range`
    while every run passes the verifier.
- `tests/test_certification_controls.py`: 20 controls, legality sites and certifier rows.
- Suites (Mac): certification controls 16, legality 22, typed certification 123, BC certification and
  feedback 40, Extensa (campaign, targets, selection, budgets, boundary, machinery, library
  operations) 123, library index/submit/typed library and format docs 112, all passed. `swdb validate`:
  524 records valid.
