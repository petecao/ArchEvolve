# 02 — Prefactor: one access layer for record reads

Created: 2026-10-06
Updated: 2026-10-09 23:10 ET (code review note); 2026-10-06 ET (ticket resolved)
**Type:** slice
**Status:** resolved
**Blocked by:** 01
**Spec:** `../spec.md`
**Time estimate:** 3–4 h

**What to build:** Every record read and query goes through one interface beside the record store; the query and site-finder modules stop opening the generated database directly. Behavior does not change. Afterwards, pointing SWDB at another database (the main database, ADR 0014) means writing one adapter.

## Acceptance

- [x] Every query command gives identical output before and after (existing tests stay green).
- [x] Only the access layer opens the generated database.
- [x] The interface is documented in the database reference.


## Answer

Resolved: 2026-10-06 ET. Implementation: `bb11cb1`; integration through ticket 03
(`b36cb584`) and the progress-only update `11a1d80` is merged into the ticket branch.

[`swdb.access`](../../../swdb/access.py) now owns record discovery, safe YAML parsing
and its existing parse cache, exact record bytes/hashes, and every generated-index
connection. `Store`, database queries, and the site finder delegate to it. Record
imports, candidate-record binding, and campaign export also use this boundary.
Existing public `Store`/`db` signatures and the SQLite schema are preserved; the
builder uses a writable connection only for its temporary generated research index.
The interface and future main-adapter constraints are documented in the
[database reference](../../../docs/reference/database.md#record-and-query-access-interface).

Decision: the future adapter must preserve the existing research query relations,
through query translation or a read-only projection. No main-database schema is
assumed while it remains unverified. URI encoding also fixes an existing query
bug for caller-selected filenames containing `?`, `#`, or `%`: the regression
failed before the change and passes with the shared opener.

Verification (Python 3.12.6; existing query seams approved by the spec):

- The query, database, site-finder, and parse-cache regression run passed **52 tests**.
- The broader query/store/view/strategy/import/write/export run reported **170 passed,
  1 skipped, and 1 failed**. The library-freshness assertion ran across an integration
  source change: pytest had loaded the earlier `BUILDER`, while its fresh CLI built
  the index with the newly merged package hash. The exact affected case passed in a
  fresh process (**1 passed**, 22.81 s), covering **171 distinct passing cases** in
  total. No product-code change was required for that process-snapshot mismatch.
  The skip is the existing view test whose "no profile" case is unavailable because
  a real profile already exists for its input/machine triple.
- Compared archived pre-change package `2c50e5f` with the implementation over the
  same records and read-only evidence: **15 identical outputs** (14 CLI queries plus
  assembled site-finder results), including 11 successes and 4 expected missing-record
  errors. The site-finder SQL and its query hash are unchanged; generated-index builder
  metadata still changes with the package code, as intended.
- Existing candidate-record mismatch check: **1 passed, 26 deselected**.
- Repository-wide SQLite-open audit: only the two access-layer functions open the
  generated database (read-only queries and the writable temporary builder).
- All seven affected production modules compile; `git diff --check` passes.

The broader command was:

```sh
/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3 -m pytest -q \
  tests/test_query_index.py tests/test_db.py tests/test_site_finder.py \
  tests/test_store_parse_cache.py tests/test_yamlio.py tests/test_view.py \
  tests/test_strategies.py tests/test_strategy_kinds.py tests/test_applies.py \
  tests/test_library_index.py tests/test_add.py tests/test_writer_persistence.py \
  tests/test_campaign_export.py
```

The fresh-process rerun was
`pytest -q tests/test_library_index.py::test_library_changes_make_the_index_stale_and_queries_rebuild`.

## Code review 2026-10-09

2026-10-09 23:10 ET. Review of the implementation against this ticket: the SQLite and
query paths hold (40 query/site-finder/parse-cache/crosswalk tests passed). Fixed:

- `access.read_record` parsed `.json` with plain `json.loads`, so a repeated key silently
  kept the last value (YAML input refused it). It now refuses repeated JSON keys
  (`DuplicateKeyError`, a `ValueError`); `swdb add` reports bad JSON instead of a traceback.
  Contract updated in `docs/reference/database.md`.
- Two campaign record copies (`campaign_targets.py`, `campaign_fixture.py`) bypassed the
  boundary with `shutil.copy`; they now use the new `access.copy_record`.
- `lanl-db-notes.md` §5 rule 1 still described the pre-ticket state; it now points to
  `swdb/access.py`.

Tests: `tests/test_feature_reports.py` (duplicate-key and malformed-JSON cases added).
