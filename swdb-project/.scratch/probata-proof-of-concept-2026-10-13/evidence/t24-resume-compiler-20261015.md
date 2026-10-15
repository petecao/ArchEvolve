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
