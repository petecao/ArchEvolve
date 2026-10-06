# 07 — mbit10 microbenchmarks: effective bandwidth by access shape

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 06
**Spec:** `../spec.md`
**Time estimate:** 2–3 h plus about 1 h of lane time

**What to build:** Measure effective bandwidth on mbit10 for stream, strided and indirect-gather reads (and the write kinds BFS uses), inside a socket lane, and add the results to the mbit10 target description with basis `measured`.

## Acceptance

- [ ] Runs through the two-lane procedure (lease check, `socket_lane.sh`, load recorded, commit recorded).
- [ ] `df -h /data1 /data` checked first; raw output under the runs folder, never in git.
- [ ] Values with repetitions and spread written to the description; requests in flight per thread derived from the gather results.
