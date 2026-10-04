# 54 — Extensa campaign budgets and pruning

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D2, D5, D7, D10)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 52 (08, 26 resolved)
**Spec:** `../spec.md`

**What to build:** An Extensa campaign cannot exhaust the shared host, the provider quota or the disk.

## Acceptance

- [ ] The loop stops at `max_iterations` (8), or after `plateau_iterations` (4) consecutive iterations in which no class's best improved in selection order. Each stop writes the matching `stop_reason`.
- [ ] A lane-hour cap (24) counts provider, certification and evaluator wall time. The loop stops before starting a step whose budgeted time would exceed the cap.
- [ ] Provider calls follow D7:
  - at most 3 counted calls per iteration and 1 setup call, with no carry-over;
  - each repair, test-generation and synthesis call is counted;
  - a usage-limit or login failure is recorded `counted: false`, pauses the campaign, releases the lane and retries the iteration after resume, without counting it as an iteration.
- [ ] A disk cap (20 GB) counts everything under `<runs root>/extensa/<campaign-id>/`. The dispatch preflight runs before every job.
- [ ] One lane per campaign unless the campaign file carries an approval for two. A native campaign's timed blocks refuse to start while the other socket's lease is held by a gem5 job of any Extensa campaign.
- [ ] Each Extensa-mode run's debug traces and checkpoint payloads are pruned right after its comparison, with a retention record, unless a team claim cites the run. Campaign records are never pruned.
- [ ] Fixture tests cover each stop reason and the uncounted pause.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).
