# 13 — Range loop with continuation and register operands

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 12
**Spec:** `../spec.md`

**What to build:** The range loop with continuation is lowered and certified, with stream bounds, strides and the continuation pair passed through registers; row bounds stay tile operands.

## Acceptance

- [ ] The range loop has an intrinsic record, library entry, lowering, differential-test driver and strict operation.
- [ ] The differential test covers rows longer than one tile, so continuation crosses tiles.
- [ ] Negative controls dropped continuation and 32-bit index wrap are rejected.

## Comments
