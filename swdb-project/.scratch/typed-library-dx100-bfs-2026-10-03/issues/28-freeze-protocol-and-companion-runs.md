# 28 — Freeze the new protocol, submit the patch, run the companion case

Created: 2026-10-03
**Type:** task
**Status:** claimed
**Blocked by:** 08, 20, 22, 23, 26, 27
**Spec:** `../spec.md`
**Needs go-ahead:** Yes: Yan-Ru approves the mbit10 dispatch before it starts (Q62).

**What to build:** The new gem5 protocol is frozen, the certified patch becomes a candidate artifact, and the parent-gather race case settles L3 for this run.

## Acceptance

- [ ] The pre-dispatch checks are recorded: socket leases, disk and memory preflight, host load, branch and commit (no rewrite provider runs, so provider logins are not checked).
- [ ] The protocol has its own requested ID, version 1, no supersedes and no region pairs; copied fields (including builds and instrumentation) and changed fields follow the spec; the baseline is the full-source scalar implementation.
- [ ] The patch is submitted against ticket 27's profile package; the candidate artifact's sha256 equals the certified tree's.
- [ ] The primary and the labeled diagnostic builds compile, and both companion runs finish on the T17 coverage workload.
- [ ] The L3 outcome is derived from the diagnostic run's evaluation record and written under Answer: observed on target (proceed); refuted (stop, set ticket 29 to needs-triage, triage ticket 31); or inconclusive (stop for diagnosis).

## Comments

Implementation support added 2026-10-03 ET: `tools/typed_library_gem5_driver.py` provides separate bounded `prepare` and `companion` stages, with no provider or remote dispatch. `prepare` takes `--profile-package`, `--id`, `--runs-dir`, and mandatory `--approval-reference`; it freezes an independent version-one protocol before submission, uses ticket 27's derived snapshot ID with the exact scalar-only bytes/protections, selects the newest passing certification for the current contract by `created_at`, requires the submitted tree to equal that receipt, and builds baseline primary plus candidate primary/diagnostic binaries. Prepare admits 4 GiB node-local memory and serial GCC uses a 4 GiB stage budget; companion/timed gem5 budgets retain the independently configured default 48 GiB.

Run `python tools/typed_library_gem5_driver.py --help` for the exact interface. Reuse the same fresh `--id` and explicit run root for each stage; a completed prepare receipt is required by companion. Both socket locks and the legacy lock, branch/commit, host observation, disk and node-local memory are recorded/checked. `progress.json` identifies the current bounded public command. Companion records its L3 outcome and admits timed work only after revalidation says observed. Five local request/admission tests pass; no target companion execution has happened. Actual acceptance remains pending.

- 2026-10-03: Claimed by root for the authorized two-lane evaluation. Bounded public drivers are prepared; actual dispatch awaits source-sync approval, and gem5 additionally requires current promotion and sufficient lane-node memory. No result is inferred from preparation.
