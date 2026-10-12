# 08 — Bind, validate and freeze services.v2

Created: 2026-10-12 01:10 ET
**Type:** task
**Status:** claimed
**Blocked by:** 03, 07
**Spec:** `../spec.md` (C1, C2, C9, C11, C12, C14; user stories 2–5, 19, 21, 23)
**Code map:** `../notes/binder.md`

**Time estimate:** about 2 hours.

## What to do

Bind `mbit10.cpu.lanl20261006.t1.services.v2` with the existing binder: same base calibration and
inputs as `services.v1` (runbook 11 command), plus the six-member allowlist (four gapbs + two t75
by `{id, sha256}`), the t75 OpenMP projections, every ticket-07 receipt and the floor-only bandwidth
field. `services.v1` stays unchanged. No error band (C14). Then whole-store `swdb validate`
(mbit10), commit and push — all before any t75 timing (C12).

## Acceptance

- [ ] `services.v2` committed and pushed; `services.v1` byte-identical.
- [ ] Whole-store validate passes (output saved).
- [ ] Bind runbook saved in `evidence/08-bind/`.
