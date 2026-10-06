# 14 — Generality: MAPLE and PageRank

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 05, 09, 10
**Spec:** `../spec.md`
**Time estimate:** 1 day

**What to build:** A MAPLE target description is written from Eric's catalog (`maple-isca2022`) and the MAPLE paper; PageRank (`gapbs-pr`) is characterized. BFS, BC and PageRank get estimates on mbit10, DX100 and MAPLE (D22).

## Acceptance

- [ ] The estimator and mechanism-model code are unchanged between the DX100 BFS estimate and the new pairs (diff shown).
- [ ] MAPLE results are labeled estimate-only, since no paired timing exists for it.
- [ ] Per-region reports for all nine kernel–target pairs.
