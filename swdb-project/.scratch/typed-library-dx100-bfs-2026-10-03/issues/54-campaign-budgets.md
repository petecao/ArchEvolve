# 54 — Extensa campaign budgets and pruning

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D2, D5, D7, D10)
**Type:** slice
**Status:** resolved
**Blocked by:** 52 (08, 26 resolved)
**Spec:** `../spec.md`

**What to build:** An Extensa campaign cannot exhaust the shared host, the provider quota or the disk.

## Acceptance

- [x] The loop stops at `max_iterations` (8), or after `plateau_iterations` (4) consecutive iterations in which no class's best improved in selection order. Each stop writes the matching `stop_reason`.
- [x] A lane-hour cap (24) counts provider, certification and evaluator wall time. The loop stops before starting a step whose budgeted time would exceed the cap.
- [x] Provider calls follow D7:
  - at most 3 counted calls per iteration and 1 setup call, with no carry-over;
  - each repair, test-generation and synthesis call is counted;
  - a usage-limit or login failure is recorded `counted: false`, pauses the campaign, releases the lane and retries the iteration after resume, without counting it as an iteration.
- [x] A disk cap (20 GB) counts everything under `<runs root>/extensa/<campaign-id>/`. The dispatch preflight runs before every job.
- [x] One lane per campaign unless the campaign file carries an approval for two. A native campaign's timed blocks refuse to start while the other socket's lease is held by a gem5 job of any Extensa campaign.
- [x] Each Extensa-mode run's debug traces and checkpoint payloads are pruned right after its comparison, with a retention record, unless a team claim cites the run. Campaign records are never pruned.
- [x] Fixture tests cover each stop reason and the uncounted pause.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).

## Answer

Resolved 2026-10-03 21:49 ET by the agent under Yan-Ru's standing implementation approval.

The logic is in `swdb/campaign.py` and the ported `swdb/extensa/search.py` (committed with tickets
49 and 52); this commit adds its tests.

- Stops: `max_iterations`; `plateau` after `plateau_iterations` consecutive completed iterations in
  which no class's best improved in selection order (higher level, or same level and higher lower
  bound); each stop writes its D6 `stop_reason` and a `stop_detail`.
- Lane-hours: provider, certification and evaluation wall time (or the adapter's declared step time)
  accumulate; a step whose budgeted time would exceed the cap is not started (`lane_hours`).
- Provider calls (D7): at most `provider_calls_per_iteration` counted calls per iteration and the
  setup allowance, no carry-over; repairs, test generation (once per contract per campaign) and
  synthesis are counted; a usage-limit or login failure is recorded `counted: false`, pauses the
  campaign, releases the lane, and the iteration is retried after `--resume` without counting as an
  iteration. Counted calls of paused attempts stay counted: when the campaign-wide total
  (setup + per-iteration x iterations, D7's 25) is spent, the next rewrite call stops the campaign
  with `provider_calls`.
- Disk: everything under `<runs root>/extensa/<campaign-id>/` counts against `disk_gb`, checked
  before every job, and `dispatch_preflight.check` runs before every job (a disk refusal stops with
  `disk`, others with `infrastructure_failure`).
- One lane unless the file carries `approval.two_lanes`; a native campaign's timed blocks refuse to
  start while the other socket's lease is held by a gem5 job of any Extensa campaign (stops with
  `infrastructure_failure`, naming that campaign).
- Pruning (ADR 0011): right after each comparison, debug traces and checkpoint payloads of its runs
  are deleted through `retention._delete` with a tagged retention record, unless a team claim (team
  or campaign store) cites the run. Campaign records are never pruned.
- `stopped_by_yanru`: a `STOP` file in the campaign folder (written by Yan-Ru) is honored before each
  iteration.

Tests: `tests/test_extensa_budgets.py` (9 cases): plateau, lane-hours, disk cap and preflight,
lane conflict, usage-limit pause/resume (uncounted, lane released, iteration retried), login pause,
the campaign-wide provider-call stop, `stopped_by_yanru`, pruning with a claimed run kept. With
tickets 52 and 53 every D6 stop reason and the uncounted pause are covered.

Assumptions (agent-decided, revisable):

- A lane conflict stops the campaign (`infrastructure_failure`) rather than waiting; Yan-Ru restarts
  it as a new campaign or after the gem5 job ends.
- `stopped_by_yanru` uses a `STOP` file; no stop command was specified.
- `max_repairs` defaults to 2 (D7's ArchEvolve-mode limit) when the campaign file omits it.
