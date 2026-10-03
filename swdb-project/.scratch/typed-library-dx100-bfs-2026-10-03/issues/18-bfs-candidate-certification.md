# 18 — BFS candidate-artifact certification

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 16, 17
**Spec:** `../spec.md`

**What to build:** `swdb certify CONTRACT_ID --candidate ID` (or `--snapshot ID --patch FILE`) judges a BFS candidate artifact by the correctness check, the contract's preservation obligation and its execution witness on the BFS matrix.

## Acceptance

- [ ] A run passes only with the verifier's PASS text, per-level frontier sizes equal to the trusted oracle's, and an accelerated-chunk count above zero wherever the scalar run reaches the contract's threshold knob.
- [ ] Frontier sizes come from DOBFS's `Starting TDStep` line, checked by exact text at build time like the verifier text; the accelerated-chunk count comes from the hook's output.
- [ ] The forged-frontier control (double-enqueues while printing the expected sizes) is rejected.
- [ ] The certification record carries the contract ID, its content sha256 and the tree sha256.

## Comments
