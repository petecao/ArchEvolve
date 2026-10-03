# 13 — Range loop with continuation and register operands

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 12
**Spec:** `../spec.md`

**What to build:** The range loop with continuation is lowered and certified, with stream bounds, strides and the continuation pair passed through registers; row bounds stay tile operands.

## Acceptance

- [x] The range loop has an intrinsic record, library entry, lowering, differential-test driver and strict operation.
- [x] The differential test covers rows longer than one tile, so continuation crosses tiles.
- [x] Negative controls dropped continuation and 32-bit index wrap are rejected.

## Comments

Claimed by Codex strict-library/certification agent, 2026-10-03.

## Answer

Completed 2026-10-03 ET. The range lowering uses register operands for continuation/stride and tile operands for row bounds. The strict device keeps program-order state and covering waits publish continuation results. The reference driver includes empty rows and a row longer than the build tile, requiring multiple range tiles. Receipt `certification.d2f2df28e392444ebcff99ebca5b7bee` passes both tile sizes and rejects dropped continuation, byte-offset wrap, and an omitted covering wait (six control cells).

Evidence scope: strict functional certification on the Mac, basis `simulated`; no target timing or hardware-coherence proof. L3/L5 and ready-bit semantics remain assumptions owned by Eric pending target evidence. Focused verification: `python -m pytest -q tests/test_typed_certification.py` — 94 passed. Raw build/run/control outputs remain under `/private/tmp/swdb-typed-library-certification-20261003/` and are named by the certification records.

Review correction, 2026-10-03 ET: the differential producer now compiles the declared pinned lowering, driver, reference semantics and build definitions, checks supported input sets and rechecks source identity. All ten lowerings have fresh passing receipts for driver SHA256 `5a30fd75e7a23db709eb7e112d9202f46037cadc8b8c9d667ac472fd77f5e976`; see [promotion packet](../drafts/promotion-review.md). Focused strict/producer suite: 109 passed. Prior receipts remain immutable historical evidence.

Dependency review correction, 2026-10-03 ET: receipts now bind the complete referenced normative entry closure before/after execution. Old unbound receipts remain history and grant no current dependency-bearing certification. All ten lowerings, the candidate and calibration have fresh passing bound receipts; see [promotion packet](../drafts/promotion-review.md). The 119 producer regressions plus exact public delivery reproduction pass (120 total); 35 library-state regressions and independent changed-reference/stale-contract custody rechecks also pass.
