# 02 — Packing, end to end

Created: 2026-09-23
**Type:** slice
**Status:** resolved
**Blocked by:** 01
**Spec:** `../spec.md`

**What to build:** the SW Ensemble Agent can ask which access-pattern strategies are
legal for one access pattern, and where one strategy could apply, with `packing` as the
first real strategy (ADR 0004).

- [x] The strategy record kind: target (access_pattern for now), effect with the `reshape` and `add_pattern` kinds, parameters, preconditions (`requires_shapes`, `requires_semantics`, `unchecked`), `benefits_when` (`basis: reported` plus a provenance ref), and at least one source.
- [x] Rules, each with a passing and a failing fixture: effect items match their kind's shape; precondition fields and values exist; benefit items are reported and sourced; a duplicate strategy (same target and effect set, parameters ignored) fails and names the existing one.
- [x] `swdb add` and `swdb add --agent` write strategies to their canonical folder (draft and `agent_run` for agents).
- [x] The `packing` seed record, with its source verified before citing (spec Further Notes). Unverifiable claims are left out.
- [x] `swdb build` includes strategies. `swdb strategies --pattern <impl>/<pattern>` returns each access-pattern strategy with `outcome` (legal / illegal / undetermined), `reasons`, `unknown_fields`, `check_by_hand` and `benefits_when`, as YAML or JSON.
- [x] `swdb find --strategy <id>` returns the access patterns where it is legal or undetermined (illegal ones are left out).
- [x] Tests cover all three outcomes, including a semantic value with basis unknown. The new fields and the query are documented in the v0.3 format doc and the query doc.

## Comments

## Answer

Resolved 2026-09-23 (ET) on branch `optimization-strategies`.

- New record kind `strategy` (`schemas/strategy.schema.json`, folder `records/strategies/`).
  Vocabularies `strategy_targets` (access_pattern) and `effect_kinds` (reshape,
  add_pattern). Each effect kind's shape is enforced: its fields are required, and a
  field of another kind is rejected.
- Rules (`swdb/strategy.py`, called from `swdb/rules.py`):
  - Effects must suit the target, and a reshape must change the shape.
  - Precondition fields must be one of the seven semantic facts, with a value of the
    right type or vocabulary.
  - Benefits have `basis: reported`, and their `source` must be a provenance entry of
    kind paper, human_report, or vendor_reference. Their `terms` must be metrics, input
    properties, or `l1d_bytes`, `l2_bytes`, or `llc_bytes`.
  - Each strategy cites at least one source.
  - A duplicate (same target and effect set, ignoring notes, parameters, and lanes)
    fails and names the existing strategy.
- `swdb add` and `add --agent` write `strategies/<id>.yaml`. An agent's record is draft
  with `agent_run`, and its duplicate is rejected with the existing ID.
- Seed `packing`: reshape step -1 single_valued_indirect → stream; add patterns
  `stream > single_valued_indirect : read` and `stream : write`; requires
  single_valued_indirect, update kind read, `index_modified_during_loop: false`, and
  `loop_carried_dependencies: false`. It cites Goto and van de Geijn (TOMS 34(3) 2008,
  doi 10.1145/1356052.1356053), checked against the author's full text. Three reported
  conditions: L2 fit, non-consecutive accesses, and reuse.
- Queries (`swdb/db.py`, `swdb/cli.py`):
  - `swdb strategies --pattern <impl>/<pattern>` returns `strategy`, `outcome`,
    `reasons`, `unknown_fields`, `check_by_hand`, and `benefits_when`.
  - `swdb find --strategy <id>` lists legal and undetermined patterns only.
  - Both take `--format yaml|json`.
  - Example: packing is legal for `gapbs-pr-jacobi/gather-contrib` and illegal for
    `gapbs-pr-gs/gather-contrib` (loop-carried dependency).
- Tables `strategies` and `strategy_effects`. Documented in `docs/format-v0.3.md`
  section 12 and in the Queries section of `docs/database.md`. Tests:
  `tests/test_strategies.py` (35 tests, covering legal, illegal by shape, update kind,
  step, and semantics, and undetermined by basis unknown).
- Decisions:
  - Effect `step` counts from 0, and a negative value counts from the end (-1 is the
    target step). A reshape step whose shape differs from `shape_before` makes the
    pattern illegal.
  - An optional `requires_update_kinds` precondition was added, because packing a
    compare-and-swap target is not legal and prose alone would report it as legal. This
    is a minor, optional addition.
- Full suite at this point: 241 passed, 3 skipped.
