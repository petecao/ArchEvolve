# 44 — BC gem5 completion witness and execution case

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 39, 40
**Spec:** `../spec.md`

**What to build:** BC correctness and coverage can be checked on gem5 even though gem5 exits before the program's own verifier runs.

## Acceptance

- [x] A BC completion-witness plug-in works like BFS's v2 witness.
- [x] A BC read-only execution case is defined for the forward pass.
- [x] Fixture tests pass; BFS is unchanged.

## Comments

## Answer

Resolved 2026-10-03 23:35 ET (agent, BC track). Regression in this state: 349 passed, 2 skipped (BC, witness, v2, read-only, gem5 driver, coverage, library).

**Built.**
- BC gem5 plug-in values (`swdb/kernels/bc.py`): ROI `bc.complete_call.v1`, checker
  `dx100.bc.verifier.v2` (witnessed), entry point `Brandes`, result field `score_results`,
  storage marker `SWDB_BC_SCORE_STORAGE`, frontier print `Starting PBFS:`.
- Trusted gem5 driver: preloads the original CSR, times one `Brandes` call, prints the score
  storage and an FNV-1a fingerprint, then checks the exact returned scores after the ROI with
  an evaluator-owned serial Brandes oracle in the source's types (NaN-closed, vacuous
  sources refused).
- `scripts/dx100_bc_verify.py`: copy of the frozen BFS gem5 driver that accepts only the BC
  checker; the kernel-agnostic trace parser `swdb/dx100_witness.py` and memory observer are
  shared runtime files.
- `swdb/bc_witness.py`: BC's v2 completion witness. It checks the BC parts itself (checker,
  protected score row, `swdb.bc.original-adjacency.v1` treatment, exact output bytes) and runs
  the frozen BFS v2 validator on a translated copy for every kernel-agnostic rule (binding,
  seal, runtime, continuation, syscall witness, artifacts).
- Read-only execution case for the forward pass: same instruction-mix rule
  (`I = 3R - S`: per chunk one stream load, two row-bound gathers and a final empty range
  loop; per non-empty range tile three gathers). BC read-only protocols need no BFS
  parent-gather race companion (`race_companion`, BFS only).

**Tests.** `tests/test_bc_gem5_witness.py`, 18 cases, fixtures only: seam selection; driver
copy differs only in its checker; BC witness accepts the BC fixture, the BFS validator refuses
it, eight identity/result mutations and output/seal tampering are refused; result-line
parsing; read-only mix observed/unobserved; forward-pass frontier sizes and exact print;
companion gating; the trusted driver built natively around upstream `bc.cc` prints PASS and
fails a NaN score that BCVerifier would accept.

**Assumptions.** No gem5 run here (ticket 45). The BC continuation allocates the Brandes work
arrays after the ROI (BFS preallocates its checker arrays); the treatment record says so.
