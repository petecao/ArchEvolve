# Acceleration mechanism and desired hardware semantics

Peter's request adds a layer between a matching `gather` capability and an implementation: describe the data path, request handling, observable result semantics, and the conditions under which the mechanism could help. A functional load result alone does not describe latency tolerance, request grouping or scheduling.

The generator now emits `hardware-behavior.md` and `.yaml` in every future candidate package. The [October 6 behavior handoff](../handoffs/hardware-behavior-20261006/README.md) supplies compact sheets for the two BFS inputs, with DX100 reads, MAPLE queue supply and MAPLE LLC assistance kept separate.

## What is included

1. **Software request:** submitted operands, source operation/mode and target accesses.
2. **Observable semantics:** result form, valid lanes/entries, iteration or queue association, duplicate handling, ordering scope, completion event and visibility obligations.
3. **Internal mechanism:** buffering, grouping, request issue, dependencies, response placement and storage reuse, with source locators.
4. **Conditional benefit:** why those mechanisms may help, the workload conditions they need and their limits. Derived reasoning is labeled separately from catalog hypotheses; neither is a measured speedup.
5. **Implementation obligations:** capacity, numeric bounds, ownership/freshness, completion/reuse, reference settings and unknowns. Future evaluator observations are requested measurements, not invented values.

The desired semantics are the existing selected operation contracts, conditional on their mapping requirements. This sheet does not synthesize a new C ABI, prescribe a complete state machine, broaden supported types/operations or approve a composed accelerator. Yan-Ru's concrete typed-library contracts remain separate.

## DX100: mechanism-level explanation

For the **public e4fc4af required indirect-load path**:

- Wait for usable index/condition elements and instruction admission. These checks do not prove global alias safety.
- Compute/translate target addresses and group them by configured physical slice/row and aligned line. Eligible accesses to an unsent line share its line entry while retaining each logical iteration and word offset.
- With reordering enabled, the source-described generator cycles through active slices and row/line records. This is a fixed policy in the inspected model, not a claim of global address sorting, downstream DRAM command order or adaptive open-row intelligence.
- Transport can stall and retry; generated work is not necessarily accepted work. Source-described cache/memory routing and arbitration have their own scope and limits.
- Returned lines fan out to their original iteration slots, including duplicate consumers. Changing request order must not lose the original result association or collapse logical occurrences.
- Offset, line and row state have distinct lifetimes. Local readiness/finish still does not discharge CPU observer visibility, synchronization or safe reuse obligations.

Grouping eligible same-line reads may reduce redundant requests, while independent issue across available memory resources may improve service overlap. This benefit is conditional on the actual address distribution, ready independent work, finite tables, transport and memory routing. Tile setup, waits, dependent index production and group-capacity stalls can erase it. These are reasoning hypotheses derived from Eric's located mechanism descriptions, not measured BFS gains.

The paper edition and public source model remain distinct. No finite illustrative scaffold, private/current model, source container or reference timing value is promoted to a universal RTL implementation requirement.

## MAPLE: mechanism-level explanation

- Software binds/configures queues and supplies pointers or bounded LIMA intervals. CPU address dependencies not covered by the described operation remain in software.
- A reservation owns finite FIFO capacity without establishing payload readiness. Pointer issue acknowledgement precedes the memory reply.
- Independent requests can be in flight; replies use reserved-slot identity to place values even when they arrive out of order. Ordinary queue consumption requires the relevant head payload to be ready.
- Capturing/dequeuing a value can release queue storage before its later NoC response or CPU arithmetic/effects finish. Queue capacity release, CPU value use and safe rebind/drain are separate obligations.
- `LIMA_PRODUCE` supplies required queue values. Speculative LIMA/pointer prefetch supplies LLC assistance; it does not replace demand-load or update results.
- Index-stream chunks do not prove arbitrary target-A address sorting/coalescing. Queue values are not kept coherent after fetch; source stability and deployment translation/fault/reuse obligations remain explicit.

The intended benefit is useful runahead: asynchronous supply overlaps long memory latency with other accesses or computation. It depends on independent requests, queue capacity, producer/consumer scheduling and core-to-engine communication cost. Head blocking, dependencies, transport or translation overhead and too little runahead can limit it. No current BFS speedup is asserted.

## Provenance and integration boundary

The sheets use Eric's source-reviewed catalog **0.1.10** from [commit 1825dfd9fdbf3ad86a0c261b0e86319475fa15f9](https://github.com/petecao/ArchEvolve/blob/1825dfd9fdbf3ad86a0c261b0e86319475fa15f9/catalog/hardware-v0.1.yaml), a pinned input from his `eric/maple-catalog-review-20261001` branch. [The preserved snapshot provenance](../examples/received/eric-hardware-catalog.20261006.provenance.json) binds its exact bytes. His [DX100 walkthrough](https://github.com/petecao/ArchEvolve/blob/1825dfd9fdbf3ad86a0c261b0e86319475fa15f9/docs/dx100-internal-mechanisms.md) and [mechanism handoff](https://github.com/petecao/ArchEvolve/blob/1825dfd9fdbf3ad86a0c261b0e86319475fa15f9/docs/mechanism-handoff-2026-10-06/README.md) supply the detailed context.

Eric's update was merged to main in PR #3 while these sheets were being published. The pinned input matches the merged 0.1.10 catalog. This generator change does not regenerate the October 1 handoffs cited by Yan-Ru's library. Earlier certifications remain evidence for their original content pins; a future executable proposal must deliberately re-bind the chosen normative catalog, signatures, library content and execution evidence. These descriptions are not a renewed certification.

The current BFS parent-read/CAS mapping still needs its named visibility/freshness assumptions. Monotonic parent updates do not themselves establish the initial-value or queue/offset visibility required by that mapping. Describing the accelerator does not discharge those assumptions or certify correctness/performance.

## Reproduce future full packages

```sh
.venv/bin/python -m archevolve \
  --input examples/received/bfs-sparse.features.v1.2.yaml \
  --input examples/received/bfs-fully-connected.features.v1.2.yaml \
  --catalog examples/received/eric-hardware-catalog.20261006.yaml \
  --methods examples/received/peter-measurement-methods.v1.2.yaml \
  --source-context examples/bfs.source-observations.yaml \
  --focus-design dx100-artifact-e4fc4af \
  --focus-design maple-isca2022 \
  --compare-design dx100-artifact-e4fc4af \
  --compare-design maple-isca2022 \
  --max-candidates 4 \
  --output-dir runs/bfs-hardware-behavior-new
```

Choose a fresh output directory to preserve published content pins. The compact October 6 handoff contains behavior sheets and their originating draft contracts; this command also produces the full query/diagram pipeline. All generation remains offline.
