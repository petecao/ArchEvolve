# Closed scalar and frame observation rule

2026-10-16 ET. Concrete next integration design. Not an admitted source theorem.
The root coordinator owns final source/semantic admission and actual jobs.

The closed function exposes exactly two observations: its returned scalar and
the unchanged contents/initializedness/identity of every incoming object. It
returns no pointer and stores no private pointer into an incoming object or a
global. The complete source AST/lowering, event order and inverse already checked
by `vector_reallocation_closed_view` establish this syntactic scope.

The source rule should relate these observations by private effect footprints,
without claiming a total encoding of arbitrary incoming Typed memory into
`Heap::cell`. The current Heap cell type contains integer and pointer cells;
it is insufficient to claim a universal float/union/byte-chunk bijection. The
source effect/frame rule can preserve incoming cells of every type because it
does not write or release any incoming object. Typed proves the scalar/read/init
and no-growth assertions of the projected C. The alternate Heap interpretation
accounts for actual source-created private identity and terminal release.

| Source step | Exact checked effect and fact | Required evidence |
| --- | --- | --- |
| Automatic declaration | Introduces receiver identity `r=fresh_id(entry)`; receiver is private, initialized only by subsequent stores and is not dynamically freeable. | Actual original source/local-storage interpretation, receiver.entry, existing automatic-storage primitive. |
| Count/value constructor | Initial receiver stores; empty return or successful fresh allocation `b`, capacity store, unbounded fill loop and size store. Every source write is to `r` or `b`; allocator frames incoming memory. | Exact original/qualified executable-body inverse; constructor35 complete target/source/hypothesis closure; constructor.frame, buffer.identity and positive.exit_image. The value is the actual source constant7, not an arbitrary assumed fill result. |
| `data()` and reserve | Captured pointer is the receiver's actual data field. The unchanged count equals capacity, so the reserve growth branch is false. | Exact data body/precondition reduction; native data, reserve precondition and no-growth assertions, plus source count/layout relation. No null-plus-zero rewrite is assumed. |
| Guarded read | Empty branch returns literal0; positive branch reads initialized live element0 and captures value7 into a scalar. | Native initialization/access/result obligations; source int image and constructor fill; unchanged guard and capture event. |
| Terminal destructor | Releases null or the fresh dynamic buffer, then receiver automatic storage ends. The captured scalar survives. No pointer is observed afterward. | Exact destructor body/inverse, destructor11, private-frame9 and zero/positive cleanup gluing. The full existing deallocator TCB frames other memory and ends only the specified allocation. |
| Return | Only the captured scalar escapes. Incoming objects retain all observable fields/cells, including types outside the local integer/pointer projection. | Complete source noescape/control-flow certificate and the explicit source effect frame rule. |

The allocator/library TCB must explicitly state fresh valid freeable output,
incoming-memory framing and release/lifetime correspondence, in addition to
allocation success and member/library correspondence. Full-TU screening and
`std::allocator` spelling do not prove that separately linked replacement
operators are absent. Their effects are covered only under that explicit TCB.

The first integration seam should be a closed-source evidence validator with
three inputs: the freshly checked source view/manifest, complete exact
content-addressed scientific dependency evidence, and the complete native
projected-C observation. Its output must identify the footprint rule, complete
TCB and original contract, and preserve every historical producer's real method,
compiler, setup and reader identity. It must reject omitted effects, changed
source/control flow, pointer escape, unknown dependency domains, missing ordinary
goals and unsupported source/type cases. Hash equality alone is an input-identity
check; source-rule validity still rests on the reviewed effect interpretation and
its complete mathematical/ordinary duties.

The existing generic `WpAdapter._proven` requires current method/setup/reader
identity recursively. Changing it to accept an old aggregate identity by name
would broaden generic admission. The first closed route instead needs an
explicit scoped dependency policy/pin for this scientific evidence, with current
source effects and exact original-to-qualified body correspondence checked
before any original constructor summary is admitted. An old qualified theorem
does not become a current original `c_model` record, and the existing ordinary
reader's `not_proven` constructor dependency must remain until this policy is
implemented and independently reviewed.

Current exact reusable components are constructor35/destructor11 and their
unchanged models/theory/targets/tool/support closures, plus the separately
accepted private-frame9. The six new gluing duties are the only new mathematical
targets in the prospective profile. The projected-C run already retained every
native term/report; fixing its metadata observer does not require another proof
run. Complete term/hypothesis interpretation is still needed before those
conditional native results can support an accepted source-facing record.

General member/type/default-catalog integration remains separate. This rule
must not enable generic member calls, returned pointers, aliasing transfers,
copy/move/swap protocols or additional element-image semantics by spelling.
