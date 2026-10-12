# 03 — Floor-only bandwidth rate

Created: 2026-10-12 01:10 ET
**Type:** slice
**Status:** ready-for-agent
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

- [ ] Seam 1: the same fixture estimated with and without the field gives identical seconds.
- [ ] Seam 3: with the field, the attribution resource floor is numeric and ≤ the estimate; without it, the floor stays unknown with a reason (existing test keeps passing).
- [ ] Schema, binder and validator accept the field; `services.v1` still validates.
- [ ] `docs/reference/` updated where the description format is documented.
