# 02: First working version: the worked example end to end

Created: 2026-10-11 15:14 ET. Updated: 2026-10-12 00:42 ET (final review fix note); 2026-10-11 16:10 ET (resolved; Answer added).
**Type:** task
**Status:** resolved
**Blocked by:** 01 — Review and commit design
**Spec:** `../spec.md` (F1, F3–F5, F8, F17, F18, F22; seam 1)
**Time estimate:** about half a day

**What to build:** A public `swdb attribute` command takes a baseline estimate, a candidate estimate and their two source snapshots, computes the diff itself, finds rewrite sites, labels each region untouched, agent_rewritten or unattributed by file and line, and writes one validated `swdb.attribution.v1` record that is indexed into `swdb_`-prefixed SQLite tables. The record holds per-group baseline and candidate seconds, shares, realized speedup, untouched drift, total speedup and the Amdahl ceiling, composed per trial and then medianed. This is the narrowest complete path; later tickets widen it.

## Acceptance

- [x] The 100 s / 60% / 40% fixture gives hand-computed shares, speedups, drift and Amdahl ceiling 2.5×.
- [x] A loop without a catalog loop ID but with a source line gets a real label, not unattributed.
- [x] One unknown region makes its group and dependent whole-program fields unknown, with reasons.
- [x] Group medians are not rescaled to sum to the total.
- [x] Mismatched inputs are refused; identical inputs give a byte-identical record.
- [x] The record pins the hashes of both estimates, both snapshots and the target description.
- [x] `swdb validate` passes and the SQLite tables hold the groups.
- [x] Tests go only through the command.

## Answer

Resolved 2026-10-11 16:10 ET on branch `fga/02-tracer`.

**Built**

- `swdb attribute --baseline-estimate E --candidate-estimate E --baseline-source S --candidate-source S --id ID`
  in `swdb/attribution.py` (registered from `swdb/cli.py`; dispatched through the existing
  `analytic_handler`, so `_dispatch` is unchanged).
- New record kind `attribution` (`swdb.attribution.v1`): `schemas/attribution.schema.json`,
  `vocab/record_kinds.yaml`, `swdb/store.py` (`attributions/`), crosswalk enum, and a
  `swdb/rules.py` branch calling `attribution.validate_record` (self-hash and input pins).
- SQLite: `swdb_attributions`, `swdb_attribution_groups`, `swdb_attribution_regions`, added as
  one appended block at the end of `swdb/db.py` (`SCHEMA +=` and `_Insert.attribution`).
  No existing table touched or renamed.
- Docs: new `docs/reference/format-v0.4-attribution.md`; new "Attribution tables" section at
  the end of `docs/reference/database.md`.
- Tests: `tests/test_attribution.py`, 8 tests, all through the public commands
  (`characterize`-free: hand-counted `contract_fixture` characterizations → `swdb estimate`
  → `swdb attribute` → `swdb validate` / `swdb sql`). Uses the stub closure
  (`records.add_stub()`), not the catalog; about 30 s.

**Decisions (recorded for later tickets)**

- No helper named `_attribution_options` (taken by review attribution).
- Reads saved estimates, their pinned characterizations and the two source records only.
  Never calls `estimate_protocol.bind`, never re-estimates.
- Sources: each side takes a `source_snapshot` **or** `candidate` record (anything with an
  `artifact`); both trees are re-verified with `artifacts.verify`. A `candidate` source must be
  the estimate's candidate subject; a `source_snapshot` must name the implementation subject.
  Only the `source_snapshot` path is tested here; ticket 03 exercises `candidate`.
- Regions are matched by snapshot-relative path + line, never by region ID. Path rule: strip
  the artifact root, else the one manifest file the path ends with; a path in neither tree is
  `untouched` (`outside_source_tree`).
- Span rule (risks A4, simple on purpose): `[min, max]` of the region's start line and its
  same-file access-pattern lines. Ticket 04 widens it (inlined helpers, shifted functions).
- Rewrite site = one non-equal `difflib` opcode per file; an empty side is written `[p, p-1]`
  (insertion point). Sites are not merged yet (ticket 04).
- Groups: per-trial sums (absent region = 0 s), then median per group (risks A7); never
  rescaled. Whole-program totals are the estimates' own `seconds`. Amdahl ceiling =
  baseline total ÷ untouched candidate seconds (story 5, literal).
- Unknowns (A8): a null region makes its group's side null and is listed as
  `{side, region, missing}` from its bounds' `missing`; ratios with an unknown operand or a
  zero denominator are null.
- Refusal: estimates must agree on `input`, `target_description_sha256`, `threads`,
  `evidence_kind`.
- Byte identity: dates = latest `updated` of the four inputs; ID from `--id`; dicts built in
  a fixed order; `identity_sha256` over the payload. `workflow.CREATION_TAGS` (Extensa mode)
  are included like other envelopes.
- `attribute` is **not** in `archevolve.EVIDENCE_COMMANDS` yet; decide in ticket 03.
- Adding `swdb/attribution.py` changes `estimator_identity()`: freeze fresh protocols for
  new estimates (risks A1). `estimate_protocol` unchanged.

**Test command** (from `swdb-project/`):

```sh
python3 -m pytest -q tests/test_attribution.py tests/test_format_doc.py tests/test_crosswalk.py \
  tests/test_validate_application.py "tests/test_db.py::test_every_table_and_column_is_documented"
```

**Final review fix (2026-10-12 00:42 ET, branch `fga/final-fixes`).**
- M8 (F47): the two estimates must also share `estimator_sha256`, else the command refuses
  (`COMPARABLE` replaces `SAME`).
- L1 (F8): an unknown `unattributed` group never lists an empty reason; call time left unknown by
  the region's own work names that work's missing items.
- L11: the module docstring cites stories 43/44 (not "F43, F44") and F35/F38/F39.
