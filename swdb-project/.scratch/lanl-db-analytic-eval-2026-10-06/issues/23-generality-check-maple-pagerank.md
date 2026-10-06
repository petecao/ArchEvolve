# 23 — Generality check: MAPLE and PageRank with no estimator code change

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 06, 08, 05
**Spec:** `../spec.md`
**Time estimate:** 1 day

**What to build:** Estimate BFS, BC and PageRank (`gapbs-pr`, already in SWDB) on mbit10, DX100 and MAPLE (D22). Adding MAPLE and PageRank must need only records and a target description.

## Acceptance

- [ ] The estimator's code is unchanged between the BFS-on-DX100 estimate and the PageRank and MAPLE estimates (diff shown).
- [ ] MAPLE results are labeled estimate-only: no paired timing exists for it.
- [ ] Per-region reports for all nine kernel-target pairs.
