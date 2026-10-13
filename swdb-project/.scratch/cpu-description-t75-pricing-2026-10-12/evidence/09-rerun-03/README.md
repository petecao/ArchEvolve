# Ticket 09 runbook: t75 estimates and attribution with services.v2

Updated: 2026-10-12 ET. Branch `cpud/08-09-bind-estimate`. Raw root (deleted after export, LR-06):
`/data/yanruj/EvolveSWDB_runs/cpud0809-20261012-a1/`.

## Order (all ET, from `order.log`)

| Step | Start → end | Commit |
|---|---|---|
| Freeze baseline `.a3` protocol | 17:56 → 18:51 | `c9f9df67` |
| Freeze candidate `.a3` protocol | 18:51 → 19:46 | `c9f9df67` |
| Estimate baseline `.a3` | 19:46 → 20:13 | `c9f9df67` |
| Estimate candidate `.a3` | **20:13 → 20:40:38** | `c9f9df67` |
| Unknowns summary | 20:40 → 20:41 | `c9f9df67` |
| `swdb attribute` (first run, pre-F1 floor) | 20:40 → 21:01 | `c9f9df67` |
| Whole-store validate | 21:01 → 21:15 | `c9f9df67` |
| `swdb attribute` (record of this ticket, F1 floor fix) | 21:16 → 21:37 | `4324b546` |
| Whole-store validate | 21:37 → 21:51 | `4324b546` |

Both whole-store checks: `OK: 728 record(s) valid` (`validate-whole-09.txt`, `validate-whole-09b.txt`).

- `c9f9df67` = the pushed `cpud/integration` commit that holds `services.v2` (ticket 08).
  Both protocols were frozen there, one after the other in one lane job (F47), and both
  estimates ran there. Both estimates share `estimator_sha256` `fcc40da1…`.
- No application ran. Workload `bfs-20261004-uniform22` was not timed (C12). Ticket 10 must time
  on **2026-10-13 ET or later** (F43 compares the ET calendar date; both estimates say `2026-10-12`).

## Why two attribute runs

The first run (`first-attribute-c9f9df67/`, kept only as evidence) had numeric shares but an
unknown resource floor in 9 regions per side, including the two hot `TDStep` regions:
`access.N.streaming_classification`. The floor ran `streaming_bandwidth` with the estimator's
coverage rule, and `services.v2` has no `cache_fit`/latency model to cover indirect accesses.
Review fix F1 (`bf21f94d`, on `cpud/integration` `4324b546`) lets `memory_service_scenario` cover
them for floor-only rates. The second run used that code on the same saved estimates (it changes
neither estimates nor shares; `attribute` only needs the two estimates to share `estimator_sha256`).
That report is the committed record. Shares and seconds are identical in both runs.

## Records (copied byte-for-byte from the mbit10 store; sha256 checked)

See `mbit10-sha256-09.txt` and `mbit10-sha256-09b.txt`.

- `records/protocols/fga03.t75-baseline.uniform22.t1.estimate.protocol.a3.badeda2d2d43b04b.yaml`
- `records/protocols/fga03.t75-candidate.uniform22.t1.estimate.protocol.a3.40eae3eb40b5a110.yaml`
- `records/estimates/fga03.t75-baseline.uniform22.t1.estimate.a3.yaml`
- `records/estimates/fga03.t75-candidate.uniform22.t1.estimate.a3.yaml`
- `records/attributions/fga03.t75.uniform22.t1.attribution.a3.yaml`

## Scripts and inputs

- `job-09.sh`: protocol requests (ticket-03 `freeze-*.yaml` with `id … .a3` and
  `target_description: …services.v2`; saved as `freeze-*.a3.yaml`), freeze, estimate, summary,
  attribute, validate. `job-09b.sh`: the second attribute and validate.
- Both ran through `../08-bind/when-free.sh` → `socket_lane.sh` in the node0 lane
  (`lane-09.json`, `lane-09b.json`). Host snapshots: `env-09*.txt`. Step times and peak RSS:
  `step-times.txt`.
- Unknowns summary: `unknowns-summary-a3.json` (ticket 01's parameterized script): 0 unknown
  regions on both sides.
