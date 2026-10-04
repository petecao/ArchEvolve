# 56 — Native-CPU Extensa campaign target for BFS

Created: 2026-10-03
Updated: 2026-10-04 12:15 ET (campaign a4, Answer update); 2026-10-04 10:55 ET (evaluator v2 pilot, Answer update); 2026-10-04 ET (resolved); 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D3, D4, D9)
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

### Update 2026-10-04 10:55 ET: A/A pilot under native evaluator v2 (tickets 61, 63)

Ticket 61 was decided as option 1 (agent-decided under Yan-Ru's 2026-10-04 delegation; revisable) and
implemented in ticket 63: native evaluator `swdb.native.evaluator.scalable.v2` with the compiled verifier
`swdb.bfs.structural.compiled.v2`. D3/D4 are unchanged. Run on mbit10 from the clone
`/data1/yanruj/ArchEvolve-native` (git bundles, not pushed), runs root `/data/yanruj/EvolveSWDB_runs`
(`/data1` had 40 GB free), node 1 through `socket_lane.sh` (Memacc checkout current with its origin), each
time with `--baselines-only` so no provider call could run before the shared Codex login has a session lock.

- `extensa-native-bfs-20261004-a2` (generation 516, 09:08 ET, commit 36e7544): first pilot block passed
  correctness on every trial; it stopped with `infrastructure_failure` at the upstream A/A block ("actual
  build differs from frozen settings"). Ticket 56's adapter timed the upstream baseline as the candidate side
  of a protocol whose candidate build is the DX100 fork's. Fixed in fd983a6: roles whose builds differ get
  an A/A protocol `<campaign>.protocol.<role>.aa` with the baseline build on both sides.
- `extensa-native-bfs-20261004-a3` (generation 517, 09:31-10:31 ET, load1 1.1-2.1, commit fd983a6): all four
  pilot blocks completed, every trial verified by the compiled verifier. Stop reason **`baseline_unstable`**.
  Max spread per class and role: Kronecker fork 0.161, Kronecker upstream 0.012, uniform fork 0.057, uniform
  upstream 0.134. 0 provider calls, 0.99 lane-hours, 2.36 GB peak disk. Summary
  `records/campaign_summaries/extensa-native-bfs-20261004-a3.summary.yaml` (a2's beside it).
- Main cause found: source 7777 is isolated in the Kronecker 22 graph; its ROI is only initialization,
  bimodal at about 49 or 58 ms. Per D3, no threshold changed; the protocol follow-up is needs-info ticket
  [64](64-native-scale22-pilot-unstable.md).

No candidate was timed, so there is no verdict per class ("single graph per class", measured: not reached).

### Update 2026-10-04 12:15 ET: campaign a4 (ticket 64 workloads, per-class gate)

Ticket 64 (agent-decided under Yan-Ru's delegation; revisable; 0.1 threshold unchanged) re-registered both
scale-22 workloads with the recorded source policy (Kronecker sources 0, 1234, 7778; 7777 had out-degree 0;
uniform unchanged), made the A/A gate per class, and admitted native blocks beside another campaign's gem5 job
when the campaign file approves it (`approval.gem5_other_socket`, other socket recorded per block).

`extensa-native-bfs-20261004-a4` ran at full scope (provider calls allowed through the Codex session lock) on
node 1 (lease generation 522, 10:59-12:01 ET, load1 1.8-3.6, commit 67c671c) while gem5 campaign
`extensa-gem5-bfs-20261004-a7` held node 0 (recorded for every pilot block). Every trial passed the compiled
verifier. Pilot max spread per class and role:

| Class | Fork scalar TDStep | Upstream DO-BFS | Class result |
|---|---|---|---|
| Kronecker 22 (sources 0/1234/7778) | 0.225 | 0.153 | baseline_unstable |
| Uniform 22 (sources 0/1234/7777) | 0.147 | 0.014 | baseline_unstable |

Both classes failed, so the campaign stopped with **`baseline_unstable`**: 0 iterations, 0 provider calls,
1.04 lane-hours, 2.68 GB peak disk. Summary `records/campaign_summaries/extensa-native-bfs-20261004-a4.summary.yaml`.
No candidate was timed, so no class has a verdict about a candidate ("single graph per class", measured: not reached).

What the per-repetition data show (no trial removed): upstream DO-BFS switches between two regimes about 15%
apart (Kronecker 157.8 / 134.6 ms; uniform 143.5 / 125.1 ms in ticket 64's diagnostics). In a4 the uniform
upstream blocks stayed in one regime (0.014), while the Kronecker upstream blocks switched (0.15); in a3 it was
the reverse. The fork baseline (0.7-1.5 s ROI) spreads 0.05-0.22 without a clear regime. a4 ran beside the a7
gem5 job and a3 partly did; whether the other socket's work drives the regimes is untested. Pinning and membind
are already in force, and no further legitimate control is available without counters or frequency control
(ticket 64). Re-running in the hope of a quieter host would select on the outcome, so no further attempt was
made; a protocol change is Yan-Ru's.
