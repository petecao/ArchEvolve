# 12 — Strict layer: byte-offset, truncation and memory-region assertions

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 11
**Spec:** `../spec.md`

**What to build:** The strict layer also catches 32-bit byte-offset overflow, silent tile truncation, and DX100 accesses outside the registered memory regions, from any thread.

## Acceptance

- [x] Each assertion rejects its own negative control.
- [x] Memory-region checks work in strict builds on every thread, because the strict layer defines the memory-region calls the vendored functional interface lacks.
- [x] The certifications from ticket 11 still pass.

## Comments

Claimed by Codex strict-library/certification agent, 2026-10-03.

## Answer

Completed 2026-10-03 ET. Byte-offset overflow, tile truncation, and memory-region membership checks run inside the strict interface for every thread. Executed negative controls reject overflow (`byte_offset_overflow`), over-capacity stream loading (`tile_truncation`), and unregistered accesses (`memory_region`). The gather and stream receipts pin these checks: `certification.68d181644cfb4ea38b10543fbea8ad7b`, `certification.a660bf4c01ea415396d29caa4a925088`. All original gather/setup differential cases still pass.

Evidence scope: strict functional certification on the Mac, basis `simulated`; no target timing or hardware-coherence proof. L3/L5 and ready-bit semantics remain assumptions owned by Eric pending target evidence. Focused verification: `python -m pytest -q tests/test_typed_certification.py` — 94 passed. Raw build/run/control outputs remain under `/private/tmp/swdb-typed-library-certification-20261003/` and are named by the certification records.

Review correction, 2026-10-03 ET: the differential producer now compiles the declared pinned lowering, driver, reference semantics and build definitions, checks supported input sets and rechecks source identity. All ten lowerings have fresh passing receipts for driver SHA256 `5a30fd75e7a23db709eb7e112d9202f46037cadc8b8c9d667ac472fd77f5e976`; see [promotion packet](../drafts/promotion-review.md). Focused strict/producer suite: 109 passed. Prior receipts remain immutable historical evidence.

Dependency review correction, 2026-10-03 ET: receipts now bind the complete referenced normative entry closure before/after execution. Old unbound receipts remain history and grant no current dependency-bearing certification. All ten lowerings, the candidate and calibration have fresh passing bound receipts; see [promotion packet](../drafts/promotion-review.md). The 119 producer regressions plus exact public delivery reproduction pass (120 total); 35 library-state regressions and independent changed-reference/stale-contract custody rechecks also pass.
