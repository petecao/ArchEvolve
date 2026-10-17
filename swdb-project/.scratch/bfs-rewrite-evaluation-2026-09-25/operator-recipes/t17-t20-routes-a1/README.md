# T17/T20 routes lane job

Created: 2026-09-28 ET. Updated: 2026-09-28 ET.

This lane job collects the frozen controlled-simulator routes. It is one
node0 `socket_lane.sh` job with four drivers, one per route and family
(`t17.uniform18`, `t17.kronecker18`, `t20.uniform18`, `t20.kronecker18`).

- **Driver order.** Each driver runs its baseline series, then its candidate
  series.
- **Replays.** One replay per source, per the frozen R11 basis.
- **Builds.** Every series uses its retained primary and diagnostic builds
  (`--primary-build`, no `--author-binary`).
- **Shared limits.** The drivers share one gem5 slot, the 52-GiB lane-tree
  sampled RSS cap, and the 60-GiB aggregate (16 GiB per driver root).
- **AC10 companion cases.** After all drivers exit, the wrapper runs
  `companion.py` once per candidate route (`bfs.dx100.competing-parent-case.v1`,
  AC10). It uses that candidate's uniform18 s0.r0 primary request as the template.

Plan: [`bfs-t17-t20-routes-simulator-batch-20260928-a1`](../../requests/bfs-t17-t20-routes-simulator-batch-20260928-a1.json).
The plan's `bound_basis` records the bounds and their derivation from the
measured T15 b3 costs.

The steps are the same as the T15 pilot b1 recipe, using `routes_operator.py`:

1. `setup`;
2. two Linux test runs inside the lane;
3. `prepare`, which starts the 48-h clock;
4. `launch.sh` in tmux, within 3,600 s of `prepare`.

After the lane job, run compare, fresh-process get and the ticket updates
outside the batch, under a 4-h bound.
