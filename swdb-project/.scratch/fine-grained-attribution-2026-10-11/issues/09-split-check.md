# 09: Split check on the real pair

Created: 2026-10-11 15:14 ET. Updated: 2026-10-11 21:17 ET (claimed for the code half).
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
