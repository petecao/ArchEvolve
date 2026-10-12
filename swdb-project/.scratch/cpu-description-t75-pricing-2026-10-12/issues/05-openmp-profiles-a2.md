# 05 — OpenMP profile set a2 with __kmpc_for_static_init_8u

Created: 2026-10-12 01:10 ET
**Type:** slice
**Status:** ready-for-agent
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
