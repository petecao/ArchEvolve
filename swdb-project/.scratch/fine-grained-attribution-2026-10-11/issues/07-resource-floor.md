# 07: Resource floor headroom

Created: 2026-10-11 15:14 ET
**Type:** task
**Status:** claimed
**Blocked by:** 02 — First working version
**Spec:** `../spec.md` (F6 (floor), F7 (floor-only ranking), F10; seam 1)
**Time estimate:** about 2–3 hours

**What to build:** For each region, `swdb attribute` computes the resource floor, max(compute bound, useful-bytes bandwidth bound) at the target description's own rates with no latency, row, queue or overhead terms, and the floor headroom. Regions are ranked by floor headroom. The existing compute and bandwidth mechanism models are reused unchanged.

## Acceptance

- [ ] Floor ≤ estimate on every known fixture region.
- [ ] A missing rate gives an unknown floor with a reason, not zero.
- [ ] No theoretical-peak parameter is read.
- [ ] Headroom names its limit.
