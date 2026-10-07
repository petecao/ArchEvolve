# Bounded source objects and ABI referent views

Updated: 2026-10-06 20:08 ET. Delegated ticket11 prerequisite; ticket09/11 custody is unchanged.

The public seam is `swdb characterize --object-scopes` on copied-store source fixtures.
The observer is optional. Absent optional fields retain historical receipt identities and
existing count-site numbering. The normalization recipe stays fixed; new observer source
and runtime hashes identify fresh executions. No address or address sequence is persisted.

A source alloca has a full target-DataLayout extent only when its element size is fixed
and the runtime array-size product and address range do not overflow. Frames exist before
ROI entry, retire on normal or supported Itanium exceptional exit, and distinguish nested
and recursive calls. Explicit lifetime start/end and stackrestore retire/recreate the
corresponding lifetimes; unproved extents, unsupported exits, scalable objects and bounded
observer-state exhaustion retain named unknowns. Defined globals have their declared
storage extent; external declarations do not prove an allocation.

An OpenMP microtask's first two `kmp_int32*` arguments admit a **four-byte ABI referent view**
for that call. This does not establish the libomp allocation base, extent or physical
residency. A containing source allocation takes precedence. Exact view aliases share one
view identity; unresolved overlap remains unknown. Views retire with their function frame;
accesses outside the admitted range remain unknown. Existing allocation-relative page and
lifetime facts remain unknown for view-only requests; distinct view coverage is explicit.

Independent public fixture expectations: two 129-byte source arrays read at byte offsets
0,64,128 yield six useful bytes, six logical allocation-relative lines, one pre-ROI and one
in-ROI page. This fixture is a contract check, never BFS/BC application evidence.

First vertical slice: the public command rejected the missing `--object-scopes` flag (RED),
then the fixed caller/callee fixture passed with the exact six-line/two-page expectation
and copied-store validation (GREEN: 1 passed, 3.51 s). This slice supports fixed allocas
and normal frame return only; dynamic/lifetime/unwind/view coverage follows separately.

Dynamic extent slice: six logical requests were unresolved (RED); checked target-element
size multiplication admitted the 129-byte runtime alloca (GREEN: 2 passed, 6.62 s).
The normalized fixture contains explicit stacksave/stackrestore and fixed-array lifetime
start/end; callbacks retire only matching frame-owned allocation identities.

ABI referent slice: actual libomp microtask execution produced one unresolved four-byte
global-thread-id load (RED). Its ABI view now covers that logical request and one view-relative
line; full allocation lifetime/page facts remain null with `bounded_view_not_full_allocation`
(GREEN: 3 passed, 10.81 s). Full allocations take precedence and keep their own lifetimes.
The shared insertion preserves the tested command-guard foundation at `93b09f4`.

## Confirmed lifecycle and integrity boundary

The source frame is a normalized LLVM function activation, after the frozen helper-inlining
recipe. Ordinary return, Itanium landingpad/resume, explicit lifetime end/restart, dynamic
array extents and direct stacksave/stackrestore are supported. Storage creation order is
tracked separately from lifetime start: a fixed entry alloca that starts its lifetime after
a checkpoint survives that checkpoint's restore. Repeated start on a live object retains
identity; end followed by start creates a new lifetime.

Funclet/coroutine/callbr lifetime classes, TLS/external globals, nonintegral/scalable extents
and unknown checkpoints cannot establish full source-object coverage. Explicit nonlocal exits
forget source frames/views and name `nonlocal_control_flow`; recovered unproved frames remain
unknown. Returns-twice and Itanium cleanup paths reconcile descendants. Defined executable
non-TLS globals have declared storage extent and pre-ROI lifetime. No allocation base,
address sequence, physical first touch, residency or cost is inferred.

The callback protocol verifies alias deduplication, overlapping-view refusal, full-storage
precedence without view-exit deallocation, child unwind retirement, checkpoint ordering,
unknown/overflow extents, unknown checkpoints, bounded thread/frame/view ownership state and
request-counter overflow. Requests overflow to null with `request_count_overflow`, never zero.
The public validator requires the three coverage buckets to partition executed requests,
checks all four scope facts as nonnegative integers or null, and refuses full allocation
page/lifetime facts when a bounded view is the only proof.

A late-source-destructor fixture exposed a finalized mutex access (RED). The opt-in gate now
closes before lazy Counts finalization and suppresses later callbacks (GREEN: all 14 public
runtime cases passed, 1.28 s). The preceding complete public source/runtime batch passed
22 cases, 36.42 s; the final combined compatibility gate follows after the stable foundation
merge. No application timing or fresh BFS/BC outcome is claimed by these fixtures.

The compiler basis is the pinned LLVM 22 DataLayout and [alloca/lifetime/stack semantics](https://llvm.org/docs/LangRef.html#alloca-instruction).
The bounded OpenMP view follows the documented [kmpc_micro ABI](https://openmp.llvm.org/doxygen/group__PARALLEL.html), not a deduction of libomp's full allocation.
