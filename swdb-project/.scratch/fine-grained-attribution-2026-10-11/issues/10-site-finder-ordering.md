# 10: Site finder uses the ranking

Created: 2026-10-11 15:14 ET. Updated: 2026-10-11 21:31 ET (resolved; Answer added).
**Type:** task
**Status:** resolved
**Blocked by:** 08 — Catalog bound and full ranking; 09 — Split check
**Spec:** `../spec.md` (F20, F23; seam 2)
**Time estimate:** about 2–3 hours

**What to build:** The site finder reads the latest attribution report for its kernel and target and orders its eligible regions by the report's ranking. A `split_unverified` report, or no report, leaves today's order. Eligibility, legality and recorded reasons do not change. Rewrite-provider prompts do not change.

## Acceptance

- [x] Order follows the ranking when the report passed its split check.
- [x] `split_unverified` or no report keeps today's order.
- [x] The eligible set is identical with and without a report.
- [x] Prompt hashes for an existing fixture are unchanged.

## Answer

Resolved 2026-10-11 21:31 ET on branch `fga/10-site-finder-order` (from integration tip `aada2c48`).

**Built**

- `swdb/site_finder.py`: one hook in `find()` plus `ORDERING_QUERY`, `ORDERING_RULE` and the pure
  `ranked(regions, rows)`. `QUERY`, `assemble` and existing SQL are untouched, so eligibility,
  legality, `rejected` and reasons cannot change. `find()` adds an `ordering` block
  `{attribution, split_check, applied, rule}`; campaigns copy only named keys, so summaries are unchanged.
- **Latest report:** among reports with a `site_finder` block whose pinned kernel and target equal
  the campaign's, the greatest `created`, then the greatest ID. Only the latest counts: if it is
  `split_unverified` or unchecked, today's order stays (no fallback to an older passed report).
- **Order:** a chosen region takes the best ranking position of any ranked region joined to it
  (`catalog_bound.site_finder_regions`); unranked regions follow in today's order (stable sort).
- `swdb attribute`: the `site_finder` block now records `kernel` and `target` (iteration's
  site-finder parameters, else the summary's); schema updated.
- SQLite (attribution block only): column `swdb_attributions.split_check_verdict` (from
  `split_check.verdict`; NULL = not checked), tables `swdb_attribution_site_finder` and
  `swdb_attribution_site_finder_regions`. Documented in `database.md` and the format doc.

**For ticket 09:** write `split_check: {verdict: passed | split_unverified, ...}` into the record and
add it to `schemas/attribution.schema.json`; the column `split_check_verdict` is already filled from it.
Until then a team store holding a report with `split_check` fails `swdb validate` (and `swdb
campaign`), so the campaign-level with-report test waits for 09; order is tested through `find()`.

**Tests:** 6 new in `tests/test_site_finder.py` (hand-written fixture reports), including the rewrite
prompt sha256 pinned on the native query campaign before the change; 1 new in `tests/test_attribution.py`.
`python3 -m pytest -q tests/test_site_finder.py tests/test_attribution.py` (from `swdb-project/`).
