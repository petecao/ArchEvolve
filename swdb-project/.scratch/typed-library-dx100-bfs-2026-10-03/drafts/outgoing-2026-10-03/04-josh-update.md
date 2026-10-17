Hi Josh,

The shared typed-library entries are published at commit `8959b4dfd149273e89884be87bee9c0adb60e0fc` on `yanrujhou_main`. The BFS contract keeps your hardware-candidate, operation and requirement IDs, including explicit assumed and not-applicable discharges. CPU parent arbitration/store and queue effects remain on the CPU.

The statement-name mapping is source-bound. Actual per-line Callgrind attribution and guarded provider scoring are still pending; I will send their scored table only when those results exist. An intended-path trace is an execution witness and does not itself establish correctness. Deliberate loop findings continue through the existing rewrite-feedback boundary; later Extensa campaign failures stay internal until deliberate team-protocol promotion.

Current repository pointers, all at commit `8959b4dfd149273e89884be87bee9c0adb60e0fc`:

- Candidate/catalog IDs and pattern strategies: `swdb-project/library/rewrite_contracts/bfs_read_offload.yaml`, lines 13–76: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/rewrite_contracts/bfs_read_offload.yaml#L13-L76
- All nine requirement mappings: the same file, lines 252–330: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/rewrite_contracts/bfs_read_offload.yaml#L252-L330
- Target execution witness: the same file, lines 217–226: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/rewrite_contracts/bfs_read_offload.yaml#L217-L226
- Proposal 1.1 content pins and exact shipped-header gate: `swdb-project/docs/reference/bfs-typed-library.md`, lines 56–61: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/docs/reference/bfs-typed-library.md#L56-L61
- Later mode boundary, still proposed: `swdb-project/docs/adr/0009-two-modes-same-evaluator.md` and `0010-extensa-mode-loop.md`, lines 3–12 of each: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/docs/adr/0009-two-modes-same-evaluator.md#L3-L12 and https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/docs/adr/0010-extensa-mode-loop.md#L3-L12

Yan-Ru
