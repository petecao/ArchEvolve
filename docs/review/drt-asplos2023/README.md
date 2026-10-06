# Independent DRT proposal review

**Verdict: APPROVE retention as a source-scoped research proposal; DEFER production v0 admission.** No blocking correction is required for that disposition. This verdict does not certify hardware, numeric correctness, a fixed-partition executable configuration, or a CPU mapping. Only this review directory changed.

Reviewed proposal commit `8d0d3c09e85ef647c896e913aafc73a2f60bb76f`, based on `c44ca66b5b1a121ed258d0d972172cda2de307b6`. The user supplied root-copy alias `b98757e`; the reviewed object is the full proposal commit above. Read README, proposal, provenance, validator and saved validation. Reused unchanged producer query checks; did not rerun the producer's writer. [sources.json](sources.json) identifies exact inspected bytes, and [validation.json](validation.json) records bounded review verification.

## Evidence and findings

Primary paper: Odemuyiwa et al., *Accelerating Sparse Data Orchestration via Dynamic Reflexive Tiling*, ASPLOS 2023 Volume 3, proceedings pp. 18–32, DOI [10.1145/3582016.3582064](https://doi.org/10.1145/3582016.3582064). Inspected the cached [author-hosted publication PDF](https://www.nealcrago.com/wp-content/uploads/TACTile_ASPLOS2023.pdf), SHA-256 `e3df45525aeafcfffd7e8b79696f2b6ff844a9a9480cef1f0723284d3eff1dd8`. PDF page 1 is proceedings page 18. Extracted text locally to `/tmp/drt-review-paper.txt`; no full text or PDF is redistributed.

Public artifact scope: [FPSG-UIUC/DRT at dc8023a27057b6568cc66ab9e1b506092f79c559](https://github.com/FPSG-UIUC/DRT/tree/dc8023a27057b6568cc66ab9e1b506092f79c559). Cached README and scheduler were inspected, plus exactly three newly retrieved files totaling 34,010 bytes: `llb_mem.cpp`, `SpMSpM_TACTile_twoInp.cpp`, and `parameters.h`. Retrieved contents match the cached pinned tree's Git blob identifiers. This revision is not authenticated as the evaluated 2023 revision.

### 1. Figure, evaluation and axis policy are correctly separated

Paper §4.3/Fig. 5 (PDF pp. 7–8) explicitly uses arbitrarily chosen 3×3 physical microtiles; §5.2.4 (PDF p. 9) uses 32×32 preprocessing for all studies. Fig. 5's 350-byte LLB, A/B 175/150-byte illustration and 160-byte PE buffer with A/B 80/80 bytes are separate from evaluated capacities and the example 5%/45%/50% split. The proposal preserves these distinctions and supplies no legal tuning domains.

With paper `Z[I,J] = sum_K A[I,K]B[K,J]` and artifact `A[I,J]B[J,K]`, paper I = code I, paper K = code J, paper J = code K. Consequently source K/J/I traversal agrees with the paper's top J/K/I axis order after translation. That does not prove layout or policy equivalence. [scheduler_8.cpp](https://github.com/FPSG-UIUC/DRT/blob/dc8023a27057b6568cc66ab9e1b506092f79c559/src/scheduler_8.cpp), lines 161–290 and 1127–1171, grows B along code J over an initial code-K interval; only when all B rows fit from J=0 does it extend code K. Ordinary A growth (1578–1593) admits precomputed rows. Precalculation (1276–1305, 1695–1740) uses either full A footprints or footprints filtered by nonempty B rows, depending on tile-build mode. These are observed source policies, not proof of the whole generic paper algorithm.

### 2. Capacity checks are present; non-ideal does not mean fixed

[llb_mem.cpp](https://github.com/FPSG-UIUC/DRT/blob/dc8023a27057b6568cc66ab9e1b506092f79c559/src/llb_mem.cpp), lines 46–77, first rejects `bytes + used_size > total_size`. Dynamic SpMSpM A and O also check their respective `max_*_size`; dynamic B checks its own maximum. Thus `DoesFitInLLB` checks both total occupancy and relevant per-tensor maxima under these modes. Equality is accepted. `AddToLLB` (8–40) adds counters without enforcing these limits itself; eviction (110–123) resets counters and optionally accounts output traffic. These functions are a byte-capacity/traffic model, not memory ownership or coherent completion.

[SpMSpM_TACTile_twoInp.cpp](https://github.com/FPSG-UIUC/DRT/blob/dc8023a27057b6568cc66ab9e1b506092f79c559/src/SpMSpM_TACTile_twoInp.cpp), lines 23–37 and 51–64, initializes inputs, calls the uninspected parser, passes the partition policy into Parameters, passes size/ratios into LLB_Mem, then invokes Scheduler_8. Initial defaults (108–134) are dynamic SpMSpM, 32×32 microtiles, 30×1024×1024 bytes, A/B/O=5%/50%/45%, and `constant_initial`. These are source defaults before parsing, not an authenticated run configuration; they also differ from the paper's example ratios.

[parameters.h](https://github.com/FPSG-UIUC/DRT/blob/dc8023a27057b6568cc66ab9e1b506092f79c559/src/parameters.h), lines 14–20 and 111–158, distinguishes ideal, constant_initial and three adaptive policies and stores the supplied policy. Scheduler lines 719–764 update A/O ratios for adaptive_prev/min/avg. Those policies use the same non-ideal A admission branch. Therefore the proposal's warning that non-ideal alone cannot establish immutable partitions is correct. A fixed-source description must name `constant_initial` and exact effective configuration, not merely `!= ideal`.

Bounded inspection partially closes the capacity question: maxima are checked and caller defaults/pass-through are visible. **The LLB constructor, SetRatios/SetSizes implementation in the uninspected header, parser overrides, actual evaluated settings and every configuration path remain unresolved.** The three-file retrieval limit is exhausted. No claim is made that observed ratios fully initialize or preserve numerical A/B/O allocations in every run.

The inspected Parameters constructor assigns `data_size=8`, `idx_size=4`, `pos_size=4` (line 137). Those are this simulator's accounting sizes, not proof of supported numeric payload types, an index ABI, or paper type domains. The proposal's empty type domains remain appropriate.

### 3. Output pressure is modeled reactively, not admitted in advance

Scheduler lines 431–479 compute a product, obtain output-log size and call `DoesFitInLLB('O', output_size)`. Failure adds the log size, models a complete output eviction, clears the log, and records writeback bytes. Final log handling and later read/merge traffic appear at 658–717 and 258–278. This is concrete evidence of output-pressure handling in the model; it is not proof that every intermediate output stays within a fixed physical allocation. In particular, adding an oversized log then evicting it is not pre-compute output reservation. Future exact output size is not used by ordinary A admission.

Scheduler lines 1522–1577 explicitly label the ideal partition branch as SoL: a temporary computed output log guides total-fit tests and A/O repartitioning. That branch must remain excluded from ordinary online fixed-partition evidence. Instant extraction/intersection defaults (caller 116–124), oracle distributor variants (Parameters 46–59), and post-run SoL analytical calls (caller 83–85) are separate from online extraction timing. Paper §5.2.3/§6.5 SW oracle traffic and idealized accelerator comparisons likewise do not supply an ordinary output oracle.

### 4. Recursive fallback and zero-admission progress remain unproved in code

Paper Algorithms 1–2/§3.2 (PDF pp. 4–5) distinguish continuing along another dimension after growth failure from recursive subdivision after an initially constrained tile cannot fit. Coarsening makes subdivisions microtile-granular (§3.2.1). This is a paper guarantee, not an observed recursive scheduler implementation.

Concrete adversarial boundary, inspected without execution: if the first B row over its chosen code-K interval exceeds its allowance, ExtractBTopTile breaks before incrementing `j_idx_stop` and sets OReuse to zero (1143–1171). Run computes `j_end_top == j_start_top` and later assigns that unchanged end to the start (198–201, 244). If the first required A row exceeds its allowance, ordinary ExtractATopTile leaves `i_end_top == i_start_top` (1579–1592), and Run similarly assigns that end back to the start (235). Neither inspected path shrinks the constrained region or reports a dedicated zero-admission failure. This supports a possible progress failure for such inputs/configurations; no runtime hang was demonstrated. Empty regions, an oversized minimum microtile and downstream empty-work behavior remain binding questions. The proposal already records this unknown.

### 5. Required tile supply is the concrete schema boundary

Paper §3 (Eq. 2), §4.1–4.3/Fig. 5 require shared contracted coordinate bounds, augmented footprint/pointer metadata, bottom-up compressed metadata construction, coordinate rebasing and distribution of paired microtiles. Aggregate → Metadata Build → Distribution forms and supplies hierarchy-local work required for compute. A read/gather label for the entire mechanism would omit work construction and admission; assistance/prefetch alone would omit its required supply role.

The current `archevolve/hardware_catalog.py` permits read/write/read_modify_write/reduce and execute/assist (lines 21–25, 171–188). It can preserve interface, result, ordering, completion and requirement prose, plus located internal mechanisms (150–161). Queries (240–322) do not filter on the proposed layout, co-tiling, capacity or lifetime obligations. The producer's rejected `tile_orchestrate` trial establishes a vocabulary mismatch; it does **not** establish that this exact new operation, role and six query constraints are the minimal necessary schema extension.

Minimal descriptive option: retain the existing out-of-v0 record and its three stages, parent-relative coordinate relationship, rebased metadata/pointer supply, located claims and explicit unknowns. An eventual catalog owner could reuse descriptive interface/internal-mechanism/requirement fields around a separately established narrow supply operation. The present evidence does not bind that operation's observable result or completion, so **safe deferral is the selected option**. Do not manufacture a gather projection, change production schema, or require a formal task DSL merely to describe this mechanism.

Consumer release, dirty-output visibility, tile/pointer lifetime, response association and CPU/coherent binding remain unknown. A second buffer port and streaming overlap (§4.2.3–4.3) do not specify acknowledgment, drain or safe reuse. The new capacity/caller sources do not resolve those contracts. Paper §5.2.1's output-sparsity comparison against MKL is not independently verified numeric-value correctness; no numeric implementation or helper was run here.

## Handoff

Accept this review for research retention only. Preserve proposal and production catalog bytes. Future admission needs an exact effective configuration and capacity initialization, a concrete required-supply/result boundary and consumer lifetime, plus independent numeric validation appropriate to that binding. The observations above refine existing unknowns rather than discharge them. No simulator, benchmark, build, paid API, corpus scan, worker, push or cleanup was performed.
