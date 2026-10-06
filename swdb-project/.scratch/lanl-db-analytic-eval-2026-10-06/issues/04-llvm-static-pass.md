# 04 — LLVM static pass: operation counts and access-shape classification per loop

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 03
**Spec:** `../spec.md`
**Time estimate:** 1–2 days

**What to build:** An LLVM 22 pass (D12) that reports, per loop, operation counts by class and each memory access's address shape (`stream`, `single_valued_indirect`, `ranged_indirect`, `pointer_chase`, `data_dependent_merge`), stride and element bytes, plus DX100 command calls, and fills the characterization's static slots.

## Acceptance

- [ ] Builds and runs on the Mac with Homebrew LLVM 22; build steps documented for mbit10 (toolchain under `/data1/yanruj`).
- [ ] Classification compared with the 13 hand-written access patterns of `gapbs-bfs-do` and the BC records; every mismatch listed with a reason.
- [ ] Output maps to `vocab/address_shapes.yaml` values only; anything else is `unknown`.
- [ ] Loops map onto existing region IDs (D33); a loop that maps to none is listed, never dropped.
- [ ] Tests cover one example of each address shape.
