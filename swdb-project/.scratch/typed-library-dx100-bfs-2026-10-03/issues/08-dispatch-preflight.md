# 08 — Dispatch preflight: disk and memory

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

**What to build:** Every mbit10 dispatch checks free disk and free memory first and records both, so a run never fills a shared disk or starves a shared memory node.

## Acceptance

- [ ] The preflight checks the disk that holds the runs folder: at least 20 GB free plus the planned raw bytes (the stage's storage budget for DX100 stages; 2 GiB for native evaluations, pairs and profiles).
- [ ] It never switches folders itself; when the runs folder is on the primary run disk and the check fails, the refusal names the secondary run folder if that disk would pass.
- [ ] It refuses unless the lane's memory node has the run's memory budget free (the stage's memory budget for DX100 stages; 4 GiB for native and profile dispatches).
- [ ] Disk, free bytes, memory node and free memory are recorded with the run.
- [ ] Native, profile and gem5 dispatches all use it; tests use fixture host observations (prior art: the storage tests).

## Comments
