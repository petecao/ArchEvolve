# Next closed public caller integration — source/design review

2026-10-16 ET. Requested design baseline: `60839d8ef180fad2dd6a65c951289444caf0fb8f`. The author advanced to `0e78d836e2260e0ab22a349dabb88cbc0d6d552c` during review; its numeric preparation delta is reviewed separately below. Frozen Git blobs distinguish both scopes. No project main, compiler/formal/prover/native/version/config tool, tests or SSH was run by the reviewer, and no repository file changed.

**Recommendation:** one closed caller heap view for the three already recognized source functions, through the normal public candidate/contract route. Keep generic callers unsupported. The ten baseline caller duties cover local lifetime/read guards; they do not establish constructor/reserve/destructor composition or the final incoming frame.

## State and seam

Start with arbitrary well-formed H0, signed-int n, a fresh automatic receiver identity r, and a scalar saved pointer pair (allocation ID,offset). Bind the exact declaration to the lowered24-byte/8-aligned receiver, fields0/8/16 and target pointer/size/int layouts. Unaddressed scalar locals/return temporary need no heap allocation. Preserve arbitrary incoming aliases and issued dead identities; add no global pointer history, exclusive ownership, empty-heap or finite-pool premise.

Compose H0 → begin_automatic → constructor → data capture → reserve → guarded scalar capture → destructor → end_automatic. Each event owns its physical original/lowered span. There is exactly one reachable destructor; the fallback is unreachable. The scalar return is captured before backing release and receiver retirement.

Automatic placement must be a uniform source-runtime output relation, not a caller-supplied requires. Prove arbitrary-entry placement feasibility or explicitly admit the source-runtime placement rule, together with storage/alignment/history/frame. An empty-heap sample alone proves neither arbitrary-entry placement nor caller composition. No restriction that all incoming heaps were generated from empty is needed.

## Required paths

| Path | Complete obligation/result |
|---|---|
| n=0; reserve(n+1) | Constructor null/size0/capacity0; reserve1 allocates an uninitialized capacity1 buffer with zero elements; guard suppresses every load; dtor releases this buffer; receiver retires; result0. The stale-named function is safe on this path. |
| n>0; reserve(n+1); current element | Constructor fills n int32 cells with7 and establishes capacity exactly n and qualified eligibility. Widened n+1 forces growth. Allocate distinct fresh ID, establish/step/exit copy prefix, release old only after copy; prove index0 and new initialized load yield7. |
| n>0; reserve(n+1); saved alias | saved retains the old ID; old release makes the load invalid even with numeric address reuse. Retain a separate stale-access negative/counterstate. Solver unknown/timeout is not refutation; never execute this UB path for native evidence. |
| n>=0; reserve(n); saved alias | Derive request<=capacity and use the actual no-growth transition Hreserve=Hctor. Preserve identity, full initialized region and saved; positive load yields7 before dtor. At zero the guard suppresses null load. |
| Contract omits0<=n | The constructor conversion precedes the guard. Negative signed n converts to an out-of-domain size_t count; later return0 cannot repair it. Entry discharge must refuse/remain unproved. |

Nonnegativity must follow from the actual public contract clause. With source int32 n and target size_t64, prove exact conversion, widened increment, and count/request<=SIZE_MAX/sizeof(int), including INT_MAX. Keep signed n+1 distinct from `(size_t)n+1`; the former can overflow at INT_MAX. Include the ordinary numeric C RTE/init/smoke kernel and a separate entry implication from the original contract to its requires.

Constructor establishes typed-int image through fresh stores, not readable/init alone. Grow preserves arbitrary index-specific values, old-buffer lifetime through copying, prefix establishment/step/exit, frame, then old-ID invalidation. No-growth requires identity/whole-region preservation, not merely equal first value. Data/index are actual receiver reads with no heap effects; index also needs0<size, and the final load needs the chosen pointer's live/typed/initialized int cell.

Dtor keeps its broad qualified pointer/free domain; no new int-image requirement. Prove free(NULL) harmless and current backing freeable/distinct from automatic receiver, then retire receiver separately without dynamic-free permission. Final H0-live descriptors/content/init are unchanged, H0-dead aliases remain invalid, and newly created receiver/buffers are dead. History/next may advance; do not claim whole-heap bit equality with H0.

## Minimal records and sound reuse

Additional current body records: qualified **ctor_count_value, reserve, dtor**, plus original exact **data** and, for the safe function, **operator_index**, unless their bodies are explicitly incorporated and completely proved by the closed caller view. Prefer these normal records rather than hiding calls behind coverage metadata. The existing count constructor using value0 does not establish value7, qualified typed image/eligibility or exact-capacity post. Old-v2 and qualified-v3 subjects cannot be interchanged based on body similarity.

Current reserve already reproves its whole grow helper. For that inline route a separate grow theorem is unnecessary; if modularized later, bind a current grow record and check its export/application relation. Eligible records do not themselves authorize asserting desired theorem axioms.

Preserve `_proven` exact subject/code, method ID/hash, evidence kind, current setup/reader, counting/unbounded scope and recursive acyclic dependency checks. Re-read physical YAML and independently reconstruct each qualification/certificate using the `standard_range_calls.bind_dependency/recheck` pattern. Match typed/runtime/foundation/semantics across views. After checker/lowering/model/method changes, re-prove records that become ineligible; do not relax identities to promote the frozen V5 result. Contract-fixture evidence cannot bootstrap a different execution-evidence boundary.

Smallest safe implementation: canonical caller prepare/check next to the closed AST checker, owning exact source/lowering/contract/header/semantics and physical dependency bytes; an explicit qualified mapping beside original model selection; independent launch-boundary rechecks; reuse the heap engine's whole deadline, mandatory flags, fresh report reader and normal schema/writer. Initially regenerate needed body/loop/branch obligations using definitions-only transitions. This fits the current isolated/no-Extern engine. A modular theorem importer needs an independently checked export and premise/application bridge before it can reuse proved statements as hypotheses.

Only complete safe/no-growth caller records may count, after entry/local/body/application/load/cleanup/frame targets all pass. Keep stale and missing-entry-premise cases separately named negatives, preserve first failures and all emitted tasks. Numeric smoke is mandatory; isolated mathematical lemmas keep their existing reporting rules, never a generic zero-smoke exception. All body record pins belong to the normal recursive DAG. Source-derived callers outside these exact forms remain unsupported.

## Independent numeric-preparation delta review:0e78d836

**PASS as pending preparation only.** The two production changes add the source parameter span/name/type and a mapped arithmetic kernel; they do not select qualified caller models, import body proofs, grant origins or discharge0<=n. The kernel preserves constructor conversion and widened reserve expression, asserts selected int32/size_t64 representations and max-size bounds, and explicitly leaves entry implication pending. Count-vs-count+1 is already validated by the closed source checker; unknown expression forms remain refused. Its requires is acceptable only as the pending callee/kernel boundary, never as a silently granted caller premise.

I independently rehashed45 raw references and3 source/test pins with zero mismatches;8 GREEN anchor instances have literal count/call source spans, kernel hashes and pending/no-dependency status. Preserved RED is missing numeric_kernel, not a false proof. GREEN producer evidence reports7 controls in31.45s; guard31.804263125s/366,837,760-byte peak, no timeout/OOM. Nine UBSan observations use0,7,INT_MAX in numeric-only harnesses; no stale-pointer or allocation source path executes. These samples establish no theorem or nonnegative-entry discharge. Documents retain all pending acceptance boundaries. The existing standalone017 actual source is untouched.

Remaining implementation/proof duties: automatic placement/layout, actual caller contract discharge, current qualified body records, full branch composition/final frame, and emitted-task/dependency/import audit. Neither the baseline certificate nor this numeric successor justifies an added caller premise or desired theorem axiom.
