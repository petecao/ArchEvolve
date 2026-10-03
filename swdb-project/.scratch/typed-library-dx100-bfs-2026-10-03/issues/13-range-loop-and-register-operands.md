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

Evidence scope: strict functional certification on the Mac, basis `simulated`; no target timing or hardware-coherence proof. L3/L5 and ready-bit semantics remain assumptions owned by Eric pending target evidence. Focused verification: `python -m pytest -q tests/test_typed_certification.py` — 86 passed. Raw build/run/control outputs remain under `/private/tmp/swdb-typed-library-certification-20261003/` and are named by the certification records.
