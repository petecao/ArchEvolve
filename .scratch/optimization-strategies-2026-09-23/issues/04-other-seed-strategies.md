# 04 — The other four seed strategies

Created: 2026-09-23
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 02, 03
**Spec:** `../spec.md`

**What to build:** every effect kind and target type works, the four remaining seed
strategies are recorded, and loop and input strategies can be queried too.

- [ ] Effect kinds `hint`, `widen`, `reorder` and `restructure_loop`, and the loop and input target types, each with a passing and a failing fixture.
- [ ] The update kind `prefetch` (a non-binding early access that returns no data).
- [ ] The strategy field `common_intrinsics`, whose IDs must resolve to intrinsic records.
- [ ] Seeds, with sources verified before citing: `software_prefetch` (hint; parameter distance), `simd_gather` (widen; parameter lanes; common intrinsic `mm512_i32gather_ps`), `vertex_reordering` (input; reorder), `loop_tiling` (loop; tile; parameter tile size).
- [ ] The duplicate rule separates all five seeds; for example, `software_prefetch` and `simd_gather` are not duplicates of each other.
- [ ] `swdb strategies --loop <impl>/<loop>` checks each loop strategy's preconditions against every access pattern in that loop and its child loops, and all of them must pass. `swdb strategies --input <impl>` lists input strategies, with prose conditions always marked as "check by hand".
- [ ] A procedure for adding a strategy or an intrinsic (sources, effect, preconditions, duplicate check), and query docs for `--loop` and `--input`.

## Comments
