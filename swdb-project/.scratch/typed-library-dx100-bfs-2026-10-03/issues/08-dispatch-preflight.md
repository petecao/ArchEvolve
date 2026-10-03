# 08 — Dispatch preflight: disk and memory

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

**What to build:** Every mbit10 dispatch checks free disk and free memory first and records both, so a run never fills a shared disk or starves a shared memory node.

## Acceptance

- [x] The preflight checks the disk that holds the runs folder: at least 20 GB free plus the planned raw bytes (the stage's storage budget for DX100 stages; 2 GiB for native evaluations, pairs and profiles).
- [x] It never switches folders itself; when the runs folder is on the primary run disk and the check fails, the refusal names the secondary run folder if that disk would pass.
- [x] It refuses unless the lane's memory node has the run's memory budget free (the stage's memory budget for DX100 stages; 4 GiB for native and profile dispatches).
- [x] Disk, free bytes, memory node and free memory are recorded with the run.
- [x] Native, profile and gem5 dispatches all use it; tests use fixture host observations (prior art: the storage tests).

## Comments

Claimed and implemented by Codex retention/evaluator agent, 2026-10-03 ET.

## Answer

Implemented 2026-10-03 ET in `swdb/dispatch_preflight.py`, called before real mbit10 native evaluations, pairs, legacy/native profiles, DX100 build/compile/execute, and DX100 profiling. Receipts identify the selected run disk, free bytes, requested raw-byte budget, reserve, lane memory node and node-local MemFree. The 20 GB reserve is conservatively interpreted as 20 GiB. Failed primary-disk admission names the secondary run folder only when its observed capacity would pass; it never switches folders. Stage memory budgets remain binding, including when that makes a real dispatch wait.

Verification uses disposable fixture host observations: exact admission boundaries, wrong-node refusal, one-byte memory shortage, alternative-disk guidance, and explicit larger stage budgets. Focused collector/custody/read-only suite: 58 passed. Real remote admission and lane scheduling belong to the operator; fixture admission is not evidence that mbit10 currently has capacity.
