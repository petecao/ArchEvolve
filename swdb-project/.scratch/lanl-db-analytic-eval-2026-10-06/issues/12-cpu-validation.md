# 12 — CPU validation: estimates against existing native mbit10 timings

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 05, 07, 08
**Spec:** `../spec.md`
**Time estimate:** 4–6 h

**What to build:** Estimate BFS and BC baselines and native candidates that already have native mbit10 evaluations, and report the error per kernel and workload class.

## Acceptance

- [ ] Uses only existing measured records; no gem5 data (D3).
- [ ] Error band per target class written where ticket 11's verdict reads it.
- [ ] Cases with large error get a per-region explanation from the report.
