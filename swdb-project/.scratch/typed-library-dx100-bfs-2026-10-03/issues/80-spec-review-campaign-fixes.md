# 80 — Spec-review fixes: Extensa campaign budgets, pruning and export

Created: 2026-10-05 22:05 ET (from the spec review of tickets 38–78, findings C5–C8, C14–C17, C19)
**Type:** slice
**Status:** claimed
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

- [ ] C5: an iteration's gem5 baseline evaluation is checked against the cap and charged like `--baselines-only`.
- [ ] C6: decided and documented in spec.md; a test covers it.
- [ ] C7: no test-generation call is made (or charged) until certification accepts its inputs; documented.
- [ ] C8: companion runs are pruned right after their comparison; per-class baselines at campaign stop; a team
  claim keeps them.
- [ ] C14: `swdb validate` refuses a base source no adapter can build candidates from.
- [ ] C15: library-operation applications are kept out of REGIONS.json, with a reason record.
- [ ] C16: new BC records take labels from the kernel plug-in and carry no race result; old records revalidate.
- [ ] C17: `swdb campaign-export` copies a candidate artifact's closure with sha256 checks, tags kept; fixture test.
- [ ] C19: new campaigns write one candidate record per class, pointing to the shared tree; ticket 56 notes a8.

## Comments

- 2026-10-05 22:05 ET: claimed by the agent (worktree branch, not pushed).
