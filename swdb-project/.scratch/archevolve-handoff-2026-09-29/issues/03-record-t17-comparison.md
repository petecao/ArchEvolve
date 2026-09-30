# 03 — Freeze T17 protocol v2 and record the comparison

Created: 2026-09-29
**Type:** slice
**Status:** claimed
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

## What to do

1. Check that run a3 (`observations/t17-t20-routes-a3-closure-20260929.json` in
   `../bfs-rewrite-evaluation-2026-09-25/`) matches protocol v2
   (`records/protocols/bfs-t17-controlled-simulator-20260928.952dead4468b86d7.yaml`).
2. Freeze v2, then run compare-evaluations under it.
3. The claim states: strategy `existing-dx100-top-down-offload` switches to the DX100
   authors' `TDStepMAA` (plus a `wait_ready(tile5)` fix); source vertex 0 only; simulated;
   1 repetition under declared determinism.

## Acceptance

- A new file in `records/comparison_results/`; `python3 -m swdb validate` passes.

## Progress

2026-09-29: Protocol v2 was already frozen before a3 dispatch at
`2026-09-28T22:44:22.338507+00:00`; its content-addressed identity remains unchanged.
Recreating or editing that freeze would invalidate its historical binding, so the
implementation preserves it and checks the exact a3 evidence under it.

`scripts/import_retained_t17_metadata.py` imports the actual retained runtime metadata
dependency closure without moving raw files, with collision digest checks and atomic
record validation. `scripts/record_t17_handoff_comparison.py` checks the source-0/
repetition-0 closure samples, exact timed companion, raw v2 witness/coverage, author-path
source reuse and `wait_ready(tile5)` fix, then invokes public `compare-evaluations` once
per graph family with explicit sealed diagnostic packages and claim scope.

The root agent coordinates this work in an owned mbit10 lane, where the raw observations
and binary/source artifacts are available. The ticket remains claimed until the two
retained comparison results are verified and synced locally.

2026-09-29 20:10 ET: After the first recheck exhausted its outer time budget, the
longer public retry is running in node1 from the isolated checkout
`/data1/yanruj/ArchEvolve_t17_handoff_20260929_a1/swdb-project`.
The 25 imported metadata records were validated there (338 records total) and
committed/pushed as `c55614e1c8c64b2a04d812789e9e59805f4c8033`; local fast-forward
waits for the running regression. The exact existing frozen v2 protocol
`bfs-t17-controlled-simulator-20260928.952dead4468b86d7`, source/binary, and
source-0/repetition-0 scope are unchanged. The companion passed and uniform18's
public submission started. Both final decisions remain pending; the claim remains
simulated joint hardware/software reuse of the authors' `TDStepMAA` plus
`wait_ready(tile5)`, with one repetition under declared determinism. No performance
qualification is inferred from the retained closure timings.
