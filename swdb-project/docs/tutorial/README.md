# EvolveSWDB tutorial

Updated: 2026-09-28 (Eastern Time).

Learn what this project does in **10 minutes**, then spend **up to 30 more
minutes** understanding its records, components, execution workflow, and extension
points. Start with basic familiarity with code, command-line tools, and graphs;
no prior ArchEvolve or simulator knowledge is assumed.

## Choose your reading path

| Order | Chapter | Time | You should be able to… |
|---|---|---:|---|
| 1 | [Overview](01-overview.md) | 10 min | Explain the project and follow a real query |
| 2 | [Records and queries](02-records-and-queries.md) | 7 min | Read the data model and interpret evidence |
| 3 | [Components](03-components.md) | 7 min | Find the code responsible for each operation |
| 4 | [BFS from source to comparison](04-bfs-workflow.md) | 9 min | Trace a rewrite, its evaluation, and its result |
| 5 | [Contributing and profiling](05-contributing.md) | 7 min | Add a record and choose the right next procedure |

The overview plus this index contain about 1,200 prose words. Chapters 2–5
contain about 3,400: roughly 23 minutes at 150 words per minute, leaving about
7 minutes for their diagrams and code examples. These are reading estimates.
Installation and actual profiling/simulation are outside the reading budget.
The final local exercise is
optional; reading its code is sufficient. References are for later lookup.

All shell examples start at the repository root. Chapters 1–4 inspect existing
metadata and may create a disposable SQLite index. Chapter 5's exercise writes
only to a temporary records folder. Execution command names in tables explain
interfaces; they are not a campaign launch sequence.

Diagrams use Mermaid. Read these pages in a Markdown viewer with Mermaid support;
the surrounding prose also explains each diagram.

## Keep nearby

- [Glossary](../../CONTEXT.md): the project's exact terminology.
- [Reference index](../reference/README.md): field definitions and detailed procedures.
- [Architecture decisions](../adr/): why identity, storage, and comparisons work this way.
- [Existing task guides](../README.md): short operational checklists.
- [Archive](../archive/README.md): dated results and investigation history.

The tutorial describes the local source inspected at commit `fb14a9b` on
2026-09-28. Example results describe those records, not fresh measurements on
mbit10. Source links are repository-relative so the tutorial travels with a clone.

**[Begin the 10-minute overview →](01-overview.md)**
