# Phase 0 decision note — draft for Yan-Ru

Date: 2026-10-03 ET
Status: draft, not sent

Source binding: ArchEvolve `yanrujhou_main`, intrinsic specification at `0b56895`, package/mapping available at `ab5a5d3`. New implementation pointers below refer to the current branch and need the final commit when sent.

1. One typed library separates reference semantics, intrinsic lowerings, library operations and rewrite contracts. Normative code and YAML hashes stay separate from evidence/reviews.
2. ArchEvolve mode runs supplied proposals once, with bounded build/correctness repair. Extensa mode is a later campaign loop with separate promotion and budgets; both share the evaluator.
3. Functional-model certification is simulated pre-check evidence. DX100 becomes an implementation only after target-bound gem5 correctness; a completion witness belongs to that check.
4. Peter v1.1 section 5 data flow is retained. CPU CAS, the redundant parent store and queue push stay on the CPU. E1–E5 fix ownership, register operands, lifecycle, capacity and completion.
5. DX100 wait coverage and CPU-to-accelerator visibility remain named assumptions owned by Eric. The parent-gather race case can observe, refute or leave L3 inconclusive; only a recorded L3 violation selects the fallback.
6. The first gem5 protocol has a fresh scalar baseline, Kronecker18 and uniform18 source0, no region pairs, and deterministic point ratios. T17 author-code performance stays context only.
7. Only bulky checkpoint/debug payloads qualify for pruning; compact evidence and team-cited traces stay. Historical cleanup requires review of an exact listing.
8. Profiling claims carry their basis and provider provenance beside facts. Per-line Callgrind gives simulated ground truth; ranks and contradiction rules are reported without a performance claim.

Working license: Yan-Ru authorized proceeding with Apache-2.0 WITH LLVM-exception; Peter confirmation is still requested. Eric follow-ups: L3/L5 visibility, region registration, cross-core issue assembly. Peter follow-up: original performance command/output.

## Statement-name mapping

| Statement | DX100 e4fc4af lines | Array | Josh request | SWDB access/step |
|---|---|---|---|---|
| bfs-td-frontier | benchmarks/gapbs/src/bfs.cc:240 | queue.shared | access-01-read | td-frontier-read/0 |
| bfs-td-row-bounds | benchmarks/gapbs/src/bfs.cc:241 | VertexOffsets | access-02-read | td-row-bounds-read/1; td-row-end-read/1 |
| bfs-td-neighbor | benchmarks/gapbs/src/bfs.cc:242 | g.out_neighbors_ | access-03-read | td-neighbor-read/2 |
| bfs-td-parent-read | benchmarks/gapbs/src/bfs.cc:243 | parent | access-04-read | td-parent-read/3 |
| bfs-td-parent-cas | benchmarks/gapbs/src/bfs.cc:247 | parent | access-04-update (CPU arbitration) | td-parent-cas/3 |
| bfs-td-parent-store | benchmarks/gapbs/src/bfs.cc:248 | parent | access-04-update (retained CPU store) | td-parent-store/3 |
| bfs-td-queue-append | benchmarks/gapbs/src/bfs.cc:249 | queue.shared (through thread-local queue) | No distinct package request; retained CPU queue effect | td-queue-append/0 |

The seven statement IDs map eight terminal accesses because row-bounds contains both offsets. Read-only handoff source: `runs/bfs-maple-comparison-v0.1/case-01/handoffs/candidate-02/candidate.yaml` at `ab5a5d3`. No handoff file is edited.
