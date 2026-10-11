# 06: Iteration 2: two baselines

Created: 2026-10-11 15:14 ET
**Type:** task
**Status:** ready-for-agent
**Blocked by:** 02 — First working version
**Spec:** `../spec.md` (F13; seam 1)
**Time estimate:** about 3 hours

**What to build:** `swdb attribute` optionally takes the previous accepted candidate. The report then gives gain this iteration (against the previous candidate) and cumulative gain (against the original baseline), and every region records the iteration that last changed it.

## Acceptance

- [ ] Iteration-2 fixture: a region rewritten in iteration 1 and untouched in iteration 2 is untouched for this iteration and rewritten for cumulative.
- [ ] Both group tables present and hand-checked.
- [ ] Without a previous candidate the report is unchanged from ticket 02.
