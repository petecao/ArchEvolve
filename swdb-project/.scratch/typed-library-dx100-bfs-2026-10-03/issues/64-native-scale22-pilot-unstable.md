# 64 — Native scale-22 A/A pilot is unstable: protocol options

Created: 2026-10-04 10:50 ET (by ticket 56, campaign `extensa-native-bfs-20261004-a3`)
**Type:** decision
**Status:** needs-info
**Blocked by:** Yan-Ru's choice below
**Spec:** `../spec.md`; [design decisions](../extensa-design-2026-10-03.md) D3, D4; [61](61-native-scale22-protocol.md), [63](63-scalable-native-verifier.md)

**What to decide:** a new native protocol for the Extensa BFS campaign. D3's A/A gate stopped the campaign
with `baseline_unstable`. This ticket proposes options only; no threshold changes.

## Finding (2026-10-04)

Campaign `extensa-native-bfs-20261004-a3` ran under native evaluator v2 (ticket 63) on mbit10 node 1
(lease generation 517, 09:31-10:31 ET, load1 1.1-2.1, commit fd983a6). Summary:
`records/campaign_summaries/extensa-native-bfs-20261004-a3.summary.yaml`. D3 unchanged: 10 paired
repetitions, sources [0, 1234, 7777], 1 thread, `-O3`. It made no provider call and used 0.99 lane-hours.

Relative spread `(max - min) / median` per pilot block (baseline side / candidate side, per source 0, 1234, 7777):

| Class | Role | Spreads | Max |
|---|---|---|---|
| Kronecker 22 | fork scalar TDStep | 0.047 / 0.109, 0.106 / 0.071, 0.161 / 0.158 | **0.161** |
| Kronecker 22 | upstream DO-BFS | 0.006 / 0.006, 0.005 / 0.005, 0.012 / 0.006 | 0.012 |
| Uniform 22 | fork scalar TDStep | 0.024 / 0.051, 0.040 / 0.050, 0.039 / 0.057 | 0.057 |
| Uniform 22 | upstream DO-BFS | 0.134 / 0.004, 0.004 / 0.006, 0.008 / 0.009 | **0.134** |

Causes visible in the evaluations:

- **Source 7777 is isolated in `bfs-20261004-kronecker22`** (1 reachable vertex). Its ROI is only the
  parent-array initialization: about 49 or 58 ms, bimodal (campaign a2 shows the same: 48.8-58.3 ms). That
  bimodality alone gives spread 0.16. Ticket 56 registered D3's sources without a reachability check.
- The fork's scalar TDStep on Kronecker sources 0 and 1234 (about 0.70-0.77 s) spreads 0.05-0.11.
- Uniform upstream source 0: one slow baseline trial (0.134); the candidate side of the same block is 0.004.

## Options (agent proposal; Yan-Ru decides)

1. **Replace isolated sources.** Register a Kronecker 22 workload whose sources are reachable in the giant
   component by a fixed rule (for example the three lowest-numbered vertices with out-degree at least 1 and
   reachable from vertex 0), keep everything else in D3, and re-run the pilot. The fork Kronecker sources 0
   and 1234 (up to 0.109) may still exceed 0.1.
2. Option 1 plus **a fixed host condition**: run native blocks only when the other socket is idle, and
   record it. The single upstream outlier suggests interference.
3. **A robust spread statistic** in a new protocol version (for example an interquantile spread). This
   changes what the 0.1 gate measures, so it is Yan-Ru's call.

Agent recommendation: option 1 first (it removes a defect in the workload, not in the gate), then decide
on 2 or 3 from that pilot.
