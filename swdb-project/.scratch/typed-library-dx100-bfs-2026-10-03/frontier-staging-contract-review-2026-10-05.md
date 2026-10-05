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

- Certification `records/certifications/certification.b7954f4df9dd4e228fb12437b845f190.yaml` (certify 1.4, Mac,
  2026-10-05 12:27 ET): contract content `dcaf63ec…`, tree `7acca955…` (the a8 artifact), candidate
  `extensa-native-bfs-20261005-a8.it1.kronecker.a0`, scan 0 findings; 20/20 cells, 8/8 controls rejected, each by
  its expected check; every clause row matched.
- Promotion `records/reviews/review.contract.bfs_tdstep_frontier_staging.a8452cbb68ab.yaml` (12:28 ET): tier shared,
  status certified. Agent-reviewed and promoted under Yan-Ru's delegation; revisable.
