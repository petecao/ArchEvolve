# 06 — Prefactor: offload strategy effect and the DX100 read-offload strategy

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** The offload strategy effect works in records and strategy queries, and a DX100 read-offload strategy exists for the BFS rewrite contract to realize.

## Acceptance

- [ ] Offload is a strategy-effect value with typed fields: the access-pattern steps moved off the core and the hardware-operation record IDs they move to.
- [ ] Strategy legality rules accept offload for access-pattern targets.
- [ ] A DX100 read-offload strategy record exists and validates.
- [ ] `swdb strategies --pattern` on the BFS neighbor-read access pattern lists it as legal.
- [ ] Existing strategy records and tests are unchanged; the new fields are documented.

## Comments
