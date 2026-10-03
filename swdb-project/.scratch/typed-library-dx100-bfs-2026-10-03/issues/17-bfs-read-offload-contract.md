# 17 — BFS read-offload rewrite contract and the YAML draft for Peter

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 06, 10
**Spec:** `../spec.md`

**What to build:** The BFS read-offload rewrite contract exists as a library entry, and a contract YAML draft for Peter is ready.

## Acceptance

- [x] Provenance cites Peter's v1.1 §5, Josh's hardware-candidate package and Eric's claims; the pattern key uses pattern classes with arrays named by role; the contract realizes the DX100 read-offload strategy from ticket 06.
- [x] Legality clauses L1–L5 with discharge modes, the runtime guards, knobs with enforced ranges, the preservation obligation and the execution-witness rules are present.
- [x] Josh's requirement map is keyed on hardware-candidate ID, operation ID and requirement ID.
- [x] The eight rewrite negative controls are listed and mapped to Extensa's three mandatory kinds; the L3 outcome rule and fallback are recorded.
- [x] The contract YAML for Peter is drafted for Yan-Ru to send; it notes that the vertex- and edge-count guards are both one higher than his §5 code, matching his §4 and Josh's byte-offset requirement.
- [x] `swdb validate` passes.

## Comments

- 2026-10-03: Claimed by root for the authorized implementation batch. ADRs remain proposed; human send/review receipts are not inferred.

## Answer

The BFS contract pins Peter v1.1, Josh package and catalog provenance, L1–L5/E1–E5, guards, legality knobs, CPU preservation, nine requirement mappings and controls. Current candidate certification passes10cells/rejects16controls; L3/L5 remain target assumptions. YAML is ready for ticket21.

Validation: current library/record validation passes379 records; focused library/strategy tests49passed; full suite and final two-axis review remain batch closeout gates.
