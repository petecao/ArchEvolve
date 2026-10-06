# 02 — Prefactor: evidence basis `estimated` and the estimate record shape

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 01
**Spec:** `../spec.md`
**Time estimate:** 1–2 h

**What to build:** Add the basis value `estimated` (D9) to `vocab/basis.yaml` and the schemas that list bases, and define where an estimate lives (a new record kind or an evaluation section; choose the smaller change and say why).

## Acceptance

- [ ] `estimated` validates wherever a basis is allowed; every existing record validates unchanged.
- [ ] An estimate names its estimator version, target-description sha256, characterization sha256, target and input.
- [ ] Comparison and selection code can tell estimates from measurements and simulations.
- [ ] Format reference updated; format-version tests green.
