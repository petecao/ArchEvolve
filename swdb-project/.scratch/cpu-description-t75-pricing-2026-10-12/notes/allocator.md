# Allocator: malloc and the 16 MiB bins (C5, C6)

Written 2026-10-12 01:02 ET at `e2611242`. Paths are relative to `swdb-project/`.

## What t75 actually needs

Read from the counted characterizations' `call_shape_counts`. Both sides are identical; ticket-03 counts, 2026-10-12.

| ABI | Bin kind | Bins executed in ROI | In `services.v1`? |
|---|---|---|---|
| `_Znam` | `known_length_bins` | 65536 ×7, 524288 ×2, **16777216 ×2**, **16777220 ×1** | 65536 and 524288 yes; 16 MiB no |
| `_ZdaPv` | `allocation_lifetime_size_bins` | 65536 ×7, 524288 ×2, **16777216**, **16777220** | same |
| `malloc` | `known_length_bins` | **64 ×2, 128, 6144, 2097152** (5 sites, 1 each, region `serial.16002263078219278542`, `alloc_MAA`) | no ABI at all |
| `free` | — | not executed in the ROI | — |

**Surprise:** malloc needs a **2 MiB** bin (2097152), which is also above the 1 MiB cap. The spec names only the 16 MiB bins as large. Nothing frees the malloc'd blocks in the ROI, so only `malloc` needs a rate. Adding `free` is harmless, but no count needs it.

`services.v1` allocator bins (gross mechanism):
- `_Znam` / `_ZdaPv`: [8192, 65536, 227416, 262144, 524288, 16384, 466112, 524284, 1048568]
- `_Znwm` / `_ZdlPv`: [8, 16, 32, 64, 128, 16384, 466112, 524284, 1048568]

## Two allocator paths in the binder (do not mix)

`services.v1` prices `_Znam`/`_ZdaPv` only through the **gross resource** mechanism. That is the `cpu_allocator_resource_calibration` kind, recipe `gross_allocator_loop_resource_v1`, a separate resource-bound `native_service_costs` with `resource_recipe`.

`swdb/cpu_service_binding.py:321-322` refuses any ABI that appears both as a paired selection and as a gross selection. So the new malloc and 16 MiB cells **must** enter as gross allocator resource records too.

Pipeline (same as `services.v1`):
1. `python3 -m swdb cpu-service-calibrate --service-group allocator --size N … --output <new dir>` writes `receipt.json` (`settings.group = allocator_v1`).
2. `python3 -m swdb import-cpu-service-calibration --receipt …/receipt.json --id mbit10.cpu.<…>.service.allocator-<x>.a1` → record `cpu_service_calibration`.
3. `python3 -m swdb.cpu_allocator_resource --source-calibration <that id> --id mbit10.cpu.<…>.resource.allocator-<x>.a1` → record `cpu_allocator_resource_calibration`.
4. Pass the **resource** ID to the binder with `--calibration`.

Prior run: `.scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-allocator-extra-runbook.md`. It is the closest model: an extra size set added as a second receipt, with bins merged in the binder.

## Code: every place that caps or enumerates

| File:line | What | Change needed |
|---|---|---|
| `swdb/cpu_allocator_calibration.py:24-25` | `NAMES = (new_array, delete_array, new_scalar, delete_scalar)`, `ABI = (_Znam, _ZdaPv, _Znwm, _ZdlPv)` | add malloc (+ free) |
| `:27` | `SIZES` default (10 bins) | — |
| `:28` | `PAYLOAD_CAP = 64 MiB` live; `EVENT_CAP = 16777216`; `RAW_CAP = 25 MiB` | 16 MiB → `n = min(65536, PAYLOAD_CAP//size) = 4` per batch, which is fine |
| `:113-115` | `sizes ≤ 10, 0 < s ≤ 1048576` | raise the cap for 2 MiB and 16 MiB |
| `:178` | `cells = [(op,size) for op in range(4) for size in sizes if args.size or …]`: **with `--size`, all four ops at every size** | **Risk:** a malloc-size run (64, 128) would also re-measure `_Znwm`/`_ZdlPv` 64 and 128, so the binder refuses "ambiguous duplicate gross allocator ABI/size" (`cpu_service_binding.py:223`). Needs an explicit (op, size) cell selection, or separate runs per op. |
| `:217-259` `validate(raw)` | `sizes ≤ 1048576` (236); count matrix uses the 4 `NAMES` (252) | version it (for example `allocator_v2`). The old `service.allocator.a1` record must still validate, because `cpu_service_native.validate` dispatches on `settings.group` (`swdb/cpu_service_native.py:79-81`). |
| `swdb/native/CpuAllocatorWork.h` | `service_allocator(...)`: op 0..3 switch (new[]/delete[]/new/delete) | add `malloc`/`free` ops. The count proof checks one opaque call per event with exact `ABI[op]` (`cpu_allocator_calibration.py:55-108`, `count_proof`). Characterize already recognizes malloc as a heap allocation (`swdb/llvm/Characterize.cpp:461-465`, `heapAllocation`), so `known_length_bins` will appear. |
| `swdb/cpu_allocator_resource.py:24-26` | `NATIVE_SOURCE` pins the **three allocator source file hashes** ("Version1 admits only this already measured shared source; future recipes require a new version") | editing `CpuAllocator*.{h,cpp}` makes `_services` refuse (`:39-40`). Add a v2 pin set or a new recipe version; keep the v1 pins for the old records. |
| `swdb/cpu_allocator_resource.py:47` | `0 < size ≤ 1048576` | raise |
| `swdb/cpu_service_binding.py:18-19` | `ALLOCATOR_FIELDS` | add `malloc: known_length_bins` (and `free: allocation_lifetime_size_bins`) |
| `swdb/cpu_service_binding.py:218-220` | gross path: ABI in `ALLOCATOR_FIELDS`, `size ≤ 1048576`, regime `fresh_process_repeated_allocate_free_batches` | raise the cap |
| `swdb/analytic_cpu_service.py:154-155` | **duplicate** `allocator_fields` dict in `_shape_parameters` (evaluator) | add `malloc` (and `free`), else `selector.calls.allocator_abi_bin_kind` |
| `swdb/analytic_cpu_service.py:173` | evaluator caps only **bulk** bins at 1 MiB; allocator bins are uncapped | none |
| `swdb/analytic_cpu_service.py:181-201` `_shape_cost` | exact-size match only; missing size → `call_shape.cost.<abi>.<bytes>` | none (C6 "no interpolation" is already true) |

## Exact-bin semantics (evaluator)

`_shape_cost` needs the following, else the whole `native_service_costs` result for that region is unknown and its covered calls are dropped:
1. exactly one shape row per site (`call_shape.exact_site.*`);
2. `unknown_lengths == 0` / `unknown_free_lifetimes == 0`;
3. full site count;
4. every executed size has a bin.

## Measurement caveat (architecture)

glibc serves 16 MiB (and 2 MiB) requests with `mmap` in a fresh process, because they are above the default 128 KiB `M_MMAP_THRESHOLD`. But freeing an mmapped chunk raises the dynamic threshold, up to 32 MiB on 64-bit. So a repeated allocate/free batch, as the calibrator runs it, may measure the brk/top-chunk path after the first free, while the application allocates once (the mmap path).

The regime is already labelled `transfer_basis: inferred`. Record this as a known transfer gap. Do not change the regime silently. The `MALLOC_MMAP_THRESHOLD_` env is in the declared control scope, and setting it would break compatibility with the app counts.

## Tests (prior art)

- `tests/test_cpu_allocator_calibration.py:7, :43, :66`
- `tests/test_cpu_allocator_resource.py:29, :47, :101, :111` (`…refuses_unrecognized_shared_work_source`, which is the NATIVE_SOURCE pin), `:130`
- `tests/test_analytic_cpu_service.py:46` `test_exact_size_service_bins_require_full_site_coverage`, `:55`, `:64`
