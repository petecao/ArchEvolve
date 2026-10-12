# Bulk: memcpy/memmove exact bins (C6)

Written 2026-10-12 01:02 ET at `e2611242`. Paths are relative to `swdb-project/`.

## What t75 needs

- **memmove:** `llvm.memmove.p0.p0.i64` in region `…/serial.12991577463451192595` (both sides) has one execution each at **140, 4388, 7300, 9044, 14496, 30164** bytes. These six are missing.
- **Already covered:** 65536 ×255 (TDStep region) is in `services.v1`.
- **memcpy:** `llvm.memcpy.p0.p0.i64` runs only 8-byte copies (×1, ×7), which `services.v1` covers through the `constant8_noalias_align8` cell.

**Good news:** all six sizes are ≤ 1 MiB and ≥ 8 B. The bulk path needs **no code change**, only a new measured batch.

## Pipeline (copy of the services.v1 bulk-total run)

Runbook: `.scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-bulk-total-runbook.md`. Preregistration: `11-bulk-total-preregistration.json`, batches `bulk.a1` (26 sizes) and `bulk.a2` (22 sizes). Elapsed receipt: `11-bulk-total-elapsed-mbit10-20261006-a1.json`. Both batches ran 01:50–02:11 UTC, about 21.5 min under a node0 lease.

Steps:
1. Count phase, then elapsed phase, per batch:
   ```
   python3 -m swdb.cpu_bulk_total_calibration --records "$RAW/records" --output "$RAW/bulk.a3.<phase>" \
     --machine mbit10 --lane mbit10-evaluation-node<N> --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin \
     --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --repetitions 7 --min-trial-s .05 --max-wall-s 900 \
     [--count-only] --size 140 --size 4388 --size 7300 --size 9044 --size 14496 --size 30164
   ```
   Set the env first: `OMP_NUM_THREADS=1 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores`, and `LD_LIBRARY_PATH=<LLVM lib dir>`. **Do not taskset the Python collector**; the timer pins one core itself.
2. Import: `python3 -m swdb import-cpu-service-calibration --receipt "$RAW/bulk.a3.elapsed/receipt.json" --id mbit10.cpu.<…>.service.bulk-total.a3`.
3. Derive: `python3 -m swdb.cpu_bulk_resource --source-calibration …service.bulk-total.a3 --id …resource.bulk-total.a3`.
4. Pass `--calibration …resource.bulk-total.a3` to the binder. **Keep** `--bulk-copy-calibration mbit10.cpu.lanl20261006.resource.bulk-total.a1`: every batch also measures the memcpy8 cell (op 0), and duplicate copy cells need an explicit choice (`cpu_service_binding.py:172-181`, "never pool").

## Code map

| File:line | What |
|---|---|
| `swdb/cpu_bulk_total_calibration.py:26-99` `calibrate` | 1–32 sizes, `8 ≤ n ≤ 1048576` (line 28). Op 0 is memcpy8 only; ops 1–3 are memmove `disjoint` / `forward4` / `backward4` at every size (line 73). `settings.group = 'bulk_total_v2'`. Live payload cap 3 MiB + 320. |
| `swdb/cpu_bulk_total_calibration.py:106-160` `validate` | Exact matrix (line 129); count proof per size. |
| `swdb/cpu_bulk_resource.py:107-123` `main` | Derives the gross resource (`gross_bulk_loop_resource_v1`). |
| `swdb/cpu_service_binding.py:152-208` `_bulk_binding` | Groups memmove cells by size across **all** calibrations (so a new batch merges in). A size needs all three `BULK_PROFILES`, else Failure (197). A duplicate size+profile is refused (169), so **do not re-measure an existing size**. The bin parameter `bulk_envelope_<size>` is the max of the three profile medians. Selectors are emitted for both `memmove` and `llvm.memmove.p0.p0.i64` (206–207). |
| `swdb/analytic_cpu_service.py:128-132` | `BULK_PROFILES`, `BULK_ABIS`, `BULK_ASSUMPTION`, `BULK_RESOURCE_ASSUMPTION` |
| `swdb/analytic_cpu_service.py:135-149` `_bulk_profile_parameters` | Checks the envelope equals the max of the source profiles. |
| `swdb/analytic_cpu_service.py:152-178` `_shape_parameters` | Bulk bins need `8 ≤ bytes ≤ 1048576` (line 173). |
| `swdb/analytic_cpu_service.py:181-201` `_shape_cost` | Exact size only; a missing size gives `call_shape.cost.llvm.memmove.p0.p0.i64.<n>`. |

## Mechanism coupling

The bulk selectors live in the **same** additive `native_service_costs` mechanism as clock and OpenMP (`services.v1` mechanism 2). Any missing item in that mechanism for a region (one OpenMP site, one bin) nulls the mechanism's seconds and its `covered_calls`. Every opaque call in that region then reappears as `call_cost.<name>` (`swdb/analytic_cpu_service.py:104-106`; `swdb/analytic.py:614-626`). Expect cascades until every piece in a region is priced.

## Tests (prior art)

- `tests/test_cpu_bulk_binding.py:34, :52, :61, :78`
- `tests/test_cpu_bulk_model.py:26` `test_full_exact_bulk_bins_clear_site_under_explicit_inferred_profile_scenario`, `:35`, `:48`
- `tests/test_cpu_bulk_calibration.py:14, :36, :58`
- `tests/test_cpu_bulk_resource.py:11, :34, :60`
