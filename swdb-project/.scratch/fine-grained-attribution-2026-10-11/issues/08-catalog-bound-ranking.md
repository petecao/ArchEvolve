# 08: Catalog bound and full ranking

Created: 2026-10-11 15:14 ET
**Type:** task
**Status:** claimed
**Blocked by:** 07 — Resource floor headroom
**Spec:** `../spec.md` (F6 (catalog), F7, F12, F21; seam 1)
**Time estimate:** about 3–4 hours

**What to build:** `swdb attribute` joins site-finder regions to estimator regions by file and line overlap (partial overlap flagged `mixed`), evaluates each matched entry's mechanism models on the region's baseline counts, and keeps the lowest as the catalog bound. It ranks regions by remaining gain bound, with floor-only regions after them.

## Acceptance

- [ ] An evaluable entry gives a numeric catalog bound.
- [ ] An entry needing rewritten counts gives unknown with `needs_rewritten_counts`.
- [ ] No match gives `no_catalog_match`, not infinite headroom.
- [ ] Known catalog bounds and floor-only regions are never ranked against each other.
- [ ] The report calls the remaining gain bound an upper limit.
