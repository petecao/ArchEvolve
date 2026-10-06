# 15 — Agreement report from flow-A campaigns

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 14
**Spec:** `../spec.md`
**Time estimate:** 3–4 h plus campaign lane time

**What to build:** After one or two flow-A campaigns: rank agreement between estimate and timing, how often the best timed candidate would survive a top-k cut by estimate, and where estimates go wrong. Calibrating a research variant of the estimator is allowed (D10).

## Acceptance

- [ ] Agreement per target and workload class, with the number of candidates behind it.
- [ ] Research variant, if any, versioned separately and refused by ticket 10's guard in team protocols.
- [ ] The pre-registered rule (D30) applied as written: at least 20 DX100 candidates with an estimate and a gem5 time; Kendall's tau at least 0.6 with its 95% interval's lower bound at least 0.3; gem5's best candidate inside the estimate's top 3 in every campaign.
- [ ] Estimates were made blind (D26): each estimate's time precedes its candidate's timing.
- [ ] A short recommendation for ticket 16.
