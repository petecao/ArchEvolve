# 18 — BFS candidate-artifact certification

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 16, 17
**Spec:** `../spec.md`

**What to build:** `swdb certify CONTRACT_ID --candidate ID` (or `--snapshot ID --patch FILE`) judges a BFS candidate artifact by the correctness check, the contract's preservation obligation and its execution witness on the BFS matrix.

## Acceptance

- [x] A run passes only with the verifier's PASS text, per-level frontier sizes equal to the trusted oracle's, and an accelerated-chunk count above zero wherever the scalar run reaches the contract's threshold knob.
- [x] Frontier sizes come from DOBFS's `Starting TDStep` line, checked by exact text at build time like the verifier text; the accelerated-chunk count comes from the hook's output.
- [x] The forged-frontier control (double-enqueues while printing the expected sizes) is rejected.
- [x] The certification record carries the contract ID, its content sha256 and the tree sha256.

## Comments

Claimed by Codex strict-library/certification agent, 2026-10-03.

## Answer

Completed 2026-10-03 ET. Candidate receipt `certification.123997581679463790ac7e9b00f3ed2b` certifies the final exact patched tree on all ten matrix cells and rejects all eight controls at both tile sizes (16 cells). The forged-print control double-enqueues while printing the oracle counts; evaluator-owned inspection of the actual queue rejects it independently of the visible print. Snapshot manifest, protected verifier/harness, canonical header bytes, and final restored tree identity are checked. Contract content pin: `867fac18c28938268242e7d4b60049f3c3e97113512a761cc8a763735a77db51`. Tree pin: `991de65287fe1fae3a20412704cccb6140a93f84cc11200032b20214f5174ff1`.

Evidence scope: strict functional certification on the Mac, basis `simulated`; no target timing or hardware-coherence proof. L3/L5 and ready-bit semantics remain assumptions owned by Eric pending target evidence. Focused verification: `python -m pytest -q tests/test_typed_certification.py` — 94 passed. Raw build/run/control outputs remain under `/private/tmp/swdb-typed-library-certification-20261003/` and are named by the certification records.
