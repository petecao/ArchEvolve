# 06 — Implementations apply strategies

Created: 2026-09-23
**Type:** slice
**Status:** resolved
**Blocked by:** 04
**Spec:** `../spec.md`

**What to build:** an implementation can record the strategies it applies, and the SW
Ensemble Agent can see whether they helped compared with the baseline.

- [x] The optional implementation field `applies`: an ordered list of `{strategy, target, parameters}`. Existing implementation records validate without edits.
- [x] Rules, each with a passing and a failing fixture: the strategy resolves; the target is a loop or access-pattern ID in the same record, or `input`, and matches the strategy's target type; each parameter is one the strategy declares.
- [x] `swdb build` includes applied strategies. `swdb implementations <kernel> --applies <id>` returns each matching implementation with its `applies` entry, its `derived_from`, and for each (input, machine) pair the newest complete profile ID of it and of its baseline, or null when either is missing.
- [x] Tested with a fixture derived implementation and fixture profiles in a temporary records folder. Documented in the format doc and the query doc.

## Comments

- 2026-09-23 (ET), code review:
  - Every declared parameter must now be given.
  - When a loop and an access pattern share an ID (gapbs-cc-sv's `compress-chase`), the
    strategy's target type decides which one is meant.
  - A schema-invalid strategy no longer crashes validation of implementations that apply
    it.
  - The database staleness key is now a hash of the database code (`builder`), not only
    of the table definitions.
  - `--applies` uses one connection and reads each baseline's profiles once.

## Answer

Resolved 2026-09-23 (ET) on branch `optimization-strategies`.

- New optional implementation field `applies`: an ordered list of `{strategy, target,
  parameters}`. Existing implementations validate without edits.
- Rules (`swdb/rules.py`), each with passing and failing fixtures:
  - the strategy resolves (x-ref);
  - the target is a loop or access-pattern ID of the same record, or `input`
    ("... is not a loop or access pattern of this implementation, nor input");
  - the target matches the strategy's target type ("strategy 'packing' targets
    access_pattern, but 'sweep' is a loop");
  - every parameter is declared ("declares no parameter 'distnace' (it declares
    distance)").
- `swdb build` fills `applied_strategies`. `swdb implementations <kernel> --applies <id>`
  returns, per implementation, `implementation`, its matching `applies` entries (with
  `position`), `derived_from`, and `profiles`. `profiles` has one item per (input,
  machine) pair where either side has a complete profile, with the newest complete
  `profile` and `baseline_profile`, or null when either is missing. `--require` still
  filters.
- Tested in `tests/test_applies.py` (12 tests) with a fixture derived implementation
  (`gapbs-pr-jacobi-packed`) and fixture profiles in a temporary records folder. The tests
  show that an incomplete newer profile is skipped and that the baseline-only inputs give
  null. Documented in `docs/format-v0.3.md` (implementation section) and
  `docs/database.md` (table and query).
- Fix found on the way: a database built by an older `swdb` lacked the new tables, and
  queries crashed with "no such table". `meta` now stores a hash of the table
  definitions, and a mismatch triggers a rebuild ("built by another swdb version"). This
  is tested.
- Full suite: 290 passed, 3 skipped (the 3 skips need valgrind and a socket lane on
  mbit10).
