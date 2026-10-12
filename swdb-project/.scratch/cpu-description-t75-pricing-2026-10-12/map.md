# Map: CPU target description that can price the t75 BFS pair

Created: 2026-10-12 00:42 ET. Spec: [spec.md](spec.md).

## Current state

- **Checkpoint (2026-10-12 01:12 ET):** 10 tickets cut from the code map in [notes/](notes/index.md)
  (it records 10 places where the code differs from the spec; tickets 01, 03 and 05 record those decisions). Implementation on
  integration branch `cpud/integration` (base `yanrujhou_main`).
- **Blocker:** none.
- **Next action:** frontier 01–06 in parallel; 07 (mbit10 calibrations) after 01, 02, 04, 05, 06.

## Tickets

Graph: 01–06 start now → 07 (needs 01, 02, 04, 05, 06) → 08 (needs 03, 07) → 09 → 10.

| # | Ticket | Blocked by |
|---|---|---|
| 01 | [Team-safe, t75 OpenMP projections, trial bind](issues/01-team-safe-projections-trial-bind.md) | — |
| 02 | [1-/2-byte store cells (memory_v2)](issues/02-memory-v2-store-cells.md) | — |
| 03 | [Floor-only bandwidth rate](issues/03-floor-only-bandwidth-rate.md) | — |
| 04 | [Allocator v2: malloc, large bins](issues/04-allocator-v2-malloc-large-bins.md) | — |
| 05 | [OpenMP profile set a2 (`_8u`)](issues/05-openmp-profiles-a2.md) | — |
| 06 | [Library-call family, indirect-call](issues/06-library-call-and-indirect-call.md) | — |
| 07 | [Calibration runs on mbit10](issues/07-calibration-runs-mbit10.md) | 01, 02, 04, 05, 06 |
| 08 | [Bind `services.v2`](issues/08-bind-services-v2.md) | 03, 07 |
| 09 | [Rerun 03: estimates + attribute](issues/09-rerun-estimates.md) | 08 |
| 10 | [Rerun 09: timing + split check](issues/10-rerun-split-check.md) | 09 |

## Context pointers

- Ticket 03 resolved (2026-10-12 01:20 ET): floor-only rate field `resource_floor_mechanisms` ([answer](issues/03-floor-only-bandwidth-rate.md#answer)).
- Code map (2026-10-12 01:02 ET, `e2611242`): [notes/index.md](notes/index.md).
- Ticket 02 resolved (2026-10-12 01:23 ET): `memory_v2` = 1- and 2-byte writes at 8 MiB, run with `--group memory_v2` ([answer](issues/02-memory-v2-store-cells.md#answer)).
- Ticket 04 resolved (2026-10-12): `allocator_v2` with malloc/free, exact bins up to 32 MiB and `--cell`; ticket-07 command in [04 answer](issues/04-allocator-v2-malloc-large-bins.md#answer).

- Origin: fine-grained attribution tickets 03 and 09 closed negative
  ([03 answer](../fine-grained-attribution-2026-10-11/issues/03-first-real-pair.md#answer),
  [map](../fine-grained-attribution-2026-10-11/map.md)).
- `services.v1` build: analytic-eval ticket 11 and its runbook
  (`../lanl-db-analytic-eval-2026-10-06/evidence/11-native-model-band-runbook.md`).
