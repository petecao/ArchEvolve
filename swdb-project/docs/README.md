# EvolveSWDB guide

Updated: 2026-09-30 (Eastern Time).

EvolveSWDB is ArchEvolve's Software Database: it connects application code,
memory behavior, optimization strategies, and evaluation evidence. Use it to
find suitable changes and check what the recorded evidence establishes.
Start with the [overview](tutorial/01-overview.md), then follow the
[tutorial](tutorial/README.md).

## One reading path

| Read | Budget | Outcome |
|---|---:|---|
| [Overview](tutorial/01-overview.md) | 10 min, including navigation | Understand the model and one PageRank example |
| [Tutorial chapters 2–5](tutorial/README.md) | 30 min total | Query records, find components, trace BFS, and contribute |

Installation, exercises, and experiments are optional and outside these budgets.

## Look up a task when needed

| Task | Guide |
|---|---|
| Query records | [Records and queries](database.md) |
| Add catalog entries | [Adding records](adding-an-application.md) |
| Rewrite and evaluate BFS | [BFS workflow](bfs-handoff.md) |
| Measure on mbit10 | [Profiling](mbit10-profiling.md) |
| Find exact fields or procedures | [Reference](reference/README.md) |
| Read prior plans and results | [Archive](archive/README.md) |

Shell examples and plain paths in current guides are relative to
`ArchEvolve/swdb-project/`. From the ArchEvolve root, run `cd swdb-project` first.
Use the [glossary](../GLOSSARY.md) for terms and [ADRs](adr/) for design decisions.
