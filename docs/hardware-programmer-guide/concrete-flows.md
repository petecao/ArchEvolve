# Three concrete operand/tuple flows

Bound to the published catalog at `e4a709c`. These are small semantic illustrations from existing claims, not executable APIs, new prototypes, measured runs, or numerical-equivalence demonstrations. Symbolic values avoid assuming an unbound payload datatype or width.

## MAPLE: two required values from an indexed interval

**Input:** the caller has already established interval `[2,4)`, with `B[2]=7`, `B[3]=3`, `A[7]=P`, and `A[3]=Q`. The bases, indexes, and storage are valid, and the source arrays remain stable until consumption. The desired operands are `P`, then `Q`.

| Step | Actor and action | Output / boundary |
|---|---|---|
| 1 | CPU establishes the interval and binds/configures a queue and the A/B bases for the paper's `LIMA_PRODUCE` operation. | A submitted required-value range; this is not an invented C signature or register encoding. |
| 2 | MAPLE reads adjacent B-index data in chunks, forms A addresses word by word, and feeds fetches into its produce path. | Requests for `A[7]` and `A[3]`. A B chunk does not imply sorting or merging arbitrary A addresses. |
| 3 | Pointer fetching reserves FIFO slots; transaction/slot association places arriving replies in their slots. | The queue's logical result sequence is `P,Q`, even if the memory replies arrive in another order. |
| 4 | CPU consumes queue values. | A consume-load response supplies the operand; the earlier produce-store acknowledgement does not certify operand readiness. |

**CPU work left:** compute the interval and any dependencies needed to obtain it, establish bases/bounds and queue ownership/counts, consume operands, and perform arithmetic and application updates. The cited MAPLE API does not establish a CAS executor. Keep fetched arrays stable through use; a coherent fetch does not make a queued value track a later CPU write. Queue reuse, overall drain and observer ordering require their own binding. Concrete C types, index encoding and full lifecycle ABI remain unknown.

Evidence: [maple-api](https://github.com/petecao/ArchEvolve/blob/e4a709c7beababfedaa0e7696ad86d538fbc5268/catalog/hardware-v0.1.yaml#L586), [maple-lima](https://github.com/petecao/ArchEvolve/blob/e4a709c7beababfedaa0e7696ad86d538fbc5268/catalog/hardware-v0.1.yaml#L597), [maple-queue-order](https://github.com/petecao/ArchEvolve/blob/e4a709c7beababfedaa0e7696ad86d538fbc5268/catalog/hardware-v0.1.yaml#L608), [maple-acknowledgement](https://github.com/petecao/ArchEvolve/blob/e4a709c7beababfedaa0e7696ad86d538fbc5268/catalog/hardware-v0.1.yaml#L628), [maple-stable-data](https://github.com/petecao/ArchEvolve/blob/e4a709c7beababfedaa0e7696ad86d538fbc5268/catalog/hardware-v0.1.yaml#L647), [maple-future-atomics](https://github.com/petecao/ArchEvolve/blob/e4a709c7beababfedaa0e7696ad86d538fbc5268/catalog/hardware-v0.1.yaml#L659).

## TMU Fig.8: one even-length CSR row

**Input:** one row has CSR interval `[4,6)`. Its columns are `idxs[4]=2` and `idxs[5]=5`, its stored values are `m0,m1`, and vector values are `b[2]=v0`, `b[5]=v1`. This row has two entries, so the example does not resolve the paper's omitted odd-row/padding ABI. Fig.8's two lanes are an illustration, not an evaluated-system tuning rule.

| Step | Actor and action | Output / boundary |
|---|---|---|
| 1 | TMU's configured row-pointer traversal supplies row begin/end, which are broadcast to two range lanes with offsets 0/1 and stride 2. | Lane ordinals 4 and 5 for this row. |
| 2 | The traversal lanes load column indexes and nonzero values; indexes drive vector-b loads. | Paired operands `[m0,m1]` and `[v0,v1]`. |
| 3 | LockStep marshals the operand vectors; GITE supplies the `ri` callback identity. TG output state machines preserve callback/operand order through outQ. | Required operands and the callback identity reach the CPU consumer when that output is delivered. |
| 4 | CPU `ri` multiplies/reduces/accumulates. GEND supplies row-end `re`; CPU `re` stores the row result and resets its accumulator. | The row's arithmetic/output store is CPU work, not a TMU scatter or multiply executor. |

**CPU work left:** provide the callback dispatch and initialized accumulator/row index; perform multiplication, reduction, accumulation and the output store under the application's numerical rules. Software also supplies valid CSR/vector bounds, source/outQ ownership and progress with the consumer. Full-chunk double buffering is described; final partial-chunk delivery, consumed acknowledgement/reuse, physical response tags and full fault/drain encoding remain unknown. A row-end callback is not a general global-memory visibility proof.

Evidence: [tmu-fig8](https://github.com/petecao/ArchEvolve/blob/e4a709c7beababfedaa0e7696ad86d538fbc5268/catalog/hardware-v0.1.yaml#L1624), [tmu-cpu](https://github.com/petecao/ArchEvolve/blob/e4a709c7beababfedaa0e7696ad86d538fbc5268/catalog/hardware-v0.1.yaml#L1635), [tmu-outq](https://github.com/petecao/ArchEvolve/blob/e4a709c7beababfedaa0e7696ad86d538fbc5268/catalog/hardware-v0.1.yaml#L1666), [tmu-unknowns](https://github.com/petecao/ArchEvolve/blob/e4a709c7beababfedaa0e7696ad86d538fbc5268/catalog/hardware-v0.1.yaml#L1728).

## COBRA: collect three Neighbor-Populate tuples

**Input:** software supplies edge tuples `(src,dst) = (2,7), (0,5), (2,1)`. Assume a bound configuration whose final bin partition includes keys `[0,2)` and `[2,4)` and sufficient private tuple capacities. This illustrates a partition; it does not prescribe ways, tuple-byte encoding, or a register ABI.

| Step | Actor and action | Output / boundary |
|---|---|---|
| 1 | CPU computes per-thread/bin counts and starting offsets, allocates bins, and configures each level through the paper's `bininit` setup. | Storage/partition configuration before tuple ingestion. |
| 2 | CPU submits index/value tuples with `binupdate`; COBRA appends them to selected L1 C-Buffers. | Buffered tuples, not application destination stores or returned old values. |
| 3 | Full buffers move through the hierarchy and are unpacked/repartitioned by progressively narrower index ranges; LLC output materializes thread-private bins. | Bin `[0,2)` contains `(0,5)`; bin `[2,4)` contains both `(2,7)` and `(2,1)`. Treat these as tuple collections, without an extra global ordering promise. |
| 4 | `binflush` pushes residual tuples through all levels. Software begins Accumulate only after every tuple has reached its bin and the required visibility is established. | CPU-visible materialized bins for software destination updates. The exact done/ACK/fence binding is not supplied by the inspected paper. |

**CPU work left:** generate tuples, compute counts/offsets and capacities, configure the hierarchy, establish producer/consumer ownership and the completion boundary, then read bins and perform Neighbor-Populate/Accumulate updates. The paper's mapping permits its changed neighbor order; this is not permission to reorder arbitrary floating-point or noncommutative work. COBRA collects tuples and preserves multiplicity; it does not merge same-index values arithmetically. Destination arithmetic/atomicity remains a software responsibility under the selected mapping.

Evidence: [cobra-init](https://github.com/petecao/ArchEvolve/blob/e4a709c7beababfedaa0e7696ad86d538fbc5268/catalog/hardware-v0.1.yaml#L1759), [cobra-insert](https://github.com/petecao/ArchEvolve/blob/e4a709c7beababfedaa0e7696ad86d538fbc5268/catalog/hardware-v0.1.yaml#L1769), [cobra-hierarchy](https://github.com/petecao/ArchEvolve/blob/e4a709c7beababfedaa0e7696ad86d538fbc5268/catalog/hardware-v0.1.yaml#L1749), [cobra-memory-bins](https://github.com/petecao/ArchEvolve/blob/e4a709c7beababfedaa0e7696ad86d538fbc5268/catalog/hardware-v0.1.yaml#L1802), [cobra-flush](https://github.com/petecao/ArchEvolve/blob/e4a709c7beababfedaa0e7696ad86d538fbc5268/catalog/hardware-v0.1.yaml#L1813), [cobra-phase-boundary](https://github.com/petecao/ArchEvolve/blob/e4a709c7beababfedaa0e7696ad86d538fbc5268/catalog/hardware-v0.1.yaml#L1737).
