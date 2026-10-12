# 02 — 1- and 2-byte store cells (memory_v2)

Created: 2026-10-12 01:10 ET
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** None — can start immediately
**Spec:** `../spec.md` (C10; seams 1 and 2)
**Code map:** `../notes/memory.md`

**Time estimate:** about half a day.

## What to build

A new memory calibration group `memory_v2` (old `memory_v1` records must keep validating) that
measures **write width 1 and write width 2** only, with the same calibrator procedure and footprint
(8 388 608 bytes) as the existing cells. Needs a 16-bit native store function. Lift the
"1-byte means read-only at 256 B" rule for v2 in the calibrator, its validator, the binder and the
evaluator (2-byte writes already pass the evaluator; 1-byte writes do not). The binder must accept
v1 cells plus v2 cells together and still refuse duplicate (operation, width) cells.

## Acceptance

- [ ] Seam 2: the calibrator runner (driven by a test double for the native timing) writes a `memory_v2` receipt that validates and that the binder admits next to the v1 receipt.
- [ ] Seam 1: bind + estimate a fixture with 1- and 2-byte stores: `memory_scenario.cell.write.1`/`write.2` unknowns are gone and those stores contribute priced seconds.
- [ ] Existing memory tests and `services.v1`-shaped fixtures pass unchanged.
- [ ] No real mbit10 run here (that is ticket 07).
