# 06 — Library-call service family and indirect-call overhead

Created: 2026-10-12 01:10 ET
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** None — can start immediately (01 confirms the call list)
**Spec:** `../spec.md` (C8, C9; seams 1 and 2)
**Code map:** `../notes/calls.md`

**Time estimate:** about a day.

## What to build

- A new calibration family "library call service" for `strlen`, the iostream calls (`ostream`
  put/flush/insert) and `ctype::_M_widen_init`, measured per call with paired receipts, modeled on the
  clock service. Record in the receipt that `flush` cost depends on where stdout goes (measure to a
  file, like the timed run) and that `_M_widen_init` is cached after its first call (the transfer
  rule is inferred; say so).
- `indirect-call`: a receipt for the call overhead only. The existing count proof keeps only
  `cost_accounting == opaque_callee` rows and so counts 0 indirect calls: add a proof that counts
  them, so the callee's work stays where it is defined.
- C9: any call still without a receipt stays `call_cost.<name>` unknown, never 0 s.

## Acceptance

- [ ] Seam 2: the runner (test double timing) writes receipts that validate and that the binder admits.
- [ ] Seam 1: a fixture with these calls is priced; removing one receipt leaves `call_cost.<name>` unknown.
- [ ] Indirect-call count is non-zero on a fixture with indirect calls.
