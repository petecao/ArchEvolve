# 56 — Native-CPU Extensa campaign target for BFS

Created: 2026-10-03
Updated: 2026-10-04 ET (resolved); 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D3, D4, D9)
**Type:** slice
**Status:** resolved
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

## Answer

Resolved 2026-10-04 06:05 ET by the agent under Yan-Ru's 2026-10-03 mbit10 dispatch approval (Q62).
The native protocol itself is blocked: follow-up [61](61-native-scale22-protocol.md) (needs-info).

**Built (Mac).** `swdb/campaign_targets.py` `NativeAdapter`, selected by `swdb campaign` when the target
is `native_cpu` and no `--fixture` is given:
- One frozen native protocol per baseline role (`<campaign>.protocol.fork_scalar_tdstep`,
  `.upstream_do_bfs`); a frozen protocol names one baseline build (dx100_scalar_func vs gapbs_native).
  D3 flags, 10 repetitions, sources [0, 1234, 7777], 1 thread, lane frozen from the verified lane.
- A/A pilot: each baseline timed against itself on each class (`swdb evaluate-pair`, then
  `compare-evaluations`); any spread above 0.1 stops with `baseline_unstable`.
- Each candidate artifact gets its own paired block against each baseline, compared separately;
  selection uses the `base_source` (fork scalar TDStep) comparison, upstream reported beside it (Q61).
- Candidate artifacts: scalar-only snapshot `bfs-dx100-scalar-only-20260929-a1.source` plus the
  provider patch (`git apply --recount`), class knobs as `SWDB_KNOB_*` defines, protections checked,
  a tagged proposal and candidate record. Child commands inherit the campaign tags
  (`SWDB_EXTENSA_CAMPAIGN`, `swdb/workflow.py`).
- Native timed blocks refuse while the other socket's lease is held by an Extensa gem5 job (marker
  under `<runs root>/extensa/active-lanes/`).
- Tests: `tests/test_extensa_targets.py` (native: two protocols, four separate paired blocks, fork
  selection with upstream beside it, pilot stop with zero calls, scale-22 stop, lane conflict).

**Run (mbit10, separate clones `/data1/yanruj/ArchEvolve-extensa{,-native}`, git bundles, not pushed).**
- Workloads (node 1, lease generation 510, 02:44-02:47 ET, load1 2.02):
  `bfs-20261004-kronecker22.3dc69be403db57e9` (converter e4fc4af, `-g 22 -k 16`, sources 0/1234/7777)
  and `bfs-20261004-uniform22.facb16e6260c3a82` (the f23b09bb graph files with D3's sources; f23b09bb
  registers source 2796003 only, which D3's protocol cannot use).
- Campaign `extensa-native-bfs-20261004-a1` (node 1, generation 511, 02:48 ET, load1 2.57): stopped at
  setup, `infrastructure_failure`: the scale-22 graphs exceed the native evaluator's materialization
  limits (2 M vertices, 32 M directed edges). No pilot block, no provider call, 0 lane-hours.
  Summary `records/campaign_summaries/extensa-native-bfs-20261004-a1.summary.yaml` (team store).

**Assumptions (agent-decided, revisable).** One protocol per baseline role (not one per campaign);
the uniform class uses a new three-source registration of the same graph; the campaign stops rather
than raising the evaluator's limits (an evaluator change is Yan-Ru's call, ticket 61).
