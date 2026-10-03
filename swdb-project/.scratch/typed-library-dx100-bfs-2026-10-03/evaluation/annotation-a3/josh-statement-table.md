# TDStep statement annotations for Josh

Updated: 2026-10-03

Draft for Yan-Ru to send. Agent predictions are source reading or inference; cache misses are Callgrind simulation.

Spearman rank correlation: 0.4925690038994379; top-3 overlap: 0.667.

| Statement | Scalar lines | Pattern class (agent) | Index provenance (agent) | Expected rank | Simulated LL misses | Callgrind rank | Contradicted |
|---|---|---|---|---:|---:|---:|---|
| bfs-td-frontier | 77–77 | stream: read | none | 4 | 6731 | 3 | no |
| bfs-td-row-bounds | 78–78 | stream → single_valued_indirect: read; stream → single_valued_indirect: read | bfs-td-frontier | 3 | 6809 | 2 | no |
| bfs-td-neighbor | 79–79 | stream → single_valued_indirect → ranged_indirect: read | bfs-td-frontier → bfs-td-row-bounds | 2 | 479207 | 1 | no |
| bfs-td-parent-read | 80–80 | stream → single_valued_indirect → ranged_indirect → single_valued_indirect: read | bfs-td-frontier → bfs-td-row-bounds → bfs-td-neighbor | 1 | 0 | 5.5 | yes |
| bfs-td-parent-cas | 84–84 | stream → single_valued_indirect → ranged_indirect → single_valued_indirect: compare_and_swap | bfs-td-frontier → bfs-td-row-bounds → bfs-td-neighbor | 6 | 0 | 5.5 | no |
| bfs-td-parent-store | 85–85 | stream → single_valued_indirect → ranged_indirect → single_valued_indirect: write | bfs-td-frontier → bfs-td-row-bounds → bfs-td-neighbor | 7 | 0 | 5.5 | yes |
| bfs-td-queue-append | 86–86 | stream: write | none | 5 | 0 | 5.5 | no |

Cost contradiction rule: absolute difference between expected rank and simulated midrank exceeds 1.
Tied miss counts receive average ranks; top-3 boundary ties use fractional expected overlap.
Pattern and index claims require a measured, simulated or person-reported access-pattern fact to contradict them.
Debug-line self costs can exclude coalesced or inlined-header work; these ranks do not prove a native bottleneck.

Region profile: `typed-library-bfs-scalar-profile-20261003-a2.profile`; sha256: `3df8599662e915ec66d6c326d1999103454ef4b49ca7125d06e33762c4d91883`.
