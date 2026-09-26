# 15 — Baseline pilot and protocol freeze

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-26 (Eastern Time)
**Type:** slice
**Status:** claimed
**Blocked by:** 11, 13, 14
**Spec:** `../spec.md`

## Paired calibration implementation — 2026-09-26 10:04 ET

Local commit `6346189` implements the bounded four-cell driver, immutable request,
and independent admission reader. Independent review repairs cover descendant
ownership, resource freshness and guard duration, failed-run cleanup, full startup
timing, exact lane/runtime metadata, and reopened request/result/code evidence.
All four old controls remain retrievable, including the failed DX100 uniform A/A
control; all four new pairs must qualify even when freezing an upstream protocol.
The shared accelerator gate remains required. Reviewers report no remaining
actionable finding in these paths.

The final combined group passed **213 tests in 158.00 seconds**; see
[the interim review and retained log](../../../docs/bfs-interim-review-20260926.md).
These are local contract and subprocess checks, not empirical calibration.
The actual paired study remains unrun behind the exact code-export hold. Its
11:58 ET latest dispatch and 15:00 ET absolute end are unchanged; no retries or
automatic extension are permitted. The 10:04 ET host audit found both sockets
and the legacy lease released, with no owned job; this is availability evidence,
not a reservation. This ticket remains claimed and no protocol was published.

## Paired calibration preparation — 2026-09-26 09:34 ET

The original expired pilot and both serial native blocks remain unchanged.
The prospective [paired pilot](../../../docs/bfs-native-paired-pilot-20260926.md)
uses all four fixed implementation/graph cells, ten repetitions per ordered
source and role, one exact compiled executable per A/A cell, and seeded balanced
adjacent order. It changes collection and whole-repetition resampling only for
new evidence and a new protocol. No paired measurement or freeze has occurred.

The fixed study has 240 primary process observations, a prospective 0.10 spread
ceiling, and the unchanged 1.05/95%/2,000-resample profitability rule. Either
direction of a numerical A/A gain in any cell vetoes admission. Four passing
controls would not establish confidence-interval coverage or statistical power.
The finite 15:00 ET end, 10,800-second driver, and 10,920-second outer bound permit
no automatic retry, discarded samples, or relaxed thresholds.

Local paired collection and campaign wiring were independently reviewed. Review
reproduced acceptance of a consistently rehashed invalid parent vector; admission
now revalidates canonical graph bytes and checks each reopened parent vector.
The public negative reproduction now rejects, and seven targeted regressions
passed. The new bounded driver and publication reader are still under development
and review. Existing diagnostics stay tied to their actual original evaluations;
new paired sampling cannot promote the old failed negative control. Shared
simulator size/correctness/coverage/replay gates remain required.

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## What to build

Conduct a bounded baseline/reference pilot through the public workflow and publish the frozen protocols for the candidate coverage matrix. Select feasible workloads and defensible measurement rules using observed resource cost, correctness, attribution, and accelerator coverage. Do not use the gains of candidates awaiting assessment to choose their workloads or acceptance policy.

## Scope and spec references

Implements D10–D13 and the pilot gates supporting AC10–AC13, AC16–AC18. Use both unaccelerated starting implementations and the authors' fixed accelerated BFS as appropriate to calibration. Kronecker and uniform-random coverage, both application sources, and the separately required artifact reference cannot be removed because a smaller pilot is cheaper. Ticket 16 owns the artifact/reference comparison execution under its independently frozen protocol.

## Acceptance criteria

- [x] Before execution, publish a bounded pilot plan with permitted baseline/reference artifacts, run/attempt and wall-time limits, resource/storage budgets, explicit stop conditions, and required host/lane checks. A budget expiry preserves evidence and an incomplete outcome rather than triggering an unbounded search for a gain.
- [ ] Real baseline/reference executions calibrate correctness-case and performance-workload sizes for both graph families. Selection reasons cite cost, coverage, and observed accelerator execution, without using performance gains from candidates being assessed.
- [x] Workload records retain generator parameters/revision, normalization, realized graph properties, canonical identities, actual ordered traversal source IDs, and representation hashes. Equivalent loaded adjacency is checked across upstream and DX100 applications rather than inferred from a shared extension.
- [ ] Real pilot evidence establishes relevant accelerator full/tail and parent-update coverage, exact timed-binary correctness, BFS ROI and selected-region timing, and actual dynamic memory observations. Scalar fallback alone cannot justify accelerated coverage.
- [ ] Native timing variability and repeated identical simulation replays inform the recorded repetition/aggregation and profitability policies. Report actual completed executions, distinguish repeated graph/source pairs from different traversal sources, and do not assume deterministic timings or successful repetitions from a guest trial count.
- [ ] Freeze candidate-workload identities, vertices, native/simulated threads and targets, concrete configurations, semantic ROI definitions, correctness coverage, region/collector attribution, instrumentation treatment, repetitions/aggregation, and profitability criteria before candidate performance assessment. Initialization within a chosen complete-BFS-call ROI remains timed.
- [ ] A public query returns the frozen protocol identities, supporting pilot evidence, rejected/incomplete calibration cases, and the rule for protocol changes and required fresh comparisons. Native, simulated, diagnostic, and simulator-host quantities remain distinguishable.
- [ ] The frozen matrix preserves all eight starting-source/route/graph obligations and the minimum of one accelerator-using candidate from each starting implementation on both families. This ticket does not manufacture candidate coverage, a gain, or completion of the separately retained artifact-reference case.

## Verification

Use public requests to conduct the real bounded pilot, register its observations, freeze its protocols, and retrieve them in a fresh process. Reuse the native evaluation/profiling capabilities already available through the dependencies and the real DX100 correctness/profiling paths. Deterministic fixtures may check enforcement of missing settings or a changed protocol, but cannot select empirical sizes, establish timing variability, or replace the pilot's accelerator and memory observations. If the bounded pilot cannot establish the required settings, report the unresolved gate with retained evidence; do not mark the freeze complete.

## Dependencies and boundaries

Ticket 11 supplies workload/protocol identity and enforcement. Ticket 13 supplies exact timed-binary correctness; ticket 14 supplies simulated region/memory profiling and, through ticket 09's ancestry, the native profiling/evaluation foundation. No dependency on ticket 16 is introduced: the candidate matrix and artifact/reference work own separately frozen protocols. This slice does not generate rewrite proposals, assess candidate profitability, execute all coverage cells, or reproduce the full artifact campaign.

## Implementation progress

2026-09-25: Root owns dependent pilot preparation. The pre-execution limits and baseline-only selection rules are in `../pilot-plan.md`. Actual calibration awaits Tickets 11, 13, and 14; this ticket is not accepted or frozen by the plan.

2026-09-25 dependent implementation: `scripts/bfs_freeze_pilot.py` prepares a
reviewable native request from actual unchanged-source packages and publishes only
after revalidation of the exact reviewed evidence and the shared accelerator size
gate. Actual spread, collector overhead, selected-source attribution, raw identity,
rejected cases, and justifications remain inside frozen settings. The fixed
5-trial/1.05/95%/2,000-resample policy is not weakened automatically. Thirteen
targeted calibration-cell and missing-evidence checks passed (0.17 seconds), with
fixtures establishing guard behavior only. See `docs/bfs-pilot-freeze.md`. No
empirical protocol or Ticket15 completion is claimed by this preparation.

2026-09-25: The bounded plan preceded execution. Both fixed graph families now
have actual scale-14 and scale-18 registrations with equivalent SG32/SG64 loaded
adjacency, retained generator commands, realized vertices/isolates, and ordered
sources `[0, 1234, 7777]`. Scale-18 version 2 corrects the effective generator
symmetrization metadata while retaining version 1 and the unchanged graph bytes.
See `docs/evidence/bfs-workloads14-20260925.yaml` and
`docs/evidence/bfs-workloads18-20260925.yaml` (repository-root paths).

The first unchanged upstream native pilot stopped during workload resolution,
before compilation or timing, because registration's five-million-edge streaming
threshold was incorrectly reused as the native materialization bound. Its source,
candidate, failed evaluation, and receipt remain in `f6df56b`. Fix `9fff245` reads
validated CSR directly within the existing native two-million-vertex,
32-million-adjacency-entry, and 512 MiB bounds. The real-size regression contains
5,005,448 adjacency entries and agrees with the independent streaming parser.
This interface failure does not justify selecting scale 16, freezing a protocol,
or claiming timing evidence; the bounded retry retains the same scale-18 graphs.

2026-09-25 actual upstream native calibration: the unchanged `gapbs-bfs-do`
retry `bfs-native-pilot-20260925-upstream18-a2` completed on verified socket lane 1
(generation 392, 22:09:24–22:36:23 Eastern). Both fixed scale-18 version-2 graphs
completed fifteen independently checked primary executions: five fresh processes
for each ordered source `[0, 1234, 7777]`, with four threads. Each family also has
six independently checked diagnostic executions, eighteen valid modeled-memory
observations, and a complete sealed source/profile package. Independent
post-collection validation rehashed source, primary/diagnostic binaries, graph,
outputs, and Callgrind summaries. See repository-root
`docs/evidence/bfs-native-pilot-20260925-upstream18-a2.yaml`, imported in `c91994c`.

| Family | Primary checks | Source medians, milliseconds (0 / 1234 / 7777) | Five-sample range / median | Package |
|---|---:|---|---|---|
| Uniform random | 15/15 | 4.893488 / 5.124849 / 6.909457 | 39.06% / 42.73% / 37.63% | Complete |
| Kronecker | 15/15 | 6.369765 / 6.685496 / 4.602018 | 38.08% / 49.13% / 46.24% | Complete |

The full driver cost was 1,618.235 seconds. Primary stage intervals were
479.168 seconds (uniform) and 503.484 seconds (Kronecker), while their recorded
subprocess sums were 46.527 and 29.535 seconds. Diagnostic stage intervals were
225.240 and 239.975 seconds, with subprocess sums 65.019 and 55.389 seconds.
The receipt preserves exact timestamps and each subprocess cost; the remaining
host cost is not attributed. These costs establish bounded upstream feasibility
at scale 18, but the substantial sample spread does not relax the fixed timing
policy. The unchanged DX100 scalar pilot, accelerator coverage, repeated simulator
replays, and protocol freeze remain outstanding. No candidate gain or complete
Ticket 15 acceptance is claimed.

2026-09-25 actual DX100 scalar calibration: unchanged `dx100-bfs-scalar` run
`bfs-native-pilot-20260925-dx10018-a1` completed on socket lane 1, generation 394,
22:44:59–23:21:08 Eastern, using exact checkpoint `2eda712`. It retained the same
version-2 graphs, ordered sources, four threads, five fresh processes per source,
and original budgets. Each family passed fifteen primary checks and six separate
diagnostic checks, with eighteen valid modeled-memory rows and a complete sealed
package. Post-collection source/binary/graph/output/raw-counter hashes and package
identities passed independent validation. Evidence is
`docs/evidence/bfs-native-pilot-20260925-dx10018-a1.yaml` (repository-root path),
returned by metadata-only Git commit `8182a0a`.

| Family | Primary checks | Source medians, milliseconds (0 / 1234 / 7777) | Five-sample range / median | Package |
|---|---:|---|---|---|
| Uniform random | 15/15 | 26.276661 / 22.068036 / 22.069061 | 40.75% / 50.37% / 55.25% | Complete |
| Kronecker | 15/15 | 20.383814 / 19.607609 / 18.452187 | 30.67% / 47.54% / 52.12% | Complete |

The DX100 driver cost was 2,167.632 seconds. Primary stage intervals were
644.027 / 698.237 seconds (uniform / Kronecker), with subprocess sums
48.343 / 32.393 seconds. Diagnostic intervals were 295.319 / 311.762 seconds,
with subprocess sums 67.419 / 58.367 seconds; residual host cost remains
unattributed. Across both starting implementations, all four native baseline
cells now have complete packages: sixty primary checks and twenty-four diagnostic
checks. These establish bounded native scale-18 feasibility. Accelerator coverage,
identical simulator replays, shared workload gates, and the final protocol freeze
remain outstanding. The observed spreads do not automatically relax acceptance
thresholds, and no candidate profitability claim is made.

## Second unchanged block — 2026-09-26

The second and final permitted native block completed on lane 1 using `8c178a7`:
all 60 primary trials passed structural checks and retained matching primary
binaries, wrappers, sources, and explicit settings. All raw references were
audited. Its 1,662.222400-second driver and four evaluation records are retained
in remote-only commit `41303ed7fb02f9a5c515e2e951d27e20869c73e9`; export remains
held. They are not part of the local 185-record catalog.

The existing fixed 2,000-resample, seed-20260925 descriptive A/A calculation
gives unchanged DX100 uniform a first/second ratio of 1.176047 and a 95% interval
[1.066142, 1.448303]. Its lower bound exceeds the initial 1.05 numerical gain
threshold. No spread ceiling or empirical protocol is frozen, so this is not
a qualified gain; it shows that the current separate-block comparison can
attribute a session difference to unchanged code. Both directions, every sample,
and observed environment differences remain retained. No cause is assigned.

External Spatter overlap affects four DX100 Kronecker stage envelopes and all
fifteen upstream Kronecker trials. The uniform cells finished before that job.
No sample is removed and no third native block is scheduled. Native profitability
readiness remains unresolved; choosing a higher spread ceiling or the more
favorable block does not repair it. Simulator correctness, shared-size coverage,
identical replays, and the original 05:56:38 ET deadline remain separate gates.

## Pilot window expired — 2026-09-26 08:20 ET

The original absolute deadline, **2026-09-26 05:56:38 ET**, elapsed without the
required simulator calibration or a defensible native profitability freeze.
The original pilot is incomplete; its native trials, failures, environment
observations, and unverified simulator evidence remain retained. No third native
block or late simulator dispatch is scheduled under this window. A subsequent
pilot would require a separately recorded finite plan before execution; the
expired window is not silently renewed. This ticket remains claimed with its
empirical acceptance boxes open.

The agent usage limit prevented observation from approximately 02:04 through
08:04 ET. Scheduled heartbeat messages during that interval do not establish
that worker or host checks occurred. Recovery checks found no owned live
measurement process. See the map's 08:10 recovery entry for the actual read-only
host snapshot and the outstanding synchronization approvals.
