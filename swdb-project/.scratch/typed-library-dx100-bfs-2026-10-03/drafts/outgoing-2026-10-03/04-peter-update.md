Hi Peter,

The typed-library work is published at commit `8959b4dfd149273e89884be87bee9c0adb60e0fc` on `yanrujhou_main`. The 21 seeded entries have recorded shared approval backed by current functional certification. The supplied BFS patch follows your v1.1 section 5 data flow and keeps CPU CAS, the labeled redundant parent store, and queue push. E1–E5 address ownership, register handles, session/region lifecycle, tile capacity, and covering waits. The inclusive count bound is 1,073,741,823, consistent with section 4 and the byte-offset requirement.

ArchEvolve evaluates one supplied proposal with bounded build/correctness repair. A later Extensa campaign will use the same evaluator but keep experiments, tuning budgets and promotion separate. That campaign is outside tickets 1–37. Paper-facing claims must retain their actual evidence tier: the functional checks are simulated pre-checks, and target gem5 correctness/performance is still pending.

Current repository pointers, all at commit `8959b4dfd149273e89884be87bee9c0adb60e0fc`:

- Contract provenance and L1–L5: `swdb-project/library/rewrite_contracts/bfs_read_offload.yaml`, lines 1–136; E1–E5/bounds note, lines 337–346: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/rewrite_contracts/bfs_read_offload.yaml#L1-L136 and https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/rewrite_contracts/bfs_read_offload.yaml#L337-L346
- Lowering API and diagnostics: `swdb-project/library/dx100/dxc_lowering.hpp`, lines 13–65: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/dx100/dxc_lowering.hpp#L13-L65
- CPU data flow and diagnostic-only probes: `swdb-project/library/dx100/bfs_read_offload.inc`, lines 45–64: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/dx100/bfs_read_offload.inc#L45-L64
- Evidence, content-bound review and submit boundaries: `swdb-project/docs/reference/bfs-typed-library.md`, lines 23–61: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/docs/reference/bfs-typed-library.md#L23-L61
- Proposed library/target/mode/retention ADRs: `swdb-project/docs/adr/0007-typed-library.md`, `0008-target-bound-correctness.md`, `0009-two-modes-same-evaluator.md`, `0010-extensa-mode-loop.md`, `0011-raw-output-retention.md`, lines 3–12 of each: https://github.com/petecao/ArchEvolve/tree/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/docs/adr

These ADRs remain proposed. The working license is Apache-2.0 WITH LLVM-exception under my authorization; your actual confirmation is pending, and I will ask about it separately.

Yan-Ru
