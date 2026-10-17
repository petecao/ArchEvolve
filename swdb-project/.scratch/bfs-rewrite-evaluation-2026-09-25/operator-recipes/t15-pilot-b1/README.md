# T15 pilot b1 operator

Created: 2026-09-27 ET. Updated: 2026-09-27 ET.

This operator runs the approved incremental T15 allocation (48 h / 96 GiB) under
resume decisions R1–R3 and R9. Its plan is
[`bfs-t15-pilot-simulator-batch-20260927-b1`](../../requests/bfs-t15-pilot-simulator-batch-20260927-b1.json).
The grid is the same as in every earlier T15 attempt: uniform18 and kronecker18,
ordered sources `[0, 1234, 7777]`, two replays, the author MAA binary, and the
MAA configuration (8 MiB L3, 16-way, tile 16,384) on 4 guest cores. That gives
12 primary/diagnostic pairs.

## Lane job shape (R3)

One `socket_lane.sh` job on **node 0** (root assignment 2026-09-27) runs two batch
drivers side by side, one per family. Each driver is its own subreaper and
cleanup ledger.

- **One gem5 at a time.** A one-slot flock pool
  (`<plan>.dispatch/gem5-slots/`) serializes gem5 across the families. The slot
  is handed to `dx100-execute`, which closes it after its last simulator stage.
  The other family's trace parsing, correctness, profile and package work
  overlaps that gem5. Measured basis: one gem5 holds 29.5–33.5 GiB of sampled
  RSS, so the 52-GiB cap admits only one.
- **Memory checks.** Each driver enforces the 52-GiB sampled cap on the whole
  lane tree, both drivers included. The node capacity check before each
  execute runs after the slot is acquired.
- **Storage.** The aggregate is 96 GiB: 4 GiB overhead reserve plus 92 GiB
  shared, with each family capped at 60 GiB. It covers `<plan>/` and
  `<plan>.dispatch/`.

## Steps (all on mbit10, in the immutable runtime checkout)

```sh
OP=.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/t15-pilot-b1/pilot_operator.py
/usr/bin/python3.12 -I -B $OP setup
bash $HELPER 0 bfs-t15-pilot-linux-tests-20260927-b1 -- \
  timeout 300 /data1/yanruj/venvs/evolveswdb-test/bin/python -I -B $OP tests --kind owned_cleanup
bash $HELPER 0 bfs-t15-pilot-linux-tests-20260927-b1 -- \
  timeout 300 /data1/yanruj/venvs/evolveswdb-test/bin/python -I -B $OP tests --kind dx100_interruption
/usr/bin/python3.12 -I -B $OP prepare        # the 48-h clock starts here
tmux new -d -s t15pilot "OPERATOR=... OPERATOR_SHA=... ADMISSION_SHA=... bash .../launch.sh"
```

Run `launch` within 3,600 s of `prepare`. No step retries or overwrites. A
failure keeps its run ID as evidence, and any correction needs a fresh ID.
