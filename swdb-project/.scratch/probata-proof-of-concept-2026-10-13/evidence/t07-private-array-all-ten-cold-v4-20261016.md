# Settled all-ten private-array generation audit

2026-10-16 ET. PASS for complete diagnostic-generation integrity. No positive
proof, healthy initializedness negative, allocator refinement or TD acceptance.

The continuation guard exited 0 in 3.026090 seconds at 175.109375 MiB, with no
inspection events, timeout/OOM, final inspection failure or unconfirmed children.
Root's three finite poststop observations were empty; shared leases were absent.
The passive audit checked 326 conditions without mismatch: all 224 prior raw
files and 231 prefix pins, all 31 immutable source blobs, selected runtime,
complete new artifact membership, and every source/normalized/property census.

| Case | Goals | Properties |
|---|---:|---:|
| positive | 327 | 454 |
| missing-store | 318 | 447 |
| wrong-cell | 326 | 453 |
| uninitialized-scalar | 316 | 445 |
| copy-positive | 339 | 465 |
| history-positive | 335 | 461 |
| reentry-missing-store | 331 | 459 |
| modular-entry-missing-store | 341 | 468 |
| reentry-positive | 331 | 459 |
| modular-entry-positive | 342 | 469 |

The aggregate is 3,306 generated goals: 2,862 ordinary and 444 smoke, with 4,580
source properties and 386 RTE initialization properties. Counts are scoped by
case; repeated helper IDs across distinct units are not conflated. Each unit
contains all 20 helpers and its exact one/two root bodies, all three bodyless
call-smoke contexts and all three normalized snapshots. The seven previous units
were consumed without rerun. Complete ordinary/smoke/property/dependency/extern
and source/direct-call/body closure passes for all ten. No old 245-goal count or
209/212 proof result was imposed or transferred.

Every intended read has an attributable payload initialization guard separately
from pointer-field initialization: local cell 0 for positive, missing-store,
history, loop reentry and modular entry; local cell 1 for wrong-cell; shared
copy destination for copy-positive; the uninitialized scalar for its separate
negative. Exact source properties and per-case goal IDs are retained in JSON.
The constructor buffer-domain postcondition and binder output initialization
remain ordinary obligations. Normalized C retains the uninitialized typed array
and exact constructor/binder/store/copy/read/destruction path.

Both exact global capability warnings remain explicit per unit. The only new
warning is conservative missing loop assigns at the pinned for-loop: line 8 in
reentry-missing-store and line 9 in reentry-positive. Each occurred once and is
retained as frame_discharged=false/proof_acceptance=false. Pedantic assigns
headers and full continuations remain intact. There are no additional classified
unsupported/builtin/cast/omission warnings. Alignment remains unresolved and the
function-pointer warning is conditionally inapplicable only for the exact direct
source/all-normalized-call census; no full C RTE claim follows.

All 444 raw smoke records have passed=true and no valid result, but the no-prover
run supplies no external smoke execution. This is no observed contradiction in
diagnostic generation, not a proof of consistency. Native JSON is absent as
expected for this prover-none artifact path; complete production inventory is
retained. Actual backend T_init/SINIT task formulas were not exported. Therefore
neither payload-mask classification nor lexical retirement/reentry is qualified.
A negative nonproof under the loop's all-memory frame approximation could result
from imprecision rather than real initialization reset and cannot qualify it.

The next new-purpose gate should compile/export actual Why3 backend tasks on the
unchanged positive/missing-store/wrong-cell C trio, preserving all helper/root,
ordinary/RTE/init/smoke goals. Use WP generation with a fresh CVC5 sentinel config,
no actual solver invocation, complete Wpo/backend-ID/source binding and imported
memory-theory closure. Do not transplant T25 local theories or assumptions. No
source invariant, initializing premise, reset/havoc fact, unrolling transformation
or goal omission is justified here. Subsequent proof must discharge positive and
all background obligations and diagnose the exact negative payload formulas.
The loop/multiple-entry, source refinement, normal-return ABI, physical caller,
full C++/device/RTE, TD and counted-provider gates remain separate and refused.
