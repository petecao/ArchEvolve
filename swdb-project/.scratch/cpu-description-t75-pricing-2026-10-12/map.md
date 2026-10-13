# Map: CPU target description that can price the t75 BFS pair

Created: 2026-10-12 00:42 ET. Spec: [spec.md](spec.md).

## Current state

- **Checkpoint (2026-10-12 21:55 ET):** tickets 01–09 resolved; both t75 `.a3` estimates are
  numeric (26.643 s / 20.770 s) and the unchecked attribution report has numeric shares and floor.
  Code-review fixes (F1–F7, [evidence/review-fixes.md](evidence/review-fixes.md)) are in
  `cpud/integration` `4324b546`. Integration branch `cpud/integration` (base `yanrujhou_main`).
- **Blocker:** none.
- **Next action:** ticket 10 (timing and split check) on **2026-10-13 ET or later** (both `.a3`
  estimates are dated 2026-10-12).

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
- Ticket 01 resolved (2026-10-12 05:40 ET, branch `cpud/01-trial-bind`): team-safe passes; t75 projections
  committed; the trial leaves 6 unknown regions per side, exactly the gaps tickets 02 and 04–07 cover
  (07 list confirmed, no free); projector pure-intrinsic fix ([answer](issues/01-team-safe-projections-trial-bind.md#answer)).
- Ticket 02 resolved (2026-10-12 01:23 ET): `memory_v2` = 1- and 2-byte writes at 8 MiB, run with `--group memory_v2` ([answer](issues/02-memory-v2-store-cells.md#answer)).
- Ticket 04 resolved (2026-10-12): `allocator_v2` with malloc/free, exact bins up to 32 MiB and `--cell`; ticket-07 command in [04 answer](issues/04-allocator-v2-malloc-large-bins.md#answer).
- Ticket 05 resolved (2026-10-12 01:40 ET): OpenMP set a2 adds class 22 `_8u`; ticket-07 command in [05 answer](issues/05-openmp-profiles-a2.md#answer).
- 06 resolved 2026-10-12 01:24 ET: `--service-group library_call` (7 paired services incl. `indirect-call`); t75 indirect call is the virtual `do_widen` after `_M_widen_init`; ticket-07 command in [06 answer](issues/06-library-call-and-indirect-call.md#answer).
- Ticket 07 resolved (2026-10-12 15:50 ET, branch `cpud/07-calibrations`): 8 records on mbit10 (node1 lane),
  whole store valid; ticket 08 binds `resource.memory-v2.a1`, `resource.allocator-v2.a1`, `service.openmp.a2`,
  `service.library-call.a1`, `resource.bulk-total.a3`; library-call pilot fix `f2d41156`; memmove 30 164 B bin is
  702 ns (noisy disjoint profile) ([answer](issues/07-calibration-runs-mbit10.md#answer), [runbook](evidence/07-calibrations/README.md)).
- Ticket 08 resolved (2026-10-12 17:55 ET, branch `cpud/08-09-bind-estimate`): `services.v2` bound on mbit10
  (sha256 `70fc5553…`), 6-member allowlist, 252 compatibility rows with 0 missing, floor-only 15 071 467 834 B/s;
  whole store `OK: 723`; `services.v1` unchanged ([answer](issues/08-bind-services-v2.md#answer), [runbook](evidence/08-bind/README.md)).
- Ticket 09 resolved (2026-10-12 21:55 ET, branch `cpud/08-09-bind-estimate`): `.a3` estimates 26.643 s (baseline) and
  20.770 s (candidate), 0 unknown regions, frozen and estimated at `c9f9df67`; attribution (F1 floor code, `4324b546`)
  rewritten 93.50%/91.67%, untouched 6.49%/8.33%, unattributed <0.002%, speedup 1.283x, floor 0.197/0.206 s;
  later estimate ended 2026-10-12 20:40 ET, so ticket 10 times on 2026-10-13 ET or later
  ([answer](issues/09-rerun-estimates.md#answer), [runbook](evidence/09-rerun-03/README.md)).

- Code-review fixes (2026-10-12 20:55 ET, branch `cpud/review-fixes`): F1 floor-only bandwidth numeric on
  `services.v2`; F2–F6, test-store fixes, T2 combined test; raw lane logs replaced by hashes
  ([review fixes](evidence/review-fixes.md), [raw logs](evidence/raw-logs.md)).

- Origin: fine-grained attribution tickets 03 and 09 closed negative
  ([03 answer](../fine-grained-attribution-2026-10-11/issues/03-first-real-pair.md#answer),
  [map](../fine-grained-attribution-2026-10-11/map.md)).
- `services.v1` build: analytic-eval ticket 11 and its runbook
  (`../lanl-db-analytic-eval-2026-10-06/evidence/11-native-model-band-runbook.md`).
