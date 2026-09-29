# 08 — Landlock guard for real providers

Created: 2026-09-29
**Type:** slice
**Status:** claimed
**Blocked by:** 02, 06
**Spec:** `../spec.md`

**What to build:** On Linux, real Codex and Claude sessions run in workspace mode inside an SWDB-owned
Landlock guard: reads limited to the workspace, the toolchain, the provider's install
directory, and the per-run home; writes limited to the workspace and the per-run home; TCP
only to port 443; an inner layer with no TCP for each tool command; and the session limits
(16 threads, 32 GB, 120 s per command, 5 GB workspace). The guard's policy is recorded with
each attempt.

## Acceptance

- [ ] Linux-only tests through `swdb submit` on mbit10: the fixture's forbidden read, forbidden write, and TCP connection are each blocked and reported, and a connection on an allowed port succeeds.
- [ ] The resource limits apply, and the full guard policy appears in the attempt's record.
- [ ] Real kinds run in workspace mode only under the guard; where the guard cannot run, they refuse.
- [ ] Tests run inside a socket lane.
