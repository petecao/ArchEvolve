# BFS intrinsic handoff — Eric's hardware evidence catalog

Current inputs: Peter's v1.2 reports. Current catalog: `hardware-catalog-v0.1`, data revision `0.1.2`, merged from Eric's PR #2. The offline adapter now queries **source-scoped operation contracts**, replacing the provisional family sketches as the primary handoff.

These are **operation-interface views**, not synthesized physical block diagrams, proofs of composition, final C signatures, or performance winners. All requirements remain to be discharged for the actual mapping. The original source has not been rewritten.

## Start here

| Workload | Interface option | View | Full contracts and evidence |
|---|---|---|---|
| Sparse BFS | DX100 artifact read operations | [Image](../runs/bfs-hardware-v0.1/case-01/diagrams/candidate-02.png), [Mermaid](../runs/bfs-hardware-v0.1/case-01/diagrams/candidate-02.mmd) | [Hardware request](../runs/bfs-hardware-v0.1/case-01/hardware-request.yaml), candidate scope `dx100-artifact-e4fc4af:read_execute` |
| Sparse BFS | Terminus CAS configuration | [Image](../runs/bfs-hardware-v0.1/case-01/diagrams/candidate-03.png), [Mermaid](../runs/bfs-hardware-v0.1/case-01/diagrams/candidate-03.mmd) | [Hardware request](../runs/bfs-hardware-v0.1/case-01/hardware-request.yaml), scope `terminus-micro2024-cas:update_execute` |
| Sparse BFS | Prodigy prefetch assistance | [Image](../runs/bfs-hardware-v0.1/case-01/diagrams/candidate-04.png), [Mermaid](../runs/bfs-hardware-v0.1/case-01/diagrams/candidate-04.mmd) | [Hardware request](../runs/bfs-hardware-v0.1/case-01/hardware-request.yaml), scope `prodigy-hpca2021:read_assist` |
| Fully connected BFS | DX100 artifact read operations | [Image](../runs/bfs-hardware-v0.1/case-02/diagrams/candidate-02.png), [Mermaid](../runs/bfs-hardware-v0.1/case-02/diagrams/candidate-02.mmd) | [Hardware request](../runs/bfs-hardware-v0.1/case-02/hardware-request.yaml) |
| Fully connected BFS | Terminus CAS configuration | [Image](../runs/bfs-hardware-v0.1/case-02/diagrams/candidate-03.png), [Mermaid](../runs/bfs-hardware-v0.1/case-02/diagrams/candidate-03.mmd) | [Hardware request](../runs/bfs-hardware-v0.1/case-02/hardware-request.yaml) |
| Fully connected BFS | Prodigy prefetch assistance | [Image](../runs/bfs-hardware-v0.1/case-02/diagrams/candidate-04.png), [Mermaid](../runs/bfs-hardware-v0.1/case-02/diagrams/candidate-04.mmd) | [Hardware request](../runs/bfs-hardware-v0.1/case-02/hardware-request.yaml) |

Candidate 1 in both cases is unchanged CPU execution as an unmeasured comparison; no new intrinsic is needed for it.

The reports now retrieve overlapping designs because both execute the same classes of BFS operations. Their workload/phase evidence stays separate. Similar retrieval is not a claim that both workloads should use the same architecture or that their speedups would be equal. The operation list foregrounds gather for the reported sparse case and stream load for the reported near-unit case; diagram placement is not a performance ranking.

## DX100: read interfaces to specify

The artifact record supplies code-observed evidence for:

- `dxc-stream_load`: native stream-load primitive.
- `dxc-gather`: native indirect load using a supplied index tile.
- `dxc-ranged-gather`: a **documented range-generation plus indirect-load sequence**, not one new instruction.

The workload requests int32 payloads and 32-bit loaded indices/range bounds where established. The catalog additionally requires correct numeric domains, active-lane/produced-size handling, region binding, continuation, ordering, and visibility. A 32-bit index encoding alone does not prove a valid byte-offset product.

The input node quotes an excerpt of the **design-wide** software contract; it is not an operation-specific operand list. The complete interface, exact operation realization, result validity, completion, type constraints, requirements, source locators, and limitations are retained in the YAML.

Some matched reads target mutable `parent` state. A read label does not establish immutability or legal hoisting/buffering. Keep CAS semantics and establish an appropriate freshness/ownership/synchronization mapping before rewriting anything.

**The inspected DX100 artifact's CAS path is explicitly excluded.** Returned-old data from another update operation does not supply compare-and-swap semantics. The DX100 paper's unknown CAS record is retained in the trace as missing evidence, not promoted to a diagrammed executor.

## Terminus: CAS is a separate, conditional option

The `terminus-micro2024-cas` record provides paper-specified CAS with a success flag. The typed BFS query still returns **needs_evidence** because the examined payload/index domains are not recorded. Partition exclusion, global concurrency, result ordering, and software/framework requirements must also be established.

This is a potential update-offload mapping after proof, not a claim that the whole project must always keep atomics on the CPU. The separate deferred Terminus configuration retains CPU execution and must not inherit the native-CAS configuration's behavior.

Peter should derive constraints for the expected value, replacement value, returned success, ordering, and discovery/queue effects only after the missing mapping evidence is resolved. No code change or executable signature is supplied here.

## Prodigy: assistance, not replacement

Prodigy consumes a Data Indirection Graph and provides nonbinding cache-fill hints. It does not replace the program's gather result or its CAS. Its typed interface details still need evidence. Any software-facing configuration/hint interface is different from an intrinsic that returns the requested load/update result.

## Parameters and next review

`parameter_contract` preserves Eric's original states. `fixed_reference` values (such as the artifact's 16,384-element tile) are reference settings, not selected tuning values. Unknown domains remain unknown. `selected_configuration` is empty. The diagrams do not infer physical port widths or wiring from software payload/index types.

For each chosen mapping, review the YAML's `operation_options`, `source_evidence`, `requirements`, `missing_evidence`, and `software_handoff` with Eric. Establish source/statement binding, operand domains, masks/validity, completion/visibility, and allowed edits before Yan-Ru rewrites a loop.

Full context: [run overview](../runs/bfs-hardware-v0.1/README.md), [sparse report](../runs/bfs-hardware-v0.1/case-01/diagrams/preview.md), [dense report](../runs/bfs-hardware-v0.1/case-02/diagrams/preview.md), [Eric's handoff](hardware-catalog-handoff.md), and [integration details](hardware-catalog-integration.md).

The earlier seed-based SPARTA and BFS runs are retained as historical examples. Their manually sketched family partitions are not the current evidence-backed interface handoff.
