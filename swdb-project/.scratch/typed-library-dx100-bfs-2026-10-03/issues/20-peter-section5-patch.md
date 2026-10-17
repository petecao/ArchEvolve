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

Completed 2026-10-03 ET. Delivered `library/dx100/peter-section5.patch` against `bfs-dx100-scalar-only-20260929-a1.source`. It changes only BFS source and adds the byte-identical `swdb_dxc_lowering.hpp`, with E1–E5, once-per-call runtime guards/context setup, threshold 64, chunk equal to build tile capacity, dynamic schedule with granularity 1, and both instrumentation hooks. The fresh CPU parent read, degree lookup, and CAS probe are gated by `SWDB_DXC_DIAGNOSTIC`; diagnostic builds probe every hint, including nonnegative hints. Preprocessing and runtime regressions verify the primary/diagnostic boundary and unchanged CPU claim/enqueue behavior. Hook counters reset before the guard so fallback calls cannot inherit a prior witness. The CPU performs CAS, the redundant parent store, and enqueue. Final receipt `certification.1e4397e31d594245bc10bd80ff2107f5` passes the entire matrix and rejects all eight controls at both capacities. Certified tree: `991de65287fe1fae3a20412704cccb6140a93f84cc11200032b20214f5174ff1`.

Evidence scope: strict functional certification on the Mac, basis `simulated`; no target timing or hardware-coherence proof. L3/L5 and ready-bit semantics remain assumptions owned by Eric pending target evidence. Focused verification: `python -m pytest -q tests/test_typed_certification.py` — 109 passed. Raw build/run/control outputs remain under `/private/tmp/swdb-typed-library-certification-20261003/` and are named by the certification records.

Review correction, 2026-10-03 ET: the differential producer now compiles the declared pinned lowering, driver, reference semantics and build definitions, checks supported input sets and rechecks source identity. All ten lowerings have fresh passing receipts for driver SHA256 `5a30fd75e7a23db709eb7e112d9202f46037cadc8b8c9d667ac472fd77f5e976`; see [promotion packet](../drafts/promotion-review.md). Focused strict/producer suite: 109 passed. Prior receipts remain immutable historical evidence.

Dependency review correction, 2026-10-03 ET: receipts now bind the complete referenced normative entry closure before/after execution. Old unbound receipts remain history and grant no current dependency-bearing certification. All ten lowerings, the candidate and calibration have fresh passing bound receipts; see [promotion packet](../drafts/promotion-review.md). The 119 producer regressions plus exact public delivery reproduction pass (120 total); 35 library-state regressions and independent changed-reference/stale-contract custody rechecks also pass.
