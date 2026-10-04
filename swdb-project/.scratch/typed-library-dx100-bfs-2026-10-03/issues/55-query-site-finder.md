# 55 — Query site finder

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md))
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 46, 52
**Spec:** `../spec.md`

**What to build:** Regions are chosen by a repeatable query instead of a fixed list.

## Acceptance

- [ ] With `regions: query` in the campaign file, `swdb campaign` selects regions by one SQL query over the SQLite access-pattern and step tables, the statements index and the indexed contract pattern keys (all from ticket 46). It never reads library YAML.
- [ ] Results are deterministic: the same database gives the same ordered region list, and the query text's sha256 is recorded in the summary.
- [ ] Each chosen region records why it was chosen: the matched pattern key, the statement IDs, and the contract and entry IDs.
- [ ] A contract applies only when its pattern key matches and every legality clause holds on the region's recorded facts. A clause with no recorded fact counts as not holding, and the reason is recorded.
- [ ] Fixture tests on BFS TDStep select the read-offload region for a gem5 campaign and the library-operation regions (ticket 51 pattern keys) for a native campaign.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).
