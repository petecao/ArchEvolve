# OpenMP: `_8u` class and t75 projections (C7)

Written 2026-10-12 01:02 ET at `e2611242`. Paths are relative to `swdb-project/`.

## What t75 calls in the ROI (both sides)

| ABI | Count | Status in `services.v1` |
|---|---|---|
| `__kmpc_fork_call` | 1 + 7 | profiles exist for argc classes n ∈ {2,3,4,5,7,8} only |
| `__kmpc_for_static_init_4` | 1 + 1 | profile exists: `ident_flags 514`, schedtype 34, incr/chunk 1 |
| `__kmpc_for_static_init_8u` | 7 | **no profile** |
| `__kmpc_for_static_fini` | 7 + 1 + 1 | exists |

Whether each t75 site matches an existing class (argc, ident flags, literal schedule) is unknown until the t75 projection exists. A mismatch gives `openmp.unsupported_abi_class`, not a cost. So check the projection's `calls[*]` against `PROFILES` before calibrating.

## Code map

| File:line | What |
|---|---|
| `swdb/cpu_openmp_profiles.py:8-20` | `PROFILES`: 22 classes. `_profile(name, ident_flags, argc, [(index,bits,value)], outcome)`. Index < 6 is `context: caller`, the rest `serialized_team` (line 21). `_8` is `_profile('__kmpc_for_static_init_8',514,9,[(2,32,34),(7,64,1),(8,64,1)])`; `_8u` would most likely mirror it. |
| `swdb/cpu_openmp_calibration.py:157-167` `check_signature` | Exact name, argc, constant `ident_flags` (32-bit), literal integer operands. |
| `swdb/cpu_openmp_calibration.py` hard-coded **22** | line 109 (source markers `set(range(22))`), 121 (cells), 188 (`len(services)==22`), 197, 200; validate line 176 requires `group=='openmp_v1'`; line 192 requires `proof['profiles']==PROFILES` |
| `swdb/cpu_openmp_binding.py:48` | `if set(profiles)!=set(range(22))`: "full22-class independent matrix required" |
| `swdb/native/CpuOpenmpWork.h:9-70` | Constructed event switch `case 0..21` with `// SWDB_OMP_EVENT i` markers; declares the `__kmpc_*` prototypes (`_8` at line 12). |
| `swdb/analytic_cpu_openmp.py:15-26` `profile_indexes` | Matches a projected signature to profile indexes. Outlined (`.omp_outlined`) must be `serialized_team`. |
| `swdb/analytic_cpu_openmp.py:29-60` `cost` | Needs projection for exactly `(characterization_id, sha256)` (else `openmp.exact_characterization_projection`, the ticket-03 reason); exact static site; supported class; `abi_sites` row; all source rates > 0; envelope = max for multi-index (dispatch_next success/terminal). |
| `swdb/cpu_openmp_binding.py:14-65` `binding` | One projection per scope characterization (line 19: `len(documents)!=len(scopes)` fails). Each must be sealed (`identity_sha256`), bind `{id, sha256}` of exactly one scope, match `static_analysis.source_ir_sha256`, and match the **all-trial executed `__kmpc_*` site union** (`_executed`, lines 10–12). Native counts also need the projection receipt compiler sha to equal `native_runtime.compiler_sha256`, `inputs_byte_identical_after_projection`, and `application_execution: false`. |

## Risk: adding `_8u` breaks validation of the existing record

Appending to `PROFILES` changes the list that `validate` compares against: `proof['profiles']==PROFILES` and `len(services)==22`. `mbit10.cpu.lanl20261006.service.openmp.a1` (in `services.v1`) would then **fail `swdb validate`**, and with it every record pinning `services.v1`.

Fix pattern: version the profile set. Keep `PROFILES_V1` (22) for `group: openmp_v1`, and add `openmp_v2` with 23 classes (or a separate one-class `_8u` receipt). Make `binding` accept the union of v1 cells (0–21) from `service.openmp.a1` plus the new class-22 cell from a new receipt. Line 48 must then be `set(range(len(PROFILES)))`, version-aware.

`profile_indexes` iterates the global `PROFILES`. That is fine if the new class only extends it, but recheck `services.v1` estimates: an added class could match an existing site and change its `profile_indexes`, which would trip `openmp.exact_constructed_profiles` for old descriptions. `_8u` has a distinct name, so this should not happen; verify with the four g16/g17 projections anyway.

## Projection script (existing)

- Script: `scripts/openmp_call_projection.py` (`project` lines 69–139, CLI lines 140–163). Helper: `swdb/llvm/OpenMPCallProjection.cpp`. Output format: `swdb.openmp-call-projection.v1`.
- Runbook: `.scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-openmp-call-projection-runbook.md` (command at lines 46–87). It needs LLVM dev headers and compiles a read-only helper. Nothing is executed. 180 s stage cap; the parent allowed 900 s for four cases.
  ```
  python3 -m scripts.openmp_call_projection --characterization <char.yaml> \
    --source-ir <counted>/normalized.bc --source-map <counted>/source.json \
    --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin \
    --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
    --timeout-s 180 --output-directory <new dir>
  ```
  Omit `--function` (whole TU). For t75, the inputs are the kept counted folders `/data/yanruj/EvolveSWDB_runs/fga03-real-pair-20261011-a1/a2/{baseline,candidate}-counted/`; confirm `normalized.bc` and `source.json` are among the 13 kept files. The characterization file comes from `records/workload_characterizations/fga03.t75-*.characterization.a2.yaml`, byte-checked.
- Export only the compact `projection.json` into the repo (the g16/g17 ones are under `evidence/11-openmp-*-projection-mbit10-20261006-a1.json`). Pass each with `--openmp-projection`.

## Ordering surprise for C4

The binder needs **one projection per scope characterization**. A trial bind that adds the two t75 counts but no t75 projections fails ("OpenMP requires one exact projection per frozen characterization"), unless OpenMP calibration is dropped from the trial, which would leave every OpenMP call unknown. So: **produce both t75 projections before the C4 trial bind.** Projections are outcome-free (static IR plus counts), so this is legal before the freeze.

## Calibrator command (services.v1 OpenMP run)

`.scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-openmp-service-runbook.md:17-35`:
- count: `python3 -m swdb.cpu_openmp_calibration --records … --output …/count --count-only --machine mbit10 --lane mbit10-evaluation-node0 --llvm-bin … --toolchain-flag=… --max-wall-s 900`
- elapsed: the same with `--repetitions 7 --min-trial-s .05`
- `--validate-receipt …/receipt.json`, then `import-cpu-service-calibration --id …service.openmp.a1`

The elapsed run took about 10 min (02:38–02:48 UTC). The required env is `OMP_NUM_THREADS=1 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores` (`cpu_openmp_calibration.py:27`).

## Tests (prior art)

- `tests/test_cpu_openmp_binding.py:40, :54, :64`
- `tests/test_analytic_cpu_openmp.py:36, :45, :52`
- `tests/test_cpu_openmp_calibration.py:16, :35, :43, :59, :83`
- `tests/test_openmp_call_projection.py`
- testkit `tests/testkit/cpu_openmp.py`
