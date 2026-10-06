# Bounded source objects and ABI referent views

Updated: 2026-10-06 19:40 ET. Delegated ticket11 prerequisite; ticket09/11 custody is unchanged.

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
