# 56 — Native-CPU Extensa campaign target for BFS

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D3, D4, D9)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 51, 53, 54, 55
**Spec:** `../spec.md`
**Needs go-ahead:** Granted. Yan-Ru approved mbit10 dispatch on 2026-10-03. One campaign within its budgets is one dispatch (Q62), and actual lane admission and receipts are still required.

**What to build:** An Extensa campaign can run BFS on native CPU.

## Acceptance

- [ ] A Kronecker scale-22 workload record is registered through the public workflow. It uses the DX100 GAPBS converter at `e4fc4afdf894f295442cef3604667a469fab8e62` with `-g 22 -k 16` and the same normalization as `bfs-20260925-kronecker18.48de8267ac2098d5`. The uniform class uses `bfs-20260925-uniform22.f23b09bb0c0601b5`.
- [ ] Campaign file `campaigns/extensa/extensa-native-bfs-<date>-a1.yaml` is committed. Its target is `native_cpu`, with `base_source: fork_scalar_tdstep` and both baselines. It uses D3's protocol, the D5 default budgets, `regions: query` and allowed tiers shared and experimental.
- [ ] The A/A pilot runs first on both graphs. If it stops with `baseline_unstable`, the summary is committed and a needs-info ticket proposes a new protocol for Yan-Ru, with no threshold change.
- [ ] Each candidate artifact is timed in its own paired blocks against both baselines, as separate comparisons. Selection uses the fork scalar TDStep comparison (Q61), and the upstream DO-BFS comparison is reported beside it.
- [ ] The acceptance campaign finishes within its budgets on one mbit10 socket lane through `socket_lane.sh`, with load and commit recorded. Its `campaign_summary` is complete and copied to the team store, and every result is labeled "single graph per class" and measured.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).
