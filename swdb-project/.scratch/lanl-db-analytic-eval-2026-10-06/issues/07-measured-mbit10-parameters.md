# 07 — Measured mbit10 parameters

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 04
**Spec:** `../spec.md`
**Time estimate:** 2–3 h plus about 1 h of lane time (mbit10)

**What to build:** Microbenchmarks measure effective bandwidth per access type and requests in flight per thread on mbit10, inside a socket lane. The results become a new mbit10 target-description version with basis `measured`, and the fixture estimate re-runs with it.

## Acceptance

- [ ] The two-lane procedure is followed: leases checked, socket-lane entry, load and commit recorded.
- [ ] Free disk is checked first; raw output stays in the runs folder, never in git.
- [ ] Values carry repetitions and spread.
- [ ] The re-run estimate cites the new description version's hash.
