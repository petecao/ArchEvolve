# 09 — DX100 estimate

Created: 2026-10-06
**Type:** slice
**Status:** resolved
**Blocked by:** 05
**Spec:** `../spec.md`
**Time estimate:** 1.5–2 days

**What to build:** The pass recognizes accelerator commands from the intrinsic records, not from a hard-coded list. The counted run counts the address stream live for a target's reorder window and DRAM address layout, storing no stream (D17, D24). The DX100 target description is written from its hardware-target record, its pinned configuration (D18), Eric's catalog and the DX100 paper (D23). The remaining version-1 mechanism models exist: offload setup, tile staging, reorder-window row counting and fetch queue. The DX100 BFS candidate artifact gets an estimate with a per-region report.

## Acceptance

- [x] No gem5 output is read (D3), and no address stream is written to disk.
- [x] A fixture with a known address pattern gives the hand-computed row-buffer hit rate.
- [x] DX100's unknown parameters are listed and ranked by how much each moves the estimate.
- [x] Nothing DX100-specific exists outside the target description (D21, D22).


## Answer

Resolved: 2026-10-06 21:15 ET. Description-driven command recognition, bounded live
allocation/lifetime/request observations, the four mechanism models and an actual
registered DX100 BFS candidate per-region estimate are implemented. Model and
observer code contains no DX100/MAA/intrinsic-name list; commands, source/backend
aliases, memory roles, layout and policy live in immutable records. The fresh
functional target derives configuration facts directly from pinned `e4fc4af`,
with [design-source citations](../evidence/09-design-source-binding.md); it has no
historical gem5 target/calibration dependency.

The [actual compact report](../evidence/09-functional-application-report-mbit10-20261006-a2.json)
and [identity/check proof](../evidence/09-functional-estimate-closeout-20261006-a2.json)
retain five complete `gapbs.functional_trial_lambda.v1` calls on mbit10, T4,
`dx100-functional-kron-g16-k16`, candidate
`bfs-functional-read-offload-20261006-a1.proposal.candidate-1`. They retain all
284 static region IDs, 153 unmapped loops, 26 observed region IDs and 258 zero-only
IDs. Exact bounds and additive setup appear separately in every trial.

| Trial | Source | Executed regions | Logical line requests | Logical row groups | Useful staged bytes | Setup events | Whole-call seconds |
|---|---:|---:|---:|---:|---:|---:|---|
| 0 | 43491 | 26 | 580126 | 23846 | 22390212 | 1351 | unknown |
| 1 | 20508 | 23 | 578081 | 25373 | 22388268 | 1351 | unknown |
| 2 | 39814 | 23 | 580167 | 24254 | 22369392 | 1322 | unknown |
| 3 | 48991 | 23 | 581502 | 28817 | 22297944 | 1333 | unknown |
| 4 | 13959 | 23 | 581800 | 27751 | 22289520 | 1322 | unknown |

The row-group fractions (0.9504–0.9589) are ideal logical grouping under explicitly
inferred allocation-relative placement and fixed command/worker windows. They
are not physical row-buffer measurements. Command tails, alias deduplication,
worker context, bounded objects/views, unsupported context and budget exhaustion
remain explicit. No address sequence, allocation base or decoded row list is
serialized. LLVM IR/binaries/stdout stay at the receipt's raw mbit10 paths; no
gem5 output or uninstrumented performance outcome enters these inputs.

All nine unknown parameter references retain basis/source/unit and exact dependent
bounds. Eight required references share dependency priority 1; unused floating
point throughput has priority 2. Null references have no defensible half/double
magnitude, so the numerical impact rank stays null. The generic report numerically
ranks complete known fixture estimates by whole-trial half/double impact, and
recomposes trials before median aggregation. Actual row-service scenarios remain
local components with unknown parallelism; changing queue capacity requires fresh
observations. This reports the limit of the ranking, rather than substituting
invented reference values.

The 25 named structural/call gaps include opaque executed runtime calls, worker
rate scope, a missing host memory mechanism and missing host/offload composition.
They are distinct from fillable numeric parameters. Whole-call seconds, ratio and
error band remain null. D25's `within_error` token therefore makes no measured
agreement or gain claim. Adding structural mechanisms, changing backend/layout/
window/request policy or altering resolved policy parameters requires fresh counts;
only classified numerical service-rate changes can reuse the immutable receipt.

Frozen protocol `bfs.functional.kron-g16.t4.estimate.protocol.a2.3c10575e0635e4cc`
pins target-description SHA-256
`6351828a0ba1536f6862d428a2522ae36ea5a39753879abdb5b637b26d8ce211`
and estimator source bundle
`3ad3ce75dc7ed90f7093c3a867ff187cf2884723adf7a98264b005c207018475`.
Count self-identity is `2b68d09d…`; its full record hash frozen by the estimate is
`07d446f8…`. Both full hashes and file hashes are distinguished in the proof.
Count source is `9ba9277`; model/report source is `e9d2c23`, executed after clean
metadata/integration merge `bc26c9b`. Fresh Linux static LLVM support links only the
verified native `SHA256.cpp.o`, preserving source-view SHA-256 guards without
linking duplicate static LLVM registries; the original failed a1 is preserved.
Candidate/source packaging review labels remain unverified/unchecked and the
profile remains `contract_fixture`. The existing strict1.6 functional certificate
and the new verified execution binding are separate evidence scopes.

Acceptance evidence: the public command fixture counts six logical requests,
three row groups, three grouped hits and hit fraction 0.5, including a partial
window. Unknown window, straddling range, alias/unwind, target-object and budget
cases retain honest unknowns. Independent setup/staging/row/queue fixtures verify
literal formulas and zero-work handling. Final affected public batch: **22 passed
in 329.09 s**; stateless-support/source-view guards: **12 passed in 325.24 s**;
composition/setup/mechanism batch: **15 passed in 18.82 s** (overlapping checks,
not additive totals). Actual copied-store validation: **617 records valid**;
all 615 original canonical YAML files are byte-identical. The [count/runbook](../evidence/09-functional-g16-counting-runbook.md)
and [format/model contract](../../../docs/reference/format-v0.4-analytic.md)
provide the stable public seams for 10, 12 and 16. Campaign blindness and a
FUNC-to-MMIO logical surrogate are not established by this historical g16 tuple.


Review follow-up: 2026-10-06 21:17 ET. A suspected repeated-region aggregation
loss was disproved by the public counted run: the pass routes both loops' access
callbacks to their first canonical source ID before the live observer computes
its union. The regression retains eight requests, 32 useful bytes, eight full
allocation requests, the exact five-line/28-byte unions, allocation call-site
counts 3/5 and eight frees. Two related lifetime/histogram checks also passed:
**3 passed in 10.35 s**. The actual application has 153 unique loop IDs plus 131
unique serial symbols with no overlap, so no count/model correction or replay is
needed. Final canonical validation is **617 records valid**, and the source
bundle still equals the frozen `3ad3ce75…`; all existing receipts remain immutable.
