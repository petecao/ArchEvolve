# 07: Resource floor headroom

Created: 2026-10-11 15:14 ET. Updated: 2026-10-12 00:42 ET (final review fix note); 2026-10-11 16:42 ET (resolved).
**Type:** task
**Status:** resolved
**Blocked by:** 02 — First working version
**Spec:** `../spec.md` (F6 (floor), F7 (floor-only ranking), F10; seam 1)
**Time estimate:** about 2–3 hours

**What to build:** For each region, `swdb attribute` computes the resource floor, max(compute bound, useful-bytes bandwidth bound) at the target description's own rates with no latency, row, queue or overhead terms, and the floor headroom. Regions are ranked by floor headroom. The existing compute and bandwidth mechanism models are reused unchanged.

## Acceptance

- [x] Floor ≤ estimate on every known fixture region.
- [x] A missing rate gives an unknown floor with a reason, not zero.
- [x] No theoretical-peak parameter is read.
- [x] Headroom names its limit.

## Answer

Resolved 2026-10-11 16:42 ET on branch `fga/07-resource-floor`.

**Built**

- Every region row of `swdb attribute` (both sides) now has `resource_floor`
  `{seconds, limiting_term, terms[{model, in_description, seconds, missing}], missing}` and
  `headroom: [{limit: resource_floor, value, reason}]`.
- New top-level `ranking`: candidate regions as `{position, side, region, tier, limit, value, reason}`.
- `swdb validate` rejects a floor above its region's known estimate.
- SQLite: `swdb_attribution_headroom` and `swdb_attribution_ranking`, appended inside the
  attribution block of `swdb/db.py`. The insert hook chains whatever `_Insert.attribution` was
  before it, so other tickets' inserts keep running.
- Schema, `docs/reference/format-v0.4-attribution.md` and `docs/reference/database.md` updated.
- 4 new tests in `tests/test_attribution.py`, all through the public command.

**Decisions**

- Floor terms: the unchanged `analytic_models.evaluate` on `compute_throughput` and
  `streaming_bandwidth`, called exactly as the estimator calls them (same models list, threads,
  `covered_nonstream` rule). So each term equals that model's bound in the estimate, and
  floor ≤ estimate holds by construction.
- Rates come only from the estimate's own `target_description_snapshot` (checked against its
  pinned hash). A missing mechanism is run with no rates: zero work = 0 s, any work = unknown
  with the rate named (`bytes_per_s`). No fallback to `cache_fit` hit bandwidth, to the base
  description in `extensions`, or to any other record (risks B3). Tested: a cache-priced
  description with no streaming rate gives an unknown floor, not the cache rate.
- No theoretical peak: the models read only `bytes_per_s` and `<class>_ops_per_s`. Tested with
  `theoretical_peak_*` parameters a million times faster in the description.
- Trials: floor per trial (absent region = 0 s), then median, like the estimate.
  `limiting_term` is the term with the larger median.
- Headroom = region `seconds` ÷ limit. Null reasons: `unknown_estimate`, `unknown_limit`,
  `zero_limit`.
- Ranking: candidate side only (the next iteration's code). Tier `floor_headroom`, largest
  first, ties by region ID; then tier `unknown` in region-ID order. Not weighted by share (F7
  says floor headroom). Positions are 1-based over the whole list.

**For ticket 08**

- Add a `catalog_bound` entry to each region's `headroom` list and a `catalog_bound` row per
  region in `swdb_attribution_headroom` (`limit_name` is in the primary key).
- Put a `remaining_gain_bound` tier before `floor_headroom` in `ranking`, and drop those
  regions from the floor tier (F7: floor-only regions follow). Extend the `tier`/`limit` enums
  in the schema.
- For the real BFS services description, every region with useful bytes will have an unknown
  floor (no `bytes_per_s`), so its regions land in the `unknown` tier.

**Test command** (from `swdb-project/`):

```sh
python3 -m pytest -q tests/test_attribution.py tests/test_format_doc.py tests/test_crosswalk.py
```

Result: 12 attribution tests pass (about 40 s). `test_format_doc.py` keeps its 2 pre-existing
failures, none for attribution fields. The documented-tables test in `test_db.py` was not run
(it copies the whole catalog); new tables and columns were checked by hand against `database.md`.

**Final review fix (2026-10-12 00:42 ET, branch `fga/final-fixes`).** L3: the floor's bandwidth term is the `streaming_bandwidth`
model's own bound, which leaves out bytes a `cache_fit` or latency model covers, so the floor is
looser but still a valid lower limit. `ranking_rule.floor_headroom` and the format doc state it;
the floor itself is unchanged.
