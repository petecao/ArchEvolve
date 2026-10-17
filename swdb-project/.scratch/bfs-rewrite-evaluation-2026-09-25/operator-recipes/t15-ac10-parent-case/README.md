# AC10 timed-binary competing-parent case

Created: 2026-09-27 ET. Updated: 2026-09-27 ET.

In T15 b1, b2 and b3, the s0 primary (timed) executions observed full and tail
tiles, but not competing-parent updates; only the diagnostic builds observed
those. Diagnostic coverage cannot stand in for the timed binary. This
correctness-only case runs the exact primary author `bfs_maa` binary
(SHA-256 `6abd8190…`), with the same MAA configuration, verifier v2, coverage
counters and gzip trace. It uses the fixed collision-heavy A2 coverage graph:
8,212 vertices, where a 4,097-vertex frontier shares 16 parents. With the
complete-call build, that graph already produced 14,546 observed
competing-parent updates.

- Run ID: `bfs-t15-ac10-parent-case-20260928-a1`.
- Lane: one short job after the T15 grid and before the freeze, in the lane gap
  root assigns.
- Bounds:
  - outer timeout 3,600 s;
  - execute budget 3,300 s (checkpoint 600, run 2,400);
  - memory 48 GiB;
  - storage 10 GiB.

```sh
bash $HELPER 0 bfs-t15-ac10-parent-case-20260928-a1 -- timeout 3600 \
  /usr/bin/python3.12 -I -B $RUNTIME/.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/t15-ac10-parent-case/run.py \
  --lane 0 --template <b3 uniform18 s0.r0 primary .request.json>
```

The case passes only if all of these hold:

- the public execution completes;
- correctness passes;
- the timing record names the exact timed binary;
- competing-parent updates are `observed`.

The controlled-simulator protocol's correctness coverage names this case, so
T17/T20 candidates repeat it with their own timed binary.
