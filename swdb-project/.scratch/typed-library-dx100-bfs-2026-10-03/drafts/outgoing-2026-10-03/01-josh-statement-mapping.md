Hi Josh,

Here is the frozen statement-name mapping for the BFS top-down read-offload loop. The source lines refer to DX100 revision `e4fc4afdf894f295442cef3604667a469fab8e62`, `benchmarks/gapbs/src/bfs.cc`; the access names and step positions refer to the original ArchEvolve handoff at commit `ab5a5d3`.

| Statement ID | DX100 source line | Array/effect | Your request | SWDB access/step |
|---|---|---|---|---|
| bfs-td-frontier | 240 | queue.shared read | access-01-read | td-frontier-read / 0 |
| bfs-td-row-bounds | 241 | VertexOffsets read | access-02-read | td-row-bounds-read and td-row-end-read / 1 |
| bfs-td-neighbor | 242 | g.out_neighbors_ read | access-03-read | td-neighbor-read / 2 |
| bfs-td-parent-read | 243 | parent read | access-04-read | td-parent-read / 3 |
| bfs-td-parent-cas | 247 | parent CPU arbitration | access-04-update | td-parent-cas / 3 |
| bfs-td-parent-store | 248 | retained redundant parent CPU store | access-04-update | td-parent-store / 3 |
| bfs-td-queue-append | 249 | queue.shared through the thread-local queue | retained CPU queue effect; no separate package request | td-queue-append / 0 |

Seven statement IDs map eight terminal accesses because row-bounds covers both offsets. The format keeps a stable statement ID beside revision/path/line, array/effect, request ID and SWDB step. Per-line profiling and provider-scoring columns will be added only after the real profile and guarded provider run; this mapping is not a scored statement table.

Source package: `runs/bfs-maple-comparison-v0.1/case-01/handoffs/candidate-02/candidate.yaml`, lines 1–39 and the context statements beginning at line 57, commit `ab5a5d3`: https://github.com/petecao/ArchEvolve/blob/ab5a5d3/runs/bfs-maple-comparison-v0.1/case-01/handoffs/candidate-02/candidate.yaml#L1-L57

The published contract retains the original hardware-candidate/catalog IDs and binds the selected read strategies: `swdb-project/library/rewrite_contracts/bfs_read_offload.yaml`, lines 13–76 and 252–330, commit `8959b4dfd149273e89884be87bee9c0adb60e0fc`: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/rewrite_contracts/bfs_read_offload.yaml#L13-L76 and https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/rewrite_contracts/bfs_read_offload.yaml#L252-L330

Admission and exact shipped-header rules: `swdb-project/docs/reference/bfs-typed-library.md`, lines 56–61, same commit: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/docs/reference/bfs-typed-library.md#L56-L61

Please flag any mismatch in these names or the format. The original handoff files are unchanged.

Yan-Ru
