Date: 2026-10-08 (ET)

Independent source-only review: sparse read-budget archive builder R2.

Selected source: /private/tmp/lanl17_build_sparse_read_budget_correction_custody_archive_20261008_a1_r2.py
22060 bytes; SHA256 4f1d57a1aa72b43a3bd3d38d9696828cb9fb0f54866b7a243d0cf06e6668a660.
Complete R1→R2 diff: /private/tmp/lanl17-sparse-read-budget-correction-archive-builder-r2-complete-r1-derivation-20261008-a1.diff
4208 bytes; SHA256 d3a0daa7a853d109b8d913a590568160b71291d3f2c76aef0cd5ddb5c2a769a3.
Preserved R1: 22060 bytes; SHA256 ffdb5f8a45596b245ac63e0abf959e711144e766bda953dbe3df6cc59a8f26d3.

Accepted narrow count correction. Exact replacement 4567→4834, 4742→5009 and README 4,567→4,834 reconstructs R2; its complete unified diff regenerates byte-exactly. Only repository_state and main's README literal differ in AST; the other 19 definitions match. Routes, policies, pins, limits and publication checks are unchanged.

Independent read-only native Git ls-tree -r -z --full-tree inventories at immutable commits:
- 5e12a9796432654d88def24ecea617d16ca605b2: 4,834 rows; SHA256 75ca629f4d117c8cac3aa05ee86df0c61846575ba90b19828753c5706e56ee71.
- 28446e8682b0a55ef4bb2050de9c46e072c39ce6: 5,009 rows; SHA256 ae8e7007bd685b8a6a8ecee8d8d092fc224ba7ce87ce90b69ed7126feb992f5e.
- The parent's exact old 17-library-preserving-sparse-retirement-custody-20261008-a1 prefix: 175 rows; SHA256 b8d1c57dfb975d00ae0c61075e27e17a42dff618412feb0e02d5121435ad23eb.
Base and old-prefix paths are disjoint. The complete parent path/mode/type/blob rows equal their exact union, retaining every original blob/mode and all 175 earlier archive entries. R2's 4,834+175=5,009 gate matches its unchanged full-tree scope.

Count-history qualification: the current scientific base's swdb-project/ subtree has 4,384 entries. The inherited 4,567 shorthand is not this commit's current subtree count and is not used as verified evidence here. A preliminary local review assertion expecting that shorthand stopped before writing this note; it invoked no selected source or archive. The root-reported R1 pre-prefix actual refusal remains its original failure history.

No concrete issue found in this narrow R2 correction. This review ran only local source parsing/hashing and read-only native Git inventories; no selected import/main/test, archive/compression, SSH, project/worktree or Git mutation occurred. It establishes neither R2 runtime success nor final-ledger/capacity/scientific admission.
