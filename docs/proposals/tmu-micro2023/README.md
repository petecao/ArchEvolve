# TMU MICRO2023 proposal for Eric

This is a source-scoped proposal against ArchEvolve `6868383615c8aa89752923850d1bf0c170b6ba0b`, for the **Tensor Marshaling Unit** in [Siracusa et al., MICRO2023](https://doi.org/10.1145/3613424.3614284), not the 2025 Manipulation Unit. [proposed-catalog.json](proposed-catalog.json) is a standalone v0-shaped proposal with one published **mapping** record, located claims, prerequisites and exclusions. It has not been installed in the production catalog. [provenance.json](provenance.json) binds the cached institutional PDF and prior research handoff; no paper bytes are redistributed or newly retrieved.

The operation is `read / csr_spmv_two_lane_operand_event_supply / execute`: TMU supplies required operands and callback events, while the CPU performs multiplication, reduction, accumulation and result stores. The role describes operand supply, not execution of all SpMV. It is neither a speculative prefetch nor a general gather ABI. Generic `gather` queries must not retrieve this mapping.

## Small Fig. 8 walkthrough

Locators below use **1-based PDF pages** in the exact 15-page institutional manuscript with SHA-256 `d8ba773f792f0950abbb6cbd19a31f68619a3546813345b5c0a1d672dafc95e2`. This corrects approximate page references in the integrated handoff: Table 1 is p5, Fig. 8 is p6, §§5.2–5.4 are p7. Fig. 8 was also inspected as a rendered PDF page.

1. `DnsFbrT(0,num_rows)` scans CSR rows, loading `ptrs[i]` and `ptrs[i+1]`. `BCast` sends the row interval to the next layer (Fig. 8 lines 2–5).
2. Two `RngFbrT` lanes scan that interval with stride 2, offsets 0 and 1. Each loads `idxs[p]`, `vals[p]`, then `b[idxs[p]]`. The dependent vector lookup is a chained memory stream; the loaded matrix values and row structure are also required inputs (lines 8–15; Table 1/2, p5).
3. `LockStep` collects the two lanes into `nnz_vals` and `vec_vals`. `GITE` registers CPU `ri` with those operands; `GEND` registers CPU `re` without operands (lines 16–21). Fig. 6, p6, assigns arithmetic and `x[i++] = sum` to the CPU.
4. For an illustrative row with three entries, the first iteration supplies positions `(beg,beg+1)`, and the next supplies `(beg+2,inactive)`, followed by `re`. The CPU reduces products of valid operands, stores the sum and advances the output row. Fig. 9, p8, illustrates the analogous stream `ri AB ab; ri C0 c0; re`. This is a logical walkthrough, not an executable buffer layout.

§4.2, p5, permits padding or a marshaled `msk` predicate for boundaries. Fig. 8 does not spell out that ABI. The adapter must establish odd-row validity and an empty-row end event that stores zero, with no fabricated operand iteration. It must also establish its numerical equivalence policy: vector reduction need not be bitwise equivalent to scalar accumulation.

## Mechanism evidence and limits

| Primary location | What is established | What it does not establish |
|---|---|---|
| p5 §4.1, Tables 1–2 | Dense constant bounds; Range parent begin/end; Index parent begin plus fixed size; iteration and dependent streams | Integer widths, legal numeric bounds or a concrete instruction ABI |
| pp6–7 §5.1 | Circular, equal-size per-TU streams move together; valid parent bounds and available space gate progress; child element ordinal follows parent ordinal | Physical response tags, slots or duplicate-response policy |
| p7 §5.2 | Active lanes follow prior predicate; all active heads must be valid. Disjunctive consumes minimum-index lanes; conjunctive emits iteration only on all-active match; LockStep consumes active unfinished lanes | An extra merge operation in this Fig. 8 mapping; unsorted-input merge legality |
| p6 §4.3; p7 §5.3 | H/B/T callbacks; serialized TG output FSMs preserve callback/operand order; double-buffered outQ overlaps producer and CPU | Memory-response ordering, consumed acknowledgment, safe chunk reuse, final partial chunk or global completion |
| p7 §5.4 | Cacheline arbitration: outer/leftmost priority, then round-robin TU, configured stream order, queue request order | General coalescer, deduplication, address predictor or fairness bound |
| pp7–8 §5.5; p9 Table 5 | Configured per-lane shared stream storage; evaluated 8 lanes, 4 TGs, 2KB/lane, 128 outstanding requests | Legal tuning ranges; those counts do not choose a new workload configuration |
| pp8–9 §5.6 | Read-only coherent LLC route; thread-private outQ injection into private L2; host L2 TLB/MMU fault handling and retry; quiesce/save/restore | Universal CPU visibility, concurrent source mutation safety, exact outstanding-request drain or replay semantics |
| p9 §6; p9 RTL paragraph | Reported gem5 v20.1.0.0 and SystemVerilog/synthesis evaluation | Public runnable artifact, evaluated source commit or inspected RTL bytes |

The paper's no-shared-read-write-data assumption must remain an explicit mapping obligation. A coherent read route does not prove the ordering or visibility of arbitrary CPU stores, callbacks that mutate inputs, or other cores. `re` is a row callback event, not evidence that its CPU store is globally visible.

## Prerequisites for a mapping or adapter

- Bind valid CSR ranges, aligned value/index ordinals, dense-vector index containment, numeric/address widths and input lifetime.
- Bind CPU callback dispatch, initialized accumulation/row state, output storage and numerical policy.
- Bind inactive lanes, odd and empty rows, source/output aliasing and concurrency consistent with paper-private source/outQ assumptions.
- Allocate TU/TG streams and capacities; establish progress under producer/CPU backpressure. Fig. 8's two lanes and Table 5's evaluated eight lanes are separate reference contexts.
- Resolve physical response association; concrete configuration ABI; chunk ready/consumed/reuse and final partial delivery; fault/retry/drain/cancellation/context-switch replay; observer visibility before implementation.

All of these remain returned requirements, including the unknown contracts. Retrieval discharges none of them. No implementation, simulation, speedup or correctness claim follows from this proposal.

## Schema fit and validation

v0 accepts an exact string subtype and `mapping_role` realization. That preserves this mapping without labeling its richer operand/event output as a generic gather. The read/address-pattern vocabulary is coarse: it describes underlying streams but cannot specify the callback grammar, lane masks, consumer ownership state machine or fault protocol. Those remain explicit claims, limitations and unknown prerequisites. Typed queries return `needs_evidence` because Fig. 6's `vfloat` and Table 1's `int` do not establish concrete widths. Untyped exact-subtype queries return `mapping_reference`, not automatic workload eligibility.

Run `PYTHONDONTWRITEBYTECODE=1 python docs/proposals/tmu-micro2023/validate_proposal.py`. It validates a copied in-memory catalog with the proposed additions, checks representative typed/untyped and excluded queries, verifies every existing record/operation and its query results remain unchanged, and writes [validation.json](validation.json). Production files are read only. Validation passed: 15 proposal query cases, 78 unchanged existing-operation query trials, and all 11 existing hardware catalog unit tests. Structural success certifies representation/reference consistency only; semantic truth and executable mapping legality still require review.

Eric's review decision is whether to admit this exact source-scoped mapping and its subtype, retaining unknowns. A later implementation owner must resolve the contracts above and obtain executable artifact evidence. Fig. 8 configuration names are paper explanatory pseudocode; this proposal supplies no concrete library, simulator or RTL.
