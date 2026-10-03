# 28 — Freeze the new protocol, submit the patch, run the companion case

Created: 2026-10-03
**Type:** task
**Status:** claimed
**Blocked by:** 08, 20, 22, 23, 26, 27
**Spec:** `../spec.md`
**Needs go-ahead:** Yes: Yan-Ru approves the mbit10 dispatch before it starts (Q62).

**What to build:** The new gem5 protocol is frozen, the certified patch becomes a candidate artifact, and the parent-gather race case settles L3 for this run.

## Acceptance

- [x] The pre-dispatch checks are recorded: socket leases, disk and memory preflight, host load, branch and commit (no rewrite provider runs, so provider logins are not checked).
- [x] The protocol has its own requested ID, version 1, no supersedes and no region pairs; copied fields (including builds and instrumentation) and changed fields follow the spec; the baseline is the full-source scalar implementation.
- [x] The patch is submitted against ticket 27's profile package; the candidate artifact's sha256 equals the certified tree's.
- [ ] The primary and the labeled diagnostic builds compile, and both companion runs finish on the T17 coverage workload.
- [ ] The L3 outcome is derived from the diagnostic run's evaluation record and written under Answer: observed on target (proceed); refuted (stop, set ticket 29 to needs-triage, triage ticket 31); or inconclusive (stop for diagnosis).

## Comments

Implementation support added 2026-10-03 ET: `tools/typed_library_gem5_driver.py` provides separate bounded `prepare` and `companion` stages, with no provider or remote dispatch. `prepare` takes `--profile-package`, `--id`, `--runs-dir`, and mandatory `--approval-reference`; it freezes an independent version-one protocol before submission, uses ticket 27's derived snapshot ID with the exact scalar-only bytes/protections, selects the newest passing certification for the current contract by `created_at`, requires the submitted tree to equal that receipt, and builds baseline primary plus candidate primary/diagnostic binaries. Prepare admits 4 GiB node-local memory and serial GCC uses a 4 GiB stage budget; companion/timed gem5 budgets retain the independently configured default 48 GiB.

Run `python tools/typed_library_gem5_driver.py --help` for the exact interface. Reuse the same fresh `--id` and explicit run root for each stage; a completed prepare receipt is required by companion. Both socket locks and the legacy lock, branch/commit, host observation, disk and node-local memory are recorded/checked. `progress.json` identifies the current bounded public command. Companion records its L3 outcome and admits timed work only after revalidation says observed. Five local request/admission tests pass; no target companion execution has happened. Actual acceptance remains pending.

- 2026-10-03: Claimed by root for the authorized two-lane evaluation. Bounded public drivers are prepared; actual dispatch awaits source-sync approval, and gem5 additionally requires current promotion and sufficient lane-node memory. No result is inferred from preparation.

## Answer

Implementation/dispatch checkpoint, 2026-10-03 ET. Preparation/companion drivers and exact current certification are ready. Real acceptance requires approved source synchronization, ticket 27 complete real package, ticket 22 human promotion, and admitted lane-node simulator memory. Latest node MemFree 26.4/15.7GiB does not meet the default 48GiB budget or the measured 32–34GiB simulator need plus headroom. No companion or L3 outcome has been produced. Monitoring continues every 30 minutes; a fresh lease/capacity/source read is required before dispatch.

- Current checkpoint, 2026-10-03 08:37 ET: source-sync/dispatch authorization and actual ticket22 promotion are complete. The remaining dependencies are a complete fresh real profile package and node-local simulator memory. Actual prior peaks32.18–32.64GiB support36GiB admission with headroom; best current node is30.18GiB. A legitimate new frozen memory configuration is being investigated; no threshold is weakened and no L3 outcome exists.

- 2026-10-03 08:43 ET: related source/dispatch authorization is complete; exact runtime f6972eb is synchronized and431 records validate. Claimed for the assigned real remote sequence. Node1 preparation will start only after the actual complete a2 package; companion remains gated on36GiB actual free memory.

- 2026-10-03 08:57 ET: actual prepare completed08:51 ET at runtimef6972eb on node1,4GiB admission. Protocol `typed-library-bfs-gem5-20261003-a1.protocol.8de9b516796360dc` is version1, no supersedes, no region pairs, with frozen T17 compiler/flags/adapter and16GB guest/MMIO treatment. Exact submitted tree equals certified tree `991de65287fe1fae3a20412704cccb6140a93f84cc11200032b20214f5174ff1`. Baseline primary, candidate primary and labeled candidate diagnostic actual builds all complete. Eight preparation metadata records/summary are published in8506be7. [Prepare summary](../evaluation/preparation-a1-summary.json).

- Companion and timed execution remain unrun; L3 is `not_run`, not refuted or observed. Actual prior RSS32.178–32.642GiB supports the explicit36GiB future budget; final free nodes30.075/22.646GiB do not admit it. No target gain is inferred from builds. [Memory audit](../evaluation/memory-admission-remediation-audit.json).

- 2026-10-03 ET: user questioned the MemFree-only block. Fresh selected-node inactive file counters show reclaimable capacity that the prior own-file inventory did not address. Corrected conservative local admission passes both reviews and39 affected tests, retaining36 GiB budget and16GB/MMIO target. Publication and fresh node0 lease/capacity read precede companion dispatch; no actual L3 or timing is inferred yet. [Clarification](../evaluation/memory-admission-clarification.md).
