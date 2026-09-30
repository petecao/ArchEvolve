# Reference

Updated: 2026-09-30 (Eastern Time).

Use the [tutorial](../tutorial/README.md) first. Open these documents when you need
exact fields, invariants, or a target-specific procedure. Navigation was updated
during consolidation; each document's content date still identifies its scope.
Dated measurements and host snapshots are historical, not live state.

Current commands and plain paths are relative to `ArchEvolve/swdb-project/`;
run `cd swdb-project` from the monorepo root. Archived procedures retain their
original paths and context.

## Catalog and storage

| Task | Reference |
|---|---|
| Write catalog records | [Format 0.3](format-v0.3.md), [format 0.4 additions](format-v0.4.md) |
| Add source, loops, access patterns, inputs | [Application checklist](adding-an-application.md) |
| Add a strategy or intrinsic | [Strategy checklist](adding-a-strategy.md) |
| Query exact SQL columns | [Database tables and queries](database.md) |
| Set up and operate the ordinary profiler | [mbit10 procedure](mbit10-profiling.md) |

Schemas in [`schemas/`](../../schemas/) and terms in [`vocab/`](../../vocab/)
remain the validation definitions. [Format 0.2](../archive/format-v0.2.md)
documents older supported records; the [0.1 proposal](../archive/format-proposal-v0.1.md)
is historical. See [ADRs](../adr/) for decisions.

## BFS contracts

| Area | Reference |
|---|---|
| Messages and source ownership | [Handoff 1.0](../bfs-handoff-contract-v1.md), [source identity](bfs-source-identity.md), [examples](../bfs-handoff-examples/) |
| Workload and comparison identity | [Frozen protocols](bfs-protocol.md), [pilot review/freezing](bfs-pilot-freeze.md) |
| Native execution | [Evaluator](bfs-native-evaluator-design.md), [paired collection](bfs-native-paired.md), [region comparisons](bfs-native-region-comparison.md) |
| Profile evidence | [Native collection](bfs-profiling.md), [packages and strategy queries](bfs-profile-packages.md), [persistence cost](bfs-persistence-cost.md) |
| Rewriting and hardware | [Worker and repairs](bfs-rewrite-worker.md), [capabilities](bfs-capabilities.md) |
| DX100 execution | [Design](bfs-dx100-design.md), [build/checkpoint/execute](bfs-dx100-execution.md), [serialized inputs](bfs-dx100-inputs.md) |
| DX100 observations | [Profiling](bfs-dx100-profiling.md), [completion witness](bfs-dx100-witness-v2.md), [trial identity](bfs-dx100-trial-identity.md), [sample grids](bfs-simulator-series.md) |
| Assessment | [Coverage contract](bfs-coverage.md), [report command](../bfs-handoff.md#final-report-regeneration--2026-09-27) |

The [archive index](../archive/README.md) locates dated admission plans, corrective
runs, and reviews. Those notes retain their original evidence and authorization
boundaries; moving a note does not supersede its contract or authorize execution.
