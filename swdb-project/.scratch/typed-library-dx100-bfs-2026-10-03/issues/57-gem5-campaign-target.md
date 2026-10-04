# 57 — gem5 Extensa campaign target

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D2, D4, D7)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 53, 54, 55 (29 resolved)
**Spec:** `../spec.md`
**Needs go-ahead:** Granted. Yan-Ru approved mbit10 dispatch on 2026-10-03. One campaign within its budgets is one dispatch (Q62), and actual lane admission and receipts are still required.

**What to build:** An Extensa campaign can run BFS on DX100 in gem5.

## Acceptance

- [ ] Campaign file `campaigns/extensa/extensa-gem5-bfs-<date>-a1.yaml` is committed. Its target is `dx100_gem5` and its baseline is the fork's scalar TDStep. Its classes use `bfs-20260928-kronecker18-s0.cf4283236c5cb50c` and `bfs-20260928-uniform18-s0.8c7e69dfa516e53c`, with source 0, 1 run, D5 default budgets, `regions: query` and allowed tiers shared and experimental.
- [ ] One gem5 baseline evaluation per class serves every candidate artifact, and comparisons are reported as point ratios.
- [ ] Each candidate artifact's DX100 session begin is checked to run inside the timed BFS call (`bfs.complete_call.v1`). A fixture where it runs outside is refused.
- [ ] The dispatch preflight admits each gem5 job against the lane's memory node (about 36 GiB per run) before it starts.
- [ ] The acceptance campaign finishes within its budgets on one socket lane. Its `campaign_summary` is complete and copied to the team store, and every result is labeled "single graph per class" and simulated.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).
