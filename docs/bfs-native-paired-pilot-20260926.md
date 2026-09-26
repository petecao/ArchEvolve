# Prospective native paired A/A pilot

Created: 2026-09-26 (Eastern Time).
Updated: 2026-09-26 (Eastern Time).
Status: prospective execution plan with an implemented, independently reviewed
driver and admission reader. Coordinator checks and exact code synchronization
remain required before dispatch. This document is not measurement evidence.

This finite plan tests whether adjacent, balanced unchanged-code pairs provide
usable native observations under the existing profitability rule. It implements
the prospective protocol-change requirement in [spec D13](../.scratch/bfs-rewrite-evaluation-2026-09-25/spec.md)
and the [paired collection contract](bfs-native-paired.md). It changes native
collection from separate serial blocks to paired collection, increases repetitions
from five to ten, and changes resampling to whole repetition blocks. Those changes
apply only to new records and a new protocol version. They do not reinterpret,
exclude, or overwrite any prior observation or comparison.

The [original pilot](../.scratch/bfs-rewrite-evaluation-2026-09-25/pilot-plan.md)
expired at **2026-09-26 05:56:38 ET**. It remains incomplete. This separately
bounded prospective plan does not restart that clock or grant more simulator
attempts. The retained separate-block DX100 uniform A/A result, ratio 1.176047
and 95% interval [1.066142, 1.448303], remains a failed negative control for that
collection method. Its high spreads, other cells, host interference, failures,
and unavailable historical metadata remain visible. No cause of the difference
has been established; pairing is a design change to evaluate, not a demonstrated
cure. See [the retained outcome](../.scratch/bfs-rewrite-evaluation-2026-09-25/issues/15-baseline-pilot-and-protocol-freeze.md)
and [the earlier review](bfs-native-calibration-review-20260925.md).

## Fixed observations and identities

Run ID: `bfs-native-paired-pilot-20260926-a1`.
Machine and lane: `mbit10`, `mbit10-evaluation-node1`.
Use the four scale-18, edge-factor-16 cells in this exact order, with the existing
registered graphs and unchanged baseline candidate artifacts:

| Order | Cell suffix | Implementation | Existing candidate |
|---:|---|---|---|
| 1 | `dx100.uniform-random` | `dx100-bfs-scalar` | `bfs-native-pilot-20260925-dx10018-a1.baseline` |
| 2 | `upstream.uniform-random` | `gapbs-bfs-do` | `bfs-native-pilot-20260925-upstream18-a2.baseline` |
| 3 | `dx100.kronecker` | `dx100-bfs-scalar` | `bfs-native-pilot-20260925-dx10018-a1.baseline` |
| 4 | `upstream.kronecker` | `gapbs-bfs-do` | `bfs-native-pilot-20260925-upstream18-a2.baseline` |

The pair ID is `RUN_ID.CELL_SUFFIX.pair`; its two evaluation IDs are
`RUN_ID.CELL_SUFFIX.baseline` and `RUN_ID.CELL_SUFFIX.candidate`. Both evaluation
roles name the same existing candidate. A/A is a negative control: the role named
candidate is not rewritten code. Preflight rejects any existing new ID or
nonempty dedicated run directory; invocation cannot resume, overwrite, or choose
a replacement ID after inspecting results.

The new machine-readable request plan must retain every original cell identity
field from [the fixed second-block request](../.scratch/bfs-rewrite-evaluation-2026-09-25/requests/native-repeatability-20260926-a1.json):
first evaluation and its SHA-256, implementation, candidate, registered workload,
canonical graph SHA-256, source snapshot SHA-256, primary binary SHA-256, resolved
compiler request, flags, and trusted driver-template SHA-256. Its proposed path is
`.scratch/bfs-rewrite-evaluation-2026-09-25/requests/native-paired-pilot-20260926-a1.json`.
It adds the pair/member IDs, collection/analysis, bounds, deadline, and explicit
`maximum_relative_spread: 0.10`; it does not modify the old request. The coordinator
reviews its exact bytes and the final code checkpoint before collection, and the
driver retains both file and canonical content hashes.

Use ordered sources `[0, 1234, 7777]`, four configured native threads, zero untimed
warmups, and exactly ten repetitions for each source and role. Keep the complete
first BFS call ROI, `bfs.complete_call.v1`, including initialization and the source's
existing in-ROI work. Keep the existing native build flags and functional DX100
scalar behavior. No source changes, new graph generation, scale fallback, warmed
calls, primary profiling, or candidate assessment belongs to this plan.

Each cell has 30 adjacent A/A pairs and 60 fresh processes. All four cells total
120 pairs and **240 primary process observations**. The collector prepares both
roles before the first trial and reuses one exact compiled executable for both
roles in that cell. Compilation is outside the measured ROI; correctness checking
is also outside it. Recompilation for another cell must preserve the pinned primary
binary hash. A new build/hash or compiler version mismatch stops the plan rather
than silently becoming another experimental condition.

Before any trial, revalidate all four first records, candidate/source manifests,
registered graph representations and loaded adjacency, retained build artifacts,
and actual compiler version. Record the current resolved compiler executable and
its hash, evaluator/driver/verifier code hashes, generated wrapper and binary hashes,
requested OpenMP settings, inherited runtime knobs, machine identity, lane receipt,
and host load. Recheck compiler/template identities before and after each cell.
The earlier first block did not retain compiler-executable hashes or all inherited
runtime settings; those historical values remain unknown. Fresh observations must
not imply that the old environment was completely identical.

## Collection and analysis fixed before execution

Collection is `native_paired.v1` with `order_seed: 20260926`. For each source, use
the collector's seeded balanced schedule: exactly five A-then-A role orders with
baseline first and five with candidate first. Traverse repetitions first, then
the same three source positions; execute the two members of each pair adjacently.
Do not regroup all baseline trials or reorder cells based on interim results.
Retain the complete prospective schedule and its hash before primary collection.

Analysis is `paired_repetition_block_bootstrap.v1`, with the unchanged point
estimator `geomean_source_median_ratio`. Each of the 2,000 resamples draws ten whole
repetition indices with replacement, using the same indices for both roles and
all three sources in a cell. Use bootstrap seed **20260925**, confidence **0.95**,
and minimum speedup **1.05**. Reversing labels uses the same declared procedure;
retain both computed directional results rather than choosing one. Cells retain
separate results; a combined number cannot conceal a failing cell.

The fixed prospective usability ceiling is **0.10** for each role/source group's
`(maximum - minimum) / median`. This is a conservative operating requirement,
selected before the new results and kept close to the 5% claim scale; it is not an
empirically established coverage guarantee. The old pilot had no frozen empirical
spread ceiling and its observed high spreads do not qualify under this new ceiling.
The fixture's similarly named setting is not empirical justification. Record all
24 new role/source spreads and the actual samples. Never increase the ceiling,
trim samples, subtract drift, or discard an overlapping-job interval to obtain
admission. The observed new baseline must actually meet the declared requirement
before its use in a freeze can be justified.

The admission result must satisfy every condition below:

1. All four planned cells and every scheduled observation are complete, real
   measured evidence. Partial grids, missing files, fixture evidence, substituted
   cells, changed identities, cross-pair samples, or failed structural checks
   leave the plan unqualified. Independently reopen and hash raw outputs and the
   registered graph, and verify every timed parent vector against its adjacency.
2. Exact A/A source, build, binary, workload, source order, requested threads,
   ROI, lane, timing/check bindings, schedule, and receipt identities are valid.
   Preserve distinct process outputs and observed environment differences.
3. All 24 role/source spreads are at most 0.10. Missing or invalid durations
   fail admission instead of yielding a neutral speedup.
4. Compute both label directions in each of the four cells. If **either direction
   in any cell has a 95% lower bound strictly above 1.05**, reject native calibration
   independently of the spread gate. Thus all eight directional checks must avoid
   a numerical gain. An apparent A/A gain is a failed negative control, never an
   improvement or a reason to choose the opposite direction.

Passing these checks establishes only completion of this finite negative control
and no observed spurious gain under its declared test. Four cells do not establish
95% interval coverage, statistical power, a controlled family-wise error rate, or
reliable detection of a true 5% improvement. It also does not identify the cause of
the old result or prove that adjacent observations are independent. Preserve
time order and host observations for that limitation. Any further count, seed,
order, estimator, workload, or threshold change needs a separately reviewed
prospective version and fresh evidence; this plan permits no adaptive rerun.

## Finite time and resource bounds

The hard end is **2026-09-26 15:00 ET**, including cleanup. Require room for the
entire 10,920-second outer bound before dispatch: the latest start is therefore
**2026-09-26 11:58 ET**. The driver measures its own monotonic elapsed time from
entry, including preflight, builds, collection, checks, and persistence; its
deadline is the earlier of start plus 10,800 seconds or the absolute end minus
120 seconds. Waiting for a lease or an engineering fix does not move the absolute
end. Do not launch a cell without room for its full 2,460-second CLI allowance.

| Bound | Fixed value |
|---|---:|
| Driver elapsed time | 10,800 s |
| Outer elapsed time, including final cleanup | 10,920 s |
| One complete pair request, and each member including waiting | 2,400 s |
| One public `evaluate-pair` command with cleanup allowance | 2,460 s |
| One compiler invocation / one primary process | 180 s / 60 s |
| Retries, repairs, replacement blocks | 0 |
| Threads / primary observations | 4 / 240 |
| Dedicated batch apparent raw bytes | 8 GiB (8,589,934,592 bytes) |
| Sampled aggregate driver-and-descendant RSS | 16 GiB (17,179,869,184 bytes) |
| Maximum resource telemetry gap / guard duration | 30 s / 30 s |
| Minimum free output-volume / source-build-volume space | 30 GiB / 10 GiB |

At 2026-09-26 09:30 ET, 5 hours 30 minutes remained until the proposed absolute
end, leaving 2 hours 28 minutes for implementation/review/dispatch before the
latest start. The retained prior 60-trial driver took 1,662.222400 seconds; a
linear 240-trial extrapolation is about 6,649 seconds (111 minutes). This is a
planning estimate, not a runtime promise: pairing, additional checking, metadata
growth, and shared-host load can change cost. The 180-minute driver cap gives
bounded headroom; if it proves insufficient, retain an incomplete outcome.

Enter only through the current verified `socket_lane.sh`, in a named tmux session
with the finite outer timeout. Recheck both socket leases and the legacy lease,
current load, available memory, affinity, storage, and exact repository revision.
Avoid an owned competing native job during collection when feasible; do not claim
control over other users or the other socket. Record interference without deleting
affected samples. Do not change governor, turbo, caches, or other users' processes.

Sources/builds stay under `/data1/yanruj`; choose the permitted raw-output volume
from fresh space checks. The dedicated batch directory starts empty, and outer
helper receipts use a separate sibling directory. Sample apparent output bytes,
free-space reserves, lane validity, deadline, and aggregate RSS at nominal five
second intervals, plus guard overhead. RSS must cover the driver and its live
descendants by parentage, including evaluator/compiler processes that create their
own sessions; a process-group-only sum is insufficient. The 16 GiB ceiling is a
prospective headroom choice for two prepared collectors' graph/checker objects
and driver preflight, not an observed memory requirement. Retain sampling scope,
sampled peak, failures, and collection times. This is a sampled guard, not a kernel
hard limit or a guarantee of the true peak between samples. Unavailable resource
telemetry fails closed. A violation terminates owned stages through the bounded
cleanup path, retains completed/partial evidence, and starts no later cell. It
does not kill unrelated host jobs or delete raw artifacts.

The prospective `resource_max_gap_seconds: 30` bound applies from driver start to
the first sample, between every pair of samples, from the final sample to driver
finish, and to each resource guard's duration. Retain and independently check all
these intervals, including sampled maximum gap and guard duration. Nominal sampling
remains five seconds; the 30-second limit bounds telemetry gaps and checking cost,
without turning sampled RSS or storage observations into a hard resource cap.

## Implementation and publication gates

The paired collector and [native freeze publisher](bfs-pilot-freeze.md) retain
separate serial and paired admission paths. The bounded public-workflow driver
`scripts/bfs_native_paired_pilot.py` and its immutable request plan implement this
study. They preflight all four cells, invoke public `evaluate-pair`, enforce the
limits above, retain exact command requests/results and hashes, and validate each
completed result before proceeding. The receipt role is
`paired_unchanged_native_calibration`; it neither profiles, assesses a candidate,
nor freezes a protocol. Local contract tests must cover changed plan/IDs, expired
or insufficient deadlines, resources, interrupted descendants, incorrect A/A reuse,
partial receipts, and retained public results. Fixture tests prove those contracts,
not empirical calibration.

The separate admission reader, `scripts/bfs_paired_calibration.py`, binds the exact new
plan, code, driver receipt, all four pair records, eight evaluations, full samples,
raw checks, environment/build identities, all spreads, and all eight directional
results. It reconstructs the same review from current artifacts immediately
before public `freeze-protocol`, rejecting changed or unavailable evidence. A
protocol for one implementation still retains and gates on the entire predeclared
four-cell negative control; no favorable subset substitutes for it. Its native
sampling freezes ten repetitions, zero warmups, the named paired collection and
analysis, the recorded seed, and the unchanged profitability settings with the
explicit 0.10 spread ceiling. Use a new protocol ID/version, with `supersedes`
when replacing an existing frozen identity; retain predecessors unchanged.

Keep source-specific earlier profile packages and diagnostics bound to their
original evaluations. Do not copy their diagnostic checks into new timed results
or recompute old overhead as though it accompanied new primary execution. The
publisher may retain them as separately identified supporting source/region/memory
evidence, subject to the existing artifact admission checks. The old failed native
control remains historical failed evidence, not new paired input or a removed
failure. Preserve separate simulator size, exact-binary correctness, accelerated
full/tail/competing-parent coverage, replay, artifact-reference, and matched-control
gates. A passing native A/A plan alone does not publish a protocol, establish an
empirical gain, or complete Tickets 15 or 21.

No remote measurement, lease acquisition, raw transfer, provider invocation, or
protocol publication is performed by preparing this document. The coordinator
reviews the concrete driver, request, admission reader, tests, and exact code
checkpoint before a separately authorized dispatch within the remaining window.
