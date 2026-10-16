# Closed no-growth source view — independent SPEC review

Date: 2026-10-16 ET. Reviewer: `caller_assess`; did not author the reviewed implementation.

Decision: **PASS for the isolated pending source projection.** No actionable SPEC defect found within that scope. This is not a theorem that the projected C refines the original caller, and it does not establish actual source/Typed eligibility, native proof, current constructor dependency admission, or caller acceptance.

## Fixed reviewed scope

| File | SHA-256 |
| --- | --- |
| `swdb/vector_reallocation_closed_view.py` | 758092d5997274b29e22f2196c46af361b7cfdfd5c9eb83ee328ae6a877eb757 |
| `tests/test_vector_reallocation_closed_view.py` | 99be4b68a902bf278b5dbb9e25ce57e2eabf51a4be9dd41f7d24bf26956925dd |
| `prototype/25-prefix10-resume-20261016/run_pure_closed_view.py` | 6d4bcb40fc2d6efdfba8a37777c7c7c2931f431c0ad874f24cc7b406d55a9def |
| `evidence/t25-closed-no-growth-view-preparation-20261016.json` | 122a9210486dda8a13f899478ecd461ab87219554b58ffd5c5c67f981d02345e |

The originating scope authorizes a concrete source-derived closed data/reserve/CFG projection, retaining original result/assigns clauses and a modular constructor, with terminal cleanup represented by explicit separate private lifetime/frame obligations under the existing allocator/library TCB. It does not authorize treating desired source correspondence, allocation origin, fresh private ownership, freeability, or a trusted projection as already proved.

Review used only current local source, exact hashes, retained metadata and stdlib/Git reading. No project import, test, compiler, native helper, verifier, solver, SSH or original-caller evaluation was run by this review. Source context is f918f5d52035fd99499280a0a8058efd0ed4ef55 plus the isolated working closed-view module/test.

## Source and contract checks

`prepare` delegates to the prior public caller view, which binds the actual C++ bytes, candidate/checker identities, exact no-growth captured-alias mode, and the unchanged three-clause contract (nonnegative signed count, assigns nothing, result conditional 7/0). It recertifies the complete lowered body rather than accepting an event list alone. The canonical body contains declaration, constructor, alias capture, reserve, a compound that captures the scalar then destroys then unconditionally returns, and one later unreachable fallback destructor. Changed/reordered/extra executable statements fail this whole-body grammar. Source/lowered event ranges and hashes also close.

The exact model identity is frozen. Complete source TU/default standard allocator substitution provenance is bound, with no preprocessing definitions, opaque summaries, probes or additional modeled types admitted. The binding correctly states that original-TU provenance does not establish a linked allocator environment without replacement effects. Existing allocation success and allocator/library contracts are explicit TCB, not newly proved absence of effects.

The source reductions have the necessary local obligations:

- The original pure `data` definition is checked exactly. Replacing its call with the actual field read retains its original readable precondition as an ordinary assertion. The captured pointer and later guarded dereference remain unchanged.
- The original reserve model body is checked by the base view. Its original valid/max-count precondition and the ordinary count-at-most-capacity assertion remain in the closed view before eliminating the false branch. The count expression and x86_64 ABI checks remain source-bound. Neither assertion is appended to the caller's inputs or treated as already discharged.
- The constructor call remains modular and its original model hash/source call are recorded. The certificate requires a current body proof and fresh allocation/fill/frame correspondence. It does not infer source freshness from a declaration or pretend WP33 natively implements fresh-memory frame semantics.
- Terminal destructor removal is an explicitly pending alternate cleanup interpretation. The complete original destructor body/precondition are recorded, representation validity remains an ordinary assertion, and dynamic freeability, release followed by automatic scope end, source ownership/no escape, Typed/Var correspondence, and all nine private-frame mathematical duties remain required. The scalar is captured before cleanup. No heap-equality substitution or allocator-effect erasure is admitted.
- Fallback cleanup elimination is bound to the exact whole-body unconditional-return CFG and the fresh unreachable event. Every closed-view edit records its preceding-view offset and inverts exactly back to the complete base view; the base inverse restores the original lowering. This is byte restoration evidence, not a semantic proof.

## Admission, tests and remaining gates

`formal_texts` is preserved exactly. `caller_premises_added` and `current_proof_records_admitted` remain empty. `source_typed_bridge_established` remains false. The original assigns clause remains recorded as assigns nothing, without changing its observer. `check` regenerates the entire text/certificate, so changes to data, CFG, lifetime transition or provenance do not become accepted input metadata. `check_launch` unconditionally raises after reconstruction; no production dispatcher or normal admission gate is broadened.

The tests use the public prepare/check/check_launch seam, inspect observable projected C and required duty metadata, and reject changed text, CFG, lifetime transition and provenance. The bounded harness replays retained genuine lowering/anchor output and denies external/native execution. The evidence distinguishes one initial missing-module RED, the first one-case GREEN, and the later five-case GREEN-v2 from an actual new compiler or WP execution. No test result is represented as current source-runtime acceptance or proof of the original caller.

Required before any later caller admission: actual source-created private identity/value/init relation through Typed+Var; the existing allocator/free TCB and effects; current constructor/body dependency; proved reserve/data/RTE/init/frame obligations; actual freeability and release/end-automatic correspondence; all nine conditional mathematical duties with full task/import/hypothesis closure; complete original observer/result/frame proof. The inherited prospective runtime metadata spells `Ctypes.ml`, while the installed Linux basename is `ctypes.ml`; a future actual bridge must resolve that physical basename and recheck the source pin. No current admitted launch consumes it.
