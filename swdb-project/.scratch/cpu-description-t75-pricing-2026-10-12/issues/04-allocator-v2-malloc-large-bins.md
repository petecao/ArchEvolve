# 04 — Allocator v2: malloc and exact large bins

Created: 2026-10-12 01:10 ET
**Type:** slice
**Status:** resolved
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

- [x] Seam 2: the runner writes a v2 receipt with only the requested cells; it validates and the binder admits it next to the v1 allocator receipt.
- [x] Seam 1: a fixture with `malloc` and 16 MiB `new[]`/`delete[]` gets priced seconds from those cells; a size with no exact bin stays `call_shape.cost` unknown.
- [x] Old allocator records and tests pass unchanged.

## Answer

Resolved 2026-10-12 01:25 ET on branch `cpud/04-allocator-v2` (base `cpud/integration` `11f7327a`).

**Result:** the allocator runner now writes `allocator_v2` receipts. They cover `malloc`/`free`, allow exact bins up to 32 MiB and measure only the requested cells. The binder merges them with the v1 gross records into one mechanism. Unmatched sizes stay `call_shape.cost.<abi>.<bytes>`.

### What changed (paths relative to `swdb-project/`)

| Where | Change |
|---|---|
| `swdb/native/CpuAllocator{Work.h,Timer.cpp,Count.cpp}` | Ops 4 = `malloc` and 5 = `free` (even op allocates, odd op releases). The size cap is now 32 MiB. |
| `swdb/cpu_allocator_calibration.py` | `GROUPS`: v1 has 4 ops and a 1 MiB cap; v2 has 6 ops and a 32 MiB cap. New `--cell OPERATION:BYTES`, repeatable, cannot be combined with `--size`. The count proof and the IR-retention check cover only the requested operations. `validate` uses each receipt's own group rules. |
| `swdb/cpu_service_native.py` | Sends `allocator_v2` to the allocator validator. |
| `swdb/cpu_service_calibration.py` | Adds the `--cell` flag. The clock group refuses it. |
| `swdb/cpu_allocator_resource.py` | `NATIVE_SOURCE_V2` pins the new source hashes, chosen by group. The v1 pins are unchanged. |
| `swdb/analytic_cpu_service.py` | `ALLOCATOR_FIELDS`, the single table, gains `malloc` (`known_length_bins`) and `free` (`allocation_lifetime_size_bins`). |
| `swdb/cpu_service_binding.py` | Imports that table instead of keeping a copy. The gross size guard is now 32 MiB. |

### Decisions and assumptions

1. **Recipe version.** The versioned thing is the receipt group (`allocator_v2`) and its source pins. The resource formula stays `gross_allocator_loop_resource_v1`, because its arithmetic did not change.
   - A new recipe ID would have to touch the schema `const`, the estimator check and the one-recipe-per-mechanism selector.
   - It would also block v1 and v2 cells from sharing one mechanism, and the binder requires one gross family per ABI.
2. **Size cap: 32 MiB, exact only.** That is glibc's 64-bit maximum dynamic mmap threshold. No interpolation was added: the evaluator already prices only exact matches.
3. **`free` is supported** in the native source, because the `malloc` cell needs it for untimed cleanup, and in the ABI tables. No ticket-07 cell requests it, because nothing frees in the t75 ROI (`../notes/allocator.md`).
4. **v1 behavior is kept.** Without `--cell`, the runner picks the same cells as before (`--size` gives the four C++ ops; no flag gives the default split). Committed `service.allocator{,-extra}.a1` and `resource.allocator{,-extra}.a1` revalidate with no problems (checked by calling each record's own validator on the Mac, not a whole-store check).
5. **Count proof.** It covers the requested operations × {smallest, largest size} × invoke/driver × N ∈ {3, 5}. For ticket 07 that is 3 ops × {64, 16 777 220} × 2 × 2 = 24 points. A 16 MiB batch holds `PAYLOAD_CAP // size` = 4 events (3 at 16 777 220).
6. **Measurement caveat (unchanged regime).** After the first `free`/`delete[]` of an mmapped chunk, glibc raises its mmap threshold. Repeated 2 MiB and 16 MiB batches may then time the heap (`brk`) path, while the app allocates once through `mmap`. `transfer_basis` stays `inferred`. Do not set `MALLOC_MMAP_THRESHOLD_`: the allocator control scope must match the app counts.

### Tests (targeted, Mac, no xdist, basetemp under `$TMPDIR`)

- `tests/test_cpu_service_binding.py` — new seam-1 tests:
  - `test_malloc_and_16_mib_array_bins_bind_beside_v1_cells_and_price_exact_sizes`: v1 + v2 bind, resource seconds 1.1, sites 29–31 covered.
  - `test_an_allocator_size_without_an_exact_bin_stays_unknown`: `call_shape.cost.malloc.128`.
- `tests/test_cpu_allocator_calibration.py` — new seam-2 tests:
  - the runner measures only the requested cells and binds beside v1;
  - the LLVM 22 count-only proof covers exactly `_ZdaPv` and `malloc`;
  - `--cell` refuses a bad operation, more than 32 MiB, a repeat, and mixing with `--size`.
- `tests/test_cpu_allocator_resource.py` — guard test: `NATIVE_SOURCE_V2` equals the current native source hashes.
- Runs: `test_cpu_allocator_calibration.py` passed 6 of 6, including LLVM 22. `test_cpu_allocator_resource.py`, `test_analytic_cpu_service.py` and `test_cpu_service_binding.py`: 26 passed, 1 failed.
- **That failure is not caused by this ticket:** `test_extensa_tagged_native_service_record_never_enters_team_binding` expects the stderr text "Extensa research evidence". `swdb/archevolve.py:125` now says "Extensa campaign … never enter team results". The refusal still happens; only the wording differs, and no code touched here is involved.

### Ticket-07 command (mbit10, from a clean pushed checkout's `swdb-project/`)

Before you run: take a free lane lease. Set `RAW` to a new folder under `/data/yanruj/EvolveSWDB_runs/` that holds a copied `records/` store. Run the count-only step first, then the timed step.

```sh
export OMP_NUM_THREADS=1 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores
export LD_LIBRARY_PATH=/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu
CELLS="--cell malloc:64 --cell malloc:128 --cell malloc:6144 --cell malloc:2097152 --cell new_array:16777216 --cell new_array:16777220 --cell delete_array:16777216 --cell delete_array:16777220"
COMMON="--records $RAW/records --service-group allocator $CELLS --machine mbit10 --lane mbit10-evaluation-node<N> --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --count-build-cap-mib 64 --max-wall-s 900 --format json"
python3 -m swdb cpu-service-calibrate $COMMON --output "$RAW/count" --count-only
python3 -m swdb cpu-service-calibrate $COMMON --output "$RAW/elapsed" --repetitions 7 --min-trial-s .05
python3 -m swdb import-cpu-service-calibration --records "$RAW/records" --receipt "$RAW/elapsed/receipt.json" --id mbit10.cpu.lanl20261006.service.allocator-v2.a1 --format json
python3 -m swdb.cpu_allocator_resource --records "$RAW/records" --source-calibration mbit10.cpu.lanl20261006.service.allocator-v2.a1 --id mbit10.cpu.lanl20261006.resource.allocator-v2.a1 --format json
```

Ticket 08 then adds `--calibration mbit10.cpu.lanl20261006.resource.allocator-v2.a1` beside the two v1 allocator resources. No requested cell duplicates a `services.v1` bin, so the binder's duplicate check passes.
