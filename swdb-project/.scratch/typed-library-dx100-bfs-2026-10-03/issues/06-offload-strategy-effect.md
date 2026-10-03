# 06 — Prefactor: offload strategy effect and the DX100 read-offload strategy

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** The offload strategy effect works in records and strategy queries, and a DX100 read-offload strategy exists for the BFS rewrite contract to realize.

## Acceptance

- [x] Offload is a strategy-effect value with typed fields: the access-pattern steps moved off the core and the hardware-operation record IDs they move to.
- [x] Strategy legality rules accept offload for access-pattern targets.
- [x] A DX100 read-offload strategy record exists and validates.
- [x] `swdb strategies --pattern` on the BFS neighbor-read access pattern lists it as legal.
- [x] Existing strategy records and tests are unchanged; the new fields are documented.

## Comments

- 2026-10-03: Claimed by root for the authorized implementation batch. ADRs remain proposed; human send/review receipts are not inferred.

## Answer

The offload effect selects exact access-pattern step positions and hardware-operation IDs. The DX100 read-offload strategy records unchecked contract conditions; existing exact seed assertions include the new strategy.

Validation: current library/record validation passes379 records; focused library/strategy tests49passed; full suite and final two-axis review remain batch closeout gates.
