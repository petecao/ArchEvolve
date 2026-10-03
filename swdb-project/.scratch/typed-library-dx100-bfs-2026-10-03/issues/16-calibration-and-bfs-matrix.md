# 16 — Calibration on the T17-fixed authors' BFS, with the BFS matrix

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 13, 14
**Spec:** `../spec.md`

**What to build:** `swdb certify --calibrate` shows the certification command works on known code, using the BFS matrix and the trusted oracle that candidate certification later reuses.

## Acceptance

- [ ] The BFS matrix: Kronecker scales 10, 14 and 16; uniform scale 14; a generated two-level graph whose accelerated frontier holds a vertex of degree above 16,384; tile sizes 16,384 and 1,024; four threads.
- [ ] The evaluator's trusted oracle computes per-depth vertex counts from each graph and source.
- [ ] Calibration builds the full DX100 source through the strict layer and passes a run only with the verifier's PASS text, per-level frontier sizes read from the authors' `Starting TDStepMAA` lines equal to the oracle's, no strict-layer assertion, and at least one DX100 operation on every graph whose scalar run has a level of more than four times 1,024 vertices.
- [ ] Positive control: the T17-fixed authors' BFS certifies. Negative controls rejected: shared context; dropped continuation; a 16,384-element chunk in a 1,024-element build; the unmodified authors' accelerated TDStep (wait on the wrong tile).
- [ ] A certification record is written; parent arrays are never compared byte for byte.

## Comments
