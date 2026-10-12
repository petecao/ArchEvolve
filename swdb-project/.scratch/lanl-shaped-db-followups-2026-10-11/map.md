# Map: follow-ups after the LANL-shaped database

Created: 2026-10-11 23:25 ET
**Type:** ticket map
**Status:** claimed (Yan-Ru asked to finish all three on 2026-10-11 23:20 ET)
**Parent:** [LANL-shaped-db map](../lanl-shaped-db-2026-10-09/map.md) (its 23:25 ET context pointer lists these)

| # | Ticket | Status | Blocked by | Time |
|---|---|---|---|---|
| 01 | [Restore the reviewed tier of the re-pinned DX100 read-offload contracts](issues/01-re-review-read-offload-contracts.md) | claimed | — | 1 h agent + Yan-Ru's review |
| 02 | [Run the full swdb suite on mbit10](issues/02-full-suite-on-mbit10.md) | claimed | — | 2–4 h |
| 03 | [Measured evaluation timings feed performance_runs](issues/03-evaluation-timings-in-performance-runs.md) | resolved | — | 2 h |

## Context pointers

- 2026-10-11 23:28 ET — 03 resolved on branch `lanl-followup/03-evaluation-timings`: finished
  measured native evaluations of an implementation now give one `performance_runs` row each
  (median of their trials); shared rule `swdb/lanl.py` `evaluated_implementation`. See the
  ticket's `## Answer`.
