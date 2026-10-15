# Ticket24 original-construct resumption

Updated: 2026-10-15 ET. Implementation checkpoint, not completed actual acceptance.
Runtime slices: `8a3bf8f5` (fixed subobjects/conditional returns), `b801e5a2`
(terminal overrun negatives). Strict actual-matrix reader: `3659d3e2`.

## Decisions and assumptions

1. Structural subobject identity is admitted only for direct automatic, trivial,
   standard-layout primitive records in one independently bound original-TU call
   closure. The original `Ring<int,3>` and `Ring<long,2>` remain separate types and
   arrays. Copies, aliases, escapes, arbitrary incoming receivers, nontrivial
   lifetimes, multidimensional fields and pointer/reference helper arguments
   remain outside this certificate. The longest closed inline path is at most
   two, matching the existing independently demonstrated parser policy. No
   validity, initializedness, separation or numerical requires is generated.
2. A pure ordinary return may carry a read under an exact source conditional.
   Its checked numerical assertion is a path implication; the original C
   expression remains intact. Only primitive integer comparisons with pure
   operands are duplicated. Calls, atomics, mutation, volatile reads and short
   circuit conditions refuse. Ordinary RTE checks the original evaluation,
   including overflow and initialization; branch smoke remains mandatory.
3. The terminal owner checker additionally recognizes the original overrun
   initializer `for(i=0;i<=n;++i)buf[i]=...`. It covers every legitimate element
   before any following array read, but its extra write remains in C and must
   fail an ordinary RTE obligation. The source, count, owner, no-escape policy,
   scalar return and terminal-release restriction remain unchanged. This is no
   general deallocation theorem. The original use-after-delete and other
   lifetime/alias negatives remain explicit compiler refusals.
4. Existing one-thread OpenMP/atomic semantics, allocation-success assumption,
   fixture-summary stand-in scope and real-valued float/rounding assumption
   remain explicit. No held-out kernel, original fixture, original contract or
   original hint was replaced to obtain an easier proof.

## Verification so far

| Profile | Result | Boundary |
|---|---|---|
| New fixed-array/conditional controls plus standard-model setup controls | 16 passed, 7.33 s | Includes original-template public fake-WP setup; no solver |
| Existing original determinism/C11/native/name/refusal profile | 29 passed, 72 deselected, 50.42 s | Bounded native C/C++ agreement; no universal agreement claim |
| Terminal-overrun and existing terminal-owner controls | 12 passed, 91 deselected, 8.16 s | Compiler policy; original invalid write retained |
| Earlier member/condition/source/copy union | 73 passed, 1 failed, 1 deselected, 79.40 s | New public test initially inherited unrelated concurrency-frame defaults; corrected to the original template's empty interface and reran in the 16-control profile |

The first sandboxed union had three additional harness failures because the
mandatory RSS watchdog could not read sysctl process state. The public fake-WP
controls were rerun outside that sandbox. The existing Frama-C parser-only test
was excluded from the follow-up union to preserve the Mac actual-verifier
reservation. No actual solver proof is claimed by these compiler profiles.

Independent source review at `8a3bf8f5` is in
[t24-fixed-arrays-source-review-20261015.md](t24-fixed-arrays-source-review-20261015.md).
It found no confirmed runtime false-proof defect, and identified a concrete
acceptance-reader gap: a seeded prelaunch refusal could count as actual
acceptance. `3659d3e2` now requires real launch, passed setup, mandatory RTE/init/
cache/machdep/smoke settings, nonempty actual ordinary/smoke inventories,
attributable open ordinary negative goals, and byte-matching report/record
hashes. Deliberate lifetime refusals have a separate reader branch. This review
is an agent source review, not personal human approval or actual WP evidence.

## Exact-source remote runner

`prototype/t24-original-matrix.py` uses the existing public candidate submission
and `swdb prove` builders from `tests/test_wp_subset.py`. It binds a required
Git SHA, refuses dirty tracked source, records a source manifest and candidate
IDs, writes incremental `matrix.json`, runs one worker, and preserves the normal
shared verifier lock and 8 GiB RSS cap. Each original group uses its unchanged
contract/hints and original safe/seeded artifacts. Model and fixture-summary
proofs are separate jobs whose exact proof IDs/hashes must occur in caller pins.
All raw evidence stays in a fresh output directory outside the repository.

The root coordinator owns mbit10 lane 0 and the sole integration publication ref.
Estimated diagnostic Ring pair: five minutes; complete matrix: 30–90 minutes,
unmeasured. Output budget: 2 GiB under `/data/yanruj/EvolveSWDB_runs/`; root checks
live leases/storage and launches through the verified socket wrapper. Actual
acceptance, normalized-source audit and current-method ticket closure remain open.

At `b801e5a2`, the complete original combined-source compiler inventory admits
all nine safe and all nine seeded units through the lower/prepare seams, with
exact original fixture summary mappings and explicit a:n/b:n metadata. The
terminal safe/seeded pair both retain checked allocation certificates. This is
18 compiler admissions, not 18 actual proof acceptances.
[Compact inventory](t24-original-compiler-inventory-20261015.json) records each
source/lowering hash; original combined sources remain at
`/private/tmp/probata-t24-original-compiler-current/`.

## Composed no-window prelaunch control

After merging integration `71771f09` into this branch at `1e01cd2d`, the new
public no-entry-window control replaces the generator's source-plan pointer
with an altered Ring source after planning. Original pinned job input bytes
remain untouched, so this specifically exercises the member-context source
reparse trigger rather than the generic changed-input guard. Removing that
single trigger produces RED: the fake verifier runs and writes a record;
restoring the exact production bytes produces GREEN: prelaunch refuses
`pointer_bounds` and writes no proof record. The temporary mutation was
restored; no production code changed for this control.

The composed fixed-array/conditional/terminal/static-model public profile
passes **19/19 in 15.55 s**. It uses a fake verifier only. RED log:
`/private/tmp/probata-t24-no-window-trigger-red.log`; GREEN output root:
`/private/tmp/probata-t24-composed-compiler-public/`. Runtime `swdb/` bytes
match frozen integration `71771f09` exactly. The remote actual Ring tracer
is separately owned by the root coordinator; this test does not relabel it.

## Original Ring actual pair accepted

Frozen integration `71771f097feb83338928430bdf78a4de8384e63b` ran the original
per-candidate template group under mbit10 node 0, lease generation 569. The
original contract, original empty hints and all nine original seeded source
substitutions were checked against the physical artifacts.

| Original artifact | Actual result | Retained obligations |
|---|---|---|
| Safe Ring int/long | proven; 89 ordinary and 1 smoke Valid | 25 RTE initialization goals; zero residual Ring/twice calls in the normalized selected entry |
| Seeded `r.get(0)` | not_proven; 88 ordinary Valid, one ordinary ensures timeout, 1 smoke Valid | Same 25 initialization goals; zero residual selected-entry calls |

Public command times were 162.54 s / 197.10 s, including validation overhead.
Counted proof-job wall times were 40.62 s / 72.80 s; peaks were 314,548,224 /
649,666,560 bytes. The outer guarded worker and normal per-proof shared lock
remained in effect. Timeout is not a solver counterexample. Independently worked
source arithmetic at `a=0,b=0` gives the required result 2, the safe result 2 and
the seeded result 0; this is labeled as worked arithmetic rather than native or
solver counterexample evidence.

[Compact independent pair audit](t24-original-template-pair-mbit10-20261015.json)
checks both record hashes, all 22 report instances, 184 candidate/baseline
artifact-file instances, physical method and canonical contract pins, naming/
checker pins, unchanged clauses/hints, exact member policy/anchors/setup hashes,
and all 980 frozen physical source files against both SHA-256 manifest and Git
blob identities. No added premise or audit error remains. Raw records, logs,
normalized C, candidate sources and manifests remain remote at
`/data/yanruj/EvolveSWDB_runs/probata-resume-t24-templates-71771f09/`.
The compact audit SHA-256 is
`6485b774905802257c7064ea4c6493f9b2d3876122eaca70fbae97a4d7bb22f8`.

This clears the original Ring/compiler-origin boundary only. The other eight
construct groups, model/summary dependency closure and lifetime actuals remain
required under the current method before ticket closure.

## Concrete seeded native diagnostics

Following the dxc precision-control finding, all eight non-allocation original
safe/seeded groups were replayed on one explicit in-domain input through native
C++ and the C lowering. All 32 observations agree between languages. Every safe
case satisfies its original clause; every seeded case violates it: class 3/4,
template 2/0, std destination 7/0, OMP 0/1, atomic final p 10/11, float
0/3.333333333333333, corrected dxc 1/4, maa 1/2. Values are safe/seeded pairs,
not timings or universal agreement claims. The float value is observed native
arithmetic; it is not a proof over IEEE rounding.

The original allocation overrun is deliberately not executed as native C++
because it has undefined behavior. Its current-policy actual RTE outcome remains
mandatory. [Inputs, source/binary hashes and outputs](t24-original-seeds-native-20261015.json)
record the Mac ARM compiler diagnostic (26.08 s). Raw files remain at
`/private/tmp/probata-t24-original-seeds-native/`. This additional native evidence
does not replace any actual WP safe/seeded/RTE/initializedness/smoke acceptance.

The current unsupported-construct source-location profile also passes 19/19 in
11.44 s. It includes the original seven required refusal kinds; these are public
lowerer controls, not actual positive WP proofs.

## Public unsupported results and original allocation actuals

The original seven named unsupported kinds now also pass through public
`swdb prove --adapter wp`: **7/7 in 30.27 s**. Every record reads
`not_proven` / `unsupported_construct`, retains the construct name and source
line in its hashed handler report, and has no goals, WP input or verifier
launch. The contract library contains a separate ordinary valid context, so
an invalid library entry cannot substitute for candidate refusal. These are
expected prelaunch negative controls, not actual solver jobs.

Frozen `71771f09` also completes the original new-array safe/seeded pair.
Safe has **42 ordinary and 7 smoke Valid**. Seeded `i<=n` has **40 ordinary
Valid**, ordinary invariant-preservation and memory-access timeouts, **4 smoke
Valid and 3 failed smoke** after the invalid fill. The three failed smoke
checks remain explicit negative evidence; the seed is never reported proven.
Both retain **11 RTE initialization goals**. A timeout is not a solver
counterexample. Native execution of the invalid write is deliberately excluded.

[Independent compact allocation audit](t24-original-allocation-pair-mbit10-20261015.json)
checks both record identities, all 26 report instances, physical candidate
artifacts, method/canonical-contract/setup identities, original clauses and
hints, certificate/source correspondence, and all 980 physical frozen source
files against SHA-256 and Git blobs. It reconstructs the exact terminal WP view
from the recorded lowering and current checker, retaining the original invalid
write. No audit errors remain. Its SHA-256 is
`a099dd64a325439944a0e1c81e2e42030ddde6fa6d32e558ead3516469d00ef3`.
Raw evidence stays at
`/data/yanruj/EvolveSWDB_runs/probata-resume-t24-remaining-71771f09/`.

Ticket22's accepted agreement criterion is CBMC on C plus finite native
C++/C differential comparison and C++ counterexample replay. No new formal
C++ equivalence theorem is required. The WP matrix and isolated concrete
seed witnesses do not themselves complete the current all-construct agreement
profile; the coordinator is arranging a separately pinned agreement-only
profile using the accepted native domain/oracle, with undefined runs excluded
and no new bounded-proof verdict implied. Whole-ticket acceptance remains open.

The subsequent original `new_out_of_range` command hit the test helper's
600-second outer subprocess timeout. Its matrix row contains an exception and
no accepted record; this is a harness interruption, not a semantic negative
result. The coordinator must check descendant cleanup before reusing the lane.
The committed runner now has a bounded `--public-timeout-seconds` option
(default 1800, range 600–7200), recorded in its manifest. Only the outer public
command budget changes; per-goal solver limits, RSS cap, shared lock and
acceptance checks stay intact. CLI help/argument validation is checked locally;
fresh actual out-of-range evidence remains required.

The explicit outer-budget control now exercises inherited `Seed.prove` through
the actual public-helper boundary: forcing the transport back to 600 produces
RED (`600 != 1800`), restoring forwarding produces GREEN. A second runner
control proves that `--cases new_out_of_range,new_after_delete` omits completed
safe/seeded pairs and unrelated dependencies while recording the exact selection
and budget in the source manifest. Both pass (transport/selection only, no solver).
Dependency proofs remain mandatory whenever a selected caller requires them.
The narrow retry is `--groups new_array --cases new_out_of_range,new_after_delete`
plus the explicit remaining `new_<control>` labels desired by the coordinator;
each fresh output still rebuilds the original candidate seed and checks source.
