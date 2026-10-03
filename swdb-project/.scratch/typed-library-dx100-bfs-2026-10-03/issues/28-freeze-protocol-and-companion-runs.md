# 28 — Freeze the new protocol, submit the patch, run the companion case

Created: 2026-10-03
**Type:** task
**Status:** ready-for-agent
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
