# AXI-Pack DATE 2024: scoped SELL operand staging

This local admission repairs the two exact findings in review `075d480686b944726d4a6f52ba5f51fca9b51a1a`: `datatype_notes` is a scalar, and the operation is `read/sell_required_l2_staging`, not generic `read/gather`. The record is selectable for an explicit published SELL staging intent. Sparse and dense BFS selection remains byte-equivalent under the same catalog identity arguments. Nothing is published to the group repository by this change.

Primary paper: **Near-Memory Parallel Indexing and Coalescing: Enabling Highly Efficient Indirect Access for SpMV**, DATE 2024, [official proceedings PDF](https://past.date-conference.com/proceedings-archive/2024/DATA/381_pdf_upload.pdf), [DOI](https://doi.org/10.23919/DATE58400.2024.10546797). Exact PDF SHA256 `dea5a1a457aeeb7a45ea839de475c7da8d6c7896f456c9b37a3ba19483b97c9a`; layout-text SHA256 `e19331926e72493e8c4efa5100b49da4b4a37504e711d1121019459bed4cb53a` independently rechecked. Source pages 2–3 were read directly again; existing reviewed artifact inventory is reused. No new retrieval, hardware execution or publication-specific RTL authentication.

## Why this mechanism differs from a generic gather

- Wide index fetches feed parallel dependent element requests (p.2 section II-A).
- A bounded W-request comparison window groups same-DRAM-block hits through one active CSHR; its hitmap and offsets record response association (p.2 section II-B).
- The response splitter and downsizer restore the narrow-request order (pp.2–3 section II-B); this is not arbitrary cross-ID/global memory ordering.
- Two distinct partial-progress rules are described: the regulator can forward a partial request window after a time limit, and a watcher watchdog can issue the pending wide request if no new window arrives (p.2 section II-B). These do not specify host readiness or a final drain ABI.
- CVA6 configures required operand staging into L2 for tiled SELL SpMV; Ara later consumes operands through ordinary AXI4 and performs vector arithmetic outside this gather operation (p.3 section II-C).

The DATE 2023 direct vector-protocol integration is a separate edition/path. Adjacent public Ara/DRAMSys transport files are not the authenticated DATE 2024 coalescer or staging driver. No intrinsic signature or simulator implementation is invented here.

## Widths, capacities and unknowns

The evaluation uses 32-bit indices, 64-bit nonzeros/metadata and 32 SELL rows per slice. These are evaluation observations, not a complete signedness/type/address-safety domain. Typed retrieval remains `needs_evidence` where the executable domain is unknown.

Table I prints **27KB** on-chip adapter storage at W=256 and **384KB** L2. The new record retains the paper's KB notation; it does not silently certify KiB or convert to exact bytes. Queue depths, N/W coupling and all fixed-reference parameters are evidence rather than an instantiated design.

First/final tile readiness, padded lanes, safe buffer reuse, result drain, translation/fault/cache visibility, response-ID behavior and publication-specific artifact binding remain explicit requirements. A paper mapping match is not implementation certification or a speedup claim.

## Validation

- Existing 100 tests passed against the extended catalog.
- Six additional methods passed: explicit typed unknowns, generic read exclusion, no update/old-value inheritance, unchanged sparse/dense BFS selection, full contract retention through candidate/comparison/intrinsic drafts, and mechanism/unit boundaries.
- All nine previous design records and all previous claims/sources are structurally unchanged from base d3bfb34.
- No loader/selector or other production code changed. The local catalog is v0.1.8 with ten records; only this new scoped mapping is added.

Next useful implementation research: authenticate the actual coalescer/L2 driver and specify first/final-tile readiness plus response/credit lifetimes. Until then the paper-derived internal mechanism annotations are usable, while runnable ABI and performance remain unknown.
