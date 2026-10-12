# 03 — Floor-only bandwidth rate

Created: 2026-10-12 01:10 ET
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md` (C11; seams 1 and 3)
**Code map:** `../notes/binder.md` (bandwidth section)

**Time estimate:** about 3 hours.

## Decision (agent, 2026-10-12 01:10 ET)

The code map shows C11 cannot be a mechanism: the estimator evaluates every mechanism
(`analytic.py:607-613`), so a `streaming_bandwidth` mechanism would change estimates, and the schema
allows only `resource_bound`/`additive_overhead`. **Choice:** a new, estimator-ignored description
field (e.g. `resource_rates.streaming_bytes_per_s` with its source calibration id/sha256) that only
the attribution resource floor reads. The binder copies the base calibration's measured
`streaming_bandwidth.bytes_per_s` (15.07 GB/s) into it instead of dropping it. Name the field to
fit the existing schema style.

## Acceptance

- [x] Seam 1: the same fixture estimated with and without the field gives identical seconds.
- [x] Seam 3: with the field, the attribution resource floor is numeric and ≤ the estimate; without it, the floor stays unknown with a reason (existing test keeps passing).
- [x] Schema, binder and validator accept the field; `services.v1` still validates.
- [x] `docs/reference/` updated where the description format is documented.

## Answer

Resolved 2026-10-12 01:20 ET on branch `cpud/03-floor-bandwidth` (base `cpud/integration` `11f7327a`).

**Field (name and shape).** New optional top-level target-description field
`resource_floor_mechanisms`: a list of mechanism-shaped items that the estimator never reads.

```yaml
resource_floor_mechanisms:
- model: streaming_bandwidth          # enum: streaming_bandwidth only
  parameters:
    bytes_per_s: {value, basis, source, unit}   # the usual parameter shape, copied verbatim
  carried_from:                       # optional; the binder always writes it
    description: {id, sha256}         # the immutable base description
    calibrations: [{id, sha256}]      # the base's calibration_sources
```

Why this shape, not `resource_rates.streaming_bytes_per_s`: it is the mechanism shape, so the
floor runs the unchanged `streaming_bandwidth` model on it exactly as the estimator would. The
name ties it to the glossary term "resource floor".

**What changed.**
- `schemas/target_description.schema.json`: the field, plus `$defs/pin` (`{id, sha256}`).
- `swdb/attribution.py` `_floor_terms`: a floor term's rates are the `resource_bound` mechanisms
  plus `resource_floor_mechanisms`. The estimator (`analytic.py`) reads only `mechanisms`, so it
  needed no change. A term from the carrier reports `in_description: true` (term shape unchanged).
- `swdb/cpu_service_binding.py` `_floor_only_bandwidth`: when memory cells supersede the base's
  memory mechanisms, every plain (`resource_bound`, no selector) `streaming_bandwidth` mechanism
  is copied verbatim into the carrier with `carried_from`. A bind without memory cells writes no
  field. For `services.v2` this carries the measured 15 071 467 834 B/s from
  `mbit10.cpu.lanl20261006a2.v2.t1`, pinned to `mbit10.cpu.lanl20261006a2.v2.calibration.t1`.
- Docs: `docs/reference/format-v0.4-analytic.md` (target description), `cpu-service-calibration.md`
  (binder), `format-v0.4-attribution.md` (resource floor).

**Acceptance evidence.**
- Seams 1 and 3: `tests/test_attribution.py::test_a_floor_only_bandwidth_rate_makes_the_floor_numeric_and_leaves_every_estimate_unchanged`.
  The same counts estimated with and without the field give identical total (70 s), region and
  bound-by-bound seconds. With it, the floor is 8 s (bandwidth-limited), below the 30 s estimate.
  `test_a_missing_bandwidth_rate_gives_an_unknown_floor_with_a_reason_not_zero` still passes.
- Binder and validator: `tests/test_cpu_service_binding.py::test_memory_cells_move_the_measured_bandwidth_rate_to_the_floor_only_carrier`
  (the fixture store validates). The clock-only bind test now also asserts no carrier.
- `services.v1` and its base still pass the schema and payload checks (a single-record check, not
  a whole-store `swdb validate`, per the Mac RAM rules).

**Assumptions and notes.**
- Validator: the schema reuses `$defs/parameter`. I added no separate finite-value check for
  carrier parameters; the binder copies already-validated base values.
- If a description had both a carrier and a `streaming_bandwidth` mechanism, the floor would take
  the max of both. The binder never produces that.
- Pre-existing failure, not touched: `tests/test_cpu_service_binding.py::test_extensa_tagged_native_service_record_never_enters_team_binding`
  expects the stderr text `Extensa research evidence`, but `require_team_safe` now says
  `Extensa campaign ... records never enter team results or protocols`. It fails at `11f7327a` too.
