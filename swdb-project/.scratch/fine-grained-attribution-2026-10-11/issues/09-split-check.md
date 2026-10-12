# 09: Split check on the real pair

Created: 2026-10-11 15:14 ET. Updated: 2026-10-11 21:28 ET (code half built; progress note added;
the real mbit10 run is still open); 2026-10-11 21:17 ET (claimed for the code half).
**Type:** task
**Status:** claimed
**Blocked by:** 03 — First real pair
**Spec:** `../spec.md` (F15, F19, F23; LR-02)
**Time estimate:** about half a day of agent work on mbit10

**What to build:** Time each group of the t75 pair natively on mbit10 with the existing BFS region thread-CPU counters, map the measured regions to groups by file and line, and apply the rule fixed before timing: pass when every group's measured and estimated shares differ by at most 10 percentage points. Write the verdict (`passed` or `split_unverified`) and the measured shares into the attribution report.

## Acceptance

- [ ] The rule and the estimates are recorded before the timing starts.
- [ ] Verdict and measured shares saved in the validated report.
- [ ] Load on mbit10 recorded with the run.
- [ ] Summary for Yan-Ru: verdict and the per-group share gaps.

## Progress

2026-10-11 21:28 ET — **code half done** (branch `fga/09-split-check-code`). The real run on
mbit10 is still needed, so the ticket stays claimed.

**What exists now:**

- `swdb attribute` takes `--baseline-profile` and `--candidate-profile` (two saved
  `region_profile` records from `swdb bfs-profile`). Why flags on the same command: it reuses
  every input check and the byte-identical record path, and one record kind holds the split.
- The rule is the constant `SPLIT_RULE` (`swdb.split_check.v1`, max |gap| 0.1) in
  `swdb/attribution.py`; it is written into every checked report and `swdb validate` refuses a
  report whose rule differs. It is recorded in code now, before any timing.
- Output: `split_check: {verdict, rule, reasons, profiles, measured_shares, gaps, regions}`.
  The profile pins carry `load_average` (host load recorded with each profile run).
- Refused: one flag alone, an unfinished profile, another tree, another input (F18) or thread
  count, a profile dated before an estimate (LR-02).
- Format: `docs/reference/format-v0.4-attribution.md` § Split check. Tables:
  `swdb_attribution_split_checks`, `swdb_attribution_split_gaps` (`docs/reference/database.md`).
- Tests: 7 new cases in `tests/test_attribution.py`, all through `swdb attribute`.

**What the mbit10 run must do (after ticket 03):**

1. Fresh native `evaluation` of the baseline candidate and the t75 candidate on the ticket 03
   workload (`bfs-20261004-uniform22.2f83a134a6bef789`), dated after both estimates.
2. `swdb bfs-profile` of each evaluation, in a socket lane.
3. Each profile's `context.candidate_sha256` must equal the artifact hash of the source record
   ticket 03's report names for that side.
4. Run (same flags as ticket 03's report, plus the two profiles):

```sh
python3 -m swdb attribute --records records \
  --baseline-estimate <t03 baseline estimate> --candidate-estimate <t03 candidate estimate> \
  --baseline-source <t03 baseline source> --candidate-source <t03 candidate source> \
  [<t03 --site-finder flags>] \
  --baseline-profile <baseline region_profile> --candidate-profile <candidate region_profile> \
  --id <t03 report id>.split-check --format json
```

5. `swdb validate`, then write `## Answer` with the verdict and the six gaps
   (`split_check.gaps`).
