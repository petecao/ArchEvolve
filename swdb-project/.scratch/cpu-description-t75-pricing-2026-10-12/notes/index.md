# Implementation notes: `services.v2` for the t75 pair

Written 2026-10-12 01:02 ET, read-only exploration of `yanrujhou_main` `e2611242`.
Spec: `swdb-project/.scratch/cpu-description-t75-pricing-2026-10-12/spec.md` (C1–C14).

| File | Covers |
|---|---|
| [binder.md](binder.md) | bind command (exact v1 runbook copy), `cpu_service_binding.py` map, allowlist, `require_team_safe`, bandwidth/floor (C1–C4, C11) |
| [allocator.md](allocator.md) | malloc, 16 MiB bins, every 1 MiB cap, the gross resource path (C5, C6) |
| [bulk.md](bulk.md) | the six memmove bins: new bulk-total batch, no code change (C6) |
| [openmp.md](openmp.md) | `_8u` class, the 22-class hard-codes, projection script (C7) |
| [memory.md](memory.md) | 1-/2-byte write cells: calibrator, native source, binder, evaluator (C10) |
| [calls.md](calls.md) | how `call_cost.*` arises, clock receipt as the model, library calls, indirect-call (C8, C9) |
| [ops.md](ops.md) | lanes, durations, freeze/estimate, timing recipe, exact F43/F44 code semantics (C12, C13) |

## Where the code contradicts or extends the spec

1. **C11 bandwidth.** The floor reads only `streaming_bandwidth` *mechanisms*, and the estimator evaluates every mechanism. So any `bytes_per_s` added as a mechanism changes the estimate. C11 needs a new carrier, such as an accounting value or an extension, plus a schema change. See binder.md.
2. **C4 order.** The binder needs one OpenMP projection per scope characterization. The trial bind cannot run until both t75 projections exist (or it must drop OpenMP).
3. **C4 tool.** `unknowns_summary.py` hard-codes the a2 estimate IDs and the repo store, and it overwrites its evidence JSON. It needs parameters before it can read trial estimates.
4. **C5/C6 sizes.** malloc needs bins 64, 128, 6144 and **2097152 (2 MiB)**, so a second over-cap size beyond the 16 MiB pair. `free` is not executed. The 1 MiB cap sits in five places, including the binder's gross path and `cpu_allocator_resource`.
5. **C5 source pin.** `cpu_allocator_resource.NATIVE_SOURCE` pins the allocator C++ source hashes. Editing that source needs a new recipe version.
6. **C5 cell selection.** With `--size`, the allocator calibrator measures all four ops at each size. Malloc sizes 64/128 would then duplicate the existing `_Znwm`/`_ZdlPv` bins, and the binder refuses duplicates.
7. **C7 versioning.** "22" is hard-coded (`cpu_openmp_calibration` ×5, `cpu_openmp_binding:48`), and `validate` compares `proof['profiles'] == PROFILES`. Appending `_8u` in place would make `service.openmp.a1`, and hence the `services.v1` closure, fail `swdb validate`.
8. **C10 scope.** The 1-byte "read-only, 256 B" rule is hard-coded in the calibrator, the binder and the evaluator. There is no 16-bit native function. Old `memory_v1` records must keep validating, so add a new group. The binder refuses duplicate (op, width) cells, so do not re-measure v1 cells.
9. **C8 indirect-call.** The existing count proof only counts `cost_accounting == opaque_callee`. Indirect-call rows lack that field, so they would count 0 events.
10. **C13 F43.** The code compares the region_profile `created` (an ET date string) to the estimates' `created`: a strictly later calendar day, on the profile record, not on the evaluation. Run the evaluation on a later day too.

## Checked and fine

- **C3:** `require_team_safe` passes for both t75 counts, `services.v1` and the base (run locally).
- **Runtime identity:** the t75 runtimes match the g16 count exactly (compiler, libc, libstdc++, libomp hashes; env scope), so existing calibrations should pass per-member compatibility.
- **Bulk:** the six memmove sizes are within all caps. One new bulk-total batch plus the existing `--bulk-copy-calibration` choice is enough.
- **2-byte writes:** these already pass the evaluator; only the calibrator, native source and binder block them.
