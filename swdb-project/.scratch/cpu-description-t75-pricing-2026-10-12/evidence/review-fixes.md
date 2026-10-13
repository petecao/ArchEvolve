# Code-review fixes (review of `cpud/integration` at `c9f9df67`)

Created: 2026-10-12 20:55 ET. Branch `cpud/review-fixes`. Paths relative to `swdb-project/`.

## What changed

| Finding | Commit | Change | Test |
|---|---|---|---|
| F1 (high) | `bf21f94d` | Floor-only `resource_floor_mechanisms` rates treat `memory_service_scenario` as covering non-stream bytes, so the bandwidth floor term is numeric on `services.v2`. Estimator unchanged. | `tests/test_attribution.py`: services.v2-shaped fixture with a gather; real-record check (t75 candidate a2 on `services.v2`: 0 unknown terms, was 9); old-commit estimates still attributed |
| 8a/8b | `8482d44c` | Native OpenMP and clock count tests copy a record closure, not the 1.1 GB store (~25 s each on the Mac). `SWDB_TOOLCHAIN_FLAGS` fixture (for example `--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13` on mbit10). | the 4 tests themselves |
| F4 | `809795d2` | Library-call `calibrate` refuses non-native caps (repetitions outside 7–11, trials < 0.05 s) first. | `test_native_run_refuses_fixture_sampling_caps_before_any_work` |
| F2/T3, F3, F5 | `88833d05` | Documented only (no Characterize change, no native source change): `indirect-call` is call overhead only; `ostream_insert`/`_M_insert` rates include drains; allocator glibc regime per bin. Allocator comment corrected. Ticket 06 answer notes the limitation. | `test_every_indirect_call_site_is_priced_as_call_overhead_only` |
| F6 | `ddd50b27` | The floor-only carrier pins only the calibration that produced `bytes_per_s`. `services.v2` is unchanged (its base lists exactly that producer). | updated floor-only carrier test; committed `services.v2` carrier re-derived |
| F7 | none | Already covered: `tests/test_openmp_call_projection.py::test_projector_pure_intrinsic_list_equals_the_count_pass_list` (passes). | — |
| T2 | `44690d47` | One seam-1 test binds all new families together and estimates one region. | `tests/test_cpu_services_v2_families.py` |

## Checks

- Targeted validator (`evidence/07-calibrations/targeted_validate.py`) on `services.v1`,
  `services.v2` and the 8 ticket-07 records: all valid, file hashes unchanged
  (`cee03869…`, `70fc5553…`, `88e09c2b…`, `1d2b525c…`, `2b6a8693…`, `5130dec1…`, `7c370ce2…`,
  `add24743…`, `a068b637…`, `10d895c7…`), at `bf21f94d` and again at `ddd50b27`.
- Any `swdb/*.py` change moves `estimator_identity()`. `.a3` protocols frozen before this branch
  keep validating (an estimate is checked against its own protocol). New estimates under those
  protocols must run at the commit that froze them.

## Not done

- Runner-dedup refactor (follow-up).
- Characterize naming for inline asm vs uncounted indirect callees (would change counts).
