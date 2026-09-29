# 03 — Freeze T17 protocol v2 and record the comparison

Created: 2026-09-29
**Type:** slice
**Status:** ready-for-agent
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
