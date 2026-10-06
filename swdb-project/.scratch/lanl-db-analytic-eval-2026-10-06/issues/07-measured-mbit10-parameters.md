# 07 — Measured mbit10 parameters

Created: 2026-10-06
**Type:** slice
**Status:** claimed
**Blocked by:** 04
**Spec:** `../spec.md`
**Time estimate:** 2–3 h plus about 1 h of lane time (mbit10)

**What to build:** Microbenchmarks measure effective bandwidth per access type and requests in flight per thread on mbit10, inside a socket lane. The results become a new mbit10 target-description version with basis `measured`, and the fixture estimate re-runs with it.

## Acceptance

- [ ] The two-lane procedure is followed: leases checked, socket-lane entry, load and commit recorded.
- [ ] Free disk is checked first; raw output stays in the runs folder, never in git.
- [ ] Values carry repetitions and spread.
- [ ] The re-run estimate cites the new description version's hash.

## Comments

2026-10-06 ET: Claimed on `codex/lanl-ticket07`, based exactly on integration `86b2a9a`. Public seams: CPU measurement runner and calibration import/target-description commands; copied-store fixture checks. Parent owns mbit10 dispatch; real receipts and hash-bound estimate rerun are required for resolution.
