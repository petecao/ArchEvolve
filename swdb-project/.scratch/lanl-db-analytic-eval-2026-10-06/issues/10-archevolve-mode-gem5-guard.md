# 10 — ArchEvolve-mode guard: no gem5 runs, no gem5 numbers

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 02
**Spec:** `../spec.md`
**Time estimate:** 2–3 h

**What to build:** Team protocols and ArchEvolve-mode commands refuse a gem5 target, a gem5-derived record, or an estimator calibrated with gem5 data (D3, D10). Extensa mode is untouched.

## Acceptance

- [ ] Refusals name the rule (ADR 0013) and the offending record.
- [ ] Existing ArchEvolve-mode gem5 records stay as history and are never cited by new team protocols.
- [ ] Tests for each refusal; Extensa gem5 campaigns still run.
