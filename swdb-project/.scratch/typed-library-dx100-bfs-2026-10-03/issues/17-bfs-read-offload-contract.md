# 17 — BFS read-offload rewrite contract and the YAML draft for Peter

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 06, 10
**Spec:** `../spec.md`

**What to build:** The BFS read-offload rewrite contract exists as a library entry, and a contract YAML draft for Peter is ready.

## Acceptance

- [ ] Provenance cites Peter's v1.1 §5, Josh's hardware-candidate package and Eric's claims; the pattern key uses pattern classes with arrays named by role; the contract realizes the DX100 read-offload strategy from ticket 06.
- [ ] Legality clauses L1–L5 with discharge modes, the runtime guards, knobs with enforced ranges, the preservation obligation and the execution-witness rules are present.
- [ ] Josh's requirement map is keyed on hardware-candidate ID, operation ID and requirement ID.
- [ ] The eight rewrite negative controls are listed and mapped to Extensa's three mandatory kinds; the L3 outcome rule and fallback are recorded.
- [ ] The contract YAML for Peter is drafted for Yan-Ru to send; it notes that the vertex- and edge-count guards are both one higher than his §5 code, matching his §4 and Josh's byte-offset requirement.
- [ ] `swdb validate` passes.

## Comments
