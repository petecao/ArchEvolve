# 20 — Peter's §5 patch with fixes E1–E5, certified

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 13, 14, 18, 19, 17
**Spec:** `../spec.md`

**What to build:** Peter's §5 rewrite, with fixes E1–E5, certifies on the Mac as a patch against the scalar-only snapshot.

## Acceptance

- [x] The patch edits the BFS source and adds a byte-identical copy of the lowering header; runtime guards run once per BFS call; knobs use the spec defaults (threshold 64, chunk size equal to the build's tile size, dynamic schedule with granularity 1).
- [x] The patch calls the accelerated-chunk hook and the compare-and-swap probe, so the gem5 primary and diagnostic builds use exactly the certified tree.
- [x] `swdb certify` with the BFS contract, `--snapshot bfs-dx100-scalar-only-20260929-a1.source` and the patch certifies it on the whole matrix.
- [x] All eight rewrite negative controls are rejected.
- [x] The certification record holds the patched tree's sha256.

## Comments

Claimed by Codex strict-library/certification agent, 2026-10-03.

## Answer

Completed 2026-10-03 ET. Delivered `library/dx100/peter-section5.patch` against `bfs-dx100-scalar-only-20260929-a1.source`. It changes only BFS source and adds the byte-identical `swdb_dxc_lowering.hpp`, with E1–E5, once-per-call runtime guards/context setup, threshold 64, chunk equal to build tile capacity, dynamic schedule with granularity 1, and both instrumentation hooks. Hook counters reset before the guard so fallback calls cannot inherit a prior witness. The CPU performs CAS, the redundant parent store, and enqueue. Final receipt `certification.5b136b7f0e374e37bb11e33d30333c6a` passes the entire matrix and rejects all eight controls at both capacities. Certified tree: `586b6c3e4edc1f040cc2c50e74fd88f1906b551b28fc0d065b6912e5cb94976c`.

Evidence scope: strict functional certification on the Mac, basis `simulated`; no target timing or hardware-coherence proof. L3/L5 and ready-bit semantics remain assumptions owned by Eric pending target evidence. Focused verification: `python -m pytest -q tests/test_typed_certification.py` — 86 passed. Raw build/run/control outputs remain under `/private/tmp/swdb-typed-library-certification-20261003/` and are named by the certification records.
