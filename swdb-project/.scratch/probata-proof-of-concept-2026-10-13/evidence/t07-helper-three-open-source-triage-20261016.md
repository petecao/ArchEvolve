# Ticket07: three open helper obligations, passive source triage

2026-10-16 ET. **The measured run is complete; the helper proof is incomplete.**209/212 ordinary goals are valid and33 smoke checks found no contradiction; every open goal was attempted by the full three-prover portfolio. No rerun, source edit, hypothesis insertion, proof hint or compiler/prover/native probe occurred in this triage. Frozen7930 and all run inputs remain unchanged. Exact source/API/report pins are in `/private/tmp/probata-t07-helper-three-open-source-triage-20261016.json` SHA2b008af5194f49d087c2e7b4717736194aeaa74b32248898188aaeff74eaef87.

The retained normalized C/property descriptions identify the exact assertions below. No .why/.mlw/.smt2/.psmt2 task or session file remains in the settled raw directory. Consequently the complete simplified/unsimplified VC hypotheses and any solver countermodel cannot be inspected here. The backend findings below are source-grounded causal analysis, not an assertion that an actual solver produced a counterexample.

| Machine goal | Exact retained source property | Assessment |
|---|---|---|
| typed_QueueBuffer_NodeID_QueueBuffer_ensures_3 | ensures gapbs_buffer_domain(\old(self)) | Strong call-result initializedness transfer hypothesis; no false C-source postcondition established |
| typed_QueueBuffer_NodeID_flush_assert_rte_initialization_9 | initializedness of copy_start | Strong modular-call return destination initializedness gap |
| typed_QueueBuffer_NodeID_flush_call_std_copy_NodeID_requires_4 | byte-offset range bound for std_copy | Concrete Typed logical-cell→byte conversion abstraction gap |

## Return destination initializedness

The constructor writes sq/local_size/in directly and obtains local_queue from swdb_new_NodeID_array. Its final domain includes initializedness of the local_queue field; the separate pointer-value postcondition succeeds. Flush initializes copy_start directly from fetch_and_add_size_t before using it in shared_queue+copy_start. The exact open ninth emitted RTE assertion is initialization of copy_start (normalized.c974; sourceheader298). Neither fact justifies demanding a new incoming initializedness premise: the destination is constructed/assigned by this body.

Pinned `/Users/yanrujhou/.opam/framac-33/lib/frama-c-wp/core/CfgWP.ml:1289` obtains the return-lvalue memory domain and havocs it. MemLoader.ml80–83 makes that domain the union of value and initialization footprints; MemVar.ml1356–1366 likewise retains SINIT for ordinary local variables (Cvalues.ml123–124 treats only scalar formals/globals as always initialized). CfgWP.ml1360–1373 then binds the returned value to the destination through a value equality, with no stored_init relation in that binding. By contrast the ordinary assignment rule CfgWP.ml769–785 explicitly emits copied_init or stored_init. StmtSemantics.ml332–347 has the same value-only call-return transfer shape.

This gives a concrete **abstract memory-transfer explanation**: the value result can satisfy the exact pointer/numeric postcondition while the destination initializedness component remains unconstrained by the inspected call-return relation. That is not a physical C counterstate satisfying the actual constructor/flush execution. Constructor postcondition is conjunctive, so without its fully retained VC the precise failing conjunct is still a hypothesis, although local_queue's call-result initializedness is the directly shared boundary.

The correct next gate is semantic qualification of that call-return transfer for the actual scalar/pointer returns, retaining all body/RTE checks and distinguishing struct padding. Do not pre-initialize the caller destination as an assumed premise or insert a contract only to force this postcondition. A backend correction would require a separately reviewed tool-method revision and suitable semantic controls; it has not been implemented or admitted here.

## Accurate from clauses are not an established repair

Pedantic pointer-result/from warnings remain real documentation/imprecision observations. However, in the inspected call-effect path, LogicSemantics.ml1013–1016 ignores _deps when compiling assigned regions, and894 treats TResult as no ordinary memory region. No result initializedness relation is added by CfgWP.cc_result. Thus adding an accurate result/from declaration must not be claimed to fix these goals without separate evidence.

Nor is initializedness of address-of-result a supported shortcut: LogicSemantics.ml211–216 explicitly aborts Address of result when the result is represented as R_var. No such syntax or axiom was inserted. This is a tool-interface boundary to establish, not permission to add a desired-result premise.

## Numeric byte offset is abstract in this Typed model

For the copy call, first is local_queue and last is local_queue+in. The source-backed buffer domain fixes local_queue to a16384-element NodeID array and bounds in<=local_size<=16384, so ordinary defined C array arithmetic has a tiny representable span. No physically invalid caller state has been established for this condition.

The pinned backend deliberately separates logical cell offsets from physical bytes. MemTyped.ml206 documents the distinction; its shift generator378–391 increments model-cell offsets by length_of_object. MemTyped.ml617 maps the ACSL byte offset through MemAddr.base_offset, which at113–117 applies table_to_offset(table_of_base(base), logical_offset). The exported theory `/Users/yanrujhou/.opam/framac-33/share/frama-c/share/wp/why3/frama_c_wp/memaddr.mlw:147` declares this table abstract and gives only zero plus strict monotonic ordering (153–159). Searches of the pinned core/theory surfaces found no corresponding sizeof scale or numeric upper-bound law.

A restricted-theory counterinterpretation makes the gap explicit: table_to_offset(t,i)=K*i, with any positive integer K, satisfies those zero/order laws. Choose K greater than PTRDIFF_MAX*sizeof(NodeID); even a one-cell difference then violates the requested byte bound. This demonstrates insufficiency of that offset-table vocabulary for the desired numeric inference, not a machine-pointer counterexample or a constructed model of the unavailable entire VC. Other memory validity/cell bounds do not supply the missing byte-scale relation in the inspected interface.

The next correctness gate must establish the supported conversion/source-array correspondence, or qualify a different memory representation/domain translation with semantic evidence. Do not add an arbitrary byte-offset axiom, assume the copy precondition at the caller, drop the obligation, weaken the frozen contract or change the algorithm merely to close this goal. Extra solver time alone does not address either identified semantic interface.

## Admission boundary

All three claims remain open until a separately reviewed source/tool correction is concretely justified and evaluated under a new method identity. Old actuals and their245/352 universe stay immutable. No counted provider run is authored here. Alignment, complete C++ allocator/lifetime/graph caller correspondence and the original TDStep proof remain unproved independently of these three logical helper obligations.
