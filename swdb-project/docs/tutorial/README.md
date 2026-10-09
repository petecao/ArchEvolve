# EvolveSWDB tutorial

Updated: 2026-10-09 (Eastern Time).

Start with the overview. Then read chapters 2–5 in order. Basic familiarity
with code and command-line tools is enough; no ArchEvolve or simulator knowledge
is required.

| Order | Chapter | Budget | Purpose |
|---|---|---:|---|
| 1 | [Overview](01-overview.md) | 10 min | Explain SWDB and follow a PageRank query |
| 2 | [Records and queries](02-records-and-queries.md) | 7 min | Read records and interpret evidence |
| 3 | [Components](03-components.md) | 7 min | Find the code for each operation |
| 4 | [BFS workflow](04-bfs-workflow.md) | 9 min | Trace rewrites, estimates, and research campaigns |
| 5 | [Contributing and profiling](05-contributing.md) | 7 min | Extend the catalog and choose a procedure |

The overview and both navigation pages stay below 1,200 words. Chapters 2–5
stay below 3,500 words. At 150 words per minute, these budgets also reserve time
for tables, diagrams, and code. Installation, the optional exercise, and execution
are outside the reading budget. References are for later lookup.

From the ArchEvolve root, run `cd swdb-project` before shell examples.
Query examples inspect stored metadata; their generated SQLite index is disposable.
The chapter 5 exercise writes only to a temporary records folder. Command tables
describe interfaces, not a campaign launch sequence. Mermaid diagrams have
accompanying explanations.

Code and local examples were checked against `yanrujhou_main` source commit
`e62a63bb1a93a37ae2c150b921a6af7ccd4ca89f` on 2026-10-09, including campaign
artifact receipts and certification infrastructure stops. Query examples used
temporary copies of their committed records, source excerpts, and typed library.
Remote paths and dated results remain retained metadata; this review ran no
measurements on mbit10.

**[Begin the overview →](01-overview.md)**
