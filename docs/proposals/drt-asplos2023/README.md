# DRT fixed-partition SpMSpM research proposal

This is one typed, source-scoped **Fig. 5 illustrative mapping** of TACTile's Aggregate → Metadata Build → Distribution path. It remains outside the production v0 catalog. [proposal.json](proposal.json) contains located claims, the mapping, requirements and schema gap; [provenance.json](provenance.json) binds reused source bytes. No production records changed.

Primary paper: Odemuyiwa et al., *Accelerating Sparse Data Orchestration via Dynamic Reflexive Tiling*, ASPLOS 2023 Volume 3, proceedings pp. 18–32, [DOI](https://doi.org/10.1145/3582016.3582064). Inspected the exact [author-hosted PDF](https://www.nealcrago.com/wp-content/uploads/TACTile_ASPLOS2023.pdf), SHA-256 `e3df45525aeafcfffd7e8b79696f2b6ff844a9a9480cef1f0723284d3eff1dd8`, from the external corpus. PDF page numbering below starts at the title page; publication/retrieval dates are distinct. Cached source provenance and Crossref metadata are supplied by the exact prior handoff; this pass re-extracted and read primary sections independently. No PDF/full text is redistributed and no new bytes were downloaded.

## Exact mapping and required supply

Use paper coordinates `Z[I,J] = sum_K A[I,K] B[K,J]`. Fig. 5/§4.3 declares DRAM→LLB `J→K→I` with A/B tiled CSC/CSC, LLB→PE `K→I→J` with CSC/CSR, and PE-local `I→J→K` with CSR/CSC. Physically preprocessed **3×3 microtiles are this figure's illustrative reference**, not the evaluated 32×32 configuration (§5.2.4). The record does not claim that the evaluated simulator used precisely every illustrative layout.

Software/configuration supplies base points, loop order/dataflow, initial tile shapes, compressed arrays, augmented microtile byte footprints, microtile pointers, and static tensor partitions. Each task carries parent-relative coordinate intervals; A.K and B.K must coincide. Macrotiles are logical collections of uniform physical microtiles (§3.2.1, §4.1, PDF pp. 5, 7). Required metadata/data supply does not establish a CPU gather ABI, coherent memory interface, or extractor execution of PE MACCs/intersections.

Aggregate uses footprint accumulators against per-tensor buffer capacity, reads compressed metadata in raster order, reverses overflow growth, and respects previously constrained shared dimensions. Evaluated `P=32` metadata words and a parallel adder are reference implementation dimensions (§4.2.1). Metadata Build constructs next-level segment/coordinate arrays bottom-up and rebases coordinates to zero (§4.2.2/4.3). Distribution supplies selected references/data and new metadata onward; the lower distributor forms microtile pairs for PEs (§4.3/Fig. 5, PDF pp. 7–8).

Fig. 5's 350B LLB with A/B=175B/150B and 160B PE buffer with A/B=80B/80B are illustrations. Remaining LLB bytes do not establish an output ownership/reservation protocol. Study1's 30MB global buffer, 32KB local buffers, all-studies 32×32 microtiles, and §5.2.4's example 5%/45%/50% split are separate references. **None are legal tuning ranges**; deployment capacities, output accounting and coupled co-tiling conditions require a binding.

## Paper policy and pinned public code

The paper's Algorithms 1–2 (§3.2, PDF pp. 4–5) prioritize stationary tensors, grow contracted then uncontracted dimensions, continue along another dimension after failed growth, and recursively subdivide the most recent dimension after an initial constrained tile cannot fit. Coarsened subdivision is at microtile granularity. Alternating dimensions for square tiles is a separate variant.

Independently inspected cached [FPSG-UIUC/DRT](https://github.com/FPSG-UIUC/DRT/tree/dc8023a27057b6568cc66ab9e1b506092f79c559) at `dc8023a27057b6568cc66ab9e1b506092f79c559`. This public revision is not authenticated as the 2023 evaluated revision. The README documents MKL-dependent executable targets and options; no source was built or run. All line locators refer to [this exact scheduler file](https://github.com/FPSG-UIUC/DRT/blob/dc8023a27057b6568cc66ab9e1b506092f79c559/src/scheduler_8.cpp).

| Pinned locator | Observed behavior and limit |
|---|---|
| `Scheduler_8::Run`, lines 161–267 | Iterates code K/J/I; extracts B, precomputes A footprints, extracts A, schedules middle DOT, and accounts for eviction/output traffic. Modeled eviction does not establish dirty-output visibility. |
| `ExtractBTopTile`, 1127–1180 | Dynamic B grows code-J rows using `AccumulateSize`, `DoesFitInLLB`, `AddToLLB`. It extends code K only if all B rows fit from J=0, then updates reuse counts. Recursive general fallback is not demonstrated here. |
| `PreCalculateARowsSize`, 1276–1305; `CalcBLLBHorizontalSum`, 1695; `AccumulateSize_AwrtB`, 1719–1740 | A-row footprints use full row sizes for serial/parallel tile build; otherwise filter by nonempty B rows. This uses input structure, not future exact output size. |
| `ExtractATopTile`, ordinary branch 1578–1595 | Non-ideal dynamic branch admits precomputed A rows until A capacity check fails. It does not itself prove future output pressure resolved. Caller/LLB policy must confirm fixed partitions; non-ideal alone is insufficient. |
| `ExtractATopTile`, ideal branch 1522–1577; `multiplyOneARowInLogOutput`, 1441 | Explicit SoL policy computes temporary output sizes, tests total capacity, then changes A/O ratios and sizes. Excluded from ordinary fixed-partition online claims. |
| `ScheduleMiddleDOT`, 298; `ExtractAMiddleTiles`, 787; `ExtractBMiddleTiles`, 970 | Existing middle-level scheduling/extraction scaffolding; not a new implementation specification. |
| Extraction overhead models, 1183–1273 / 1599–1692; `EarlyFetchA/BBasicTiles`, 1311/1358; `updateBWLog`, 1085; `AccumulateSize`, 1744 | Existing overhead, fetch-flag, bandwidth and byte-accounting scaffolding. Complete hardware Metadata Build, response tags and coherent CPU binding are not established by these pointers. |

Paper I=code I, paper K=code J, paper J=code K. This permutation aligns mathematical axes; it does not prove identical layouts, admission policies or full implementation equivalence. The paper fallback remains distinct from the observed source-specific B/A policy. Zero-admission progress, oversize minimum microtiles and output partition pressure are open requirements. `DoesFitInLLB` is an observed call; its implementation and all caller settings were not inspected.

Oracle static distribution, ideal LLB partitioning, ideal zero-cycle extraction, idealized OuterSPACE/MatRaptor studies and oracle software traffic analysis are separate evidence scopes. None supplies ordinary online output-size knowledge. The paper reports an **output sparsity** comparison with MKL (§5.2.1), not an independently verified numeric-value oracle. Queuing simulation, Accelergy estimates and public source inspection do not establish RTL or deployed hardware.

## Task identity, completion and lifetime

Tensor membership, parent coordinate intervals and paired microtile references identify the mathematical task. Rebased metadata needs the parent-origin interpretation. A future adapter must define a stable task/epoch association and how responses select exact tensor/tile/metadata slots; this proposal invents no packet encoding.

The paper describes formation followed by distribution, with pipelined metadata/data streaming. A second buffer port overlaps tile i distribution with tile i+1 formation; lower-level extraction can start on initial metadata. Hiding formation costs requires compatible processing rates (§4.2.3/4.3). These observations do not discharge dirty-output visibility, downstream acknowledgment, pointer/tile reuse, outstanding-response drain, cancellation, faults or coherent CPU binding. Those remain explicit `unknown` requirements, along with numeric correctness and evaluated-revision identity.

Sparse occupancy can let larger logical tiles reduce rereads. Dense co-constrained tiles invoke fallback; preprocessing, metadata traversal and formation that cannot overlap can consume the reuse benefit. No performance result is transferred to DX100.

## Precise v0 gap and validation

`archevolve/hardware_catalog.py` currently permits operations `read`, `write`, `read_modify_write`, `reduce`, with roles `execute`/`assist`. v0 can serialize descriptive result prose, but it cannot retrieve **tile orchestration** by its layout, co-tiling, capacity-admission, task identity and consumer release contract. Labeling the entire mechanism a read executor would collapse task construction into fetched values; labeling it assistance would lose its required supply role. A narrow read-supply projection might be possible after a concrete result/lifetime binding, but this proposal provides none.

The explicit gap is `tile_orchestrate` / `required_hierarchy_local_supply` / `hierarchy_local_tile_work`, plus queryable layout/cotiling/capacity/identity/release/observer constraints. These are research vocabulary, not production schema changes. Numeric payload types and index widths remain unknown; microtile shape and 32-word metadata vector width do not establish them. This proposal has **no v0 projection** and cannot be promoted by simply changing its format string.

Run `python -B docs/proposals/drt-asplos2023/validate_proposal.py`. It checks typed research invariants, located in-memory references (including a dangling-reference rejection), exact reused byte hashes, PDF identity/page count, disk floors and unchanged production catalog bytes against `c44ca66`. It confirms v0 rejects the research format and new operation vocabulary. It checks generic gather/stream/prefetch/update queries, typed float32/32 and float64/64 queries, and every existing operation query remain unchanged and include no proposal record. This is deliberate **non-admission**, not a claimed v0 compatibility trial. The validator writes only local [validation.json](validation.json).

A later catalog owner can review the schema gap; a simulator owner can verify caller/LLB policy and establish task ownership, output spill visibility, response association and lifetime before proposing an adapter. Future acceptance should cover empty regions, oversized constrained first tiles, zero admission, co-tiling coverage, delayed/reordered responses, backpressure and safe consumer release, with numeric comparison to a scalar reference. No simulations, benchmarks, builds, ports or invented implementation were performed here.
