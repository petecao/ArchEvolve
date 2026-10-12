# 02 — 1- and 2-byte store cells (memory_v2)

Created: 2026-10-12 01:10 ET
**Type:** slice
**Status:** resolved
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

- [x] Seam 2: the calibrator runner (driven by a test double for the native timing) writes a `memory_v2` receipt that validates and that the binder admits next to the v1 receipt.
- [x] Seam 1: bind + estimate a fixture with 1- and 2-byte stores: `memory_scenario.cell.write.1`/`write.2` unknowns are gone and those stores contribute priced seconds.
- [x] Existing memory tests and `services.v1`-shaped fixtures pass unchanged.
- [x] No real mbit10 run here (that is ticket 07).

## Answer

Resolved 2026-10-12 01:23 ET on branch `cpud/02-memory-v2` (base `cpud/integration` at `11f7327a`).

**Built** (paths under `swdb-project/swdb/`)

- New calibration group `memory_v2`: writes only, widths {1, 2}, default footprint 8 388 608 B,
  regime `resident_serial_constructed_requests`. Select it with `--group memory_v2`; the
  default stays `memory_v1`.
- `cpu_memory_calibration.py`: a `GROUPS` table (operations, widths, ROI function, retained
  primitives per group). `regime(op, width)` is small only for 1-byte reads. `optimized_proof`
  and `validate` read the group's table. `--element-bytes` accepts 2.
- `native/CpuMemoryWork.h`: `service_store8` / `service_store16` (volatile stores with a
  `size_t` ring cursor). The timer and count driver accept width 2 and 1-byte writes.
- `cpu_service_native.validate` dispatches `memory_v2`. `cpu_memory_resource` accepts it, so
  ticket 07 can build the gross resource record.
- Binder (`cpu_service_binding._memory_binding`) and evaluator
  (`analytic_cpu_service._memory_construction`): width 2 is allowed. "Small" now means
  `width == 1 and op == read` (the 256 B ring). Every other cell is resident.

**Decisions (assumptions stated)**

- **Writes only; no 1- or 2-byte reads.** The ticket scopes v2 to writes. Also, the v1 read ring
  stores the next index in a `T`, so a 1- or 2-byte ring cannot span 8 MiB (at most 256 or
  65 536 elements). Spec C10's "reads and writes" would need a new ring design. t75 needs only
  the two stores.
- **New native functions; the v1 body is untouched.** `memory_body` indexes with `T`. A
  `uint8_t` or `uint16_t` write cursor would wrap at 256 or 65 536 elements and silently shrink
  the footprint. The new `store_body` uses a `size_t` cursor. `service_memory8/32/64` are
  unchanged; only the dispatcher gained two branches.
  - Consequence: the native source hashes change for future v1 runs.
  - The stored v1 records still validate. Checked: `service.memory.a1` and
    `service.byte-read.a1` pass `cpu_service_native.validate`.
- **No cell overlaps v1.** `memory_v2` cannot measure (read, 1) or any 4- or 8-byte cell. So
  v1 plus v2 never trips the binder's duplicate refusal. Binding the same v2 cells twice is
  still refused.
- **The volatile check is unchanged.** The constructed stores are volatile, and so are t75's
  2-byte stores. `_primitive_supported` does not test `volatile` for `ordinary_write`.
- **Ticket 07 command:** add `--group memory_v2 --operation write --element-bytes 1
  --element-bytes 2 --footprint-bytes 8388608`. The pipeline line in `notes/memory.md` lacks
  `--group`.

**Tests** (seams 1 and 2; targeted files only, no xdist)

- `tests/test_cpu_memory_calibration.py`:
  - `test_narrow_store_cells_form_a_separate_memory_v2_group_at_the_resident_footprint`:
    portable runner. v1 refuses narrow writes; v2 refuses other operations and widths.
  - `test_narrow_stores_are_counted_as_exact_one_and_two_byte_writes`: LLVM 22 count proof and
    O3 proof (`store volatile i8`/`i16`, exact write-1 and write-2 coefficients).
  - `test_native_memory_v2_receipt_admits_narrow_writes_and_keeps_its_own_matrix`: native
    import validates. A v1 tag, the small regime, a read proof or width 4 is refused.
- `tests/test_cpu_memory_service_binding.py`:
  - `test_narrow_store_cells_bind_beside_v1_and_price_one_and_two_byte_stores`: bind v1 + v2,
    then estimate. No `memory_scenario.cell.write.1` or `.2`; memory seconds
    3×0.1 + 4×0.3 + 2×0.5 = 2.5.
  - `test_narrow_store_receipt_bound_twice_is_an_ambiguous_duplicate`.
- Existing memory tests pass unchanged.
- One failure outside this ticket:
  `test_cpu_service_binding.py::test_extensa_tagged_native_service_record_never_enters_team_binding`.
  It fails in the ADR 0013 team-safe guard, before any memory code runs. The guard's message
  no longer contains "Extensa research evidence". Ticket 01 touches that guard.
