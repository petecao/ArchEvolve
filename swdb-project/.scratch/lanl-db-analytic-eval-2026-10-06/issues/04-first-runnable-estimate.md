# 04 — First runnable version: estimate a streaming loop on the mbit10 CPU

Created: 2026-10-06
**Type:** slice
**Status:** claimed
**Blocked by:** 01
**Spec:** `../spec.md`
**Time estimate:** 1.5–2 days

**What to build:** From a tiny C++ fixture kernel with one streaming loop, `swdb characterize` produces a workload characterization (static facts from the LLVM pass, plus trip and access counts from one counted native run), and `swdb estimate` turns it, with a minimal mbit10 target description, into an estimate: seconds per region and in total, a per-region report naming the limiting bound, basis `estimated`. The slice includes the basis value, characterization v1, target description v1, the compute-throughput and streaming-bandwidth mechanism models, the estimate record (a new kind or an evaluation section: choose the smaller change and record why), the two commands and their tests.

## Acceptance

- [ ] `estimated` validates wherever a basis is allowed; every existing record validates unchanged (D9).
- [ ] Characterization v1 and target description v1 have schemas and documentation written for outside readers (D7, D11).
- [ ] The fixture's characterization and estimate match hand-computed counts and bounds.
- [ ] An unknown parameter makes the bound that needs it unknown, never zero.
- [ ] Counts are taken at source level and record the host (D12).
- [ ] Tests run through the commands on a copied record store and skip cleanly when LLVM 22 is missing.

## Comments

2026-10-06: Claimed by ticket04 implementer on `codex/lanl-ticket04`, based on integration commit `fb842a8`. Confirmed public seams are characterize/estimate commands on a copied record store and validate.
