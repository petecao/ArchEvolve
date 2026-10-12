# Binder: CPU service binding → `services.v2`

Written 2026-10-12 01:02 ET against `yanrujhou_main` `e2611242`. Read-only notes; paths relative to `swdb-project/`.
Spec decisions served: C1, C2, C3, C4, C11.

## Command (exact services.v1 bind)

Source: `.scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-native-model-band-runbook.md` lines 11–37.

```sh
python3 -m swdb.cpu_service_binding --records "$LANL_CPU_STORE" \
  --target-description mbit10.cpu.lanl20261006a2.v2.t1 \
  --characterization bfs.kron-g16.t1.characterization.objects.a1 \
  --scope-characterization bc.kron-g16.t1.characterization.objects.a1 \
  --scope-characterization bfs.kron-g17.t1.characterization.objects.a1 \
  --scope-characterization bc.kron-g17.t1.characterization.objects.a1 \
  --calibration mbit10.cpu.lanl20261006.service.clock.a2 \
  --calibration mbit10.cpu.lanl20261006.resource.allocator.a1 \
  --calibration mbit10.cpu.lanl20261006.resource.allocator-extra.a1 \
  --calibration mbit10.cpu.lanl20261006.resource.memory.a1 \
  --calibration mbit10.cpu.lanl20261006.resource.float-memory.a1 \
  --calibration mbit10.cpu.lanl20261006.service.byte-read.a1 \
  --calibration mbit10.cpu.lanl20261006.resource.bulk-total.a1 \
  --calibration mbit10.cpu.lanl20261006.resource.bulk-total.a2 \
  --calibration mbit10.cpu.lanl20261006.service.openmp.a1 \
  --memory-footprint-bytes 8388608 \
  --memory-cas-policy max_constructed_success_failure_median \
  --bulk-profile-policy max_constructed_profiles_median \
  --bulk-copy-calibration mbit10.cpu.lanl20261006.resource.bulk-total.a1 \
  --openmp-next-policy max_constructed_success_failure_median \
  --openmp-projection .scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-openmp-bfs.g16-projection-mbit10-20261006-a1.json \
  --openmp-projection .scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-openmp-bc.g16-projection-mbit10-20261006-a1.json \
  --openmp-projection .scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-openmp-bfs.g17-projection-mbit10-20261006-a1.json \
  --openmp-projection .scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-openmp-bc.g17-projection-mbit10-20261006-a1.json \
  --id mbit10.cpu.lanl20261006.t1.services.v1 --format json
```

For `services.v2`, add:
- `--scope-characterization fga03.t75-baseline.uniform22.t1.characterization.a2`
- `--scope-characterization fga03.t75-candidate.uniform22.t1.characterization.a2`
- two more `--openmp-projection` files, one per t75 count (see openmp.md; **required even for the C4 trial bind**)
- the new calibration IDs, then `--id mbit10.cpu.lanl20261006.t1.services.v2`

Not a `swdb` subcommand: the module has its own `main()` (`swdb/cpu_service_binding.py:360-383`). So `archevolve.guard_cli` does not run, but `bind()` calls `require_team_safe` itself.
It writes the new record straight into `--records` with `writer.commit` (line 356). Point the C4 trial bind at a **scratch copy of the store** (ticket 03 used `$RAW/records`); never at `records/`.

## Code map: `swdb/cpu_service_binding.py` (387 lines)

| Lines | What |
|---|---|
| 18–19 | `ALLOCATOR_FIELDS` (`_Znam`, `_Znwm`, `_ZdaPv`, `_ZdlPv`). No `malloc`/`free` (C5). |
| 26–77 | `_compatibility(target, char, calibration, service, fixture)`: per-member check. Same `target`; serial T1; same compiler version and `compiler_sha256`; `libc.so*`/`libstdc++*` hash sets equal; interposer (`LD_PRELOAD`, `LD_AUDIT`) absence scope; allocator (`MALLOC_*`, `GLIBC_TUNABLES`) controls when `scope.allocator_regime`; `libomp` hashes and `OMP_/KMP_/GOMP_` env when `scope.openmp_regime`. |
| 82–85 | `_scope_compatibility`: runs `_compatibility` for **every** scope characterization. Reasons are prefixed `scope.<char id>.` when there is more than one scope. |
| 87–149 | `_memory_binding` (see memory.md). Width guard `(1,4,8)` at line 102. |
| 152–208 | `_bulk_binding` (see bulk.md). Size guard `8..1048576` at line 165. |
| 213–233 | `_allocator_resource_binding` (gross recipe). Size guard `size>1048576` at line 219. |
| 236–357 | `bind(args)`. |
| 243–245 | Allowlist = `[{id, sha256: artifacts.digest(c)}]` for primary + every `--scope-characterization`, deduplicated, primary first. |
| 246 | Base must have `estimator_variant: team`. |
| 247 | `require_team_safe(store, target, *scopes, *args.calibration, command='bind-cpu-services')`. |
| 251–304 | Per-calibration loop: allowed kinds `cpu_service_calibration`, `cpu_{memory,bulk,allocator}_resource_calibration`. Each is revalidated (`validate_record`). Services routed by scope: allocator-resource, `openmp_regime`, `bulk_regime`, `seconds/request` (memory), else scalar/allocator-paired. A scalar needs `scope.event_abi` or `denominator.proof.event_abi` (line 284–286). Duplicate scalar ABI refused (303). |
| 305–311 | OpenMP → `swdb/cpu_openmp_binding.py:binding`. |
| 325–329 | Memory cells **remove** every `MEMORY_MODELS` mechanism (`streaming_bandwidth`, `requests_in_flight_latency`, `cache_fit`, `memory_service_scenario`) from the base. This is why `services.v1` has no `bytes_per_s`. Also refuses an already-bound base (line 326). |
| 334–338 | With >1 scope, each `native_service_costs` / `memory_service_scenario` selector drops `characterization_sha256` and gets `characterization_allowlist`. |
| 341–345 | Any non-empty compatibility `missing` → `selector.calibration_admission[param] = reasons` (parameter stays but is unpriced). |
| 347–355 | Evidence `extensions.cpu_services_binding` (`format: swdb.cpu-services-binding.v1`): base pin, primary, allowlist, calibration `{id, sha256}`, compatibility rows, selections. `version` = digest of evidence. |

## How the allowlist is enforced at estimate time

`swdb/analytic_cpu_service.py:20-31` `_scope_missing(selector, context, prefix)`.
The estimate context carries `characterization_id` and `characterization_sha256` (`swdb/analytic.py:597-602`, `_estimate_regions`).
`{'id', 'sha256'}` must be literally in the list → otherwise `service_scope.characterization_allowlist` (`native_service_costs`, line 38) or `memory_scenario.characterization_allowlist` (`memory_service_scenario`, line 271). This is the ticket-03 failure: every unknown region names both.

## `require_team_safe` (C3)

`swdb/archevolve.py:80-172`. It walks every value recursively. Bare ID strings and nested `{id: ...}` pins resolve through the store, so it covers the full lineage. It refuses:
- any record with `mode: extensa` whose `kind` is not in `extensa_boundary.OWNED_KINDS = {candidate, proposal, source_snapshot}` (`swdb/extensa_boundary.py:32`);
- `estimator_variant: research`;
- `gem5` in identity fields (`backend`, `simulator`, `model`, `target`, `hardware_target`);
- `basis: simulated` facts in a target description;
- a `gem5` numeric `source`;
- an unverifiable `calibration_sources` entry.

Review records with `origin.mode: extensa` skip their `evidence` key.

**C3 check, done read-only on the Mac (2026-10-12, ~180 s, store load included):** `require_team_safe(Store('records'), X, command='probe')` **PASSES** for `fga03.t75-baseline…characterization.a2`, `fga03.t75-candidate…characterization.a2`, `services.v1` and `mbit10.cpu.lanl20261006a2.v2.t1`.
The candidate record `records/candidates/extensa-native-bfs-20261005-a8.it1.kronecker.a0.yaml` has `mode: extensa`, but `candidate` is an owned kind, so it is allowed. Ticket 03's `characterize` and `estimate` already passed `guard_cli` (both are in `EVIDENCE_COMMANDS`, `archevolve.py:15`).

## Per-member compatibility: expected result for t75

`observation_contract.native_runtime` of both t75 counts is byte-equal to `bfs.kron-g16…objects.a1` (checked 2026-10-12):
- same compiler sha `31a40dc3…`;
- same `libc.so.6`, `libstdc++.so.6.0.33`, `libomp.so` and `libarcher.so` hashes;
- same env scope and OMP env.

Existing calibrations should therefore pass `_compatibility` for t75. The C4 trial bind confirms it: look for empty `missing` in `extensions.cpu_services_binding.compatibility[*].scopes`.

## Where things live

- `services.v1`: `records/target_descriptions/mbit10.cpu.lanl20261006.t1.services.v1.yaml` (598 KB). Mechanisms:
  1. `compute_throughput`
  2. `native_service_costs` (additive_overhead: clock, 15 OpenMP ABIs, memcpy/memmove bins)
  3. `memory_service_scenario` (resource_bound)
  4. `native_service_costs` (resource_bound, gross allocator, `resource_recipe`)
- Base: `records/target_descriptions/mbit10.cpu.lanl20261006a2.v2.t1.yaml`. It **does** carry `streaming_bandwidth.bytes_per_s = 15071467833.99156` (measured, lines 52–59) and `cache_fit.bytes_per_s`/`cold_bytes_per_s`. Calibration record: `records/cpu_calibrations/mbit10.cpu.lanl20261006a2.v2.calibration.t1.yaml`.

## Bandwidth for the resource floor (C11): code contradicts a naive approach

- `swdb/attribution.py:683` `FLOOR_MODELS = ('compute_throughput', 'streaming_bandwidth')`.
- `swdb/attribution.py:686-704` `_floor_terms` reads only `target['mechanisms']` with `model == 'streaming_bandwidth'` and accounting `resource_bound` (default). It reads the estimate's `target_description_snapshot` (`_add_limits`, line 1091).
- `swdb/analytic.py:607-613` (`_estimate_regions`) evaluates **every** mechanism in `target['mechanisms']`. `resource_bound` goes to `bounds`; `additive_overhead` goes to `overheads`.

So putting `streaming_bandwidth` back as a mechanism changes estimates. `max(bounds)` can rise, which violates C11 and Seam-1 check 5. An `additive_overhead` copy is worse: the estimator adds it, and the floor ignores it.

The schema allows only `resource_bound|additive_overhead` (`schemas/target_description.schema.json:71-75`; also `schemas/attribution.schema.json:425`).

C11 needs a new carrier that the estimator skips and the floor reads. Two options:
1. A new accounting value such as `floor_only`. Change the schema enum, skip it in `_estimate_regions`, and check `analytic_sensitivity.py:37` and `analytic_count_reuse.py`, which also iterate mechanisms.
2. An `extensions.resource_floor` block that `_floor_terms` turns into a synthetic `streaming_bandwidth` mechanism.

Either way, also update the `_floor_terms` docstring and F6 wording, which say "the description's own mechanisms only".

Prior art for floor tests: `tests/test_attribution.py:1049` `test_resource_floor_is_below_the_estimate_and_headroom_names_its_limit`, `:1079` `test_a_missing_bandwidth_rate_gives_an_unknown_floor_with_a_reason_not_zero`.

## Tests (prior art)

- `tests/test_cpu_service_binding.py`:
  - `:81` `test_binding_freezes_exact_outcome_free_characterization_allowlist_and_checks_every_member`
  - `:115` `test_extensa_tagged_native_service_record_never_enters_team_binding`
  - `:11` / `:43` / `:65`
- `tests/test_analytic_cpu_service.py:80` `test_exact_characterization_allowlist_admits_only_named_counted_scope`; `:98` admission-overrides test.
