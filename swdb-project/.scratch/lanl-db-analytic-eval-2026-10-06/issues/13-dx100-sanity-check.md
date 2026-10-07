# 13 — DX100 sanity check against the paper

Created: 2026-10-06
Updated: 2026-10-06 ET
**Type:** slice
**Status:** resolved
**Blocked by:** 10
**Spec:** `../spec.md`
**Time estimate:** 2 h

**What to build:** The estimated DX100 speedup for BFS, and for any other kernel the paper also reports, is compared with the speedups Khadem et al. (ISCA 2025) report, labeled a weak check (D14).

## Acceptance

- [x] Reported numbers are cited with page or table and basis `reported`.
- [x] Differences in inputs, core counts and configuration are listed beside the numbers.
- [x] The result is labeled a sanity check, never a validation.

## Answer

Updated: 2026-10-06 ET. Added the public read-only `scripts/paper_sanity_check.py` seam, documented in `docs/reference/paper-sanity-check.md`. The sealed request and actual report are `evidence/13-dx100-paper-sanity-request-20261006-a1.json` and `evidence/13-dx100-paper-sanity-20261006-a1/report.{json,md}`. Khadem et al. v2 PDF page 9/Figure 9 gives approximate BFS 2.9×, BC 2.2×, and PR 1.2× plot readings with reported basis and explicit ±0.1× manual reading resolution. Page 8/Section 5/Table 3 supplies the graph/core/cache scope.

The actual ticket 10 BFS ratio remains null/incomparable. BC and PR have no DX estimate supplied at this point; the report says so explicitly and supports a new sealed comparison after ticket 14. Uniform versus Kronecker inputs, bottom-up versus complete DOBFS ROI, simulated hardware cores versus requested software threads, and LLC/configuration differences appear beside the numbers. No accuracy validation or error-band claim is made.

Nine public tests passed (3.86 s), including stale request, estimate content pin, malformed basis/unit/locator/number, wrong kernel and output preservation refusals. `evidence/13-paper-sanity-closeout-20261006.json` seals the proof. All prior canonical/library/application and `swdb/` bytes remain unchanged; no estimator/mechanism code change, provider call or remote execution.
