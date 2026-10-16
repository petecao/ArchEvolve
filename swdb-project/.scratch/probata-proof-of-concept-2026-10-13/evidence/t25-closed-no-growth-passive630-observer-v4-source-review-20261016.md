# Projected-C 630 passive observer V4 — independent delta review

Date: 2026-10-16 ET. Reviewer: `caller_assess`.

Decision: **PASS for read-only CSV/source reconciliation**, relative to the exact V3 source review (SHA3c58b30a4a24f6f7b18d48f5caf14f95e3970310af798315ec5488cec9b4459d). This source review used only local stdlib/AST reading, without observer/project/native/compiler/verifier/solver execution or SSH.

Fixed source: `prototype/25-closed-no-growth-20261016/passive-630-observer-v4.py`, SHAbca320c2fd9ea6f4082f99a953828f51f90807f92ede42725f11a70d06c08706. V3 remains preserved: its read-only pass refused because native named assertion descriptions include `assert label:` while the CSV cell holds the predicate. This was a passive observer normalization gap, not another formal run or failure of the assertions.

The sole V4 delta adds exact normalization for four source-generated assertions: data-requires line132, reserve-requires line136, no-growth line137 and destructor-representation line143. It accepts only root-owned `user assertion` rows with the exact property ID/label, IPCodeAnnot variant, End-User emitter, registered origin/status, exact actual input source file, exact physical line/label and equal normalized native/CSV predicate. The input remains pinned by its complete SHA-256. It neither suppresses an assertion nor changes its predicate/status or creates a new proof classification. All other V3 parsing, goal/property/task closure, exact registered constructor call exception, source/runtime/raw identity checks and nonacceptance flags remain unchanged.

The original entry refusal, ordinary reader not_proven/unclassified result, exact smoke attempt arrays, current constructor dependency gap, allocator/library TCB and source/Typed bridge gap remain preserved. Root-authorized passive execution may proceed; its output still requires independent reconciliation. No second proof run is required.
