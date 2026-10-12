# 10: Site finder uses the ranking

Created: 2026-10-11 15:14 ET
**Type:** task
**Status:** claimed
**Blocked by:** 08 — Catalog bound and full ranking; 09 — Split check
**Spec:** `../spec.md` (F20, F23; seam 2)
**Time estimate:** about 2–3 hours

**What to build:** The site finder reads the latest attribution report for its kernel and target and orders its eligible regions by the report's ranking. A `split_unverified` report, or no report, leaves today's order. Eligibility, legality and recorded reasons do not change. Rewrite-provider prompts do not change.

## Acceptance

- [ ] Order follows the ranking when the report passed its split check.
- [ ] `split_unverified` or no report keeps today's order.
- [ ] The eligible set is identical with and without a report.
- [ ] Prompt hashes for an existing fixture are unchanged.
