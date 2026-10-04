Hi Eric,

The shared typed-library entries are published at commit `8959b4dfd149273e89884be87bee9c0adb60e0fc` on `yanrujhou_main`. The contract pins DX100 design `dx100-artifact-e4fc4af`, revision `e4fc4afdf894f295442cef3604667a469fab8e62`, and your catalog claim IDs.

L3/L5 visibility, covering waits, and relevant observer/reuse behavior remain named assumptions. Functional certification does not establish target coherence. The parent-gather companion reports negative-hint CAS conflicts and explicit L3 violations for the exact candidate/workload. Observing conflicts with no violation leaves L3 assumed; a zero-race or otherwise inconclusive case does not assure L3 holds. A recorded L3 violation selects a separate CPU-parent-load contract. Independently, a completed target execution that fails a required witness is refuted overall; an incomplete execution is inconclusive. The target companion and first timed gem5 runs have not executed yet.

Primary code has no extra CPU parent probe: fresh-parent loads and initial-degree probes are compiled only into the diagnostic companion, which checks every hint, including nonnegative values. CPU CAS/store/queue behavior remains intact in the primary candidate.

Current repository pointers, all at commit `8959b4dfd149273e89884be87bee9c0adb60e0fc`:

- Catalog identity: `swdb-project/library/rewrite_contracts/bfs_read_offload.yaml`, lines 13–30: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/rewrite_contracts/bfs_read_offload.yaml#L13-L30
- L3/L5 and named ownership: the same file, lines 103–136: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/rewrite_contracts/bfs_read_offload.yaml#L103-L136
- Required target witness and L3 outcome predicates: the same file, lines 217–226 and 332–336: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/rewrite_contracts/bfs_read_offload.yaml#L217-L226 and https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/rewrite_contracts/bfs_read_offload.yaml#L332-L336
- Wait lowering and diagnostic predicate: `swdb-project/library/dx100/dxc_lowering.hpp`, lines 40–64: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/dx100/dxc_lowering.hpp#L40-L64
- Diagnostic-only probe placement: `swdb-project/library/dx100/bfs_read_offload.inc`, lines 45–53: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/dx100/bfs_read_offload.inc#L45-L53
- Completed-failure versus incomplete-run status: `swdb-project/docs/reference/bfs-typed-library.md`, lines 49–54: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/docs/reference/bfs-typed-library.md#L49-L54

Yan-Ru
