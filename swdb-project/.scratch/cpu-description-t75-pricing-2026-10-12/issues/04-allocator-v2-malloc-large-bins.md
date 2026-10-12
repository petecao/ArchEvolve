# 04 — Allocator v2: malloc and exact large bins

Created: 2026-10-12 01:10 ET
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** None — can start immediately (01 confirms scope before ticket 07 measures)
**Spec:** `../spec.md` (C5, C6; seams 1 and 2)
**Code map:** `../notes/allocator.md`

**Time estimate:** about half a day to a day.

## What to build

- A new allocator recipe version (the C++ source hashes are pinned in
  `cpu_allocator_resource.NATIVE_SOURCE`; old receipts must keep validating).
- Add `malloc` to the calibrator ABI list, the binder allocator fields and the evaluator's own ABI table
  (`analytic_cpu_service.py:154`). `free` is not executed in the ROI: add only if ticket 01 finds it.
- Allow exact bins above the 1 MiB cap for exactly the measured sizes: `_Znam`/`_ZdaPv` at
  16 777 216 and 16 777 220 bytes, and `malloc` at 64, 128, 6 144 and 2 097 152 bytes. The cap sits
  in the calibrator, its validator, `cpu_allocator_resource` and the binder's gross path (five places).
  Keep "no interpolation": an unmatched size stays unknown.
- Per-operation cell selection, so a run can measure only the new (operation, size) cells and not
  duplicate existing `_Znwm`/`_ZdlPv` bins (the binder refuses duplicates).

## Acceptance

- [ ] Seam 2: the runner writes a v2 receipt with only the requested cells; it validates and the binder admits it next to the v1 allocator receipt.
- [ ] Seam 1: a fixture with `malloc` and 16 MiB `new[]`/`delete[]` gets priced seconds from those cells; a size with no exact bin stays `call_shape.cost` unknown.
- [ ] Old allocator records and tests pass unchanged.
