# One post-ROI syscall diagnostic

Updated: 2026-09-26 (Eastern Time).

The retained `bfs-dx100-smoke-20260925-a6` reaches its sealed ROI and prints one
PASS, Verification Time, and Average Time, but ends at its continuation tick limit.
Its correctness remains unverified. This probe observes the existing syscall
path; it does not modify the pinned model, guest binary, graph, or checker.

The fixed request is
`.scratch/bfs-rewrite-evaluation-2026-09-25/requests/dx100-exit-probe-a1.yaml`.
Its only differences from a6 are the new ID
`bfs-dx100-exit-probe-20260926-a1`, `verification.max_ticks: 10000000000`, and
`verification.post_roi_trace: SyscallBase`. The trusted driver accepts that exact
optional trace string and rejects other values before checkpoint or simulation.
Inherited environment cannot enable tracing. The ordinary MAATrace setting
remains unchanged during the ROI; the additional flag activates once, after the
sealed statistics and receipt have been synced to disk. The continuation receipt
retains `flag`, `enabled_tick`, `scope`, and `output`, while the execution context
retains the wrapper hash and explicit post-seal instrumentation treatment. Trace
output uses the existing bounded simulation log.

The exact a4 checkpoint manifest, original `bfs_maa`, source, mode, 8 MiB/16-way
LLC, four simulated cores, and 16 GB guest memory remain bound to a6. No new
checkpoint is generated. The public adapter keeps its 48 GiB process-group RSS,
750-second simulation, 1,100-second total, and 2 GiB raw-storage bounds. The thin
driver has the same 1,200-second outer bound and 30-second cleanup reserve as the
earlier smoke driver. Its public evaluation child has at most 1,150 seconds and
uses the shared TERM/owned-group cleanup. The smaller post-ROI tick allowance is
10 ms at the declared 10^12 ticks/s; it is a diagnostic bound, not an assumption
that complete teardown must finish in that time.

Before dispatch, the root coordinator must review and checkpoint the adapter,
request, and driver. Use a fresh idle checkout of that commit. Recheck both socket
leases and the legacy lease, live owners, helper revision, load, disk, and all
retained input hashes. The unchanged capacity helper must pass immediately before
claim and again inside the selected lane: estimated node capacity at least 52 GiB
and global MemAvailable at least 64 GiB. The estimate includes its existing 1 GiB
uncertainty discount. No reclamation, policy change, or gate relaxation is allowed.

Inside the verified lane, the fixed invocation is:

```sh
python3 scripts/dx100_trace_probe.py \
  --runs-dir /data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925 \
  --lane 1
```

The selected lane may be 0 only after the same fresh checks. Enter it through the
verified `socket_lane.sh` under a named tmux session and `timeout`; never run the
driver unconfined. Use new outer evidence names beginning
`exit-probe-a1-dispatch1` for lane, capacity, driver log, and exit status. Existing
a6 paths and hashes must remain untouched. A capacity refusal is a preflight
result, separate from execution; a later reviewed opportunity needs a new outer
dispatch suffix so receipts are never overwritten.

One actual execution is allowed, with no automatic retry. Preserve CLI exit 1,
failed terminal conditions, sealed observations, trace, phase RSS, and all raw
hashes. `exit_group(0)` without normal termination supports an exit/context issue
but does not prove Process-pointer aliasing. A futex without exit_group redirects
the diagnosis. A tick limit or missing trace leaves the issue unresolved. PASS
alone cannot establish correctness; this probe never produces a performance,
accelerator-use, or artifact-reference claim.

Local verification: 15 public adapter cases pass, covering default suppression,
strict trace values, fsync-before-enable order, one post-seal activation, and the
unchanged rejection of PASS followed by a tick-limit event. One fixed-request
guard test rejects changes to model/binary/checkpoint/input/configuration or
resource bounds. These are local contract fixtures, not real simulator evidence.
