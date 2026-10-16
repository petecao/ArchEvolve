# Ticket24 finite agreement pilot: independent admission review

Created: 2026-10-15 ET. Read-only source/artifact review; no new tests, compilers,
solvers, provider or remote jobs. Only this note and its compact audit JSON were
written outside the repository.

## Decision

**Admissible to scale the finite-only runner to all9 original construct groups at
the reviewed clean freeze. No blocking source/admission finding was identified.**
This admits the planned experiment, not unrun rows or ticket completion. Results
remain finite native C++/ordinary-C agreement, with actual WP safe/seeded acceptance
and source-to-WP-view checks audited separately. No proof records or formal C++
equivalence are established.

Reviewed checkout `/private/tmp/probata-t24-agreement` is clean at
`e48a302e0081ce46d8c2f865568951913833d276`. Runner:
`swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/t24-finite-agreement.py`;
CLI controls: `swdb-project/tests/test_t24_finite_agreement.py`.
Pilot `/private/tmp/probata-agreement-pilot-e48a302e/native/agreement.json`
SHA256=`1f1bb4e026f814cb277094248040afef3cbd44046c049e779ee0cd3b03ef65a1`.

## Independent pilot validation

Recomputed **2,040 declared file references /1,059 unique resolved paths: zero
missing/hash mismatches**. This includes runner/runtime sources, generated original
safe/seeded TUs, C/C++ native inputs, harness, contracts, domain, binaries, outputs,
compiler configuration, physical headers and link inputs. Counts include repeated
references; they are not2,040 different files. The manifest itself was separately
hashed. No pilot binary was executed during this review.

Independently reconstructed `_domain` for the template unit as the49-row Cartesian
product of `[-2,-1,0,1,2,INT_MIN,INT_MAX]` for `(a,b)`; order matches retained
`domain.txt`. On both safe and seeded rows, all49 C/C++ comparison lines match,
25 end=done and24 end=infeasible. The latter correspond exactly to original
`-1000<=a,b<=1000` filtering. Zero known/sanitizer UB exclusions.

For every defined safe row, the observed result equals `2*(a+1)+4*b`; for every
defined seeded row, result equals that expression minus2, matching original
`r.get(1)` to `r.get(0)` mutation. Seeded output retains the same named postcondition
failure on both sides; it is still finite defined-output agreement, not a successful
functional proof. Manifest counts and output hashes match the retained streams.

Outer command selects templates at the exact freeze. `resources.json` reports
exit0,9.786s wall,1,108,099,072bytes peak RSS, no timeout/OOM. These are retained
runner observations, not a new execution. Separate retained CLI-control summary
at `/private/tmp/probata-agreement-controls-green/{pytest.log,resources.json}`
reports5 passed in34.40s and exit0. The five controls' source assertions cover
original template pair, first defined C-only mismatch, one-sided sanitizer failure,
retained-output tamper, and explicit allocation-seed UB-only exclusion. This review
did not independently rerun or reconstruct all their temporary outputs.

## Why the runner is appropriate for the accepted22 subcheck

1. **Source/glue:** ordinary lowering comes from the actual pinned original TU;
   C++ compiles the full original TU, preserving classes/templates that the old
   synthesized-name cutter cannot reconstruct. Original safe/seeded fixture bytes
   are generated from pinned `GROUP_FILES` and exact shared `SEEDED_BUGS`; source
   hashes remain separate. No WP view or summary stub enters this comparison.
   dxc/maa C links the actual pinned fixture definitions; C++ TU includes those
   same definitions. This is fixture-summary glue, not real device semantics.
2. **Premises/oracle/domain:** uses current `tr.harness`, `Plan`, clauses and22's
   `_domain` with seed22, not a new hand-selected witness. Physical capacities and
   finite size extents are explicit; original requires remain. Converting unary
   `*p` to `p[0]` is exact for these allocated initialized one-element buffers;
   current normalized clauses contain only the intended atomics dereferences.
   No new input premise grants a symbolic theorem. Small finite value choices and
   deterministic sampling remain explicit coverage limits.
3. **Observations:** shared harness compares return, input-buffer poststate,
   relevant scalar/global observations and named post/frame checks as22 does.
   Complete lines are compared, including infeasibility; equal infeasible-only
   streams cannot pass. Original constructor/destructor effects reach those
   observations through the actual functions. Unobserved arbitrary execution
   state is not claimed equivalent.
4. **UB:** explicit source-specific exclusions remain in requested domain, with
   indexes/reasons; they are not new requires. Both native sides use ASan/UBSan
   and nonrecovering diagnostics. A one-sided sanitizer set fails instead of being
   masked into agreement. `-fwrapv` is retained from22 and disclosed; known seeded
   signed-overflow is still excluded. Sanitizer silence does not prove universal
   absence of UB. Allocation's all-undefined seed is explicitly
   `excluded_undefined_only`, never `agree_on_defined_inputs`.
5. **Pins/control:** source/runtime/compiler/configuration/header/link inputs and
   raw/normalized/defined outputs are independently auditable. C-only fault control
   names the first defined witness and stops the batch. The report and every row
   explicitly state `formal_verifier_launched:false`; success is experiment
   completion under stated finite criteria, not a counting proof verdict.

## Conditions on full9 acceptance

Retain exactly this frozen runtime/source set and outer resource guard for the
next launch; a source change requires a fresh freeze and affected review. Each
safe group must have nonzero defined comparisons and matching observations.
Defined seeded groups need the same; precondition/known-UB/sanitizer exclusions
stay separate. The new_array seeded row can complete only as the explicitly
UB-only control. It provides no numeric agreement on undefined source executions.

Treat a genuine mismatch, one-sided UB, compile/glue failure or no-defined-coverage
as a failed/incomplete row and stop; do not shrink the original contract, change
the domain retroactively or classify the result as a new formal proof.
The first full9 run still has to establish its own actual outcomes and physical
artifact audit. The pilot covers templates only.

System library boundary is honestly declared: link-time physical libraries/SDK
stubs are hashed; dyld-cache runtime bytes are not independently hashed. Header
closure/configuration pins bind the actual compiler context; this finite fixture
runner does not provide unrestricted production standard-library admission or
allocator soundness. That limitation does not block the finite experiment.

The all9 native profile does not execute `wp_pointer_bounds.prepare` or certify
the terminal-release/member/conditional WP views. Keep their independent checked
source relations and actual RTE/initializedness/smoke evidence; combining records
must preserve those boundaries. This review does not reopen symbolic CBMC
admission or require18 redundant formal jobs solely for native agreement.

Compact independently reconstructed audit:
`/private/tmp/probata-t24-agreement-pilot-review.json`.
