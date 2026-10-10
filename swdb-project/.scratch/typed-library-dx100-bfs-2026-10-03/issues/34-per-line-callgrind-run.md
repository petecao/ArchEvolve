# 34 — Per-line callgrind run on mbit10

Created: 2026-10-03
**Type:** task
**Status:** resolved
**Blocked by:** 08, 33
**Spec:** `../spec.md`
**Needs go-ahead:** Yes: Yan-Ru approves the mbit10 dispatch before it starts (Q62).

**What to build:** One real per-line profile of the scalar BFS exists on Kronecker 18.

## Acceptance

- [x] The go-ahead and the run environment are recorded.
- [x] The region profile with per-line data is committed after Yan-Ru approves.

## Comments

- 2026-10-03: Claimed by root for the authorized two-lane evaluation. Bounded public drivers are prepared; actual dispatch awaits source-sync approval, and gem5 additionally requires current promotion and sufficient lane-node memory. No result is inferred from preparation.

## Answer

Historical initial checkpoint, superseded by actual execution below: 2026-10-03 ET. Per-line TDStep collection and the bounded remote driver are ready. Actual Kronecker 18 profiling is blocked by the same configured-origin source export approval as ticket 27. The latest live host/preflight observations are in [evaluation plan](../evaluation-plan.md). No measured per-line profile is claimed. Monitoring continues every 30 minutes; a fresh lease/capacity/source read is required before dispatch.

2026-10-03 08:09 ET update: source export approval is cleared and source through `7561d88` is published. The review-spec agent owns this measurement together with ticket27 on node0 after synchronization. Current node0 memory admits the 8GiB profiling stage; fresh preflight and socket lease remain required. No measured result exists yet.

- 2026-10-03 08:40 ET: real a1 native correctness passed, but the per-line profile remained partial and the driver failed; no complete package exists. Failed raw and compact metadata are retained in010bec7. The continuous complete-BFS/single-dump collector correction passed58 affected tests twice and independent Standards/Spec review. Fresh a2 is authorized after exact source publication/synchronization; only its actual validated evidence can resolve this ticket.

## Actual execution checkpoint

2026-10-03 08:51 ET: fresh a2 public driver completed at08:47 ET under synchronized runtime `f6972ebbf9c842c1a7091716505577d06c637231`. Native evaluation `typed-library-bfs-scalar-profile-20261003-a2.native` is complete with correctness passed. Complete package `typed-library-bfs-scalar-profile-20261003-a2.package.v1.619546ae9c6f60fe` contains23 regions,31 validated TDStep/outlined-worker per-line rows, and7 mapped statement costs. Root independently read back exact package/driver/native/source identities and the single `dump_position:0` coordinates; strict counter checks remain unchanged.

The region profile remains labeled partial for bounded source attribution, as required by its coverage limits. Per-line costs have simulated basis and whole-call cache history; zero mapped-line misses and an absent queue-append debug row do not prove zero semantic/native cost. No gain is claimed. Failed a1 raw and metadata remain preserved. Raw a2 resides only on mbit10; [compact execution summary](../evaluation/profile-a2-success-summary.json) and public YAML records will be exported through Git after both current remote jobs stop. Actual execution acceptance passes; final ticket closure waits the required Git publication of these records after both remote jobs stop.

- 2026-10-03 08:57 ET: required record publication is complete in `8506be73d9e44cbd783e50c977b111f171588a1d`, pushed from mbit10 and read back locally through Git. Independent raw/package/source/binary audit passed; all443 records validate remotely. Ticket resolved with execution and publication acceptance fulfilled.
