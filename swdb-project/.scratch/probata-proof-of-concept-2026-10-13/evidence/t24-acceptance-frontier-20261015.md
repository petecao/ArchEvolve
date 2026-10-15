# Ticket24 current acceptance frontier

2026-10-15 ET. Baseline `c6636b0db5e5d861c243721f3eeef41a3d00051b`.
Compiler inventory only; no verifier/provider/remote job launched for this audit.
Raw input hashes, C lowerings, reports and script:
`/private/tmp/probata-t24-frontier-20261015/{compiler-inventory.json,inventory.py}`.
The script uses original per-group sources and current fixture metadata. Imported
proof eligibility and actual full-candidate setup are deliberately separate.

| Original group | Current compiler boundary | Retained actual evidence and remaining work |
|---|---|---|
| classes / enum / constexpr | Pass with existing explicit a:n metadata | Original standalone Bag/Counter safe146ordinary+11smokeValid, seeded one invariant timeout/11smokeValid at2f85/c4cf. Full original per-candidate route/current method replay remains. [Class evidence](t24-member-lifetimes-mac-20261015.json). |
| new[] / terminal delete[] | Pass with checked terminal-release certificate | Earlier focused initialized nonescaping fixture proves49ordinary+7smoke; use-after-delete and unsupported lifetime/alias shapes refuse. Current full safe/out-of-range/seeded/refusal acceptance replay needed; do not replace with general allocator theorem. See ticket24 checked terminal release section. |
| templates / two Ring instantiations | Refuse Ring_int_3_put opaque embedded items origin | Needs exact typed fixed member-array/subobject policy for live contextual receivers. No allocation flattening or validity-to-origin inference. Original source and contract remain intact. |
| OpenMP at one thread | Missing a:n metadata; with matching explicit domain still refuses pure if(a[i]>...) condition placement | Add only typed metadata matching original initialized valid range. Narrow ordinary guard immediately before pure IfStmt condition, with exact source-node membership and no init declaration, side effects, calls, short circuit or volatile reads. No body-effect waiver. Then current safe/seeded actual pair. |
| floats | Missing a:n metadata; adding matching explicit domain passes compiler checks | Existing requires already state valid initialized double a[0..n-1]. Add typed metadata only, then actual safe/seeded replay under the recorded real-float-model assumption. |
| std::min/max/swap/copy combined | Refuse return's n>0 ? b[0] : 0 conditional access placement | Exact call provenance and qualified-copy discharge exist. Needs narrow path-conditioned ordinary numeric obligation or checked source-preserving view; guard must not force access on n==0. Then all5 current model records + original safe/seeded caller. [Caller evidence](t24-std-copy-callers-mac-20261015.json). |
| __atomic / __sync | Compiler passes, models inventoried | Focused exchange/fetch/CAS result callers and negative input-init control have historical actual records. Full original group has no fresh current-policy acceptance. Needs its9 models and original safe/seeded caller, all init/RTE/smoke. |
| __dxc / maa summary fixtures | Compiler shape passes with declared fixture summary mapping | Old actual summary proofs are on explicitly labeled stand-in definitions. Current import must bind exact actual callee body/closure/domain/proof method; no production DX semantics claim. Original full caller/dependency-pin replay pending. |
| unsupported constructs / naming | Existing public refusal and deterministic lower/C-compile controls retained | Run focused current union after changes; never change a positive fixture into an expected refusal. |

The frozen1ece remote construct shard stopped after5PASS/1FAIL at standalone
std_copy_int's opaque origin before any full original group. Its14unique model
subjects comprise13proven models plus the failed copy, and3stand-in summaries
proved:17dependencies total, not17models plus3summaries. Qualified copy was later
repaired/proven independently on Mac/Linux. These exact historical results and
hashes remain in [remote audit](helper-construct-mbit10-20261015.json),
[qualified body](t24-std-copy-qualified-body-mac-20261015.json), and
[focused Linux callers](focused-parser-owner-final-20261015.json). Old methods or
matching names alone do not make a dependency eligible under the current setup.

The allocator does not currently block the original narrow new[] fixture's
compiler path. WP33 still lacks general deallocation semantics. Any later lifetime
extension must preserve the original source and use an independently checked view
or translation with ordinary validity/init/numeric/lifetime obligations; a false
freshness/validity premise or dropped lifetime goal is not acceptance.

## Closeout boundary

The active pure IfStmt placement slice was implemented at081c67fd, with a needed
AtomicExpr purity hardening atef41e5f8. Its original OMP compiler tracer went RED
at condition placement and then GREEN. A separate compiler RED showed that a
hidden __atomic_fetch_add side effect could be treated as pure; the new explicit
AtomicExpr refusal closes that admission gap without claiming an actual false
proof. Exact condition AST membership and purity are checked before an ordinary
guard is emitted ahead of the if. Later branch-body mutation does not execute
before that condition read. Init bindings, short circuit, calls, volatile and
mutating-index conditions remain refused. The original OMP/floats fixtures gain
only explicit typed a:n metadata matching their intended existing range interface;
their numeric/validity/initializedness requires and hints are unchanged. This typed
input qualification is explicit, never inferred from validity.

At the user's closeout steering, no std conditional-return, embedded Ring array,
new allocator or other frontier implementation was started. Those remain the
concrete compiler/proof gaps above, not scheduled work or silently passed criteria.
No new batch verifier or remote job was launched. Finish only the active slice's
focused compiler/public stand-in review and preserve a resume pointer. Ticket24
stays claimed; final method review/freeze and whole-ticket acceptance are open.
