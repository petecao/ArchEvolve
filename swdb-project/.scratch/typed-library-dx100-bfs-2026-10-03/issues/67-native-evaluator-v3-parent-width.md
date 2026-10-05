# 67 — Native evaluator v3: parent values are checked at full width before narrowing

Created: 2026-10-04 20:55 ET (from the final code review's open P3, [code review](../code-review-2026-10-04.md))
**Type:** slice
**Status:** claimed
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

- [ ] New evaluator `swdb.native.evaluator.scalable.v3` with driver `tools/bfs_native/driver_scalable_v3.cc.in`
  and trial format `swdb.bfs.native.trial.v3`; verifier `swdb.bfs.structural.compiled.v2` (criterion
  unchanged) is pinned with it.
- [ ] The v3 driver accepts only an integral parent element type of at most 64 bits (compile-time check)
  and narrows by saturation, so its int32 vector gets the same verdict and reason from the compiled verifier
  as the full-width vector gets from `verify_parents`.
- [ ] v2 is unchanged: its template, trial format and every v2 protocol behave as before.
- [ ] Differential tests: v2 and v3 drivers on the same candidates; in-range vectors are byte-identical; a
  wide out-of-range parent passes under v2 (the bug, kept as a regression witness) and is rejected under v3
  with `verify_parents`' full-width reason; non-integral element types do not build.
- [ ] A native campaign file may pin v3 (`protocol.evaluator`).
