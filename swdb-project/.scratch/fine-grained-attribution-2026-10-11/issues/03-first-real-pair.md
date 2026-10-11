# 03: First real pair: t75 BFS attribution report

Created: 2026-10-11 15:14 ET
**Type:** task
**Status:** ready-for-agent
**Blocked by:** 02 — First working version
**Spec:** `../spec.md` (F9, F16, F18; LR-01, LR-02)
**Time estimate:** about half a day of agent work on mbit10; 30 min if it ends on a negative report

**What to build:** Estimate the t75 native BFS candidate (`extensa-native-bfs-20261005-a8.it1.kronecker.a0`, contract `bfs_tdstep_frontier_staging`) and its baseline with the BFS g16/g17 CPU target description, on the exact input that ticket 09 will time. Save both estimates, with their order recorded, before any new timing. Run `swdb attribute` on the pair and save the real report. If an estimate comes out unknown, close on a negative report naming the missing pieces.

## Acceptance

- [ ] Both estimates saved before timing, order recorded, same input as the planned timing.
- [ ] A real attribution report saved and validated, or a negative report.
- [ ] Record shares of rewritten, untouched and unattributed time in the map's current state.
- [ ] Follow the mbit10 rules: lane lease, `df -h` before large runs, raw output outside git.
