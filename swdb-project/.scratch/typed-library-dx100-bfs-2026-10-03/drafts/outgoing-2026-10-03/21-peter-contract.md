Hi Peter,

The reviewed BFS read-offload contract is published; here is its exact YAML source:

`swdb-project/library/rewrite_contracts/bfs_read_offload.yaml`, commit `8959b4dfd149273e89884be87bee9c0adb60e0fc`, SHA-256 `a7251e256aadc175ba3c9766c457f79ee1991df5784a9b9de84a650157d5d8eb`:
https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/rewrite_contracts/bfs_read_offload.yaml

The contract pins your v1.1 section 5 specification (lines 6–12) and the original hardware handoff/catalog identity (lines 13–30). It preserves CPU CAS, the intentionally redundant parent store and queue push (L4, lines 115–124). L3/L5 and observer/reuse behavior remain assumptions rather than target guarantees (lines 103–136, 280–305). All nine hardware requirements have explicit discharge mappings (lines 252–330).

The required target witness is at lines 217–226; E1–E5 and the inclusive 1,073,741,823 count-bound note are at lines 337–346. The 21 seeded entries now have recorded shared approval backed by current functional certification. Target gem5 correctness, coherence observations and performance remain unexecuted.

Related implementation at the same commit:

- `swdb-project/library/dx100/dxc_lowering.hpp`, lines 13–65: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/dx100/dxc_lowering.hpp#L13-L65
- `swdb-project/library/dx100/bfs_read_offload.inc`, lines 11–72: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/dx100/bfs_read_offload.inc#L11-L72
- `swdb-project/library/dx100/peter-section5.patch`, lines 1–139: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/dx100/peter-section5.patch#L1-L139

Yan-Ru
