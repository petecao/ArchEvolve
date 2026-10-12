# 04: Rewrite-site edge cases

Created: 2026-10-11 15:14 ET
**Type:** task
**Status:** resolved
**Blocked by:** 02 — First working version
**Spec:** `../spec.md` (F1, F2, F14, F24; seam 1)
**Time estimate:** about 3–4 hours

**What to build:** `swdb attribute` handles the hard cases of mapping changed lines to regions: two sites sharing a region merge into one; a region only partly inside a site counts as rewritten and is flagged `mixed`; untouched functions are matched across inserted or deleted lines; a rewritten helper inlined into an untouched caller is labeled by its own file and line; unattributed time above 10% of the total sets a flag on the report.

## Acceptance

- [x] One fixture per case, each with hand-checked labels.
- [x] No region's time is counted in two sites.
- [x] Unattributed above 10% is flagged and the report is still written.

## Answer

Resolved 2026-10-11 18:36 ET on branch `fga/04-rewrite-sites`.

**Built** (all in `swdb attribute`; record fields in `docs/reference/format-v0.4-attribution.md`)

- **Merged sites (F1).** Each `difflib` change run is a span; spans one region overlaps on
  either side merge transitively into one site, numbered by its first span. New site field
  `spans`; `path` and the line envelopes are null when a site's spans lie in several files.
  A region lists at most one site.
- **Mixed (F14).** New region field `mixed`: rewritten, but some line of its pieces unchanged.
  Its whole time stays in the rewritten group.
- **Shifted functions (story 14).** New region field `matched_region`: an untouched region is
  paired with the other side's untouched region whose home span and inlined pieces equal its
  own carried through the line diff, same kind; one-to-one only, IDs never compared.
- **Inlined code (story 15).** Home span = start line + accesses inside the region's own
  lexical function (same file); other accesses become `inlined` pieces `{path, lines}` per file
  and enclosing function. Any piece overlapping a span makes the region rewritten. This also
  stops an untouched inlined helper from stretching a caller's span across other functions.
  Without a recognizable function the ticket 02 rule (all same-file accesses) applies.
- **Unattributed flag (F24).** `whole_program.unattributed_threshold` (0.1) and
  `unattributed_flagged` (true above 10% of either total; null if unknown; report still written).
- SQLite (inside the `swdb_attribution*` block): `swdb_attributions.unattributed_flagged`,
  `swdb_attribution_regions.mixed`, `.matched_region`; documented in `database.md`.
- `swdb/cpp_lexical.py`: additive `function_spans(text)` (one scan per file; same result as
  `enclosing_function` + `function_span`, checked on `apps/gapbs/src/bfs.cc`).

**For later tickets:** region rows now carry `mixed`, `inlined`, `matched_region` (schema
`additionalProperties: false`); ticket 05's origins should keep `_match_untouched` limited to
`untouched`. `matched_region` is the per-region join ticket 06 can use for "last changed".

**Test command** (from `swdb-project/`): `python3 -m pytest -q tests/test_attribution.py tests/test_format_doc.py tests/test_crosswalk.py`
(5 new tests; `test_format_doc.py` keeps its 2 pre-existing failures, none from attribution fields).

**Review fix (2026-10-11 22:10 ET, branch `fga/review-fixes`).** The glossary's "Rewrite site"
now says one or more changed spans, merged when one region overlaps several (finding 7).
