# 05 — OpenMP profile set a2 with __kmpc_for_static_init_8u

Created: 2026-10-12 01:10 ET
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md` (C7 (profiles); seam 1)
**Code map:** `../notes/openmp.md`

**Time estimate:** about half a day.

## What to build

A versioned OpenMP profile set (`a2`) that adds `__kmpc_for_static_init_8u` with its own ABI class.
"22 profiles" is hard-coded (`cpu_openmp_calibration` ×5, `cpu_openmp_binding:48`) and `validate`
requires `proof['profiles'] == PROFILES`, so the old set must stay as-is for `service.openmp.a1`
and the `services.v1` closure. The calibrator can measure the a2 set (or only the new class); the
binder accepts an a2 receipt.

## Acceptance

- [ ] Seam 1: a fixture calling `__kmpc_for_static_init_8u` gets priced seconds; without the a2 receipt it stays `call_cost.__kmpc_for_static_init_8u` unknown.
- [ ] `service.openmp.a1` and `services.v1`-shaped fixtures still validate.
- [ ] Seam 2: the runner (test double timing) writes an a2 receipt that validates and binds.

## Answer

Resolved 2026-10-12 01:40 ET on branch `cpud/05-openmp-a2`.

**Result:** OpenMP profile set `a2` = the frozen 22 `a1` classes plus class 22,
`__kmpc_for_static_init_8u` (`ident_flags 514`, argc 9, schedtype 34, incr 1, chunk 1,
`serialized_team`). `a1` stays byte-for-byte the first 22 classes, so
`service.openmp.a1` and `services.v1` are untouched.

**What changed (paths under `swdb-project/`):**

- `swdb/cpu_openmp_profiles.py`: `PROFILE_SETS = {'a1': 22, 'a2': 23}`, receipt groups
  `openmp_v1` / `openmp_v2`.
- `swdb/cpu_openmp_calibration.py`: collection now writes `openmp_v2` receipts. The count
  proof always covers all 23 classes; `--profile N` (repeatable) times only the named classes
  (`settings.measured_profiles`). `validate` accepts both groups; `a1` must still time all 22.
- `swdb/native/CpuOpenmpWork.h`, `CpuOpenmpCount.cpp`, `CpuOpenmpTimer.cpp`: event 22 with
  `swdb_loc514`, retired by `__kmpc_for_static_fini` outside the window (same as `_8`).
- `swdb/cpu_openmp_binding.py`: accepts cells 0–21 (a1) or 0–22 (a2). Cells may come from
  several receipts (a1 from `service.openmp.a1`, class 22 from the new receipt); a duplicate
  index is refused. An a2 bind writes `selector.openmp_profile_set: a2`.
- `swdb/analytic_cpu_openmp.py`: classifies sites with the selector's set (absent = `a1`).
  An unknown set value gives `openmp.profile_set` unknown.

**Acceptance:**

- [x] Seam 1: `tests/test_cpu_openmp_binding.py::test_wide_unsigned_static_init_is_priced_once_the_a2_receipt_is_bound`
  (10 calls × 2e-8 s = 2e-7 s, hand-computed) and `..._without_the_a2_receipt_stays_unknown`
  (`call_cost.__kmpc_for_static_init_8u`, `openmp.unsupported_abi_class`).
- [x] `a1` still validates: the real `records/cpu_service_calibrations/mbit10.cpu.lanl20261006.service.openmp.a1.yaml`
  passes the record validator; all 106 OpenMP site classes in `services.v1` re-derive
  unchanged under both sets; existing `services.v1`-shaped fixture tests pass.
- [x] Seam 2: `tests/test_cpu_openmp_calibration.py::test_runner_with_a_timing_double_writes_an_a2_receipt_for_the_new_class_that_imports_and_binds`
  (command runner and count proof doubled; receipt imports, binds with the a1 fixture, estimates).

**Tests:** targeted files `test_cpu_openmp_binding.py`, `test_analytic_cpu_openmp.py`,
`test_cpu_openmp_calibration.py`, `test_estimator_generality_guard.py`: 26 passed, 2 failed.
The 2 failures are the native-LLVM tests (`test_count_only_matrix...`,
`test_portable_probe...`). They hit the 180 s wall budget on the Mac, and they fail the same way
at the base commit `11f7327a`. They need mbit10 (ticket 07). Mac sanity check only:
the new header compiles with LLVM 22, the optimized IR keeps one `_8u` call, and event 22 runs
legally in a T1 team.

**Assumptions:**

1. The `_8u` constants mirror `_8` (schedtype 34, incr 1, chunk 1, ident flags 514). This is
   unverified for t75. If ticket 01's t75 projections show other literals, those sites stay
   `openmp.unsupported_abi_class`. Check `calls[*]` against `PROFILE_SETS['a2']` before ticket 07.
2. Ticket 07 times only class 22. `services.v2` binds `service.openmp.a1` (0–21) plus the new
   receipt (22). The two receipts must share libomp and control scope; per-cell compatibility
   still applies.
3. This commit cannot re-collect an `a1` receipt (the header now has 23 markers). Old `a1`
   records still validate.
4. The estimator bundle hash changes (any `swdb/*.py` edit), as for every ticket in this effort.

**Ticket-07 command (mbit10, socket lease, clean pushed checkout, from `swdb-project/`):**

```sh
export OMP_NUM_THREADS=1 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores
export LD_LIBRARY_PATH=/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu
# LANL_OMP_A2_RAW: new folder under /data/yanruj/EvolveSWDB_runs/ holding a copied records/ store
python3 -m swdb.cpu_openmp_calibration --records "$LANL_OMP_A2_RAW/records" --output "$LANL_OMP_A2_RAW/count" --count-only --machine mbit10 --lane mbit10-evaluation-node0 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --max-wall-s 900
python3 -m swdb.cpu_openmp_calibration --records "$LANL_OMP_A2_RAW/records" --output "$LANL_OMP_A2_RAW/elapsed" --profile 22 --machine mbit10 --lane mbit10-evaluation-node0 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --repetitions 7 --min-trial-s .05 --max-wall-s 900
python3 -m swdb.cpu_openmp_calibration --validate-receipt "$LANL_OMP_A2_RAW/elapsed/receipt.json"
python3 -m swdb import-cpu-service-calibration --records "$LANL_OMP_A2_RAW/records" --receipt "$LANL_OMP_A2_RAW/elapsed/receipt.json" --id mbit10.cpu.lanl20261006.service.openmp.a2 --format json
```

The count-only proof must show 23 classes, 4 points and 23 projected sites. Ticket 08 then
passes both `--calibration mbit10.cpu.lanl20261006.service.openmp.a1` and
`--calibration mbit10.cpu.lanl20261006.service.openmp.a2`.
