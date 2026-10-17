# Memory: 1- and 2-byte store cells (C10)

Written 2026-10-12 01:02 ET at `e2611242`. Paths are relative to `swdb-project/`.

## What t75 needs (both sides, `alloc_MAA` in `MAA_functional.hpp`)

| Region | `memory_service_counts.requests_by_update_kind` |
|---|---|
| `alloc_MAA.39.0` | read 8B ×768, **write 1B ×256**, write 8B ×512 |
| `alloc_MAA.33.1` | read 8B ×64, **write 2B ×64** |

Access primitives:
- `access.113`: line 40, 8-bit store, `volatile: false`, stride 24, 256 elements.
- `access.107` / `access.109`: lines 34–35, 16-bit store, **`volatile: true`**, 32 elements each.

These are tiny counts; they matter only for non-null seconds.

`services.v1` request cells (mechanism `memory_service_scenario`):
- add-update 4/8
- CAS 4/8
- float add 8
- **read 1 @ 256 B** (`fixed_small_byte_read_constructed_requests`, paired, `service.byte-read.a1`)
- read 4/8 and write 4/8 @ 8 MiB (`resident_serial_constructed_requests`, gross `resource.memory.a1`)

## The 1-byte "small" rule is hard-coded in four places

| File:line | Rule |
|---|---|
| `swdb/cpu_memory_calibration.py:92-93` (`calibrate`) | width 1 only with `operations == ['read']` and footprint ≤ 256 |
| `swdb/cpu_memory_calibration.py:155` | regime = `fixed_small_byte_read_constructed_requests` if width == 1 |
| `swdb/cpu_memory_calibration.py:173-185` `optimized_proof` | widths `(1,8),(4,32),(8,64)`; width 1 retains only `volatile_read` |
| `swdb/cpu_memory_calibration.py:206, 209, 211, 219` (`validate`) | `retained_primitives == {'1':['volatile_read'],'4':PRIMITIVES,'8':PRIMITIVES}`; widths ⊂ (1,4,8); width-1 read-only ≤ 256; regime by width |
| `swdb/cpu_memory_calibration.py:249` (CLI) | `--element-bytes choices=(1,4,8)` |
| `swdb/native/CpuMemoryWork.h:27-40` | only `service_memory8/32/64`; **no 16-bit function**; dispatch by `sizeof(T)` |
| `swdb/cpu_service_binding.py:102` (`_memory_binding`) | `width not in (1,4,8)` gives Failure |
| `swdb/cpu_service_binding.py:107-111` | `small = width == 1` forces the small regime and `op == read`, `size == 256`. Non-small cells must equal `--memory-footprint-bytes`, else they are silently skipped (111). |
| `swdb/analytic_cpu_service.py:204-228` `_memory_construction` (evaluator) | `small = width == 1`; the regime must match; `(small and (kind != 'read' or size != 256))` gives `memory_scenario.supported_construction` (lines 213–216) |

Width **2** writes pass the evaluator already: non-small, resident regime. Only the calibrator, the native source and the binder block them. Width **1** writes need the evaluator change too.

Redefine "small" as `(width == 1 and op == 'read' and footprint == 256)` everywhere, and let other width-1/2 cells use `resident_serial_constructed_requests` at 8 MiB.

## Versioning: keep old records valid

`validate` is reached for stored records through `cpu_service_native.validate`, which dispatches on `settings.group` (`swdb/cpu_service_native.py:76-78`, `group == 'memory_v1'`). The existing `service.memory.a1` / `service.byte-read.a1` records are checked against the current width table and `optimized_proof` expectations. Changing them in place breaks `swdb validate` on `services.v1`'s closure.

Add a `memory_v2` group (widths {1,2,4,8}, its own retained-primitive table) and leave the `memory_v1` checks as they are.

## Binder duplicate trap

`_memory_binding` refuses a duplicate `(op, width)` (line 113, "ambiguous duplicate constructed memory cell"). The new receipt must therefore **not** re-measure cells `services.v1` already selects:
- read 4/8 and write 4/8 @ 8 MiB;
- read 1 at 256 (the key `(read,1)` collides even at another footprint).

Measure only what is missing:
- write 1 and write 2 at 8 MiB;
- optionally read 2 (spec C10 says "reads and writes").

Either drop read 1 @ 8 MiB, or decide explicitly which read-1 cell replaces the 256 B one.

## Pipeline (services.v1 memory run)

- `python3 -m swdb.cpu_memory_calibration --records … --output … --operation write --element-bytes 1 --element-bytes 2 --footprint-bytes 8388608 --machine mbit10 --lane mbit10-evaluation-node<N> --llvm-bin … --toolchain-flag=… --repetitions 7 --min-trial-s .05 --max-wall-s 900`. Run `--count-only` first. CLI at `cpu_memory_calibration.py:245-259`.
- Import: `python3 -m swdb import-cpu-service-calibration --receipt … --id …service.memory-narrow.a1`.
- Gross resource: `python3 -m swdb.cpu_memory_resource --source-calibration … --id …resource.memory-narrow.a1`. Recipe `gross_constructed_resource_v1` (`swdb/cpu_memory_resource.py:21-24`); `_services` accepts groups `memory_v1`/`memory_float_v1` only (line 28), so **add `memory_v2`**.
- Evidence of the prior runs: `.scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-memory-service-mbit10-20261006-a1.json` (memory, about 8.5 min, 00:17–00:25 UTC), `11-byte-read-service-mbit10-20261006-a1.json` (about 4 min), `11-memory-total-resource-mbit10-20261006-a1.json`.

## Evaluator primitive check (volatile)

`swdb/analytic_cpu_service.py:231-243` `_primitive_supported`. `ordinary_write` needs:
- `opcode == store`, `not_atomic`, `read_write is False`;
- `element_bits == 8*width`, non-vector, `ir_lanes == 1`.

It does **not** test `volatile`, so the volatile 16-bit stores (107, 109) are accepted. The constructed cells are volatile too (`CpuMemoryWork.h:6`, `volatile T *data`), so the transfer is consistent. Keep the primitive label `ordinary_write`; if a stricter volatile check is ever added, both sides must agree.

## Footprint

- `--memory-footprint-bytes` must be a power of two in 64 B..8 MiB (`cpu_service_binding.py:94-96`). `services.v1` used 8388608; keep it (C10).
- The evaluator's `_memory_construction` has the same bound (line 214).
- Coverage: `_source_memory_proof` (lines 245–264) needs exactly one supported profile per access with a nonzero count. A missing (kind, width) cell gives `memory_scenario.cell.write.<w>` (line 312) and `memory_scenario.primitive.access.<id>` (line 260). Those are the five ticket-03 items.

## Tests (prior art)

- `tests/test_cpu_memory_calibration.py:14, :36` (`test_all_memory_request_primitives_bind_exact_service_and_driver_counts`), `:113, :141, :154` (`test_byte_read_uses_independently_counted_verified_small_cycle_not_widened_access`)
- `tests/test_cpu_memory_service_binding.py:49, :75, :83`
- `tests/test_cpu_memory_service.py`, `tests/test_cpu_memory_resource.py`, `tests/test_analytic_memory_models.py`
