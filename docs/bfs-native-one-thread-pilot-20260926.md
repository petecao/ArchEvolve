# Prospective requested-one-thread native A/A calibration

Created: 2026-09-26 (Eastern Time).
Updated: 2026-09-26 (Eastern Time).
Status: implemented local client and fixed plan awaiting independent review; not an admitted
execution request, protocol freeze, or measurement result.

## Question and evidence boundary

This is one separately versioned, baseline-only configuration: does the same
fixed native A/A study meet its existing variability and negative-control gates
when its requested `OMP_NUM_THREADS` is `1`? Preserve the other seven requested
runtime inputs. Do not choose `ACTIVE`, change source or graphs, warm the kernel,
trim observations, assess a rewritten candidate, or infer a remedy before data.

[Spec D12–D13](../.scratch/bfs-rewrite-evaluation-2026-09-25/spec.md) identifies
threads as part of the comparison protocol (lines 244–248), requires a new
version for later configuration changes (line 262), and requires baseline
calibration and prospective budgets before candidate assessment (lines 362–367).
The complete-call ROI and in-call initialization remain unchanged (line 238).
The old statistical settings and all original outcomes remain immutable.

The [completed four-thread study receipt](../.scratch/bfs-rewrite-evaluation-2026-09-25/observations/native-paired-terminal-20260926.json)
retains 240 passed correctness observations and **7 of 24** spread groups above
0.10, including upstream uniform 0.1591826 and DX100 Kronecker 0.5340568. All
eight directional confidence intervals covered one. Its 7,824.3898-second
driver cost and failures remain evidence for that configuration. The earlier
serial negative-control failure and expired original pilot also remain visible
in [T15](../.scratch/bfs-rewrite-evaluation-2026-09-25/issues/15-baseline-pilot-and-protocol-freeze.md).
Neither study becomes a passing control through this plan.

Retained peaks occurred at several repetition positions, not just the first
call. Recorded environment inputs and sparse host observations do not establish
actual team size, worker placement, preemption, or a causal startup/scheduling
explanation. One requested thread is an untested configuration hypothesis.
Passing this finite study would not establish 95% interval coverage, statistical
power, a cause of the old variability, or a candidate speedup.

## Exact prospective configuration

Run ID: `bfs-native-one-thread-pilot-20260926-a1` (`RUN_ID` below).
Target/lane: `mbit10` / `mbit10-evaluation-node1`.
Ordered sources: `[0, 1234, 7777]`. Repetitions: 10. Warmups: 0.
ROI: `bfs.complete_call.v1`; one fresh process and its first complete BFS call
per observation. There are 30 adjacent pairs / 60 primary observations per cell,
120 pairs / **240 primary observations** overall, in this exact cell order:

| Cell suffix | Unchanged implementation / candidate | Registered workload |
|---|---|---|
| `dx100.uniform-random` | `dx100-bfs-scalar` / `bfs-native-pilot-20260925-dx10018-a1.baseline` | `bfs-20260925-uniform18.cd2169a5c421baf7` |
| `upstream.uniform-random` | `gapbs-bfs-do` / `bfs-native-pilot-20260925-upstream18-a2.baseline` | `bfs-20260925-uniform18.cd2169a5c421baf7` |
| `dx100.kronecker` | `dx100-bfs-scalar` / `bfs-native-pilot-20260925-dx10018-a1.baseline` | `bfs-20260925-kronecker18.48de8267ac2098d5` |
| `upstream.kronecker` | `gapbs-bfs-do` / `bfs-native-pilot-20260925-upstream18-a2.baseline` | `bfs-20260925-kronecker18.48de8267ac2098d5` |

The pair ID is `RUN_ID.CELL.pair`; members are `RUN_ID.CELL.baseline` and
`RUN_ID.CELL.candidate`. Both roles use the same existing unchanged candidate;
the candidate label is solely an A/A role. No new source snapshot or rewrite is
needed. Every new ID and dedicated output directory must be unused.

The new JSON plan must copy all four original first-record hashes and immutable
source, graph, compiler, flags, template, and primary-binary identity fields from
the [old fixed plan](../.scratch/bfs-rewrite-evaluation-2026-09-25/requests/native-paired-pilot-20260926-a1.json),
whose current file SHA-256 is
`f0be176dc9ad29843aadc17afac07439ebc79d89b2c2a6b204843d615d47cc00`.
It must separately pin all 12 completed four-thread pair/member records and their
terminal receipt. These historical identities are inputs to comparison of
configurations and retention, never new statistical observations.

Keep the scale-18, edge-factor-16 graphs, generator revision/seed, normalization,
loaded adjacency, representation hashes, compiler `/usr/bin/g++`, compiler
version, build flags, driver template, generated wrapper, and primary binary
hashes. In particular, changing the environment is not permission to change a
compile-time macro. Reopen artifacts and require fresh compilations to match the
pinned primary binaries. Invoke the declared compiler path for both version and
build; separately hash its resolved executable. A mismatch stops this attempt.

The exact version-1 [requested runtime policy](bfs-native-runtime-20260926.md) is:

```json
{"version":1,"environment":{"OMP_NUM_THREADS":"1","OMP_DYNAMIC":"FALSE","OMP_PROC_BIND":"close","OMP_PLACES":"cores","OMP_THREAD_LIMIT":null,"OMP_WAIT_POLICY":null,"GOMP_SPINCOUNT":null,"GOMP_CPU_AFFINITY":null}}
```

All four nulls mean explicitly unset, matching the completed driver's retained
snapshot, not missing observations. Construct this environment before each
public child call; new unfrozen evaluations capture it explicitly. Reopen every
new member and diagnostic record and strictly validate its complete policy and
controlled environment against this map. Do not manufacture a frozen protocol
to run calibration or retrofit this map into an old record. The declared context
thread count also becomes one; it describes the same requested-input change.

Collection remains `native_paired.v1`, balanced AB/BA with seed `20260926`:
five orders per role/source, repetitions outermost, fixed sources inside each
repetition. Retain the complete schedule/hash before collection. Reuse one exact
compiled binary for both A/A roles in each cell. Analysis remains
`paired_repetition_block_bootstrap.v1`, drawing ten complete repetition indices
per resample for both roles and all sources, with `geomean_source_median_ratio`,
2,000 resamples, seed `20260925`, confidence `0.95`, and minimum speedup `1.05`.
All 24 `(max - min) / median` spreads must be at most **0.10** and all eight
directional lower confidence limits must be at most **1.05**. Neither favorable
direction nor a subset of cells can substitute for the full control.

## Two finite sequential phases

The new window is **2026-09-26 14:00–22:00 ET**. Dispatch requires the entire
18,240-second allowance to remain; latest coordinator entry is **16:56 ET**.
The shared clock includes the recorded outer-launch start, at most five seconds
before coordinator entry, and all preflight and artifact readback. It stops only
after final accounting, persistence, and bounded cleanup. The supplied outer end
must equal that outer start plus 18,240 seconds and be no later than 22:00 ET.
Waiting, a delayed prerequisite, or an engineering repair does not move that end.

| Bound | Primary phase | Fresh diagnostic phase |
|---|---:|---:|
| Driver work, including phase preflight/readback/final accounting | 10,800 s | 7,200 s |
| Outer time including cleanup | 10,920 s | 7,320 s |
| Apparent retained bytes, including failed outputs/builds/receipts | 8 GiB | 8 GiB |
| Sampled driver plus descendant RSS | 16 GiB | 16 GiB |
| Retries / repairs / replacement IDs | 0 | 0 |

The combined bound is **18,240 seconds (5 hours 4 minutes), 16 GiB retained
bytes**, with at most 16 GiB sampled owned RSS because phases are sequential.
The 2026-09-26 implementation review assigns at most **4 GiB of that same
16 GiB total** to the new build tree. Admission requires 46 GiB free on the raw
volume (30 GiB reserve plus the full 16 GiB allowance) and 14 GiB on `/data1`
(10 GiB reserve plus the 4 GiB build subset). When they are the same filesystem,
apply the larger requirement once; do not sum duplicate free-space reservations.
Build bytes are counted in the shared and current phase totals, and their
separate 4 GiB ceiling is checked throughout. This allocation does not increase
either phase or shared storage limits.
There is no extra uncharged coordinator interval: initial coordination/preflight
belongs to the primary phase and interphase/final coordination belongs to the
diagnostic phase. If diagnostics are skipped, finalization is charged to the
primary phase. Each cleanup reserve is 120 seconds; work cannot borrow cleanup
time or unused time/storage from the other phase. Final writes/hashes are
followed by deadline/storage checks; crossing a ceiling cannot retain success.

Primary limits stay at 2,400 seconds per pair and per waiting member, 2,460
seconds per public `evaluate-pair` CLI, 180 seconds per compiler, and 60 seconds
per primary process. Reserve a complete next CLI allowance before starting each
cell. The 9,840-second sum of four CLI ceilings leaves 960 seconds within the
primary work cap for shared preflight, validation, and persistence; this is a
cap, not a guarantee that every cell fits. Complete all four planned cells even
if an interim statistical gate fails, unless a correctness/execution/resource
failure prevents completion. Never add a trial or replace a failed output.

After the entire primary grid and its retained readback, compute both-direction
controls for all four cells. **Run all four diagnostic packages only if all
primary admission gates pass.** Otherwise retain the complete unqualified
control, mark every diagnostic `not_dispatched_primary_unqualified`, finalize,
and stop. This branch is fixed before observations and cannot selectively retain
favorable cells or admit a partial calibration.

Each diagnostic uses the new cell's baseline-role evaluation, the same exact
source/runtime/graph/ROI context, one diagnostic repetition over all three
sources, automatic function/loop attribution, and modeled memory collection.
This means three guarded-region and three memory executions per cell, **24
additional diagnostic executions** overall, never primary timing observations.
Use these explicit public requests and budgets:

| Public operation per cell | Fixed requested ID / inputs | CLI ceiling |
|---|---|---:|
| `bfs-profile` | `RUN_ID.CELL.baseline.profile`; evaluation `RUN_ID.CELL.baseline`; repetitions 1; memory true; discovery/build/run/total 120/180/600/1,200 s | 1,260 s |
| `profile-package` | requested ID `RUN_ID.CELL.baseline.package`; exact primary/profile IDs and `_context(primary)` | 180 s |
| `get ACTUAL_PACKAGE_ID --chain` | Fresh retained public response for the returned immutable package | 180 s |

These 12 public commands total at most **6,480 seconds**, leaving **720 seconds**
inside the 7,200-second diagnostic work cap for preflight, compiler/collector
identity checks outside those public commands, independent admission, and final
accounting. Reserve 1,620 seconds before beginning each cell. Existing profile
requests already include compiler discovery and both diagnostic builds within
their 1,200-second total; do not charge them again or grant extra time.
Every command uses the existing public CLI with exact request, stdout, stderr,
status, elapsed, artifact hashes, and code identity retained. A package's actual
ID is content-addressed (`requested_id.v1.<hash>`); retain and validate that
returned identity, version, and requested ID rather than guessing its suffix.

The four old profile records contain 55.4–67.4 seconds of summed stage elapsed
time each; this omits other collector work and describes four-thread diagnostics
only. It supports using the existing finite profile ceilings, not a promised
one-thread runtime. A source-attribution profile may legitimately retain
`outcome: partial` with explicit coverage limits. Admission requires a complete,
current public package and valid function/loop/memory observations under the
existing package validator; it must not demand invented exhaustive attribution.

Sample deadline, output bytes, free space, verified lane, and driver/descendant
RSS at nominal five-second intervals. Retain PID/start identities across child
sessions, with a maximum 30-second telemetry gap and guard duration, including
entry-to-first and last-to-finish intervals. This is sampled enforcement, not a
kernel RSS cap or proof of an unobserved peak. Minimum free reserves remain
30 GiB on the output volume and 10 GiB on the source/build volume. Before launch,
require room for all prospective bytes in addition to those reserves; count new
builds and dispatch artifacts exactly once even across the two directories.
Historical immutable artifacts are reused read-only and remain separately named.
Use the separately reviewed `bfs_owned_rss.DescendantRSS` observation basis
`linux.proc_pid_stat.field24.v1`: PID/start/state/RSS pages come from the same
stat record, with the observed page size retained. Never replace unavailable
live RSS with zero. A client-owned reentrant lock serializes sampling with the
whole owned-descendant cleanup operation; waiting spends the existing sampling
or cleanup allowance. Retain every observed PID/start pair even across PID reuse.
Readback checks driver/pane ancestry, direct children, sampled ownership
continuity, and nonoverlapping guard intervals against their measured duration.
Between expensive stages, retain the existing capacity
estimator's raw node/global inputs and require estimated node availability of
20 GiB and global availability of 24 GiB. Those margins for the 16 GiB sampled
ceiling are prospective headroom assumptions, not guaranteed allocations; do not
reapply admission thresholds against memory already allocated to a live child.

Enter only through the current verified socket-lane helper and a named tmux
session. Use one lane sequentially, retain both socket/legacy lease observations
and actual load, and repeat capacity/free-space admission before expensive work.
Other legitimate lane users are recorded, not disrupted. Owned earlier
measurement drivers must be terminal and have their cleanup audits checked
before launch; the actual pins must be supplied at admission. Use bounded owned
descendant cleanup and a terminal audit of sampled/ancestor PID-start identities;
leader exit alone is insufficient. Preserve the exact zero-RSS terminal launcher
zombie exception already documented for host audits, never arbitrary workers.
No raw output or source is copied to the Mac.

## Required implementation and evidence seams

The accepted design is implemented in these new files:

- `.scratch/bfs-rewrite-evaluation-2026-09-25/requests/native-one-thread-pilot-20260926-a1.json`:
  exact configuration, IDs, historical hashes, conditional phase policy,
  bounds/window, and the independently accepted runtime/code identity.
- `scripts/bfs_native_one_thread_pilot.py` and
  `tests/test_bfs_native_one_thread_pilot.py`: a small dedicated client and
  admission reader over public `evaluate-pair`, `bfs-profile`, `profile-package`,
  and `get`; no evaluator backend or edits to the measured old clients.

Reuse `bfs_native_pair.schedule`, its full raw/graph/parent-vector receipt
validator, the existing bootstrap/negative-control functions, compiler identity
checking, `bfs_process` bounded stages, owned-descendant resource sampling, and
current package admission primitives. Keep fixed study constants local to the
new client. Do not monkeypatch old module constants or pass altered historical
records to its four-thread validator. Its new result validator explicitly
permits only the declared thread/runtime delta, preserving every other source,
target, ROI, graph, compiler, wrapper, and binary identity. Retain exact hashes
of the new client and every imported runtime primitive actually used.

The existing publisher has intentional four-thread/five-trial historical
assumptions in `bfs_freeze_pilot.prepare`, and `bfs_paired_calibration.qualify`
selects the old fixed driver. A future explicit, separately named one-thread
calibration selector must use the new reader and all four fresh diagnostic
packages. It must retain and revalidate all old serial-control packets and the
completed four-thread failed study in distinct historical sections, then use
only the new grid as the new configuration's statistical input. New selected
packages must be bound to their exact new 30-observation baseline primaries;
old four-thread diagnostics cannot support a one-thread primary by relabeling.
Preserve shared accelerator feasibility/correctness/coverage and all simulator,
reference, and controlled-comparison gates unchanged. Preparation may remain
unpublishable; this client neither calls `freeze-protocol` nor resolves T15.

`bfs_native_campaign.validate_inputs` already checks package threads and source
context against frozen settings; the separately reviewed runtime repair also
requires the primary's strict runtime policy to equal the frozen policy before
provider work. Its evaluation requests already use `settings.threads`, and
profiling replays the primary policy. Current fresh-submit behavior additionally
requires the proposal to name the first assessment package, while
`validate_existing_candidate` correctly requires the exact original proposal.
Consequently, existing T18/T19 candidates originating from four-thread packages
cannot currently satisfy a one-thread assessment through those two interfaces.

After calibration, a **separate additive existing-candidate change** may
distinguish the immutable origin profile package from the two fresh frozen
assessment packages. It must retain the exact original proposal, source,
payload/interpretation, diff-to-artifact replay, provider receipt, already-used
provider time, remaining repair budget, and creation chain. It must separately
bind the new protocol and assessment packages, unchanged baseline source and
manifests, region/semantic protections, and applicable capability requirements.
An explicit transition receipt enumerates the requested threads/runtime change
from origin to assessment; unsupported semantic or capability requirements fail
closed. Both fresh assessment packages must still match every frozen runtime,
graph, source, and ROI requirement. Neither the origin package nor original
proposal is relabeled, resubmitted, or passed off as one-thread evidence.

That later change needs focused fresh-submit compatibility and adversarial
origin/assessment/source/runtime/budget tests. It must not bypass the runtime
guard now being reviewed, infer that prior correctness holds on the new target,
or introduce provider calls merely to rebind context. No candidate assessment,
proposal mutation, new provider allowance, or campaign implementation belongs to
this baseline plan.

Required focused checks before code admission cover exact thread-only changes,
strict eight-input replay (including null removal), all-four/both-direction
gates, immutable prior failures, wrong old-package context, altered/missing
runtime or raw records, full next-stage allowance, both phase/overall clocks,
final-write accounting, stale telemetry, no overwrite/retry, and detached owned
descendant cleanup. Fixtures are contract tests, not calibration evidence.

The runtime-policy repair must finish independent review first. Final source
commit, imported historical record hashes, host tool/collector identities,
terminal prerequisite audit hashes, storage placement, and exact executable
command remain explicit admission inputs until verified. Unknown values keep
the plan unadmitted; they cannot be filled from assumptions or an expired pin.
No launch, export, experiment, or protocol publication is authorized by this
document's creation.

## Concrete launch inputs for later admission

Before launch, retain a required-new admission JSON with `code_commit` equal to
the independently reviewed full commit, `plan_sha256` equal to the client's
canonical plan digest, aware `prepared_at`, `coverage_commit` equal to the fixed
historical coverage commit in the plan, and `proofs` equal to the plan's four
exact path/hash references. The coverage prerequisite admits only terminal
cleanup and retains its failed work outcome. Compute the admission file hash;
do not substitute an earlier code pin or mutable terminal file.

Inside the verified node1 helper, the future wrapper supplies the actual pane
PID/start ticks and prospective outer timestamps. Its bounded command shape is:

```sh
timeout --signal=TERM --kill-after=120s 18120s \
  env -u PYTHONPATH -u PYTHONHOME -u PYTHONSTARTUP -u PYTHONUSERBASE \
    PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
  python3 scripts/bfs_native_one_thread_pilot.py \
    --expected-commit REVIEWED_FULL_COMMIT \
    --admission ADMISSION_JSON --admission-sha256 ADMISSION_SHA256 \
    --runs-dir /data/yanruj/EvolveSWDB_runs/bfs-native-one-thread-pilot-20260926-a1 \
    --outer-start ACTUAL_AWARE_START --outer-end EXACT_START_PLUS_18240_SECONDS \
    --pane-pid ACTUAL_PANE_PID --pane-start-ticks ACTUAL_PANE_START_TICKS
```

These placeholders must be observed and pinned before dispatch. The client
retains the same controlled Python inputs for public children and rejects
untracked or ignored runtime files outside interpreter cache directories.
The complete `scripts`, `swdb`, `schemas`, `vocab`, and `tools/bfs_native` source
inventory, plan, and Python executable are hashed and rechecked. The reader
also reopens every cell's declared compiler path, resolved executable, hash,
and declared-path version output; a resealed unrelated compiler cannot pass.
An external final audit still establishes driver/launcher terminal state, lane
release, and the complete owned-process union. This client does not attest its
own disappearance, and it adds no intermediate primary-phase admission for
another workflow.

## Phase-accounting correction before dispatch — 2026-09-26 14:54 ET

Final readback reproduced a monitor/phase-transition race: a storage count read
before the switch could be compared with the newer diagnostic baseline and
falsely fail the nonnegative phase-byte guard. The regression failed with
`phase storage allowance exhausted` before the correction. A shared reentrant
lock now keeps each accounting snapshot and the phase/baseline transition
consistent. Its wait and work remain inside the existing 30-second guard and
remaining phase allowance. Final primary reads are charged before diagnostics
begins; no phase, storage, statistical, or launch limit changes.

The complete client suite now passes 69 tests with two Linux-only skips; an
independent reviewer repeated the race and phase-budget cases. The earlier
`d484afb2` export was never dispatched as a pilot. Its superseding exact code
pin and actual Linux cleanup proof remain required before the single attempt.
