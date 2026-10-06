# 06 — Estimate protocols and the gem5 refusal

Created: 2026-10-06
**Type:** slice
**Status:** in-progress (Codex, `codex/lanl-ticket06`; base `86b2a9a`)
**Blocked by:** 04
**Spec:** `../spec.md`
**Time estimate:** 3–4 h

**What to build:** Estimate protocols freeze the estimator version and the target description's hash like other frozen protocols. Team protocols and ArchEvolve-mode commands refuse a gem5 target, a gem5-derived record, or an estimator calibrated with gem5 data, naming ADR 0013 and the offending record (D3, D10). Extensa mode is untouched.

## Acceptance

- [ ] A test per refusal case.
- [ ] Existing ArchEvolve-mode gem5 records still validate, as history.
- [ ] Extensa gem5 campaign tests still pass.
