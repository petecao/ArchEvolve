# Interim BFS implementation review

Updated: 2026-09-26 (Eastern Time).

This is an interim review and repair receipt. It does not replace the required
independent review after all implementation and empirical acceptance tasks finish.
Two independent reviewers inspected the three-dot diff from
`1bdb7d4037916dea782c40239a6415b61a47f3c1` to `8175ca1`, using the
[BFS spec](../.scratch/bfs-rewrite-evaluation-2026-09-25/spec.md), repository
rules, domain documents, and ADRs. They reproduced the findings locally without
provider calls or lab-host execution. Their review covered selected correctness
and durable-workflow boundaries; it was not exhaustive acceptance certification.

## Standards

**P2: YAML-only request values broke durable retrieval.** The public request
readers accepted binary tags and other values that could be written as YAML
but could not be indexed or returned as JSON. A public evaluation with a binary
value reproduced a `TypeError` after persistence. This violates ADR 0002's
authoritative-record/generated-index contract and the promised retrievable failed
outcomes. The repair shares one message parser, retains the original invalid text
and reason, and rejects incompatible metadata before writing. Follow-up review
also reproduced YAML-constructor exceptions and colliding numeric/string object
keys; both are now guarded. Generated public source-position maps use string
keys consistently. Existing records are not rewritten.

**P2: duplicated process cleanup missed descendants.** The campaign supervisor
sent TERM but sent KILL only if the group leader survived. A leader that exited
while a descendant ignored TERM left the owned child running. The other supervisor
already handled this case correctly. This was a concrete consequence of the
Duplicated Code heuristic, rather than a separate written repository rule.
Both paths now share `stop_group`; campaign interruption handling protects cleanup
from repeated signals and retains failure/log receipts. An actual local
TERM-resistant descendant regression verifies cleanup.

Standards: two findings; highest severity P2. Repairs have focused passing tests;
integrated validation remains separately recorded below.

## Spec

**P1: a candidate could change the graph used as correctness truth.** The old
DX100 complete-call wrapper passed the candidate's mutable `Graph` to the protected
`BFSVerifier`. A compiled candidate replaced the path 0–1–2 with self-loops and
returned `[0,-1,-1]`; the old checker printed PASS. This violates the spec's
independent structural correctness and protected success criteria (lines 81,
217–219). The new `dx100.complete_call.v2` wrapper captures registered original
serialized adjacency in independent arrays before checkpoint/ROI and checks the
exact returned parent buffer afterward. It accepts valid alternative trees,
including candidates that mutate their own graph. The extra allocation is bounded
at 2 GiB and explicitly part of the new instrumentation treatment. Tests use actual
compiled BFS source and stub m5 events, not simulator acceptance evidence.

**P2: native region comparisons could not consume actual native profiles.**
The comparator required inline primary region timings, while `bfs-profile` stores
separate diagnostic-binary observations in a region profile and sealed package.
This prevented the spec's selected-region/BFS comparison (lines 96, 236). The
additive `native_diagnostic_profile.v1` treatment binds exact packages, compiler,
collector, source, graph, trial grid, and post-freeze raw observations. It reports
thread CPU ratios separately from primary wall timing and never grants a gain
from diagnostic timing. Fixtures use the actual retained 24-region layout with
explicitly synthetic counters. Simulated diagnostics now also require their own
actual source/repetition identity rather than relabeled primary cells.

Spec: two findings; highest severity P1. No additional scope-creep finding was
reported. Known missing empirical acceptance remains open in Tickets 13–21.

## Integration follow-up

Cross-review identified two propagation obligations for the new wrapper adapter:
the bounded repair path must accept genuine v2 compiler failures, and downstream
qualification must reject historical unsafe complete-call wrappers even when
they used the v1 checker. Historical records remain retrievable. These repairs
are implemented: the public repair path passes, and three public qualification
regressions verify legacy retrieval, aggregate rejection, and unchanged native/
author treatment. Independent cross-review found no additional reproduced
original-graph or native-region defect.

Focused results already completed:

| Boundary | Evidence | Scope |
|---|---|---|
| Invalid messages and persistence | 40 tests passed, 16.53 s | Public durable failure/retrieval plus pre-write rejection |
| Existing proposal/native workflows | 31 passed, 376.09 s | Positive behavior after shared parser change |
| Candidate/author/v2 witness | 114 passed; separate oracle/witness group 87 passed | Explicit local fixtures and compiled oracle semantics |
| Legacy execution rejection | 2 passed | Unsafe wrapper rejected before simulation |
| Native region/campaign integration | 31 passed, 68.66 s | Actual profile representation with synthetic counters |
| Simulated region comparison | 12 passed, 70.83 s | Explicit diagnostic trial identity |
| Supervisor/admission/repeatability | 51 passed, 2.68 s | Includes real local descendant cleanup |

These groups overlap and must not be summed into a unique-test total. Full-suite
and final integrated results will be recorded when finished. A clean full-suite
run at `6a1bd7d` finished with **951 passed, 3 skipped in 2031.80 s**. Its log is
`/private/tmp/bfs-full-suite-20260926-0116-6a1bd7d.log`. This verifies that pinned
checkpoint; it predates the oracle, region, persistence, and cleanup repairs in
this receipt and is not their full-suite verification.

The first combined comparison run retained **90 passed, 3 failed** in 279.10 s
at `/private/tmp/bfs-comparison-integrated-20260926.log`. The three failures
were simulated-region fixtures that lacked the newly required independent-graph
treatment and therefore rejected before their intended positive/collector/raw
counter checks. The fixtures now identify the new treatment; the production
qualification gate is unchanged. The corrected 12-case module passed in 66.74 s
(tool session `30486`, chunk `943cea`). An intermediate assertion-only run
retained 11 passes and one failure (session `34291`, chunk `099fa1`): the invalid
cell correctly failed during package assembly before comparison. The regression
now asserts both that coverage reason and the subsequent incomplete-package
rejection. All failures remain retained. The other 81 cases from the combined
run passed; this is not a claim that one uninterrupted combined rerun passed.

Additional integration checks passed: 12 bounded-rewrite cases including the
public v2 compiler-repair path, both adapter eligibility cases, three public
legacy-oracle qualification cases, 31 aggregation/v2 cases, and seven positive
package/build/profile persistence cases. Catalog validation reports 185 valid
records. Both prospective author-policy request files validate after their
parser identity refresh; neither was published or executed.

## Second independent review and repairs — 2026-09-26

Separate Standards and Spec reviewers inspected the fixed checkpoint `0467c72`
against the same starting commit, spec, tickets, and repository rules. This was
a risk-focused review of the current implementation, not a line-by-line audit of
every generated record or a replacement for the final post-acceptance review.

| Axis | Finding | Repair and evidence |
|---|---|---|
| Standards, P2 | DX100 and build cleanup skipped surviving descendants after the session leader exited | Shared `swdb.processes.stop_group` always finishes the owned group, including after the leader is reaped. All migrated provider and driver callers clean up on success, failure, timeout, and interruption. |
| Spec, P2 | `bfs-hotspots` indexed native CPU fields for valid simulated profiles and raised `KeyError` | Select the profile's actual native or simulated metric, label inclusive logging-only intervals, and leave unentered scopes unranked. Five focused public tests passed; independent replay of the original simulated fixture succeeds with fixture evidence and no gain claim. |
| Spec, P2 | An explicit executable-backend requirement was bypassed when required operations were omitted or empty | Apply readiness checks independently of operation-list length. Seventeen public tests passed in 319.16 s; independent review confirmed schema rejection of non-Boolean flags and preservation of default source-only behavior. |

Cleanup peer review reproduced an additional normal-completion leak in provider
and stage callers after the initial helper repair. Cleanup now runs in `finally`
for every outcome. The final focused group passed **34 tests in 68.19 s**,
including real local TERM-resistant children, public build/provider paths, and
durable stage receipts. The positive natural-language provider-fixture workflow
passed separately in **20.72 s**. These are local subprocess and contract tests;
no external provider or simulator was invoked. The final cleanup log is
`/private/tmp/bfs-shared-cleanup-final-20260926.log`, SHA-256
`90d967d735c0cfeeeb8fa000f9d97acea830b58f31a19bf9627aef0b8392a83c`.
The positive fixture log is `/private/tmp/bfs-provider-positive-final-20260926.log`,
SHA-256 `906d1a0ad3ddb112a7b869c052d6f55b37e3bd5116e84c6bcf3a590e09afb1b4`.
Independent cleanup cross-review found no remaining actionable issue and reran
all 16 descendant-process regressions successfully in 53.26 s. Those cases
overlap the 34-test group and are not additional unique tests. The standalone
build helper also imports successfully when invoked from outside the repository.

The clean isolated full suite at **`0467c72` passed 1,097 tests with 3 skips in
2071.53 s**. Its log is `/private/tmp/bfs-full-suite-20260926-0156-0467c72.log`,
SHA-256 `466b0e6f8091c79d3b2b75cb66c51e295b5fc61afdcf9f79b625aa1c29657d64`.
That run predates the three repairs in this section; their focused checks must
not be presented as a full-suite run of a later checkpoint. Actual acceptance
and the required final independent review remain incomplete.

## Parser and paired-collection review — 2026-09-26 09:44 ET

The actual a1 v2 run failed because the pinned simulator emits unconditional
CPU progress lines into its redirected debug trace. Commit `b3a2cbe` retains
those observations under a strict grammar without allowing them to supply exit
evidence. Independent review found and closed a metadata-only progress/exit tick
ordering gap. The combined parser/adapter/probe group passed **121 tests in
57.30 seconds**, retained at
`/private/tmp/bfs-progress-parser-corrective-20260926.log`. The actual failed run
stays failed; its corrected a2 follow-up was not dispatched before its cutoff.

Commit `721fa72` adds paired native collection and whole-repetition analysis.
Independent review reproduced admission of a consistently rehashed raw output
whose parent vector was empty. Admission now revalidates registered graph bytes
and reruns structural verification on every reopened parent vector. The original
public reproduction rejects, and the combined paired/campaign suite passed
**30 tests in 136.68 seconds**, retained at
`/private/tmp/bfs-paired-core-final-20260926.log`. The existing clean managed
validation checkout is running the full suite at this exact commit; completion
is not yet claimed. Its log is
`/private/tmp/bfs-full-suite-20260926-0939-721fa72.log`.

The separately uncommitted pilot reader preserves all four historical controls,
including the known false gain when preparing an upstream protocol, and retains
the shared accelerator gate. Its history/gate tests passed **22 cases in
4.46 seconds**. A root integration of those cases and five numerical-control
cases passed **27 tests in 4.65 seconds**, retained at
`/private/tmp/bfs-paired-publisher-focused-20260926.log`. These overlap earlier
groups; they are synthetic contract fixtures, not empirical calibration.

The new finite driver and its resource/receipt admission remain under review.
Review has identified sampled-monitoring gaps, process ownership checks, and a
signal race during failed-run persistence. No native paired study, empirical
freeze, final acceptance cell, or final post-acceptance review is claimed.

## Paired pilot admission repairs — 2026-09-26 10:03 ET

Independent driver and publisher reviews are complete for the prospective paired
study. Repairs cover descendant ownership, sampled-resource freshness and guard
duration, cleanup signal races, full startup timing, exact lane evidence,
inherited runtime metadata, and request/result/runtime artifact bindings. The
publisher requires all four historical and prospective cells; selecting an
upstream protocol cannot hide the earlier DX100 failed control. The shared
accelerator gates remain required. Reviewers reported no remaining actionable
finding in these paths after the repairs. This is interim review, not the final
post-acceptance Standards/Spec review of the whole deliverable.

The final combined driver, admission, history, numerical-control, freeze, and
region-comparison group passed **213 tests in 158.00 seconds**. Its log is
`/private/tmp/bfs-paired-pilot-final-20260926.log`, SHA-256
`a33720198706f1ab61e18750c7110c3d360d42d79b151a105c38c32285a61721`.
These are local contract and subprocess checks; no new mbit10 measurement or
provider invocation occurred. Current catalog validation reports 186 valid
records.

The full suite at pinned `721fa72` is still running and has one failure so far:
an old campaign test mocked protocol validation while omitting the newly read
mandatory sampling field. The failure was reproduced separately and retained in
`/private/tmp/bfs-paired-region-regression-20260926.log`. The fixture now explicitly
covers serial and paired modes and verifies that paired primary collection occurs
before diagnostic collection. Both cases passed separately and are included in
the 213-case group. The original full-suite run is preserved unchanged; it is not
reported as green or as verification of the later driver checkpoint.

## Full-suite result and documentation repair — 2026-09-26 10:20 ET

The isolated run at **`721fa72` finished with 1,164 passed, 3 failed, and
3 skipped in 2,474.56 seconds**. Its unchanged log is
`/private/tmp/bfs-full-suite-20260926-0939-721fa72.log`, SHA-256
`a2eac04e206f2a11fc1054f56ba7db25ef35ead5e3dfbb0306370ca910f09185`.
The three failures are exactly the campaign fixture described above and two
format-document checks. No other test failure occurred.

The document checks identified missing explicit definitions for six paired
receipt fields. [The paired contract](bfs-native-paired.md) now documents the
request/schedule/receipt digests, observations, preparation timestamp, and the
remaining paired fields, including incomplete outcomes. Its calibration link
also reflects the implemented separate admission reader. Independent review
confirmed the descriptions against the schema and collector. All four format
checks pass in 0.03 seconds; the original two-failure reproduction remains in
`/private/tmp/bfs-format-paired-regression-20260926.log`, while the passing log is
`/private/tmp/bfs-format-paired-corrected-20260926.log`, SHA-256
`988344a7589dd35ded61b8e784dcd5bc43cb64ba0f19a2bda1a7ec44b380abcb`.

The fixture correction and document checks are targeted post-failure evidence,
not a relabeled full-suite pass at a newer commit. The new explicit campaign
candidate-reuse path is under separate implementation/review and is not covered
by the pinned full run. No new remote evaluation occurred.
