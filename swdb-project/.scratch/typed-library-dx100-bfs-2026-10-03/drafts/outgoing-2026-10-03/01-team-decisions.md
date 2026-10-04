Hi Peter, Eric and Josh,

The typed-library implementation and its recorded reviews are published on `yanrujhou_main` at commit `8959b4dfd149273e89884be87bee9c0adb60e0fc`. The 21 seeded entries now have approved shared admission backed by current functional certification. Target gem5 evaluation has not run yet.

Here are the eight Phase 0 decisions implemented for tickets 1–37:

1. One typed library separates reference semantics, intrinsic lowerings, library operations and rewrite contracts. Normative YAML/code identities are separate from execution evidence and reviews.
2. ArchEvolve mode evaluates one supplied proposal with bounded build/correctness repair. The later Extensa campaign will share the evaluator, with its own budgets, selection and promotion. This delivery does not implement that later campaign.
3. Functional-model certification is simulated pre-check evidence. An implementation requires correctness on its stated hardware target, including required completion/execution witnesses.
4. Peter v1.1 section 5 retains CPU CAS, the redundant parent store and CPU queue push. E1–E5 address per-thread ownership, register operands, lifecycle, capacity and covering waits.
5. L3/L5 visibility and DX100 wait coverage remain named assumptions. A parent-gather diagnostic can observe or refute L3, or leave the case inconclusive. A recorded L3 violation requires a separate CPU-parent-load contract. A completed target run that fails a required witness is refuted overall; an incomplete run is inconclusive.
6. The first gem5 comparison will use a fresh scalar baseline, Kronecker18 and uniform18 at source 0, no region pairs, and deterministic point ratios. The historical T17 author-code performance is context only.
7. Compact correctness, witness-chain, region and companion evidence stays. Historical debug/checkpoint cleanup requires an exact reviewed listing; team-cited payloads stay protected.
8. Profiling/scoring tables carry their evidence basis and provider provenance. Per-line Callgrind attribution is simulated ground truth, with rank/contradiction reporting and no target-performance claim.

Published pointers:

- Typed library, certification, admission and proposal boundaries: `swdb-project/docs/reference/bfs-typed-library.md`, lines 5–61, commit `8959b4dfd149273e89884be87bee9c0adb60e0fc`: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/docs/reference/bfs-typed-library.md#L5-L61
- Contract provenance, legality assumptions and target witness: `swdb-project/library/rewrite_contracts/bfs_read_offload.yaml`, lines 1–30, 93–136 and 212–226, same commit: https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/rewrite_contracts/bfs_read_offload.yaml#L1-L136 and https://github.com/petecao/ArchEvolve/blob/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/library/rewrite_contracts/bfs_read_offload.yaml#L212-L226
- Proposed ADRs: `swdb-project/docs/adr/0007-typed-library.md`, `0008-target-bound-correctness.md`, `0009-two-modes-same-evaluator.md`, `0010-extensa-mode-loop.md`, and `0011-raw-output-retention.md`, lines 3–12 of each, same commit: https://github.com/petecao/ArchEvolve/tree/8959b4dfd149273e89884be87bee9c0adb60e0fc/swdb-project/docs/adr
- Original hardware handoff package: `runs/bfs-maple-comparison-v0.1/case-01/handoffs/candidate-02/candidate.yaml`, lines 1–39, commit `ab5a5d3`: https://github.com/petecao/ArchEvolve/blob/ab5a5d3/runs/bfs-maple-comparison-v0.1/case-01/handoffs/candidate-02/candidate.yaml#L1-L39

The ADRs remain proposed. The working license is Apache-2.0 WITH LLVM-exception under my authorization; Peter's actual confirmation is pending, and I will ask him separately. No target correctness or performance result is implied by this note.

I will send Josh the statement-name mapping separately so its format and bindings are easy to review.

Yan-Ru
