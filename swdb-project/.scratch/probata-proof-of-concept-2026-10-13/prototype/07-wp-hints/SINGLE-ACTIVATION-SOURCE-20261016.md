# Selected single-activation source domain

2026-10-16 ET. Source/compiler preparation only. Allocator refinement, heap/SINIT
equivalence, lifetime/reset, full TD and counted acceptance remain refused. No C
model, TD body, helper contract, source algorithm, initialization fact or proof
hint changes in this package.

The selected-source gate now binds the material `lqueue` declaration directly to
the first statement of the one OpenMP parallel captured body, outside any loop
or conditional ancestor. Clang's repeated capture declaration is the same
dump-local object, not a second source lifetime. The final flush must be the
parallel body's direct terminal statement on that object. Stable observations
retain the main hash and source byte ranges; no declaration ID is compared
across compiler dumps or processes.

This checks the source shape needed for the proposed default-capacity mapping:
one `QueueBuffer<int>` construction per normal implicit-task activation, with
the exact default 16384, uninitialized typed array new, two push sites, final
flush and matching array delete. The selected main remains
`093c56b91837122380fd5e66766c92947e5f1c5194dd4c038936bc28934864dc`.
The new observation explicitly leaves runtime threads=1, interprocedural
reentrancy and allocator/lifetime refinement unqualified. Direct placement and
terminal flush do not prove a whole call graph or generic OpenMP execution.

The public compiler/AST controls use real derived copies of this selected main,
the exact fork header and full physical include closure. Two genuine feature
REDs were preserved: the prior gate accepted a two-iteration lexical allocation
site, then its successor accepted a conditional final flush. The minimal gates
refuse both. Each negative is parsed only; no program is executed. A separate
early-return control was rejected by Clang with `cannot return from OpenMP
region` before AST inspection. It is an excluded source-language case, not a
third feature RED or evidence about backend initialization. The initial control
launcher also refused its own external output path before compilation; that
mechanical failure is retained separately.

Validation retains the two source-domain GREEN compiler receipts, the original
35 passing public selected-source controls on the final gate, and five pure
controls of the actual retained ASTs and explicit unqualified flags. The final
pure profile reuses the two real RED compiler ASTs and checks their refusal
without repeating compilation. All use the
shared B lease and an 8GiB time/RSS guard. The 35-control regression completed in
15.142616 seconds with 158.09375MiB peak sampled tree RSS and no inspection
events. The final pure retained-AST control completed in 0.365613 seconds with
38.28125MiB and no inspection events. Its earlier two-control predecessor had
one transient AccessDenied event, no final inspection failure and no
unconfirmed children; that receipt is retained separately. Detailed pins, all prior failures and other resource
receipts are in the adjacent evidence record. Historical source/evidence and all
five hand-model directories remain preserved; old receipts describe their old
source freezes rather than the new generator bytes.

The next proof obligations follow actual stores, rather than initialization
premises. Construction sets the occupied count to zero and does not fill the
payload. A buffered push writes exactly the new occupied cell, preserving the
previous occupied prefix. A full-buffer push flushes only that already written
prefix, resets the count, and writes the new cell0. Final flush reads only the
occupied prefix. These are obligations of the helper bodies and their caller
composition; this document supplies no assumed lemma, loop annotation or proof
acceptance. The same-path missing-store and wrong-cell tasks must remain
exposed; a trivial/Valid negative is a qualification failure.

| Remaining gate | Required argument or evidence |
|---|---|
| Source allocation/frame | One live source typed array corresponds to the private typed array, with extent, alignment, same-array provenance, normal allocation success and unobservable address/allocator-hook scope explicit. |
| Actual heap initializedness | Preserve every generated task and cluster context. The local SINIT=false observation is distinct from heap Init; arbitrary local heap Init is only a candidate conservative abstraction, not an exact false/reset theorem. |
| Real-store prefix | Prove every helper ordinary/RTE/init obligation and the store/flush composition. No hidden initializedness premise or automatic payload fill. |
| Lifetime and repeated calls | Establish nonescape, matched normal retirement, threads=1 and activation/frame renaming. Generic lexical reentry fixtures remain unsupported; missing loop frames are not reset evidence. |
| Caller/source domain | Incoming SlidingQueue remains symbolic num_nodes. Graph/pvector/device and physical layout contracts, unsupported raw Graph/-m families and normal caller discharge remain explicit. |
| Full TD/count | Preserve original functional postconditions and dimensions, independently review the source refinement, and obtain fresh complete actual proof and counted evidence under root admission. |

The successful wrong-cell export is a separate diagnostic milestone. Its real
cell1 initializedness task remains nontrivial after the real cell0 push; it does
not prove a negative, lifetime reset, source refinement or full TD. No positive
or missing-store generation was replayed for this source package. Root owns any
subsequent formal admission and execution.
