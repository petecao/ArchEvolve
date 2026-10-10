# 05 — Indirect accesses and the BFS baseline on the CPU

Created: 2026-10-06
Updated: 2026-10-09 23:49 ET (code review note appended)
**Type:** slice
**Status:** resolved
**Blocked by:** 04
**Spec:** `../spec.md`
**Time estimate:** 1.5–2 days

**What to build:** The pass classifies `single_valued_indirect` and `ranged_indirect` accesses (and `pointer_chase` or `data_dependent_merge` where it can, otherwise `unknown`); the counted run records executions and footprint per access; characterization regions are the existing profile-package and site-finder region IDs, including loops the compiler outlines for OpenMP (D33); the requests-in-flight (latency) and cache-fit mechanism models exist. The BFS and BC baselines get estimates on a small Kronecker graph, covering what their paired timing covers (D16).

## Acceptance

- [x] Classifications are compared with the 13 hand-written access patterns of `gapbs-bfs-do` and the BC implementation records; every mismatch is listed with a reason.
- [x] One fixture kernel per indirect address shape, with hand-computed answers.
- [x] Loops that map to no region are listed, never dropped.
- [x] Estimates for `gapbs-bfs-do` and the BC baseline, each with a per-region report.

Claimed: 2026-10-06 ET by Codex ticket 05 worker, branch `codex/lanl-ticket05`; base `86b2a9a`.

Historical implementation checkpoint (superseded by Answer below): 2026-10-06 ET — indirect hand fixtures, registered per-trial
BFS/BC binding and composable memory models implemented. Compact remote command
context: `../evidence/05-registered-counting-runbook.md`. Acceptance remains pending
the actual small-Kronecker mbit10 per-region estimates and pattern-comparison receipts.


Historical partial acceptance evidence (superseded by Answer below): 2026-10-06 ET. The immutable actual mbit10 a1 records
(`5d0fbdb`, counted source `67f1b3b`) compare all 13 BFS and 20 BC handwritten patterns.
Direct matches are **0/13 and 0/20**; every mismatch has a nonempty explanation.
Individual lowered SSA sites do not prove the full handwritten multi-step chains or
shared-helper instances, and direct stream contracts differ from the observed
lowered address shapes. This establishes comparison, not classifier agreement.
All 129 BFS and 165 BC unmapped loop IDs are retained. The independent gather,
ranged-indirect, pointer-chase and data-dependent-merge fixtures have hand-computed
counts/footprints; atomic and sparse OpenMP fixtures retain memory and worker facts.

Corrected source `cda8f2d` excludes metadata/hint runtime costs while retaining
executed events, counts checked arithmetic explicitly, and preserves opaque runtime
costs as unknown. The final affected estimator/protocol batch passed 22 tests;
independent arithmetic/hint and metadata fixtures and the fake-verified binding
repair passed separately. All 555 records validate after importing immutable a1
receipts. Parent reported the corrected a2 BFS count passed on mbit10; BC is running.
The fourth acceptance item remains pending real frozen-protocol per-region reports.


## Answer

Resolved: 2026-10-06 ET. Registered BFS/BC characterization, generic indirect
memory mechanisms and frozen per-region estimates are implemented. Actual mbit10
counts and estimates use `kron-g16-k16`, four threads and five independent trial
sources `[64863, 35711, 18064, 30164, 1014]`, preserving the complete trial-lambda
ROI, helper/outlined-worker attribution and exclusive region counts. New source
binding requires registered source/input/ROI/run-argument evidence; historical
receipt validation does not require inaccessible remote raw files.

| Actual baseline | Reported observed regions | Zero-only region IDs | Trial estimates | Direct handwritten matches | Unmapped loop IDs | Uncovered runtime symbols | Whole-call seconds / ratio |
|---|---:|---:|---:|---:|---:|---:|---|
| `gapbs-bfs-do` | 27 | 229 | 5 | 0 / 13 | 129 | 13 | unknown / unknown |
| `gapbs-bc-brandes` | 31 | 277 | 5 | 0 / 20 | 165 | 18 | unknown / unknown |

All 13 BFS and 20 BC patterns have explicit comparison results and mismatch
reasons in the [actual per-region report](../evidence/registered-estimates-mbit10-20261006-a2.json).
Individual lowered SSA address sites do not prove complete handwritten multi-step
chains or ambiguous shared-helper instances, and direct stream contracts differ
from observed lowered shapes. This is comparison evidence, not classifier
agreement. All unmapped loops are listed, with qualified generated IDs retained.

Each indirect shape has an independent fixture with literal hand-computed
counts/footprints: single-valued gather, ranged indirect, pointer chase and
data-dependent merge. Atomic accesses retain address/width/read-write semantics;
sparse OpenMP fixtures prove distinct executing-worker counts without treating
team size as an active-worker multiplier. Requests-in-flight latency and cache-fit
models compose with compute/stream models. Zero work produces zero cost; missing
counts, unsupported memory service and opaque external-call costs remain unknown.

The corrected a2 count source is `cda8f2db11996402bcb483bf98440eedc07feaa7`,
with immutable receipts imported in `eaa56d0`. The measured-target/frozen-estimate
execution source is `b5acc909ef9df813352004e88633fac4db4b55e7`; metadata export
`68df1dd` includes both per-region estimates, separate frozen protocols and the
[bound target/fixture receipt](../evidence/bound-calibration-fixture-mbit10-20261006-a1.json).
The remote job exited zero at `2026-10-06T22:01:24Z` on node0, lease generation 473.
The T1 contract fixture has a positive estimate; it is not an application accuracy
check. Raw count/estimate files remain under the paths recorded in these receipts;
only project source and structured count/estimate metadata were Git-transferred.

Both application protocols pin target `mbit10.cpu.lanl20261006a2.v2.t4`, canonical
SHA-256 `0a7b3143000e6f805f20192e6b5c1ea11a74c1d61b7994dd19f718486750b88e`,
and estimator bundle `645fc669120506b9d87aa32859d72aac928cb6a8e419d48ddc9e54a258595017`.
BFS protocol hash is `fe3608feddadc0492beef6d9226fabdc2a188f7c208102633164f3a12d68960f`;
BC protocol hash is `c9f75f1d64afca1d1ba14ddffa74c19036373a795d1780e62112ce69d1f3e57f`.
Raw JSON `file_sha256` values and exported canonical YAML byte hashes have distinct
scopes. Verification checked wrapper seals, canonical record byte hashes, target/
protocol/characterization identities, unchanged estimator identity, all five
trials and each exact compact trial-bound input/result against its persisted record.
Top-level bound/region seconds are medians; root/first-observed inputs are diagnostic
templates. Exact formula inputs live in `trials[].regions[].bounds[].inputs`.

Executed compiler hints/noalias annotations carry no runtime operation cost;
checked arithmetic records the result and overflow predicate explicitly. True
allocation, OpenMP, clock and bulk-memory calls retain their counts and known or
unknown byte sizes. The 13/18 opaque runtime symbols, unsupported memory shapes and
serial/partial worker transfers from aggregate T4 rates still prevent complete
whole-call estimates. Distinct workers observed during a trial do not establish
balanced or instantaneous concurrency. No CPU error-band agreement or speedup is
claimed; timing pairing and fuller CPU service coverage belong to ticket 11.
Immutable a1 receipts retain their original accounting and are not rewritten.

Validation: the final affected estimator/protocol batch passed **22 tests**;
independent checked-arithmetic/hint, noalias-metadata and binding-rejection repairs
passed separately. The combined 05/07 compatibility batch passed **7 tests**,
covering typed measured-target binding, immutable native trials, v2 numerator
proofs, calibration dependency preservation, JSON scientific-number decoding and
memory models. The compact-report CLI smoke passed after the metadata-only input
scope labels, preserving scientific values, null totals and known partial call
sizes. Final `python3 -m swdb validate` passed **584 records** locally, matching the
remote receipt. Exact commands and evidence boundaries are in the
[runbook](../evidence/05-registered-counting-runbook.md).

## Code review 2026-10-09

Added 2026-10-09 23:49 ET. Corrects the cause given above for **0/13 and 0/20 direct
matches**; the history above stays as written.

- **Real cause: a classifier defect, not lowered multi-step chains.** The pass could not
  see through loop-invariant base pointers that the counting IR reloads every iteration
  (C++ container members, OpenMP captured variables). It also read an OpenMP chunk bound
  as an index array. In the a2 BFS record, OpenMP worker code had 0 `stream` accesses out
  of 5.1M executed (BC: 0 of 31M), and 3.5M BFS accesses were labeled `constant`.
- **Second defect: invariant addresses charged as DRAM requests.** `constant` accesses
  counted as dependent requests in `requests_in_flight_latency`. They made up most of the
  latency bound that limits the a2 BFS/BC per-region reports, for example 19.6 of 25.3 µs in
  `loop:bfs.cc:2357` (td-edge).
- **Third defect: the comparison could not match multi-step patterns.** The test asserting
  it could never fail.
- **Fixed in source** (not yet re-counted): `swdb/llvm/Characterize.cpp`,
  `swdb/analytic_models.py`, `swdb/analytic_binding.py`, plus tests. On the g4 test graph the
  per-step comparison now matches **8/13 BFS** and **8/20 BC** patterns; the remaining
  mismatches name the failing step. The format doc lists all changes:
  `docs/reference/format-v0.4-analytic.md#code-review-corrections-2026-10-09-et`.
- **Still true:** the a2 receipts, counts and estimates above are immutable history and
  keep the old classifications. Fresh mbit10 counts and frozen protocols are needed before
  any application estimate uses the fix.

**Decided 2026-10-10 09:12 ET (Yan-Ru, accepting the review's recommendation):** a stride-0 stream pays only its first-touch bytes (invariant rereads are cache- or register-resident); a pattern step matches on element width plus address shape, which does not prove the exact array, and that limit stays documented; a CSR-style loop in a helper with no enclosing loop classifies as `stream`.
