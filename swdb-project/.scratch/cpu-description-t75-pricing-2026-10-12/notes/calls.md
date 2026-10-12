# Calls: the library-call service family and indirect-call (C8, C9)

Written 2026-10-12 01:02 ET at `e2611242`. Paths are relative to `swdb-project/`.

## How a call becomes `call_cost.<name>`

1. Characterize writes `unmodeled_calls` rows `{site, region, name, execution_count, body_counted, cost_accounting}`. Indirect calls get `name: indirect-call`, `line: 0` and **no** `body_counted`/`cost_accounting` fields (`swdb/llvm/Characterize.cpp:470`).
2. `swdb/analytic.py:144-146` `_uncovered_call`: a call is uncovered unless `body_counted` is set or `cost_accounting ∈ {no_runtime_operation, source_normalized_operations}`. A missing field defaults to `opaque_callee`, so indirect-call counts as opaque.
3. `swdb/analytic.py:607-626` `_estimate_regions`: each mechanism runs. A site is "covered" only when a mechanism returns **known** seconds and lists it in `inputs.covered_calls` with the exact count. Leftover executed uncovered calls add the bound `unmodeled_calls` with `missing = ['call_cost.' + name]`, so the region is unknown.
4. `swdb/analytic_cpu_service.py:33-107` `native_service_costs` matches selectors **by exact `name`** (line 70). Scalar selector shape: `{name, parameter, unit: 'seconds/call'}`; cost = count × rate. **All or nothing per region:** any `missing` in the mechanism leaves `covered_calls = []` (line 105). One unpriced shape bin or OpenMP site in a region therefore re-surfaces every call there as `call_cost.*`. That explains the large cascade in ticket 03.

C9 holds by construction: a call with no selector stays `call_cost.<name>`. Nothing is priced at 0 unless it is `body_counted` or has a known count of 0.

## Model to copy: the clock service (paired receipts)

| File:line | What |
|---|---|
| `swdb/native/CpuServiceWork.h:6-17` | `service_clock(n, invoke_clock)`: a loop where `invoke` adds one `system_clock::now()` per iteration; `asm volatile` keeps the value; a checksum is returned. The driver is the same loop with `invoke = false`. |
| `swdb/native/CpuServiceTimer.cpp`, `CpuServiceCount.cpp` | Timer (gross vs driver, alternating order) and the count driver. |
| `swdb/cpu_service_calibration.py:27-52` `register_cli` | `cpu-service-calibrate --service-group {clock, allocator}` and `import-cpu-service-calibration`. |
| `swdb/cpu_service_calibration.py:177-255` `calibrate` (clock branch) | Pilot doubles `n` until both gross and driver ≥ `min_trial_s`; 7 reps alternate `service_first` / `driver_first`; 25 MiB raw cap; service id `clock.now`. |
| `swdb/cpu_service_counts.py:12-56` `clock_proof` | 6 count runs (`invoke` × n ∈ {32,64,96}) through `swdb characterize --fixture --counting-pipeline source-normalized-v2`. Counts **opaque_callee, not body_counted** calls; needs exactly n vs 0; the single callee name becomes `proof.event_abi`. |
| `swdb/cpu_service_calibration.py:55-85` `derive_service` | rate = median((gross − driver)/events); any rate ≤ 0 gives `missing: paired_driver_subtraction_resolution` and the value null. |
| `swdb/cpu_service_native.py:63-115` `validate` | Dispatch by `settings.group`. The **no-group fallback is clock-only**: line 104 needs exactly one service `clock.now`; `[[32,32],[64,64],[96,96]]` points; 3 source files. |
| `swdb/cpu_service_binding.py:283-304` | Scalar binding: `event_abi` from `scope.event_abi` or `denominator.proof.event_abi`. The selector is `{name: abi, parameter: service_<k>, unit}`. A duplicate ABI is refused. |

Evidence of the prior clock run: `.scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-clock-service-mbit10-20261006-a2.json`. Node0 lease, about 4.5 min (23:55–23:59 UTC), 0.01716 µs/call (17.16 ns), source commit `05e1b7b0`.

## What a new "library call service" group needs

- **Native source.** One shared source with one counted service per ABI:
  - `strlen`, at a fixed constructed length;
  - `_ZNSo3putEc`, `_ZNSo5flushEv`;
  - `_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l` (`__ostream_insert`, string of length l);
  - `_ZNSo9_M_insertImEERSoT_` (`operator<<(unsigned long)`);
  - `_ZNKSt5ctypeIcE13_M_widen_initEv`.

  Each needs its own paired driver.
- **Settings.** A new `settings.group` (for example `library_call_v1`), a validator branch in `cpu_service_native.validate`, and a generalized `clock_proof` that checks **one exact ABI per service**.
- **Binder.** No change needed if each service carries `scope.event_abi`; the scalar path already handles it. The binder still refuses a duplicate ABI.
- **Shape caveat.** Those calls show `unknown_lengths` in `call_shape_counts`; that is fine, because a scalar selector ignores shape rows. The transfer of string length and stream state is inferred: label it in `event_definition` / `scope`, as the clock does.
- **Architecture caveat: `flush`.**
  - `_ZNSo5flushEv` on `std::cout` issues a `write(2)` syscall when the buffer is non-empty. Its cost depends on where stdout goes (pipe, file or tty) and on buffer size.
  - The constructed receipt must pin stdout's sink. The evaluator's timing harness redirects stdout to a file or pipe; match that.
  - `_M_widen_init` runs once per `ctype` facet (cached after the first call), so a steady-state loop measures the cached early-return path. The app calls it once. This is a known first-call versus warm mismatch; document it as inferred.
- **Counts in t75 (per side).**
  - region `serial.995486541436624707`: strlen ×1, `__ostream_insert` ×1, widen_init ×1, indirect ×1, put ×1, flush ×1;
  - region `DOBFS.180.0`: strlen ×14, `__ostream_insert` ×14, `_M_insert<unsigned long>` ×7, put ×7, flush ×7, clock ×14.

  These are printing calls inside the `bfs.complete_call.v1` ROI.

## `indirect-call`

- **Count proof.** `clock_proof` keeps only rows with `cost_accounting == 'opaque_callee'` (`cpu_service_counts.py:39-40`). Indirect rows lack that field, so the **existing proof would count 0 events**. A new proof must accept the `indirect-call` row; the binder then sees `event_abi: indirect-call`.
- **Overhead only (C8).** In t75 the indirect call is most likely the `std::endl` manipulator through `operator<<(ostream&(*)(ostream&))`. Its callee (`endl<char>`, an inline template) is defined in the TU, so its body is counted. That is consistent with `put`/`flush`/`widen_init` appearing as separate opaque calls with matching counts.

  The constructed receipt should time an indirect call to a counted, trivially small callee, minus a driver that makes a direct inlined call of the same body. Otherwise the callee work is charged twice.
- **Scope.** The scalar selector `name: indirect-call` would price **every** indirect site in every allowlisted count. That is acceptable for T1 serial; note it.

## Tests (prior art)

- `tests/test_cpu_service_calibration.py`:
  - `:10` `test_import_service_fixture_retains_paired_trials_and_reported_cost`
  - `:28`
  - `:42`
  - `:63` `test_portable_clock_receipt_binds_separate_source_normalized_call_counts`
  - `:93`, `:109`, `:121`
- `tests/test_analytic_cpu_service.py`:
  - `:14` `test_exact_scalar_service_coverage_adds_once_and_clears_its_opaque_call`
  - `:27` `test_service_missing_rate_zero_and_counted_body_keep_honest_coverage`
  - `:38`
- `tests/test_cpu_service_binding.py:65` `test_duplicate_exact_abi_cannot_create_an_ambiguous_cost`
