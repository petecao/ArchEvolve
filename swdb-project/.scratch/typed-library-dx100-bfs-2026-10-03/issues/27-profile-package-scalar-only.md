# 27 — Real profile package for the scalar-only snapshot on mbit10

Created: 2026-10-03
**Type:** task
**Status:** needs-info
**Blocked by:** 05, 08
**Spec:** `../spec.md`
**Needs go-ahead:** Yes: Yan-Ru approves the mbit10 dispatch before it starts (Q62).

**What to build:** A complete, real profile package exists for the scalar-only DX100 snapshot, so the first submission rests on real profile evidence.

## Acceptance

- [ ] The go-ahead, leases, preflight, host load, branch and commit are recorded.
- [ ] A native evaluation and a region profile run for the scalar-only snapshot, and the profile package assembles as complete.
- [ ] The records are committed after Yan-Ru approves.

## Comments

- 2026-10-03: Claimed by root for the authorized two-lane evaluation. Bounded public drivers are prepared; actual dispatch awaits source-sync approval, and gem5 additionally requires current promotion and sufficient lane-node memory. No result is inferred from preparation.

## Answer

Implementation/dispatch checkpoint, 2026-10-03 ET. The bounded scalar native/profile driver is ready and dispatch is authorized by Yan-Ru ticket 1–37 request. Real execution is blocked by source export approval: automatic approval review rejected git push origin yanrujhou_main to git@github.com:petecao/ArchEvolve.git because destination authorization was not established. The existing repository/branch approval question is pending. No source export workaround or real profile exists. Monitoring continues every 30 minutes; a fresh lease/capacity/source read is required before dispatch.
