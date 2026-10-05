# 67 — Native evaluator v3: parent values are checked at full width before narrowing

Created: 2026-10-04 20:55 ET (from the final code review's open P3, [code review](../code-review-2026-10-04.md))
Updated: 2026-10-04 21:15 ET (resolved, commit ce42a45)
**Type:** slice
**Status:** resolved
**Blocked by:** —
**Spec:** `../spec.md`; [63](63-scalable-native-verifier.md), [66](66-native-protocol-after-isolation-test.md)

**What to build:** A native evaluator version whose driver can never turn an out-of-range parent of a
wider element type into a valid int32 parent. Evaluator v2, its driver template and every protocol that
pins it stay unchanged.

## Finding (final code review, 2026-10-04)

`tools/bfs_native/driver_scalable.cc.in` (evaluator v2) writes each returned parent as
`static_cast<uint32_t>(static_cast<int32_t>(parent[i]))`. A candidate that returns a wider element type
(for example `int64_t`) with the value `p + 2^32` for a valid parent `p` is truncated to `p`. The compiled
verifier then passes a vector that the full-width criterion (`verify_parents`) rejects. The template hash
is pinned in frozen protocols (`instrumentation.template_sha256`), so the fix needs a new evaluator version.

## Acceptance

- [x] New evaluator `swdb.native.evaluator.scalable.v3` with driver `tools/bfs_native/driver_scalable_v3.cc.in`
  and trial format `swdb.bfs.native.trial.v3`; verifier `swdb.bfs.structural.compiled.v2` (criterion
  unchanged) is pinned with it.
- [x] The v3 driver accepts only an integral parent element type of at most 64 bits (compile-time check)
  and narrows by saturation, so its int32 vector gets the same verdict and reason from the compiled verifier
  as the full-width vector gets from `verify_parents`.
- [x] v2 is unchanged: its template, trial format and every v2 protocol behave as before.
- [x] Differential tests: v2 and v3 drivers on the same candidates; in-range vectors are byte-identical; a
  wide out-of-range parent passes under v2 (the bug, kept as a regression witness) and is rejected under v3
  with `verify_parents`' full-width reason; non-integral element types do not build.
- [x] A native campaign file may pin v3 (`protocol.evaluator`).

## Answer

Resolved 2026-10-04 21:15 ET by the agent (commit `ce42a45`, worktree branch, not pushed). Requested by
Yan-Ru's 2026-10-04 instructions; the design details are agent-decided (revisable).

- `tools/bfs_native/driver_scalable_v3.cc.in`: `narrow_parent<T>` has a `static_assert` that `T` is integral
  and at most 64 bits, and saturates values outside int32 to INT32_MAX or INT32_MIN. Since every admitted
  graph has at most 2^23 vertices, such a value is out of range at full width; the compiled verifier rejects
  the saturated form with `verify_parents`' full-width reason (`parent[v] is not an integer in [-1, n)`), at
  the same first index. The trial record (`swdb.bfs.native.trial.v3`) adds `parents_saturated`.
- `swdb/bfs_native_scalable.py`: `EVALUATOR_V3`, `is_scalable`, `driver_for`, per-evaluator trial formats.
  v3 keeps one gzip copy per distinct verified parent vector in an evaluation (content-addressed by raw
  SHA-256). A single-thread BFS returns the same vector on every repetition of a source, so a 20-repetition
  block keeps 3 copies per side instead of 60 (a5 kept about 0.35 GB per evaluation at 10 repetitions).
  Receipts re-verify every observation from its (possibly shared) copy, as before.
- `swdb/bfs_native.py`, `bfs_native_pair.py`, `bfs_protocol.py`, `campaign_targets.py`: the scalable path
  takes v2 or v3; the campaign file enum admits v3.
- v2 is unchanged: template, trial format and protocols (`test_v2_identity_is_unchanged`).

**Tests** (`tests/test_bfs_native_v3.py`, Mac clang): in-range vectors byte-identical between v2 and v3 on
three graphs, both SG widths and two sources; four wide cases (int64 valid parent + 2^32, int64 -1 - 2^32,
uint32 unreached, uint64 + 2^32) pass the v2 verifier (the P3, witnessed) and get exactly `verify_parents`'
full-width verdict under v3; `double`/`float` elements do not build under v3. End to end, `evaluate-pair`
and `compare-evaluations` under a v3 protocol with the CI-width gate (ticket 66) keep one parent copy per
source and reject a changed retained copy. `tests/test_extensa_targets.py` freezes v3 into every role's
protocol. On mbit10 (x86_64, g++ 13.3, `-O3 -Wall -fopenmp`) the v3 driver builds against the upstream GAPBS
and DX100-fork BFS sources without warnings (2026-10-04 21:05 ET, commit `ce42a45`; build only, not timing).
