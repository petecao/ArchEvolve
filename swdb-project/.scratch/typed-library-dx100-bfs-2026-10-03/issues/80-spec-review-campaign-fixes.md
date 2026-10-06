# 80 — Spec-review fixes: Extensa campaign budgets, pruning and export

Created: 2026-10-05 22:05 ET (from the spec review of tickets 38–78, findings C5–C8, C14–C17, C19)
Updated: 2026-10-06 00:25 ET (resolved)
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md` ("Extensa mode": budgets, records, site finder; "Raw-output retention and pruning");
[design decisions](../extensa-design-2026-10-03.md) D6, D7, D9, D10; ADR 0010, ADR 0011;
[52](52-campaign-skeleton.md), [54](54-campaign-budgets.md), [55](55-query-site-finder.md),
[56](56-native-campaign-target.md), [57](57-gem5-campaign-target.md), [73](73-provider-capacity-and-protected-regions.md),
[75](75-certify-a8-frontier-staging.md)

**What to build:** the remaining spec-review findings against the Extensa campaign loop, each verified first and
covered by a regression test. Yan-Ru asked (2026-10-05) that the review findings be addressed properly; every
judgment call below is **agent-decided under delegation; revisable**. Committed records are never rewritten.
Mac only; no mbit10 runs.

## Findings

- **C5.** The gem5 per-class baseline evaluation inside an iteration runs before the step's clock starts and is
  never charged to the lane-hour cap (`--baselines-only` charges it).
- **C6.** The provider-capacity backoff (ticket 73) can sleep up to 48 min inside the lane, uncharged; the spec
  says a pause releases the lane and does not count.
- **C7.** The independent test-generation call is charged, but its inputs never reach certification.
- **C8.** The gem5 adapter returns only the observed run's ID, so companion runs and the per-class baselines
  keep their bulky debug traces.
- **C14.** A native `base_source` other than `fork_scalar_tdstep` is accepted although every candidate artifact
  is built from the fork's scalar-only snapshot.
- **C15.** Library-operation regions are offered in REGIONS.json but every use is refused (a8 iteration 2).
- **C16.** BC evaluation records carry BFS "parent" labels and an `inconclusive` `parent_gather_race`.
- **C17.** Only the campaign summary reaches the team store; ticket 75 imported the a8 candidate by hand.
- **C19.** Identical trees across classes reuse the first class's candidate ID (a8's uniform best is
  `…it1.kronecker.a0`).

## Acceptance

- [x] C5: an iteration's gem5 baseline evaluation is checked against the cap and charged like `--baselines-only`.
- [x] C6: decided and documented in spec.md; a test covers it.
- [x] C7: no test-generation call is made (or charged) until certification accepts its inputs; documented.
- [x] C8: companion runs are pruned right after their comparison; per-class baselines at campaign stop; a team
  claim keeps them.
- [x] C14: `swdb validate` refuses a base source no adapter can build candidates from.
- [x] C15: library-operation applications are kept out of REGIONS.json, with a reason record.
- [x] C16: new BC records take labels from the kernel plug-in and carry no race result; old records revalidate.
- [x] C17: `swdb campaign-export` copies a candidate artifact's closure with sha256 checks, tags kept; fixture test.
- [x] C19: new campaigns write one candidate record per class, pointing to the shared tree; ticket 56 notes a8.

## Comments

- 2026-10-05 22:05 ET: claimed by the agent (worktree branch, not pushed).

## Answer

Resolved 2026-10-06 00:25 ET by the agent (worktree branch `worktree-agent-a1b55357276740991`, not pushed; Mac only,
no mbit10 runs). Every judgment call is **agent-decided under Yan-Ru's delegation; revisable**, and is listed in the
spec's "Awaiting ratification" table. No committed record was rewritten. Each finding was confirmed in the code
first; each new test fails on the code before its fix (checked for C5, C6, C8, C14 and C19 against the pre-fix
loop: 10 of 10 failed).

| Finding | Fix | Where | Tests |
|---|---|---|---|
| C5 | An iteration's gem5 class baseline is charged (`_spent`) and the comparison re-checked (`_step`), as `--baselines-only` does. | `swdb/campaign.py` `_evaluate` | `tests/test_campaign_budget_fixes.py` (2) |
| C6 | **Decision: charge, not release.** The socket lease belongs to the `socket_lane.sh` wrapper for the life of the campaign process, so an in-process wait cannot release it; releasing means exiting, which turns a 60 s capacity blip into a manual resume of an unattended run. Capacity backoffs and guard retry waits are charged to lane-hours (`budgets.used.provider_wait_hours`); a wait past the cap stops `lane_hours` without waiting; the calls stay uncounted. | `Campaign._wait` | 3 |
| C7 | No certify version takes generated inputs (each matrix is frozen), so no test-generation call is made or charged until one does; `skipped_calls` records it. Wiring it in is a new certify version, left for later. | `_test_generation` | existing campaign tests updated |
| C8 | gem5 `compare` returns the companion runs with the observed run; class baselines (and their component runs) are pruned at stop, A/A block runs after the block; claims keep them. | `Gem5Adapter.compare`, `_prune_baselines`, `_pilot` | 2 |
| C14 | `swdb validate` refuses `base_source` other than `fork_scalar_tdstep` (every adapter builds from the scalar-only snapshot). | `TargetAdapter.BASE_SOURCES`, `file_problems` | `tests/test_campaign_candidate_records.py` (2) |
| C15 | Library-operation applications stay out of REGIONS.json and go to `site_finder.excluded` with the reason; the region is still offered (uncertified edit); `site_finder.QUERY` unchanged. | `_regions`, `EXCLUDED_ENTRY_KINDS` | `tests/test_site_finder.py` (1) |
| C16 | New non-BFS gem5 records record `context.coverage_labels` and take the plug-in's labels (`competing_score_updates`, `score_storage`); BC records omit `parent_gather_race`. `read_only_checks.py` and `dx100_coverage.py` are not hash-pinned in `records/` or `library/` (current and historical sha256s checked); old records revalidate with the BFS labels. | `swdb/dx100_coverage.py`, `swdb/read_only_checks.py`, `swdb/dx100.py` | `tests/test_bc_coverage_labels.py` (3) |
| C17 | `swdb campaign-export CAMPAIGN_FILE --candidate ID [--claims] [--dry-run]`: candidate closure plus citing team claims, byte for byte, sha256 checked, tags kept; byte conflicts refuse everything; rejected candidates are refused. | `swdb/campaign_export.py` | `tests/test_campaign_export.py` (2) |
| C19 | One candidate record per class; a second class with the same tree points to the first tree (`extensions.shared_tree`). gem5 then builds and runs companions per class record (the comparison accepts only its own candidate's companions). a8 naming noted in [56](56-native-campaign-target.md). | `TargetAdapter.materialize` | 1 |

**Tests.** Full suite on the Mac once, 4 partitions, `tmp_path_retention_policy=none`, basetemps in the session
scratch folder and deleted afterwards: **4,429 passed, 38 skipped, 0 failed** (4,413 + 16 new).

**Deliberate non-changes.** Committed records (a8's `it1.kronecker.a0` naming, BC evaluations with BFS labels) stand;
`site_finder.QUERY` and its recorded sha256 are unchanged; no certify version changed; `competing_score_updates` is
not added to the protocol accelerator cases (BC protocols do not require it); hash-pinned `swdb/dx100_witness.py`
untouched; export copies records only, never raw run output; no lane release mid-wait (see C6).
