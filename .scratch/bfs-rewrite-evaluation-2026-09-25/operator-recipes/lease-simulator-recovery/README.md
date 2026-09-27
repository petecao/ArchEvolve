# Fixed lease-recovery simulator operator

Prepared: 2026-09-27 Eastern Time. Data-only preparation; no dispatch.

Runtime is exactly `07baead5fe5cf3718e18e1d2313db6899f2638c8` with all 806
tracked Git files in `runtime-manifest.json`. This is a minimal adaptation of the
reviewed `simulator-recovery` packet: new lease plan IDs/date/runtime roots, fresh
proof receipt from configuration, and removal of the historical8cb proof adapter.
It reuses the unchanged SHA-pinned `supervision-recovery/operator.py` admission
helpers; include that exact file in the operational Git packet. This shared helper
is operational code outside the scientific runtime and is not executed as a group.

| Batch | Prospective runtime root | Original latest full-series start | Original absolute end |
| --- | --- | --- | --- |
| T15 | `/data1/yanruj/EvolveSWDB_t15_lease_recovery_runtime_20260927_a1` | 2026-09-27 03:13:39.851819 ET | 2026-09-27 09:14:09.851819 ET |
| T16 | `/data1/yanruj/EvolveSWDB_t16_lease_recovery_runtime_20260927_a1` | 2026-09-27 14:15:47.225985 ET | 2026-09-27 20:16:17.225985 ET |

Use separate clean Git checkouts because each batch owns its record mutations.
No records or raw failures from T15's previous attempt may be edited. The new
plans retain all old preparation charges, plus the full 600-second/2-GiB fresh
proof reservation; T15 also charges its failed batch through independent closure
(4,551 seconds). Nominal residual budgets are 34,452 seconds for T15 and 73,826
for T16, but actual elapsed absolute windows always take precedence. Each series
still requires the original 21,600 seconds plus shared 30-second cleanup. No new
scientific allowance or retry count is introduced by the operator.

The configurations now pin the independently closed fresh group final receipt
SHA256 `c144b6600a1d00832f476a41f90313489ddc96bcb9ff52d03b700a26540b6925` (19,484 bytes), at:
`/data/yanruj/EvolveSWDB_runs/bfs-supervision-lease-recovery-linux-20260927-a1.final.json`.
The operator checks the receipt hash, complete state, exact07ba runtime, and
absence of any historical proof alias; existing validators reopen actual proof,
51-case supplement, prerequisite/source/build and retained-cost evidence. The helper comparison at 02:31:56 ET confirms tracking tip `2ffb83ae` equals
the installed entire host subtree; both scripts remain unchanged and clean. Node1/T15 and node0/T16 remain prospective selections only, subject to
fresh socket/legacy locks and capacity/disk admission at launch.

Deliver the packet through private Git, preserving both existing proof groups and
all failed scientific artifacts. Proposed operator checkout:
`/data1/yanruj/EvolveSWDB_lease_simulator_operator_20260927_a1`.
After independent review, invoke the existing metadata preparation using an
absolute configuration path (this creates admission only, not a workload):

```sh
/usr/bin/python3.12 -I -B "$OPERATOR" prepare t15 "$CONFIG"
/usr/bin/python3.12 -I -B "$OPERATOR" prepare t16 "$CONFIG"
```

Use each route's own configuration for its command. Actual admissions are written
exclusively to the new plan's `.dispatch/admission.json`. Preparation fails if
either raw or dispatch root already exists. Do not retry by deleting evidence.

After independent admission readback, root may use `launch.sh` in a named tmux
pane with exact `OPERATOR`, `OPERATOR_SHA`, `CONFIG`, `CONFIG_SHA`, `KIND`, and
`ADMISSION_SHA`. The existing batch driver retains child ownership, original
clock, cleanup and resource limits. The wrapper records actual outer exit and
outputs in the charged dispatch root. Root must independently close the complete
PID/start union, generation release, cleanup ledger and final raw/dispatch bytes.
No successful proof, readiness or exit-code-only observation is a simulator sample
or T15/T16 acceptance claim.

Independent fresh group closure confirmed all 51+5+2 cases passed without skips,
27.728543 seconds and 3,395,584 allocated bytes over all five roots. Strict cleanup
ledgers and two process-union observations closed generations441/442/443. Both
plans still charge the full600 seconds/2GiB. Root authorized data-only admission
preparation after this closure; scientific launch remains root-owned.
