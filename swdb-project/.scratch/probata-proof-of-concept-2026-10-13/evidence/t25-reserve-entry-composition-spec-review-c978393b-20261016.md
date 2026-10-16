# Ticket 25 reserve-entry composition: independent spec review

Date: 2026-10-16 ET.

**Decision: PASS for the scoped pending reserve-entry application. No actionable findings.**

Baseline: `c978393b119a3614229a37f0f2c8ca2a097c750b`. The reviewed working-tree changes are limited to the five files below. The new test file was untracked when reviewed; its exact bytes are included in the hash set.

## Correctness and source correspondence

1. The new duty derives request bounds and growth/no-growth selection from the explicit pending predecessor `t25v3_eligible(h,r,o,b,bo,n,n)` and `0 <= n <= 2147483647`. For the source request `count+1`, mathematical `n+1` is positive, at most 2147483648 and strictly greater than capacity `n`. For `count`, the request equals capacity and the branch is false. Actual source conversion, machine arithmetic, typed-object image and layout correspondence remain separately pending.
2. The source receipt binds exact qualified reserve precondition, branch/helper call and constructor exact-capacity clause spans. Each span includes its byte hash and full model-source hash. The caller source call and reachable lowered reserve event are retained. The supported canonical packet route regenerates the candidate from physical source; the pure test metadata is explicitly worked metadata, not evidence that its placeholder source spans describe a real translation unit.
3. No axiom, public caller premise, assumed constructor result or admitted body record is added. The predecessor must still be established by completed construction. The growing state remains pending. The nongrowing receipt's `state_after = h` describes the checked branch with no body store or helper call. Neither branch grants an alias-liveness fact, reserve postcondition or caller scalar-result theorem.
4. Growing current-buffer and stale-alias candidates receive the same entry duty. Their later observation and liveness obligations remain distinct and pending. Public caller admission remains unsupported, with no proof records admitted and no restriction on incoming pointer maps.

## Test scope and inventory

All relevant production/test count literals are updated from 127 to 128. The current preparation inventory is 35 constructor duties, 67 reserve duties, 11 destructor duties, ten local laws, one numeric kernel and four applications: **128 pending targets**.

The new pure seam tests cover growing and nongrowing requests, unsupported request/type/capacity metadata and safe/stale equivalence. Public packet controls require canonical reconstruction and preserve pending metadata. These assertions do not claim formal acceptance.

## Reviewed content hashes

Paths below are relative to `swdb-project/`.

| File | SHA-256 |
|---|---|
| `swdb/vector_reallocation_composition.py` | `fbce29f010d92be33b09a0f31c440f8db97c7f0dfd0769a41a59e71bdfe6e108` |
| `swdb/vector_reallocation_caller_packets.py` | `a30b633404723d99c84ee3473eb0a352fe6641274e036524451826940abc59f0` |
| `tests/test_vector_reallocation_reserve_application.py` | `3a35e5eeb9529c48e0954078ff0932a60aff93ce5dfea1d3fa219b314242bf3c` |
| `tests/test_vector_reallocation_caller_packets.py` | `65d81ff24c0a59d315ee9a34e90ac744da20d0d8be674f78a858516efe19e95e` |
| `tests/test_vector_reallocation_copy_prefix_cases.py` | `723baac37d99a2370f8f06b447f4b7d1199c98808ae98b6f2ab6342439e8ce2d` |

## Evidence limits

This review used read-only Git/source inspection and Python standard-library AST/hash checks. All five reviewed files parse. The reviewer ran no project imports, tests, compiler, native project helper, verifier, solver or SSH command and edited no production file.

The reported pure RED/GREEN and retained-parser replay RED/GREEN receipts were not independently validated by this review. Neither those controls nor this PASS establish actual WP grammar/task closure, a member-body theorem, source-runtime correspondence, full caller composition or ticket completion. Existing standalone qualified-model boundaries remain unchanged. Ticket 25's full acceptance remains open.
