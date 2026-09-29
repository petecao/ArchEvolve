# Fixed a3 driver and observer launcher

Navigation updated: 2026-09-28 (Eastern Time).

Date: 2026-09-26 ET. Status: local preparation; no dispatch recorded here.

The launcher adds process supervision around the unchanged a3 client. The
prospective topology is one named tmux pane, then `timeout --signal=TERM
--kill-after=30s 1170s`, the verified socket-0 helper, and
`scripts/bfs_witness_launch.py`. Its two children are the fixed a3 client and
the separately pinned read-only observer, each in its own process session.
Observer address-space and CPU limits apply only to that observer subprocess.

The CLI takes `--expected-commit`, `--driver-checkout`, `--output-dir`,
`--outer-started`, `--outer-deadline`, `--pane-pid`, `--pane-start-ticks`, and the
existing paired/provider completion paths and SHA-256 arguments. The original
wrapper supplies aware outer timestamps exactly 1,200 seconds apart. Both
must fit the unchanged a3 window, ending by 2026-09-26 15:40 ET, with latest
launch 15:20 ET. Supervisor preparation consumes that same allowance; it cannot
start a new clock. The observer receives that exact outer deadline. No retries,
request changes, source changes, or old-attempt promotion occur.

The driver checkout must remain
`/data1/yanruj/EvolveSWDB_dx100_continuation_20260926_a3` at commit
`1018432fdb3800522d723afb874f3bffa41dd0e5`; the a3 client file and canonical
request have independent fixed hashes. The supervisor/observer checkout has a
separate caller-selected prospective commit pin. Its tracked launcher, observer,
sampler and cleanup source bytes must match that commit before either child
starts. Fresh socket-0 admission and the exact captured pane ancestry are
verified inside the helper.

Use the new child directory
`/data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925/witness-a3-dispatch1/supervisor`.
It must not exist. The surrounding dispatch directory retains the helper lane
and outer exit files. The supervisor retains `launcher.json`, separate driver
and observer stdout/stderr, `driver.exit`, `observer.exit`, `supervisor.exit`,
and the observer's new `observer/` directory. Each started child's actual
PID/start-time, command, exit status and output hashes are retained. A child
that could not be started is labeled `not_started`, never assigned a fabricated
exit code.

The supervisor attempts bounded waits and reaps for both direct children,
including after a cleanup error. Failure to reap is retained as
`unknown_unreaped`, with a nonzero combined exit. An observer failure
stops the owned driver; a driver failure still permits the observer to record
its terminal identities within the same bound. At interruption or timeout,
cleanup signals only a still-live, identity-verified owned session leader's
process group. Each wait is capped by the remaining shared cleanup allowance;
already-reaped numeric PID/group identities are never signaled. The launcher
reuses the existing interruption context and process identity helpers. It never signals the
shared tmux server or declares independently sessioned descendants reaped.
Success requires both actual exits to be zero and the observer's successful
bounded sampling receipt to name the exact driver, observer and pane identities
and the original absolute deadline. Any failure gives
a nonzero combined exit. An independent terminal audit must still verify every
retained process identity and the released lease; the supervisor receipt is
not that cleanup barrier and carries no gain or correctness claim.

Local process tests establish supervision and failure handling only. They do
not execute a3, invoke a simulator, or provide mbit10 evidence.
