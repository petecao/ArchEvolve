# Ticket 08 runbook: bind services.v2 on mbit10

Updated: 2026-10-12 ET. Branch `cpud/08-09-bind-estimate`. Raw root (deleted after export, LR-06):
`/data/yanruj/EvolveSWDB_runs/cpud0809-20261012-a1/`.

## Result

| Record | File sha256 |
|---|---|
| `records/target_descriptions/mbit10.cpu.lanl20261006.t1.services.v2.yaml` (new) | `70fc555390552fad5c150e53d9ff9ecc9d3262a1a8d3f9eb908aab7b10e4b66a` |
| `records/target_descriptions/mbit10.cpu.lanl20261006.t1.services.v1.yaml` (unchanged, `cmp` equal) | `cee03869aa2ab624d0eb1ef54b8807603d2a222d749113c7d65d847549c45c6d` |

- `version` (digest of the binding evidence): `c55908ad94e16556f42de1b092b4a9c1096b37d576d60b9453c1126c04959170`.
- Allowlist: 6 members (four gapbs g16/g17 counts, then the two t75 `…characterization.a2` counts), each `{id, sha256}`.
- 14 calibrations; 252 compatibility rows, **0 with a missing item**, so no `calibration_admission` anywhere.
- Mechanisms: `compute_throughput`, `native_service_costs` (additive), `memory_service_scenario`,
  `native_service_costs` (gross allocator, resource-bound). No `streaming_bandwidth` mechanism.
- `resource_floor_mechanisms`: one `streaming_bandwidth` item, `bytes_per_s` = 15 071 467 833.99 B/s
  (measured), carried from `mbit10.cpu.lanl20261006a2.v2.t1` and pinned to
  `mbit10.cpu.lanl20261006a2.v2.calibration.t1` (ticket 03 carrier).
- The binder's commit added only this one file to the store copy (`diff -rq` against the checkout).

## Exact command

`job-08.sh` (this folder), run from a clean detached worktree of `b8be5305` on mbit10:

```sh
python3 -m swdb.cpu_service_binding --records "$RAW/records08" $(cat bind-args.txt)
python3 -m swdb validate --records "$RAW/records08" --library <checkout>/swdb-project/library
```

`bind-args.txt` = the `services.v1` runbook-11 arguments plus:
- `--scope-characterization fga03.t75-{baseline,candidate}.uniform22.t1.characterization.a2`;
- `--calibration` for the five ticket-07 records (`resource.memory-v2.a1`, `resource.allocator-v2.a1`,
  `service.openmp.a2`, `service.library-call.a1`, `resource.bulk-total.a3`);
- `--openmp-projection` for the two ticket-01 t75 projections;
- `--id mbit10.cpu.lanl20261006.t1.services.v2`.

The floor-only bandwidth needs no flag: the binder carries it whenever memory cells supersede the
base's memory mechanisms (ticket 03).

## Where and how it ran

- Lane: `when-free.sh 08` waited for a free socket lease, then ran `job-08.sh` through
  `Memacc-evolveswdb-lane/AgenticRefiner/scripts/host/socket_lane.sh` (blob `261e7e04`, equal to
  `origin/yanrujhou_main`). Lane record: `lane-08.json` (node0, lease generation 519, load1 7.39
  at start). Both leases were held by another session's full test suites from 15:47 to 17:20 ET;
  the job started when node0 freed.
- Order: `order.log`. Host snapshots: `env-08-start.txt`, `env-08-end.txt`.
- Step times (`step-times.txt`): bind 20 min 20 s, 7.1 GB peak RSS (the commit's whole-store
  check is inside); whole-store `swdb validate` 13 min 46 s, 3.9 GB.
- Whole-store check: `validate-whole.txt` = `OK: 723 record(s) valid` (722 before, plus services.v2).
- Pre-check: before the lane run, the same arguments ran on the Mac with `writer.commit` replaced
  by a capture (nothing written; 201 s). It gave the same allowlist, 252 rows and 0 missing.
- No application ran. Workload `bfs-20261004-uniform22` was not timed (C12).
