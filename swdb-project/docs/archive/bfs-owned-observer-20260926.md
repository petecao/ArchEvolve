# Owned process observations for the a3 proof

Navigation updated: 2026-09-28 (Eastern Time).

Date: 2026-09-26 ET.

`scripts/bfs_owned_observer.py` observes one declared driver PID/start-time and
its descendants through Linux procfs. It is a read-only companion to the fixed
a3 proof, not a cleanup controller. The coordinator runs it in the same socket
lane and inside the proof's existing 1200-second outer allowance, with that
same absolute deadline. It does not extend the proof's work or cleanup budget.

The observer follows the initial parent chain only as far as the exact declared
tmux pane, including that pane and excluding the shared tmux server. A missing,
reused or non-ancestor pane rejects observation. The reused `DescendantRSS`
sampler follows children across process sessions and retains PID/start-time
identities for already observed children that become reparented. Periodic
sampling can miss short-lived children; this receipt cannot prove that every
process that ever existed was observed.

The fixed bounds are a nominal five-second interval, a ten-second observed
maximum gap, a two-second observed sample cost, 242 samples, 4096 retained
identities, and 8 MiB of output. Sample cost includes reading procfs, serializing
the sample and the durable sample/receipt writes; the individual JSONL row's
`observer_wall_s` describes the procfs-read portion only. The command limits
its own address space to 512 MiB and CPU time to twenty seconds. These are not
limits on the observed simulator. A blocked filesystem call remains subject to
the enclosing timeout; the observed cost checks do not provide a real-time
scheduling guarantee. The final hash and persistence are charged to the same
deadline. There is no upward-configurable duration or automatic retry.

The new output directory contains `resource-samples.jsonl` and
`process-observations.json`. The latter records `driver_identity`,
`launcher_identity`, `observer_identity`, the bounded `ancestry`, all retained
`owned_processes`, and the final hashed `resource_samples` reference. Its
implementation identity binds the observer script, sampler script and Git
revision. Its RSS scope describes the driver tree only; the observer is included
in that total only if it is itself a descendant. It is not a combined 48 GiB
simulator-plus-observer budget claim.

`state: driver_terminated` with `sampling_complete: true` means the original
driver identity disappeared or became a zero-RSS zombie before the deadline.
It always leaves `cleanup_verified: false`. Live and uncertain descendants stay
explicit in the receipt, including the observer's own identity. The external
coordinator must wait for the observer and independently recheck the full union
of ancestry, sample, driver and observer identities after termination. Only
that later audit can establish the cleanup barrier. The observer never sends
signals to another process, waits for or reaps a child, or treats a reused PID
as its original owner.

Failure receipts preserve observed identities and reasons where storage is
available. Existing output directories are never overwritten. The successful
synthetic procfs tests exercise normal termination, surviving detached children,
PID reuse, stale/non-ancestor identities, unreadable live processes, sampling
races, wall/storage limits and finalization costs. They are test evidence, not
an actual mbit10 observation or simulator execution. A later 3600-second
coverage run requires its own separately declared observation budget; this
a3-only utility must not silently be extended for that purpose.
