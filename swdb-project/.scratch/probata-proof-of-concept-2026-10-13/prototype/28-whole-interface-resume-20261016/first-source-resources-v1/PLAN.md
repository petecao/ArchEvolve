# First-source model resource profile

2026-10-16 ET. Prospective source-only resource preflight; no compiler/native/proof run.

The exact first 3148 source makes four stream loads. For two value lanes, each
load's scalar setup creates 30 immutable nodes and each lane can create 14 more:
active predicate 2, index 3, read 1, conditional output up to 5, work root 2 and
join 1. Thus this conservative slice alone accounts for 232 nodes and exceeds the
unchanged backend default128 before the source's later families are emitted.

The proposed explicit source profile owns `DXM_NODES=1024` before the unchanged
backend body, after the existing choice hooks. A preexisting macro is a compile
error. Source hash/function and all four component hashes must be exact. No
backend default, ownership rule, receiver reset or payload initialization changes.

| Fixed source category | Count | Conservative nodes per | Total |
|---|---:|---:|---:|
| Stream loads | 4 | 58 | 232 |
| Stream store | 1 | 56 | 56 |
| Scalar/vector/reduce group | 1 | 88 | 88 |
| Indirect calls | 5 | 36 | 180 |
| Range | 1 | 208 | 208 |
| Scalar/register/CPU observations and writes | 1 | 64 | 64 |

The accounting total828 is a reviewable source preflight, not an independently
proved allocation theorem or scientific result. It includes slack for missing
version nodes and scalar/CPU activity. Actual node-capacity checks remain on every
allocation; a counterexample or refusal there cannot count as a successful source
proof. The model's other capacities, numeric/domain/lifetime/source/ownership
checks and full-domain draw rules are untouched.

`dxm_cover` checks `steps++ < 20*DXM_NODES` and stack depth against `DXM_NODES`.
Only its retained actual opaque CBMC loop selectors receive `20*1024+1=20481`.
Other helper loops keep513 and original source loops keep1. A helper owner or
selector outside the actual checked helper census refuses. No selector is
invented, removed or reconstructed from source; the normal actual `--show-loops`
observation is still required. Every unwinding assertion remains enabled.

Coherent V4 must use the same prefix/profile in profile preparation and fresh
public composition, retain it in assembly/certificate/method settings, pin this
module in the producer manifest, and record the actual per-loop unwind rows.
The memory55b9 path keeps its original default model and cannot select this
first-source resource profile. Actual verifier cost/RSS and sufficiency remain
unmeasured and subject to root's admitted whole-process guard.
