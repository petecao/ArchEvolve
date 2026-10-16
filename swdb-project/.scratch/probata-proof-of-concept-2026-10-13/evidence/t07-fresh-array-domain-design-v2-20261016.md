# Ticket07 fresh private array: corrected exact-source design v2

2026-10-16 ET. **Use an uninitialized caller-private typed automatic array as the smallest candidate for the one TDStep-local QueueBuffer lifetime. Keep allocator/source correspondence refused until the gates below pass.** Do not replace the incoming SlidingQueue's symbolic allocation with a 16384-element array. No repository edits, Git/SSH, compiler/verifier/version commands, native controls, or formal jobs occurred in this task.

The companion JSON contains SHA-256 pins, exact excerpts and paths for installed WP sources, frozen hand-model sources, exact fork source/provenance, the project offload unit and prospective out-slot artifacts: `/private/tmp/probata-t07-fresh-array-domain-design-v2-20261016.json`, SHA-256 `04a0ff3d2b3a61d675398ca5330989550e2b1d0e74ded98fdf233e6f914269d9`. The frozen helper source is the root-supplied 7930f3a1f8d59cb7b338f54844dea7728bc8864c checkout; no Git command was used to re-establish that identity.

## Provenance correction and exact proof-unit scope

The v1 note remains unchanged at `/private/tmp/probata-t07-fresh-array-domain-design-20261016.{md,json}`. Its allocation citations used the local upstream `apps/gapbs/src` tree; they were insufficient evidence for the modified DX100 fork and are superseded by the source citations in this v2 note. Similar-looking upstream code is not treated as fork correspondence. The installed WP findings and the prospective design were not actual formal acceptance in either revision.

The exact fork is `arkhadem/DX100` commit `e4fc4afdf894f295442cef3604667a469fab8e62`. Retained `sliding_queue.h`, `bfs.cc` and `benchmark.h` were independently rehashed and checked against their retained immutable source metadata: SHA-256, byte length and Git blob SHA-1 all match (9 checks, zero mismatches). No network refetch or Git command was used. The corrected source bytes are:

| Exact source | SHA-256 | Git blob SHA-1 |
| --- | --- | --- |
| fork `benchmarks/gapbs/src/sliding_queue.h` | `3d5a1d3cff924737c2fc7c6b4fcbb859270f1fcc626c25aac4c780b7b6f4c02c` | `fed319ea556423c55db8d995a97ea21a0f950da8` |
| fork `benchmarks/gapbs/src/bfs.cc` | `6835fc42dfadcb60c1c3fae543f736903977f135fd7c55cd495c0e481b572465` | `3f6d91b29dca5c2a42e918795f3f59e0f1bc630f` |
| fork `benchmarks/gapbs/src/benchmark.h` | `87c20752c8437dd5152d00e7c995bedfab15b8929219f85846f47e0f9a4b339f` | `1e305e5e7a6297ae5d96f5a50dc72fe8e3e1c651` |

The actual proof unit is project-authored `library/dx100/bfs_read_offload.inc` in the frozen7930 checkout, not a file claimed to originate verbatim in the fork. Its independently computed SHA-256 is `3c5867a2b8919806f681603836bd0cff448f21634485abf84e49ed71f25515ef`. The fork supplies the class allocation/member semantics; the offload file supplies the actual allocation call and use/lifetime context. The source-model bridge between those files and generated C remains an obligation.

In that exact offload unit, line21 constructs `QueueBuffer<NodeID> lqueue(queue)` with no second argument, so the fork constructor's default16384 at98 is the direct source of the specialization. Scalar NodeIDs enter only through `lqueue.push_back(v)` at53 and63; final `lqueue.flush()` is67, with automatic object destruction at block exit68. Device registration14–17 names the incoming queue, offsets, graph neighbors and parent; gather/device calls30–44 likewise do not name `lqueue` or its private payload. The fork header's `local_queue` is private at93, and its complete uses are new101, delete105, indexed write111 and std::copy117. No pointer getter is present.

These are bounded structural nonescape observations. They do not prove arbitrary allocator replacements/hooks, exception paths, standard-library implementation behavior, whole-program macro/include context or general OpenMP executions cannot expose addresses. Admission must preserve those limits and qualify the exact normal-success, one-thread source execution rather than upgrade this local census into a general escape theorem.

## Why shipped malloc is not a supported shortcut

Installed `share/libc/stdlib.h:607–626` specifies malloc with `allocates`, `\fresh` and `\aligned`, with no payload-initialization guarantee. Its calloc specification at 580–601 separately adds initialized and zero bytes. Thus calloc/global-zero behavior changes the required source behavior and cannot model `new NodeID[n]` without an initializer.

Installed WP `LogicSemantics.ml:873–885` explicitly rejects `\aligned`, and rejects `Pallocable`, `Pfreeable`, `Pfresh` and `Pdangling`. The existence of an allocation-size table and comments mentioning malloc in `MemTyped.ml:64–95` does not establish implemented dynamic allocator semantics. Do not delete those predicates from malloc and retain only desired validity/separation postconditions: that would introduce an unqualified trusted allocator, not prove the source allocation. No claim about every `allocates`-clause path follows merely from this bounded inspection; the required freshness/alignment path already fails the inspected supported interface.

## Two allocations with different ownership boundaries

| Source allocation | Exact location and lifetime | Correct boundary |
| --- | --- | --- |
| `QueueBuffer<T>::local_queue = new T[local_size]` | exact fork `sliding_queue.h:98–105`; project offloaded TDStep constructs the default-size local QueueBuffer at `bfs_read_offload.inc:21`, flushes at67 and closes the block at68; fork baseline TDStep does so at `bfs.cc:237,254–255` | Under the existing threads=1 restriction, one successful normal allocation of 16384 `NodeID` elements, used only inside that block |
| `SlidingQueue<T>::shared = new T[shared_size]` | exact fork `sliding_queue.h:34–42`; fork `DOBFS` begins at `bfs.cc:314` and constructs `queue(g.num_nodes())` at330; this is incoming state at project offloaded TDStep entry | Incoming live typed array of symbolic `num_nodes` elements; lifetime spans DOBFS, not one TDStep; history initializes only occupied entries |

Only the first allocation is a candidate for this local lowering. The second remains a caller/producer-history obligation. `queue->shared_max_size == num_nodes` stays symbolic. The occupied prefix, distinct visited entries and same-array/liveness facts remain; the untouched suffix must have no unconditional initialization fact. The graph/queue capacity cannot be narrowed to 16384. A universal automatic-storage allocator, or a fixed-size replacement for DOBFS's queue, is not proposed.

`NodeID` is `int32_t` in exact fork `benchmark.h:29`. Neither source new-expression supplies a value initializer. The source algorithm writes queue entries before consuming them; it does not depend on payload zero values.

## Concrete private ABI and scope mapping

At the original one-thread QueueBuffer construction site, introduce `NodeID storage[16384];` **without** `static`, `extern`, a brace initializer, memset, calloc, an arbitrary-value initializer, or an initializing havoc primitive. Declare it in a new lexical block around the constructor, all buffer uses and destructor. The object is compiler-created private storage. It is not an additional incoming TDStep argument or precondition. Its C declaration supplies typed extent and language alignment, while the source correspondence maps the successful C++ new-array identity to this fresh private object.

The generated constructor receives an extra `NodeID *storage` private ABI argument (or an exact pointer-to-array argument for the 16384 specialization). Its binding adapter receives that storage plus the fresh typed pointer-output slot from the separate out-slot lowering. The adapter body is an ordinary pointer store, conceptually `*out = storage`; it does not allocate, read payload, or initialize payload. Rename/document it as a storage-binding adapter, not as an independently verified implementation of general operator new.

The old summary `result == &swdb_lqueue_storage[0]` becomes an explicit relation to that constructor invocation's storage argument. `gapbs_buffer_domain` must name the invocation's live typed-array witness/extent, not any shared global address. Caller-generated output slots must be valid live pointer objects, separate from receiver, master and payload array. Storing a valid pointer initializes only that pointer object. It must not add `\initialized(storage + (0 .. n-1))`.

The old global declaration and all equality references to it are removed in the new method. Do not retain an unused static/global twin whose binit facts can leak into the new path. The constructor's modular contract adds only the compiler-private storage/output-slot interface conditions. These are discharged by newly created local objects at each lowering site; they are not strengthened preconditions for a real C++ caller. The original real algorithm, source arguments, effects and TDStep postconditions stay unchanged.

For the public TDStep specialization, `given_size` is exactly 16384, so the actual typed array extent is exactly 16384. A general helper contract over `1 <= n <= 16384` can expose only the n-element accessible window, and every source operation must remain within that window. It cannot infer that the source array really has 16384 elements for all n, or accept arithmetic/dereference outside n just because the backing automatic array is larger. If exact n-object correspondence for a more general constructor is required, either qualify a separate exact-size typed producer or refuse that general correspondence. Do not silently claim the specialization proves every constructor instantiation. No VLA support is established here.

## Initializedness in the installed backend

The global surrogate is materially wrong for this purpose. `Cvalues.ml:121–124` treats non-struct globals/formals as always initialized. `MemTyped.ml:566–574` generates binit for those globals, and the shipped `memory.mlw:22–24` makes binit bases initialized throughout. `CodeSemantics.ml:415–438,616–625` also shows initializer processing can introduce zero value plus initializedness. An uninitialized automatic declaration must never be routed through a fabricated initializer.

For automatic locals, `MemTyped.ml:1080–1094` sets their allocation-table extent on block entry and sets it to zero on exit. `MemVar.ml:973–1036` additionally tracks lexical allocation and local initialization state. `CfgWP.ml:1443–1464` invokes those enter/leave relations. `CfgWP.ml:769–785` emits explicit stored/copied initializedness for ordinary stores. These are promising existing mechanisms, not an actual qualification result.

There is a specific remaining backend gate: an address-taken array can use the Typed heap initialization map rather than the per-variable SINIT map (`MemVar.ml:530–542`). Consequently the inspected local scope-init code alone is not a proof that every array payload cell receives false initializedness in the exact generated VC. Inspect the actual normalized variable classification and generated VC before acceptance. At minimum the initial payload mask must be unconstrained/conservative with no unconditional true facts, so a read before a source write remains unprovable. Do not assert false/true mask axioms, force a WP memory classification, or add a synthetic havoc solely to obtain the expected verdict. A model that requires arbitrary incoming mask history may leave untouched cells unconstrained; it must preserve that history rather than silently mark every cell initialized.

The source correspondence should track payload value and initializedness separately, per element. For the fresh scalar new-array, no payload read is defined before its first real store. After reuse/flush, previously written cells can stay initialized; `in = 0` does not reset object storage or its initialization history. An arbitrary mask cannot be collapsed to `i < in`. Only the currently occupied prefix is required initialized by flush, while earlier initialized but now inactive cells remain possible. No desired initializedness premise is introduced at the original source entry.

## Source-refinement conditions

The normal-execution mapping needs both directions, with the private array and output slots projected away from observable source state:

1. Map the successful C++ new-array to a fresh typed private array with the same exposed element extent, payload definedness/value history and legal endpoints. Preserve the source pointer identity consistently across constructor, push, flush, copy and destroy.
2. Show the allocation identity is unobservable: no escaped payload pointer, pointer-to-integer conversion, ordering/comparison against unrelated objects, allocator replacement/hooks, address logging or retained alias after destruction. The adapter cannot assume these facts merely because the object is local. Enforce them from the exact source/call-use graph; unsupported cases are refused.
3. Generate distinct storage for overlapping/nested lifetimes. Under the existing one-buffer scope, the exact TDStep block already gives one lifetime. Sequential TDStep calls get new lexical lifetime events even if machine addresses are reused; no alias may survive and connect them.
4. Match deallocation with block retirement. The stand-in has explicit destroy immediately followed by block exit (`tdstep_standin.c:221–226`); prove that no source/model payload use occurs between those events. If a destroy becomes earlier than last scope use, a no-op destructor is unsound. Refuse that form or change scope placement so retirement is immediate. No general `\freeable` theorem is claimed.
5. Preserve the normal successful-allocation scope. Allocation failure/exception, resource exhaustion, custom operator-new observability and general multithreading are not equated with stack allocation. These must remain explicit unsupported boundaries, not silently assumed new success/termination results.
6. Retain exact same-array object and representable-span facts before subtraction. A shared allocation base alone does not imply one array. Physical alignment comes from the exact typed producer under the source semantics; WP's unsupported `\aligned` limitation remains visible. This proposal does not prove a generic incoming raw pointer is aligned.

## Global frame to private frame; helper TU versus TDStep

The old TDStep contract exposes `swdb_lqueue_storage[...]` in function assigns and separates its base from all incoming objects/device tiles. Remove that artificial global component from the new external frame and distinct-block predicate. Do not replace it with a new caller requirement naming a local object that does not exist at function entry. Fresh private object creation discharges separation at its lexical introduction; the generated proof/source certificate must establish this, not assume a fresh-base axiom.

Internal loops and helper contracts must still describe writes to the live payload array through `self->local_queue`. Loop assigns must include the currently live private array where required. Deleting the old global frame does not waive payload writes or initialization effects. At function exit no private payload object is externally accessible; preservation of all preexisting source objects remains required.

The helper-only root TU currently consists of a header include proving all 19 helper bodies. It does not execute TDStep's local allocation site. After the private ABI change, those modular helper proofs remain meaningful under their explicit storage-domain contract, but they cannot establish that a real caller supplied a fresh array. Add dedicated allocation-site control wrappers with automatic arrays in the root/control TU, and separately audit the TDStep lowering site. A header-only constructor proof whose storage comes from an unconstrained input pointer does not close allocator/source correspondence.

## Same-path controls and exact acceptance gates

The positive and negative controls must use the **same** local array declaration, constructor/storage-binding adapter, output-slot route, source/method and complete RTE initializedness settings. They differ only in the tested source operation:

| Control | Required observation after an independently admitted run |
| --- | --- |
| Constructor binds pointer; one real payload store; read/copy that cell | Pointer-output initialization and matching stored payload initializedness discharge, with ordinary obligations valid |
| Same construction; omit payload store; read/copy that cell | Payload initializedness/RTE obligation stays non-valid; parse errors/tool failures do not count |
| Same construction; store cell 0; read/copy cell 1 | Cell 1 remains unproved initialized; catches whole-array or wrong-cell initialization leakage |
| Same construction; uninitialized scalar returned/stored through out-slot | Original bad source-read RTE remains non-valid; out-slot initialization does not sanitize the source read |
| Same construction; flush/reset and later read previously initialized cell | Preserve allowed history, rather than asserting every inactive cell uninitialized |
| Missing typed producer, escaped alias, post-destroy use, wrong extent or misalignment provenance | Source gate refuses before proof, or exact relevant lifetime/domain obligation remains non-valid; no fabricated undefined C execution is required |

No native control result exists from this task. Native defined executions can check value/effect equivalence and instrumentation can count stores, but ordinary native execution cannot certify indeterminate payload initializedness and must not execute UB negatives as evidence. Formal controls must retain complete goals, smoke checks and source inventories. Fresh methods legitimately change goal counts; map the semantic obligations instead of forcing the historical245-goal count.

The minimum next step is an independent review of this scoped representation and a source-frozen private-ABI implementation with these controls. Root may then admit a finite formal component. Until its normalized init-map path, same-path controls, lifetime/source mapping and full new obligation inventory are independently audited, **allocator correspondence, full C_RTE, TDStep proof and ticket07 completion remain false**.

## Relation to the separately frozen output-slot package

Parent-supplied commit `1c018f1162cdef8fa97d70908a44f1a9bd2f7d5b` in `/private/tmp/probata-resume-t07-outslot` explicitly refuses allocator correspondence. Its `OUTSLOT-ABI-20261016.md` and `standin_outslot/abi-map.json` were read passively and are pinned in the companion JSON. The current allocator output interface is `void swdb_new_NodeID_array_out(size_t n, NodeID **swdb_out)` with a bodyless global-storage contract. The proposed separate refinement passes private typed storage plus its actual capacity through the constructor and adapter; the adapter becomes an ordinary proved pointer store with no payload initialization. All15 returning helper bodies,5 standard/builtin summaries and2 device output interfaces remain mapped. This note does not modify or admit that frozen package.
