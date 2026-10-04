# 03 — Freeze T17 protocol v2 and record the comparison

Created: 2026-09-29
**Type:** slice
**Status:** resolved
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

The root agent coordinated this work in an owned mbit10 lane, where the raw observations
and binary/source artifacts are available. Qualification waited for both retained
comparison results to be verified and synced locally.

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

## Answer

2026-09-29 21:46 ET: Both public `compare-evaluations` operations completed with
`decision.state: gain`, empty rejection reasons, and `gain_claim: true`. The exact
records are retained locally and on mbit10 in commit
`cadf16b2fe9a945ebfc066eeccd78357a9ad05a8`; their file hashes match across hosts.

| Family | Comparison record | Baseline primary ROI (s) | Candidate primary ROI (s) | ROI speedup | Finished (ET) |
|---|---|---:|---:|---:|---|
| uniform18 | [bfs-t17-handoff-20260929-a1.uniform18](../../../records/comparison_results/bfs-t17-handoff-20260929-a1.uniform18.yaml) | 0.019544523158 | 0.006344415474 | 3.0805868937958523× | 2026-09-29 20:59 |
| kronecker18 | [bfs-t17-handoff-20260929-a1.kronecker18](../../../records/comparison_results/bfs-t17-handoff-20260929-a1.kronecker18.yaml) | 0.018487688048 | 0.006605155742 | 2.7989783693430432× | 2026-09-29 21:41 |

The existing v2 protocol identity was rechecked unchanged:
`952dead4468b86d796172d7dfb2ef9fb8170bec1591b4160c562df660ce181ff`.
Its original freeze is `2026-09-28T22:44:22.338507+00:00`. The public retry ran from
`c55614e1c8c64b2a04d812789e9e59805f4c8033` in the isolated checkout on node1,
lease generation 489, and exited 0 at 2026-09-29 21:41 ET. Subsequent Git sync did
not change the evaluation checkout recorded in `retry-checkout.txt`.

The claim is simulated primary `bfs.complete_call.v1` timing against scalar TDStep,
source vertex 0/source position 0/repetition 0 only, with one repetition per family
under declared `deterministic_simulator_replay.v1`. Attribution is
`joint_hardware_software`: the candidate alone enables MAA and strategy
`existing-dx100-top-down-offload` reuses the authors' `TDStepMAA` plus
`wait_ready(tile5)`. Both primary roles passed source-0 correctness. This establishes
neither a provider-discovered accelerator algorithm nor general-source coverage;
the singleton bootstrap interval supplies no independent repeated-run uncertainty.

The verified candidate source artifact is
`ca09d2f439a56f295c5ccdc5e18a5fd5a4c2c9726005365f8125cc1d8979740a`, with BFS file
SHA-256 `fda0c52f8114058db6ac9810fa7a97795e92d42cebba9c5868354bc3aecf73e1`.
The retained timed candidate binary, also used by the accepted companion, hashes to
`852e62314b7114079975fe25d70da4e77596490bcfa89fb4f7c64af585485527`; both primary
roles' binary hashes were rechecked against the actual files. The companion record
`bfs-t17-ac10-companion-20260928-a3.execute` binds 14,546 observed competing parent
updates to the same timed binary and its accepted source-0 check.

Diagnostic complete-call per-thread elapsed ratios are 1.988871829364087 and
1.752146312036966; they include waiting/overlap and do not replace the primary ROI
ratios above. The scalar baseline never invokes the MAA region, so its regional
ratio is null; the candidate invokes it six/seven times respectively.

Terminal evidence remains under
`/data1/yanruj/EvolveSWDB_runs/t17-handoff-20260929-a1/`: `retry-exit.txt` is 0,
`retry-stderr.txt` records both gain decisions, and `comparison/summary.json`
matches `retry-stdout.json` (SHA-256
`9873109c2cab8029b88c889c47722af2a1e08e9336d736e3d8f3786cc2a93893`). Both
requests and public stdout match the persisted comparison records. The root agent
recorded `python3 -B -m swdb validate` exit 0 with `OK: 352 record(s) valid` before
publishing the two records. Provider ticket07's final review remains in progress;
the root agent owns its final QA update.
