# 08: Catalog bound and full ranking

Created: 2026-10-11 15:14 ET. Updated: 2026-10-12 00:42 ET (final review fix note); 2026-10-11 22:10 ET (review fix note); 2026-10-11 19:30 ET (resolved).
**Type:** task
**Status:** resolved
**Blocked by:** 07 — Resource floor headroom
**Spec:** `../spec.md` (F6 (catalog), F7, F12, F21; seam 1)
**Time estimate:** about 3–4 hours

**What to build:** `swdb attribute` joins site-finder regions to estimator regions by file and line overlap (partial overlap flagged `mixed`), evaluates each matched entry's mechanism models on the region's baseline counts, and keeps the lowest as the catalog bound. It ranks regions by remaining gain bound, with floor-only regions after them.

## Acceptance

- [x] An evaluable entry gives a numeric catalog bound.
- [x] An entry needing rewritten counts gives unknown with `needs_rewritten_counts`.
- [x] No match gives `no_catalog_match`, not infinite headroom.
- [x] Known catalog bounds and floor-only regions are never ranked against each other.
- [x] The report calls the remaining gain bound an upper limit.

## Answer

Resolved 2026-10-11 19:30 ET on branch `fga/08-catalog-bound` (from integration tip `d0c80a8a`).

**Built** (all in `swdb attribute`; fields in `docs/reference/format-v0.4-attribution.md`)

- **Input.** New `--site-finder <campaign_summary ID>` (and `--site-finder-iteration`, default:
  the last iteration whose region rows carry `why`). The record pins the summary in a new
  top-level `site_finder` block; `swdb validate` re-checks the pin. Without it, every catalog
  bound is null with `no_site_finder` and the ranking is ticket 07's.
- **Join (F21, risks C1/C2).** Site-finder lines name the full-source revision, so each
  site-finder region is placed in each side's own tree by the function its ID names
  (`cpp_lexical.function_span`, as ticket 73's `workspace_region_lines`). A region joins when a
  piece (home span or inlined piece) overlaps the span; `mixed` when a piece lies outside.
- **Mechanisms (F25).** Entry `uses_intrinsics` (also through `uses_library_operations`) ->
  library intrinsics' `hardware_operations` -> the pinned description's functional observation
  commands whose operations they all provide -> events -> offload mechanisms
  (`selector.domain: offload`, or `selector.event_ids` naming an event). Evaluated with the
  unchanged `analytic_models.evaluate`, estimator context, max(bounds) + overheads, per trial
  then median. No gem5 (F10).
- **Region `catalog_bound`:** `{seconds, entry, reason, mixed, site_finder_regions, entries[], missing}`.
  Reasons: `needs_rewritten_counts` (a missing item starts `address_stream_counts` or
  `accelerator_calls`), `unknown_catalog_entry` (missing rate, `entry_changed`, `not_in_library`),
  `no_catalog_match`, `no_site_finder`. Also on `this_iteration` rows.
- **Headroom:** a `catalog_bound` entry follows `resource_floor`; its null reason is the bound's.
- **Ranking (F7):** tiers `remaining_gain_bound` -> `floor_headroom` -> `unknown`. RGB =
  share x max(0, 1 - bound / estimate), share = region / candidate total. A region with a known
  bound never enters the floor tier (null RGB -> `unknown`, reason `unknown_share`/`zero_total`/
  `unknown_estimate`). New top-level `ranking_rule` says the RGB is an upper limit, never an
  expected gain.
- **SQLite:** `catalog_bound` rows in `swdb_attribution_headroom` (`limiting_term` = entry); new
  `swdb_attribution_catalog` (one row per region and entry). Documented in `database.md`.
- **Spec:** F25 added to the decisions table.

**Decisions made here (revisable)**

- RGB clamps at 0 (an entry slower than the current code offers no gain); a 0 s region gives 0.
- Join is per function, so every region of the function joins (coarser than the site-finder lines).
- An entry whose library content differs from the hash the site finder recorded is not evaluated
  (`entry_changed`), so a bound never comes from a different entry version.

**For ticket 03 / 10**

- On the real native BFS pair (a8 summary, CPU services description) every entry is a library
  operation with no intrinsic, so all regions are `no_catalog_match` and the ranking is floor-only
  (or `unknown`, per ticket 07's note on `bytes_per_s`). Checked by reading the a8 summary.
- Open question for Yan-Ru: `contract.bfs_read_offload` uses the MMIO intrinsics
  (`dx100.mmio.v1.*` operations), while the DX100 functional description declares
  `dx100.functional.v1.*` operations, so under F25 it also gives `no_catalog_match` there. A
  catalog bound for it needs either the functional intrinsics in the contract or an
  operation mapping between the two families.
- Ticket 10 can read `catalog_bound.site_finder_regions` to map ranked regions back to site-finder
  region IDs.

**Test command** (from `swdb-project/`):
`python3 -m pytest -q tests/test_attribution.py tests/test_format_doc.py tests/test_crosswalk.py`
(27 attribution tests pass, 2 new; `test_format_doc.py` keeps its 2 pre-existing failures, none
from attribution fields). The documented-tables test in `test_db.py` timed out on the Mac
(its whole-catalog build exceeds the 600 s subprocess limit); instead every `swdb_attribution*`
table and column from `db.SCHEMA` was checked against `database.md` by script: none missing.

**Review fix (2026-10-11 22:10 ET, branch `fga/review-fixes`).** Supersedes two "revisable"
decisions above.
- F30 (finding 2): the join is by moved lines, not by function. New `--site-finder-source`
  names the revision tree; lines move by offset inside the function (`cpp_lexical.definition_spans`:
  any column, every overload). Without a way to move them the whole function joins, recorded as
  `join: function` with its reason. New fields `catalog_bound.joins`, `site_finder.regions[].placements`,
  `site_finder.revision_source` (pinned, re-checked by `swdb validate`).
- F31 (finding 3): an unplaced site-finder region gives `site_finder_unplaced`, never `no_catalog_match`.
- F32 (finding 4): no `content_sha256` -> `entry_unhashed`; tests now cover `entry_changed`,
  `not_in_library` and `entry_unhashed`. F28 test: an MMIO entry on a functional description is `no_catalog_match`.
- F35: entries run on baseline counts (a candidate row through `matched_region`; none -> `no_baseline_counts`).
- F36: unknown bounds rank in the `unknown` tier with their reason; only `no_catalog_match`/`no_site_finder` are floor-only.
- F29: the 0 clamp stays and is stated in `ranking_rule`; ties go by floor headroom, then ID.
- F38: entries use each trial's own `unmodeled_calls`.

**Final review fix (2026-10-12 00:42 ET, branch `fga/final-fixes`).**
- L4: a test now asserts `ranking_rule.remaining_gain_bound` starts "Upper limit, never an
  expected gain" (box 5).
- M4 (F45): new `ranking_rule.comparison`: one ranking over the cumulative comparison;
  `this_iteration` bounds are informational.
- M7: the schema's `catalog_bound` description says "baseline counts" (F35); `database.md`'s
  headroom reasons point to the format doc's one list instead of a stale copy.
