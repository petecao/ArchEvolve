# 06: Iteration 2: two baselines

Created: 2026-10-11 15:14 ET
**Type:** task
**Status:** resolved
**Blocked by:** 02 — First working version
**Spec:** `../spec.md` (F13; seam 1)
**Time estimate:** about 3 hours

**What to build:** `swdb attribute` optionally takes the previous accepted candidate. The report then gives gain this iteration (against the previous candidate) and cumulative gain (against the original baseline), and every region records the iteration that last changed it.

## Acceptance

- [x] Iteration-2 fixture: a region rewritten in iteration 1 and untouched in iteration 2 is untouched for this iteration and rewritten for cumulative.
- [x] Both group tables present and hand-checked.
- [x] Without a previous candidate the report is unchanged from ticket 02.

## Answer

Resolved 2026-10-11 16:43 ET on branch `fga/06-two-baselines`.

**Built**

- `swdb attribute` takes optional `--previous-estimate E --previous-source S` (the previous
  accepted candidate, named explicitly: no record marks acceptance, risks C8) and a repeatable
  `--earlier-source S` (accepted candidates before the previous one, oldest first).
- With them, the record keeps its top-level comparison **cumulative** (original baseline →
  candidate) and adds a `this_iteration` block: `iteration`, `previous_estimate`,
  `previous_source`, `earlier_sources`, and the same `rewrite_sites`, `regions`, `groups`,
  `whole_program` for previous → candidate. Every region row in both comparisons gets
  `last_changed_iteration`.
- Without them, the record is byte-for-byte the ticket 02 shape (test pins the key list and
  checks the cumulative part equals an iteration-2 report's).
- Validation: `this_iteration` pins (previous estimate, previous source, earlier sources)
  must be unchanged. SQLite: `swdb_attribution_iterations`,
  `swdb_attribution_iteration_groups`, `swdb_attribution_iteration_regions` (new tables in
  the attribution block; existing attribution tables untouched; `swdb_attribution_groups`
  stays cumulative).
- Docs: "Iterations: two baselines" section in `docs/reference/format-v0.4-attribution.md`;
  three tables in `docs/reference/database.md`.

**Decisions (for later tickets)**

- Inside `this_iteration`, `baseline` means the previous accepted candidate (same row shapes,
  so groups/regions/sites code and schema are reused via `#/properties/...` refs).
- Iteration number = 2 + number of `--earlier-source` trees.
- `last_changed_iteration`: original baseline regions 0; otherwise the newest *k* + 1 such
  that `_label` on the diff from iteration *k*'s tree into the region's version gives a
  non-`untouched` origin; 0 if none; null for `unattributed`. It calls `_sites`/`_label`,
  so ticket 04/05 rule changes (mixed, merged sites, library/intrinsic/offload origins)
  carry over automatically; any non-`untouched`, non-`unattributed` origin counts as changed.
- Earlier sources are trees only (no estimates needed).
- The previous estimate must agree with the candidate on `input`, `target_description_sha256`,
  `threads`, `evidence_kind`; one `--previous-*` flag without the other is refused.

**Test command** (from `swdb-project/`):

```sh
python3 -m pytest -q tests/test_attribution.py
```

Doc coverage checked with `tests/test_format_doc.py` (no attribution field in its 2
pre-existing failures) and an in-memory `db.SCHEMA` check against `database.md`.
