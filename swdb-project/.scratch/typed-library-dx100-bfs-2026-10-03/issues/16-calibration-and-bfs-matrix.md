# 16 — Calibration on the T17-fixed authors' BFS, with the BFS matrix

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 13, 14
**Spec:** `../spec.md`

**What to build:** `swdb certify --calibrate` shows the certification command works on known code, using the BFS matrix and the trusted oracle that candidate certification later reuses.

## Acceptance

- [x] The BFS matrix: Kronecker scales 10, 14 and 16; uniform scale 14; a generated two-level graph whose accelerated frontier holds a vertex of degree above 16,384; tile sizes 16,384 and 1,024; four threads.
- [x] The evaluator's trusted oracle computes per-depth vertex counts from each graph and source.
- [x] Calibration builds the full DX100 source through the strict layer and passes a run only with the verifier's PASS text, per-level frontier sizes read from the authors' `Starting TDStepMAA` lines equal to the oracle's, no strict-layer assertion, and at least one DX100 operation on every graph whose scalar run has a level of more than four times 1,024 vertices.
- [x] Positive control: the T17-fixed authors' BFS certifies. Negative controls rejected: shared context; dropped continuation; a 16,384-element chunk in a 1,024-element build; the unmodified authors' accelerated TDStep (wait on the wrong tile).
- [x] A certification record is written; parent arrays are never compared byte for byte.

## Comments

Claimed by Codex strict-library/certification agent, 2026-10-03.

## Answer

Completed 2026-10-03 ET. The full vendored authors source is reconstructed into a private build copy, with the T17 store-result wait fix and trusted read instrumentation. Calibration receipt `certification.344e44857df44a0eac5150c6342c5873` passes all ten cells: Kronecker scales 10/14/16, uniform scale 14, and a generated two-level graph with frontier 4,200 and a 17,000-degree vertex; tile capacities 16,384/1,024; four threads; source 0. The independent serialized-CSR oracle yields per-depth counts. PASS text, actual queue uniqueness/counts, authors frontier text, strict assertions, and execution coverage are checked. Seven applicable control cells reject shared context, dropped continuation, a 16,384 chunk in the 1,024 build, and the unmodified wrong-store wait. Parent arrays are never compared byte for byte.

Evidence scope: strict functional certification on the Mac, basis `simulated`; no target timing or hardware-coherence proof. L3/L5 and ready-bit semantics remain assumptions owned by Eric pending target evidence. Focused verification: `python -m pytest -q tests/test_typed_certification.py` — 109 passed. Raw build/run/control outputs remain under `/private/tmp/swdb-typed-library-certification-20261003/` and are named by the certification records.

Review follow-up, 2026-10-03 ET: fresh calibration with the frozen corrected producer again passes ten cells and rejects seven controls. Prior calibration receipts remain historical evidence.

Dependency review correction, 2026-10-03 ET: receipts now bind the complete referenced normative entry closure before/after execution. Old unbound receipts remain history and grant no current dependency-bearing certification. All ten lowerings, the candidate and calibration have fresh passing bound receipts; see [promotion packet](../drafts/promotion-review.md). The 119 producer regressions plus exact public delivery reproduction pass (120 total); 35 library-state regressions and independent changed-reference/stale-contract custody rechecks also pass.
