# 54 — Extensa campaign budgets and pruning

Created: 2026-10-03
**Type:** slice
**Status:** needs-triage
**Blocked by:** 08, 26, 52
**Spec:** `../spec.md`

**What to build:** An Extensa campaign cannot exhaust the shared host, the provider quota or the disk.

## Acceptance

- [ ] At most 8 iterations; stop after 4 iterations in which no class's best improved in the selection order.
- [ ] A lane-hour cap (default 24) counts provider, certification and evaluator time.
- [ ] A provider-call budget (default 3 per iteration across all agent roles) applies; a usage limit or login failure pauses the Extensa campaign, releases the lane and does not count as an iteration.
- [ ] A disk cap (default 20 GB) and the dispatch preflight apply; one lane at a time unless Yan-Ru approves two; native timed repetitions never overlap a gem5 job of the same Extensa campaign.
- [ ] Extensa-mode runs have their bulky raw output pruned right after their comparison, unless a team claim cites them.

## Comments
