# 04 — The other four seed strategies

Created: 2026-09-23
**Type:** slice
**Status:** resolved
**Blocked by:** 02, 03
**Spec:** `../spec.md`

**What to build:** every effect kind and target type works, the four remaining seed
strategies are recorded, and loop and input strategies can be queried too.

- [x] Effect kinds `hint`, `widen`, `reorder` and `restructure_loop`, and the loop and input target types, each with a passing and a failing fixture.
- [x] The update kind `prefetch` (a non-binding early access that returns no data).
- [x] The strategy field `common_intrinsics`, whose IDs must resolve to intrinsic records.
- [x] Seeds, with sources verified before citing: `software_prefetch` (hint; parameter distance), `simd_gather` (widen; parameter lanes; common intrinsic `mm512_i32gather_ps`), `vertex_reordering` (input; reorder), `loop_tiling` (loop; tile; parameter tile size).
- [x] The duplicate rule separates all five seeds; for example, `software_prefetch` and `simd_gather` are not duplicates of each other.
- [x] `swdb strategies --loop <impl>/<loop>` checks each loop strategy's preconditions against every access pattern in that loop and its child loops, and all of them must pass. `swdb strategies --input <impl>` lists input strategies, with prose conditions always marked as "check by hand".
- [x] A procedure for adding a strategy or an intrinsic (sources, effect, preconditions, duplicate check), and query docs for `--loop` and `--input`.

## Comments

## Answer

Resolved 2026-09-23 (ET) on branch `optimization-strategies`.

- Effect kinds `hint` (step), `widen` (lanes: a number ≥ 2 or a declared parameter),
  `reorder` (properties, optional index_locality), and `restructure_loop` (vocabulary
  `loop_restructures`: tile, interchange, split, fuse). New targets `loop` and `input`.
  Effects must suit the target: access_pattern takes reshape, add_pattern, hint, and
  widen; loop takes restructure_loop and add_pattern; input takes reorder. An input
  strategy's preconditions must be prose.
- `update_kinds` gains `prefetch`. The strategy field `common_intrinsics` resolves to
  intrinsic records (x-ref), and table `strategy_intrinsics` holds it.
- Seeds, each checked against the source's full text:
  - `software_prefetch`: hint step -1; parameter distance; requires single_valued_indirect
    and `index_modified_during_loop: false`; source Ainsworth & Jones, CGO 2017; common
    intrinsic `mm_prefetch`.
  - `simd_gather`: widen by `lanes`; read only; `loop_carried_dependencies: false`;
    source the Intel guide entry; common intrinsic `mm512_i32gather_ps`. No reported
    benefit is recorded, because none was verified.
  - `vertex_reordering`: input; reorder index_locality → clustered; sources Gorder
    (SIGMOD 2016) and Balaji & Lucia (IISWC 2018).
  - `loop_tiling`: loop; tile; parameter tile_size; source Wolf & Lam, PLDI 1991.
- The duplicate rule separates all five seeds. `software_prefetch` and `simd_gather` are
  not duplicates, and a widen with a different lane count is a duplicate of
  `simd_gather`.
- `swdb strategies --loop <impl>/<loop>` checks every access pattern in the loop and its
  child loops. It is illegal if any pattern fails (reasons prefixed with the pattern) and
  undetermined with `<pattern>.<field>` unknowns. `swdb strategies --input <impl>` lists
  input strategies as undetermined, with prose in `check_by_hand`. `find --strategy`
  rejects non-access-pattern strategies (exit 2).
- Procedure: `docs/adding-a-strategy.md`. Query docs: `docs/database.md`, Queries.
  Format: `docs/format-v0.3.md` section 12. Tests: `tests/test_strategy_kinds.py`
  (24 tests).
- Decision: `loop_tiling` has no checkable semantic precondition. Wolf & Lam's legality
  test (a fully permutable band) needs dependence vectors the records do not hold, and
  `loop_carried_dependencies: true` does not make tiling illegal. Requiring `false`
  would mislabel legal loops, so the condition is prose in `unchecked`.
- Follow-up, out of scope here: the workload view (`swdb/view.py`) maps an unknown
  update kind to `read_modify_write`. A recorded `prefetch` pattern would appear that way
  until the view learns `prefetch` (the spec leaves the view unchanged).
