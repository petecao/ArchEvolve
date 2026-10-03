# 34 — Per-line callgrind run on mbit10

Created: 2026-10-03
**Type:** task
**Status:** claimed
**Blocked by:** 08, 33
**Spec:** `../spec.md`
**Needs go-ahead:** Yes: Yan-Ru approves the mbit10 dispatch before it starts (Q62).

**What to build:** One real per-line profile of the scalar BFS exists on Kronecker 18.

## Acceptance

- [ ] The go-ahead and the run environment are recorded.
- [ ] The region profile with per-line data is committed after Yan-Ru approves.

## Comments

- 2026-10-03: Claimed by root for the authorized two-lane evaluation. Bounded public drivers are prepared; actual dispatch awaits source-sync approval, and gem5 additionally requires current promotion and sufficient lane-node memory. No result is inferred from preparation.

## Answer

Implementation/dispatch checkpoint, 2026-10-03 ET. Per-line TDStep collection and the bounded remote driver are ready. Actual Kronecker 18 profiling is blocked by the same configured-origin source export approval as ticket 27. The latest live host/preflight observations are in [evaluation plan](../evaluation-plan.md). No measured per-line profile is claimed. Monitoring continues every 30 minutes; a fresh lease/capacity/source read is required before dispatch.

2026-10-03 08:09 ET update: source export approval is cleared and source through `7561d88` is published. The review-spec agent owns this measurement together with ticket27 on node0 after synchronization. Current node0 memory admits the 8GiB profiling stage; fresh preflight and socket lease remain required. No measured result exists yet.
