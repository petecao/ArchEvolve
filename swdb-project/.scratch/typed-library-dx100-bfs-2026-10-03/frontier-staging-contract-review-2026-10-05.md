# Review — `contract.bfs_tdstep_frontier_staging` and certify 1.4 (ticket 75)

Date: 2026-10-05 12:20 ET. Reviewer: an independent agent (not the ticket 75 author), read-only, under
Yan-Ru's 2026-10-05 delegation ("certify it"). Agent-reviewed under Yan-Ru's delegation; revisable by Yan-Ru.

## Verdict

PROMOTE AFTER FIXES. No blocking problem for the exact a8 tree; the legality argument holds for this code and
the trial record supported the claims. Every finding below was addressed before the final certification
(resolution column).

## Findings and resolutions

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | major | The prelude's seam macros (`compare_and_swap`, `QueueBuffer`) exist only in certification builds, so authored `#ifndef QueueBuffer` could run other code on the target; neither scope check nor scan stopped it (same gap in DX100 1.3). | Native contracts: the harness scan refuses any authored preprocessor directive other than `#pragma omp`, and the token `defined` (`certification_isolation.scan(..., directives=True)`); `SWDB_NATIVE` joins the harness prefixes. Test: `test_scope_and_directive_refusals_before_any_build`. The DX100 path keeps 1.3's scan (its rewrites author `#ifdef` blocks): **open for Yan-Ru**. |
| 2 | major | The scope region included the signature and allowed top-level additions after TDStep. | Certify requires the region to be exactly one function definition with the snapshot's signature (token-level brace match); contract and ticket reworded. Tests: `extra_global`, `signature` variants. |
| 3 | major | The a8 candidate record was not in the team store, so a Mac certification would bind an ID the store cannot find. | The candidate and proposal records are imported byte for byte into `records/` (tagged `mode: extensa`); written into the ticket's plan. |
| 4 | major (wording) | The two staging controls act on step inputs and do not depend on the candidate; the drop fault dropped the whole first window (never a true partial batch); `stale_row_offset` does not exercise the frame S3. | Contract and profile state the controls' nature; S1/S2 are discharged per candidate by the positive matrix. The drop fault now fires only on windows larger than the batch, on a new control graph `staging-tail-17` (one full batch of 16 plus a one-vertex tail with a unique leaf). S3 is now `assumed`, owned by the promotion reviewer per candidate, with the a8 evidence. |
| 5 | minor | C2 said "if and only if"; (iii) was not per location; "every execution" is not an ISO claim (plain reads race with the CAS). | C2 now says "if" (sufficient), states (iii) per location, and scopes the argument to the original under GCC's de facto model; it notes the rewrite removes one race and adds none. |
| 6 | minor | C1 and S3 are "structural" but nothing structural checks them. | C1 states that seam bypass leaves `forged_frontier` / `claim_without_write` alive and that the reviewer checks spelling per candidate; reviewer confirmed for a8 that every claim is `compare_and_swap(parents[v], curr_val, u)` with the push only on success. S3: see 4. |
| 7 | minor | `stale_row_offset` filed as `overlapping_pointer`; `evidence_basis: simulated` for native runs; host differs from target; witness forms not exclusive; `--sources` could override the profile. | Note on the control kind; the record's `profile.target_scope` states the certifying host and that the target check is the evaluator's verifier on mbit10 (`evidence_basis` stays `simulated`, the schema constant for pre-check evidence); the witness forms are exclusive and the other form makes a record invalid; native contracts refuse `--sources`. |
| 8 | — | Correct as written: `gather_stream` citation (rows 1), chain-form pattern key, knob binding, provenance. | — |

## Legality confirmed by the reviewer

(ii) matches `platform_atomics.h:30-31`; the barrier and flush at the end of the parallel region publish
`parent`; S3 holds for this code (flushes write at `shared_in` or later); the `omp simd` loops carry no
dependence; `schedule(static)` over whole batches is fine; `SGOffset` is `int32_t` (`graph.h:90`); no new
aliasing.

## Verified by the reviewer

`tests/test_certification_native.py` 9 passed; `test_certification_isolation`, `test_typed_library`,
`test_library_index` 107 passed; `Library.validate()` 0 problems; the a8 scope and scan accepted the tree and
(before fix 1) accepted the detection variant too.

## Certification and promotion after the fixes

- Certification `records/certifications/certification.b7954f4df9dd4e228fb12437b845f190.yaml` (Mac,
  2026-10-05 12:27 ET; its command version reads "1.4" but it is the 1.3-isolation native path, written before
  ticket 76's certify 1.4 was merged): contract content `dcaf63ec…`, tree `7acca955…` (the a8 artifact), candidate
  `extensa-native-bfs-20261005-a8.it1.kronecker.a0`, scan 0 findings; 20/20 cells, 8/8 controls rejected, each by
  its expected check; every clause row matched.
- Promotion `records/reviews/review.contract.bfs_tdstep_frontier_staging.a8452cbb68ab.yaml` (12:28 ET) for content
  `dcaf63ec…`. That content was superseded by the 1.4 port below (the profile pin changed), so this review no
  longer makes the entry shared; it stays as history.

## Second review: the port to certify 1.4 (2026-10-05 14:20 ET)

Ticket 76 put certify 1.4 (blinded, attributed) on `yanrujhou_main` while ticket 75 ran. The coordinator asked
for the same tree to be certified under both versions, and for promotion only if 1.4 also certifies. The native
path was merged and ported (`library/native/certification/v1_4/`, `certify_native_v14`). A second independent
reviewer (read-only) returned PROMOTE AFTER FIXES:

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | blocking | No 1.4 certification of the a8 tree; the contract content changed with the profile pin. | Certified under 1.3 and 1.4 after the merge; promotion re-issued for the new content (ticket 75 Answer). |
| 2 | blocking | New files untracked. | Committed in the merge. |
| 3 | major | partial_batch_dropped ran on a graph no positive cell used, so the input named the control. | Every control-only graph also gets a positive cell at the control thread count (22 cells). |
| 4 | major | No record-level tests for the native 1.4 rules. | Added: each attribution rule both ways, the native witness, the other-target witness, a fault line in a no-fault run, repeated `fault hidden` lines. |
| 5 | minor | Stale and lost-claim rules looser than needed. | Stale hits are limited to the recorded stale row; the lost-claim rule also requires the returned parent to fail the parent check. |
| 6 | minor | Only one `fault hidden` line parsed. | Hidden lines accumulate. |
| 7 | minor | Record file names reveal the fault through `/proc/self/fd` (also DX100 1.4). | Native runs name record files by nonce; the DX100 path is **open for Yan-Ru** (not changed here). |
| 8 | minor | 1.3 wording in C1, the profile note and the schema. | Reworded. |

No DX100 regression was found. `source_digest` now also covers `library/native/` and `certification_native.py`,
so DX100 `sources_sha256` values differ from ticket 76's `29f3bcab…` from this commit on.
