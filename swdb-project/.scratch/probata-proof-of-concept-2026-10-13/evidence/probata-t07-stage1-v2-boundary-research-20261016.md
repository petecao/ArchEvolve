# Ticket07 stage1 V2 boundary research and minimal next plan

Created: 2026-10-16 00:41 ET. **Remove the redundant unsupported pointer predicate in a new source freeze; retain the RTE coverage limits.** No frozen source was edited and no compiler, native program, Frama-C, version probe, solver, provider or SSH process was run. This report passively reads the root-dispatched V2 raw output and installed primary tool source.

V2 generated245 goals/352 properties:212 ordinary goals,33 smoke goals, and31 attributable initialization RTE properties. All ordinary goal functions are exactly the19 helper bodies. Five additional function names are smoke checks at exact calls to declared bodyless summaries, not additional body proofs. None of these generation counts or smoke passed flags constitutes solver acceptance; no external prover was requested.

## 1. Supported, minimal source-domain rewrite

Apply only `/private/tmp/probata-t07-pointer-domain-replacement-proposal-20261016.py`'s eight text changes in a **new** source worktree. The file is an inert proposal and was not applied. Six unsupported conjuncts occur in gapbs_models.h (span1,copy1,pvector index2,end2); two more occur in TDStep's capacity endpoints. Drop each pointer_comparable conjunct, preserving all other clauses and executable C tokens.

This does not drop the pointer safety domain. Every affected endpoint pair retains live object-pointer conditions and a common allocation base; source/destination arrays retain their valid/readable/writable and initialized ranges, ordering and pre-subtraction byte-offset representability bounds. In this already restricted live-array domain, same-array pointer comparisons are defined. In the span predicate the second endpoint is formed from the same typed array pointer by a nonnegative bounded count; in copy/vector relations, common-base membership, endpoint ordering and range validity remain independently stated. No null/expired pointer, cross-allocation subtraction or arbitrary byte-buffer reinterpretation is admitted by deleting the redundant comparison predicate. This reasoning is limited to the declared array/object representation; common allocation base alone is not a general C++ subobject/iterator theorem.

Installed primary source supports the chosen replacement: LogicSemantics.ml dispatches object_pointer to OBJ validity; MemTyped.ml1024–1039 implements same-base location ordering and pointer differences through byte offsets and element size. The unknown pointer_comparable builtin instead goes through the kernel's generic pointer profile, including inserted void-pointer casts, while WP reports the builtin undefined. The V2 log's6 unsupported sites and associated sint32-to-sint8 cast warnings coincide with this predicate. Do not replace it with an axiom, char-pointer cast, warning suppression or unchecked ghost assertion. Retaining supported live/base/span/offset premises is the repair. A new generation is still required to observe whether all such warnings disappear.

## 2. The two global RTE warnings have different applicability

WP wpRTE.ml128–140 prints the unaligned-pointer and invalid-function-call warnings when RTE generation runs, controlled by global enabled options. It then explicitly sets pointer_alignment=false and pointer_call=false in the generation flags. These are tool coverage limits, not proof failures attached to a particular source line and not evidence that a particular helper is invalid.

**Function-pointer calls:** this exact normalized TU/helper source has direct named function calls only; no helper parameter, local, field or expression carries or invokes a function pointer. Static inspection of the normalized C and the exact19-body source therefore supports *inapplicable for this finite TU*. This is not a waiver for another source or a complete support claim for indirect calls. The same source/normalized hashes and direct-call census must be bound in the next applicability receipt; a source change invalidates the classification.

**Alignment:** do not mark this warning inapplicable merely because no cast appears. Helpers dereference typed pointer arguments, objects and array cells. The Typed model and source-origin assumptions must represent properly aligned real typed objects; the current tool does not generate the missing alignment guard class. C++ new/automatic/static typed objects and their legal field/element offsets provide a legitimate caller/source alignment route, but a full physical alignment correspondence for every public helper input is not established by V2 or by valid alone. Do not add an unsupported aligned predicate, invent address-modulus axioms or claim full C RTE coverage. Preserve the residual boundary explicitly until a caller-backed typed-allocation/alignment argument is qualified. A later solver pass could establish the emitted goals under this source/model boundary; it would still not prove the omitted alignment class.

Keep the two exact warnings in raw output and in structured capability-boundary metadata. Do not globally allow an unsupported warning class or silently convert such warnings into success. A future generation result can say diagnostic generation completed while scope qualification remains pending. Root's cold gate must inspect the exact warning instances, decide the source-specific applicability and preserve any unresolved residual condition before stage2. All new unsupported builtins/casts, changed warning texts/locations or unclassified capability omissions remain blocking. The other pedantic missing-from warnings remain retained imprecision observations; do not rewrite contracts solely to silence them or omit any generated obligation.

## 3. Correct the inventory census without dropping goals

The V2 production inventory attributes all212 ordinary goals to the exact19 bodies. It attributes five dead-call smoke checks to the *callee* bodyless function. The old condition seen_functions==helpers would falsely reject these expected smoke checks. Replace that condition with the following scoped rules:

1. Every ordinary row must have smoke=false and a helper function; the ordinary function set must equal all19 helpers. Goal IDs remain unique/nonempty and scheduled count must equal complete inventory count. Do not assume future counts stay245 after a new source freeze.
2. Retain every smoke row. A helper-owned smoke is allowed normally. A smoke owned outside the helper set is allowed only for an exact declared bodyless callee and an independently matched direct-call context in the staged pinned header. Unexpected functions, ordinary goals on bodyless subjects or ambiguous contexts refuse.
3. Match each outsider to exactly one property row with the same machine property ID, same callee and same source line, non-Extern dead-call description. The exact frozen source call must be inside the expected helper body. Existing production records omit filename/caller in this case, so source line attribution requires this isolated one-header component and a unique pinned source occurrence; if ambiguous, extend contextual reporting rather than guessing. Recompute the map from the new frozen source, never reuse V2 line numbers after deleting clauses.

The V2 contextual map is:

| Bodyless callee | Actual helper caller | c9 header line |
|---|---|---:|
| __sync_bool_compare_and_swap_NodeID | compare_and_swap |162|
| __sync_fetch_and_add_size_t | fetch_and_add_size_t |173|
| swdb_new_NodeID_array | QueueBuffer_NodeID_QueueBuffer |272|
| swdb_delete_NodeID_array | QueueBuffer_NodeID_destroy |279|
| std_copy_NodeID | QueueBuffer_NodeID_flush |299|

The declared atomic-load function is not called by this helper TU and gets no inferred smoke exemption. Existing six-function bodyless assumption attribution remains a separate requirement; a dead-call smoke is not itself an Extern contract. None of the five checks is deleted or downgraded. Actual stage2 must still satisfy every retained generated smoke criterion alongside every ordinary/RTE/init/frame/termination/contract obligation.

## Next finite plan

Root should freeze the eight-conjunct source change, re-review the unchanged executable C and domain equivalence, then build a fresh stage1 recipe with the corrected ordinary/smoke census and explicit warning-boundary records. Keep all19 bodies, explicit post-parse initialization function set, Typed/RTE/smoke/none/cache-none, one worker,120s/8GiB guard and fresh output. Rebind every source/recipe pin and the new call-context map. No automatic stage2 and no historical proof or hints. New generation must resolve the undefined-predicate/cast failures, retain the capability-boundary warnings and pass the independently reviewed census before root considers the separately scoped solver component.

JSON source/raw inventory and exact contextual goal/property rows: `/private/tmp/probata-t07-stage1-v2-boundary-research-20261016.json`, SHA-256 `9eda4de905d2f81260c46b22da1e2da144d47728724c1120b9fb37e39d6a8cde`. Proposed inert source transformation SHA-256 `5165da8a951b983f233b1259d3e319788b5ab6cc7939e8fe2cac834fe0f9fc03`.
