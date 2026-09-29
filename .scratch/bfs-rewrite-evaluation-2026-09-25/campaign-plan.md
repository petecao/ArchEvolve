# Representative BFS campaign plan

Navigation updated: 2026-09-28 (Eastern Time).

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-26 (Eastern Time)

This is dependent preparation for Tickets 17–20. No proposal is submitted without
complete real baseline packages, and no candidate performance is assessed before
Ticket 15 freezes compatible protocols. `scripts/bfs_campaign_proposal.py` is a
representative operator/test client. It supplies the selected strategy; the rewrite
worker may apply and repair that intent but may not choose another optimization.

## Selected strategies

| Ticket | Source and payload | Selected transformation | Evidence limit |
|---|---|---|---|
| 17 | DX100 scalar, natural language | Initialize the existing per-thread MAA resources inside DOBFS and use the existing TDStepMAA sequence; wait on its returned-old-parent destination tile before consuming it | Actual changed DOBFS and observed offload are required; selecting the preexisting DOBFSMAA entry point is insufficient |
| 18 | DX100 scalar, patch | Dynamic frontier scheduling with 64-vertex chunks, removal of the redundant successful-CAS parent store, and conditional diagnostic printing | This is a combined CPU rewrite; any measured gain is attributed to the complete patch |
| 19 | Upstream direction-optimizing BFS, structured instructions | Remove only the initial curr bitmap clear that is overwritten by BUStep's destination clear before use | Preserve front's initial clear and every BUStep destination clear; otherwise return unresolved |
| 20 | Upstream direction-optimizing BFS, annotated source | Add a supported DX100 top-down helper and prefer it for frontiers larger than four 1,024-vertex blocks; retain the CPU direction policy for smaller frontiers | Charge checked offset conversion and initialization to the complete call; retain upstream source identity and independent correctness |

The upstream offload adaptation uses public queue/graph/pvector accessors, checked
32-bit CSR offsets, actual returned tile lengths, scalar tails, serialized parent
updates, and the old-parent values needed for duplicate suppression and scout
counts. It does not claim that a masked scatter is a CPU atomic compare-and-swap.
The pinned author's `wait_ready(tile3)` follows a store whose old-value destination
is tile5. The selected candidate strategy waits for tile5 before consuming it; the
independent artifact/reference source stays unchanged. The candidate evaluator,
not this planning inference, determines whether actual execution is correct.

Each proposal identifies both queried baseline packages in its parameters and one
exact selected package/source/region context in the versioned envelope. Both graph
families must use the same final source-specific accelerator candidate. If a repair
creates a new candidate, evaluate that new identity on both families and retain
the earlier outcomes. No source-dependent graph substitution is allowed.

## Bounds and outcome rules

- Native campaign execution uses `scripts/bfs_native_campaign.py`, consuming the
  existing frozen protocol, two real baseline packages, and operator-authored
  proposal JSON. It runs new protocol-bound baseline and candidate trials,
  diagnostics, packages, comparisons, and fresh-process retrieval. Pre-freeze
  baseline packages provide proposal context; their times cannot substitute for
  new frozen-protocol baseline measurements.
- The explicit `--existing-candidate ID` route retains the exact original
  `--proposal` JSON and reopens its initial completed candidate through public
  queries. It checks proposal/source/package/artifact identities and replays the
  retained patch in a bounded temporary source snapshot. Matching file hashes
  alone do not establish that the selected patch produced the candidate. Reuse
  invokes no provider and rejects `--provider-config`, prior repair history,
  changed bindings, or missing original interpreted-provider budget metadata.
  Optional `--repair-config` permits the existing single build/correctness repair
  only within the retained allowance; reuse never resets consumed provider time.
- When the explicitly new one-thread calibration qualifies, the optional
  `--reassessment` manifest binds each retained original native candidate to the
  two fresh packages and separately frozen new protocol. Both original package
  identities, the unchanged proposal/payload, source/region protections, exact
  patch replay, and original consumed provider budget remain retained. Unknown
  historical runtime inputs are not inferred. This mode forbids provider and
  repair configurations and performs no submission or repair, even after a build
  failure. [Contract and evidence](../../docs/archive/bfs-native-reassessment-20260926.md).
  Its implementation does not qualify calibration or publish a protocol.
- Native interpretation uses at most 300 seconds per call, one repair, a 600-second
  provider total, and a USD 5 provider-call cap. Each evaluation permits 180 seconds
  to build and 60 seconds per trial. Serial evaluations permit 1,200 seconds total;
  a newly frozen paired protocol permits 2,400 seconds per complete pair and per
  member including waiting, as fixed in the [paired contract](../../docs/reference/bfs-native-paired.md).
  These new-mode bounds do not alter any earlier pilot's allowance. Each diagnostic collector
  permits 120 seconds for discovery, 180 seconds to build, 600 seconds per case,
  and 1,200 seconds total. The enclosing native campaign is capped at four hours
  per source/route, including any rerun of both families after one repair.
- The more substantial accelerator port may use 600 seconds per provider call,
  at most two build/correctness repairs, a 1,800-second provider total, and a USD 10
  provider-call cap. Its simulation bounds are selected from the unchanged
  baseline/reference pilot and frozen before dispatch. Fixed model-build and
  artifact-reference caps remain in their separate plans.
- All jobs enter an owned socket lane. Other tasks' leases are honored. Source,
  generated drivers, and binaries use `/data1/yanruj`; large raw outputs use the
  recorded overflow volume. Recheck the 10 GiB source/build and 30 GiB raw-volume
  free-space reserves before dispatch. No third unconfined measurement job runs.
- Failed compilation, correctness, timeout, missing profiling, and unsupported
  capability outcomes remain retained. A regression or no-gain result never
  triggers a different optimization or further performance tuning. Ticket 21
  separately requires at least one correctness- and policy-qualified ROI gain;
  this plan does not guarantee one or weaken that requirement.

Real performance and accelerator coverage remain unmeasured at this preparation
stage. The final report must distinguish completed workflow cases, actual offload,
complete evidence packages, comparison outcomes, and the overall acceptance gate.
