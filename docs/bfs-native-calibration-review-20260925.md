# BFS baseline variability and fixed-recipe review

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-26 (Eastern Time)

The completed pilots establish native scale-18 feasibility and checked results,
but do not establish a cause for their timing variation or adequate precision for
a 5% gain claim. This read-only review changes no request, threshold, source,
protocol, or measurement. The three interpreted recipes remain unsubmitted after
automatic approval review rejected their source/profile export to Claude.

Evidence is the four `bfs-native-pilot-20260925-{upstream18-a2,dx10018-a1}`
evaluation records, their complete packages, the two pilot evidence receipts,
and `docs/evidence/bfs-campaign-preparation-20260925-a1.yaml`. Retained host
receipts and all 60 process stdout logs were rehashed on mbit10 at 23:54 Eastern;
no raw files were copied locally and no execution was launched.

| Starting implementation / family | Per-source medians, ms (0 / 1234 / 7777) | Range / median | Sample coefficient of variation | Initial host load1 |
|---|---|---|---|---:|
| Upstream / uniform | 4.893 / 5.125 / 6.909 | 37.63–42.73% | 14.25–15.65% | 11.90 |
| Upstream / Kronecker | 6.370 / 6.685 / 4.602 | 38.08–49.13% | 14.00–20.05% | 17.03 |
| DX100 scalar / uniform | 26.277 / 22.068 / 22.069 | 40.75–55.25% | 16.63–23.82% | 11.34 |
| DX100 scalar / Kronecker | 20.384 / 19.608 / 18.452 | 30.67–52.12% | 11.53–21.16% | 23.09 |

Each range covers three separate five-sample source groups; the different sources
are not fifteen repeats of one workload. Coefficients use sample standard
deviation divided by the arithmetic mean. These descriptive statistics are not
a confidence interval or a selected acceptance ceiling.

**What the retained observations establish.** All four builds record
`OMP_NUM_THREADS=4`, `OMP_DYNAMIC=FALSE`, `OMP_PROC_BIND=close`, and
`OMP_PLACES=cores`. Therefore missing requested OpenMP binding is not an observed
explanation. The lane constrains the socket; no retained trace identifies each
worker's actual CPU, migrations, preemption, or effective team size. OpenMP's
binding semantics distinguish requested places from actual execution telemetry
([OpenMP specification](https://www.openmp.org/spec-html/5.0/openmpse52.html)).

The trusted driver constructs the graph serially, then times exactly one DOBFS
call in each new process (`tools/bfs_native/driver.cc.in:20–78`). There is no
within-process repetition from which to separate startup and steady execution.
OpenMP team creation can be part of the first parallel work inside the call;
allocation, initialization, and final normalization must remain charged to this
ROI. The first observation is not consistently the slowest: its rank ranges
from first to fifth across the twelve source groups. Dropping the first sample
or adding warmups would change the declared experiment and is not justified by
these observations.

The initial snapshots report 76–105 GiB available memory and no configured swap.
Governor and turbo-control sysfs files were unavailable in all four receipts.
These are evaluation-start snapshots, not per-trial load/frequency traces.
They cannot identify the load or scheduling conditions during a 4–32 ms call,
nor establish that memory pressure was absent throughout the run.

All upstream process stdout logs are empty. For every DX100 source, its five
logs have identical frontier-size sequences: six levels for uniform and six or
seven for Kronecker. Each also prints `Initializing MAA`. The corresponding
initialization and level prints occur inside DOBFS, including the functional
API's initialization (`apps/dx100/benchmarks/gapbs/src/bfs.cc:314–356` and
`benchmarks/API/MAA_functional.hpp:27–73`). Different printed level counts do not
explain the within-source spread. Variable output latency remains an unmeasured
possibility; it also cannot explain upstream variability by itself.

Consecutive process stage starts are 25.1–30.4 s apart upstream and
33.5–43.2 s apart for DX100. Recorded subprocess wall costs are 1.37–3.68 s;
neither quantity is BFS ROI time. The elapsed gaps and other host cost are not
attributed to YAML, verification, scheduler load, or any other cause here.
Instrumented thread-CPU observations come from different binaries and cannot
be substituted for missing CPU/preemption measurements of the primary calls.

**Finite follow-up, authorized for checkpoint review and coordinated dispatch.** The
existing [pilot plan](../.scratch/bfs-rewrite-evaluation-2026-09-25/pilot-plan.md)
allows at most two complete unchanged calibration blocks per size/family. One
successful block exists for each native cell. Use only the remaining second
block, not a loop that continues until a favorable result:

1. Predeclare four new evaluation IDs and their order: DX100 uniform, upstream
   uniform, DX100 Kronecker, upstream Kronecker. Reuse the exact version-2 graphs,
   sources `[0, 1234, 7777]`, lane 1, four configured threads, zero warmups,
   complete-call boundary, and five fresh processes per source. Keep the actual
   repetition-major source order. This is 60 additional primary observations,
   not candidate assessment. No additional profiling is needed merely to study
   primary repeatability; existing packages remain tied to their own evaluations.
2. Retain the current build-180 s, process-60 s, evaluation-1,200 s ceilings:
   four evaluations allow at most 4,800 s, within a predeclared 5,400 s driver
   and 5,520 s outer cleanup bound. Stop if the overall pilot's remaining
   12-hour budget or existing 30/10 GiB raw/build free-space reserves cannot
   cover it. No further complete block is authorized by this proposal.
3. Keep source/compiler/flags/driver/environment identities explicit. Verify
   the unchanged artifact and driver hash against the first block; retain
   any rebuilt binary difference. If build inputs changed, report a changed
   experimental condition instead of treating it as pure execution noise.
   Normal leases/load checks apply. Avoid scheduling our own competing job
   during this finite block when feasible, while acknowledging that other
   users' activity remains uncontrolled.
4. Preserve every checked sample. Report each source's five values, median,
   range/median, time order, and the difference between blocks. Treat the
   original and new blocks as an unchanged-source A/A negative control. Apply
   the existing 2,000-resample, seed-20260925, per-source median-ratio calculation
   descriptively in both label directions. An apparent gain above the existing
   1.05/95% lower-bound rule for unchanged code is evidence against readiness,
   not a real gain. Do not create a frozen comparison or choose the better block.
5. A single A/A result without a false gain does not validate nominal coverage.
   Five observations provide little tail information; even the full sample
   range covers a continuous population median with only 93.75% probability
   under independent sampling (`1 - 2*(1/2)^5`). The current bootstrap is an
   approximation, not a small-sample coverage guarantee. Preserve the 1.05 floor
   and 95% requirement; do not set the spread ceiling just above the observed
   maximum. If the second block still leaves precision or drift unresolved,
   report native profitability calibration as inconclusive. A larger study,
   different count, batching, or warmed-call target needs a separately reviewed
   versioned plan before any candidate timings.

This design separates execution-level variation from unobserved within-process
variation and uses a finite negative control. It does not import a paper's
steady-state warmup rule into the project's cold first-call objective.
Kalibera and Jones distinguish repetition levels and require uncertainty to be
estimated at the relevant level; their steady-state examples have a different
objective from this ROI ([author manuscript, sections 6–9](https://kar.kent.ac.uk/33611/45/p63-kaliber.pdf)).
No claim of statistical power or guaranteed 5% detectability is made.

The coordinator authorized this one remaining block on 2026-09-26, within the
existing two-block and 12-hour limits. The exact order and record identities are
in [the request plan](../.scratch/bfs-rewrite-evaluation-2026-09-25/requests/native-repeatability-20260926-a1.json).
All four new IDs start with `bfs-native-repeatability-20260926-a1`:

| Order | Evaluation suffix | First-block prefix |
|---:|---|---|
| 1 | `.dx100.uniform-random.evaluation` | `bfs-native-pilot-20260925-dx10018-a1` |
| 2 | `.upstream.uniform-random.evaluation` | `bfs-native-pilot-20260925-upstream18-a2` |
| 3 | `.dx100.kronecker.evaluation` | `bfs-native-pilot-20260925-dx10018-a1` |
| 4 | `.upstream.kronecker.evaluation` | `bfs-native-pilot-20260925-upstream18-a2` |

The [bounded public-workflow driver](../scripts/bfs_native_repeatability.py)
checks all four first-block records, unchanged source artifacts, registered
graphs, retained raw hashes, compiler versions, and trusted driver template before
dispatching any trial. It pins the earlier resolved compiler and flags in each
new public `evaluate` request. Each completed evaluation must retain fifteen
independently checked samples in the prescribed order and the identical primary
binary and wrapper hash. A changed binary or failed evaluation stops the remaining
cells; no retry or additional profiling follows. Per-source medians and spread
are descriptive. The driver does not run a gain test or create a comparison.

The first block did not retain a compiler executable hash or all inherited
OpenMP/GNU runtime knobs, so historical equality of those details cannot be
asserted. The second block records the current executable hash and selected
inherited runtime settings. It also preserves both evaluator-module identities:
validation and metadata handling changed since the first block, while the trusted
timed driver and resulting primary binary are required to match. No known change
is silently labeled execution noise.

After the reviewed Git checkpoint and fresh host/lease checks, the prospective
inner command is:

```sh
python3 scripts/bfs_native_repeatability.py \
  --runs-dir /data/yanruj/EvolveSWDB_runs/bfs-native-repeatability-20260926 \
  --records "$PWD/records" --lane mbit10-evaluation-node1 \
  --pilot-remaining-seconds REMAINING_SECONDS
```

The last argument is computed immediately before dispatch from the hard deadline
`2026-09-26 05:56:38 ET`. The coordinator conservatively counts the entire calendar
interval since the pilot plan's first commit, `a7d8d153`, at
`2026-09-25 17:56:38 ET`, including idle and engineering time. This predates the
earliest actual native pilot. The driver independently checks this deadline and
requires at least 5,400 seconds remaining; the argument cannot reset the clock.
Use the normal
socket-lane helper in a named tmux session and an outer 5,520-second timeout.
The 5,400-second internal deadline includes preflight, with at most 1,260 seconds
for each public evaluator and its cleanup. The evaluator itself retains its
180/60/1,200-second bounds. Logs stream to retained files and owned process groups
receive TERM, a grace period, then KILL on interruption. A second invocation
cannot overwrite or resume these fixed IDs. No measurement has been dispatched
by this preparation.

The run directory must initially be empty and dedicated to this block. Its four
evaluations and driver logs have a separate 4 GiB apparent-byte ceiling, sampled
at nominal five-second subprocess intervals (plus guard overhead) along with free-space,
lane, and deadline checks. Crossing the sampled ceiling terminates the owned
stage and retains its failure and raw output; it does not delete evidence or
increase the allowance. This batch bound leaves the original 40 GiB combined
pilot-output cap and 30/10 GiB free-space reserves unchanged. Dispatch receipts
from the outer lane helper belong in a separate sibling directory so they do not
violate the initial empty-directory condition.

**Fixed recipes and acceptance limits.** The review found no new demonstrated
source-semantics defect in the literal patch or the requested transformations.
The two offload recipes are constraints for not-yet-produced code, so their
correctness remains an implementation and execution obligation.

| Recipe | Source-level assessment | Remaining acceptance obligation |
|---|---|---|
| DX100 literal patch | Successful CAS already performs the parent update (`platform_atomics.h:30–31`); deleting the following identical store preserves the successful enqueue. Dynamic chunks change work assignment, while each thread's queue buffer, flush, and parallel-region end barrier remain. Guarding the level print is an explicit selected change. | The retained builds use `-DGEM5`, not the native `-DFUNC` build. They establish compilation and 31 discovered scopes, not native execution, correctness, profiling, or gain. Any eventual gain includes the declared printing change. |
| Upstream structured instructions | `curr` first becomes BUStep's destination, whose first action is `next.reset()`; it is swapped into `front` only afterward (`src/bfs.cc:46–56,136–154`). Deleting only the initial `curr.reset()` is supported by this dataflow. | Review the actual generated diff; preserve `front.reset()`, every BUStep reset, direction policy, and verifier. No candidate exists yet. |
| DX100 offload instructions | The request preserves scalar DOBFS identity and moves tile/register initialization into its complete-call ROI. The pinned helper currently waits on input tile3 after storing into result tile5; requiring `wait_ready(tile5)` before consuming old values or releasing the critical section addresses the actual result dependency (`bfs.cc:170–193`). | Prove full/tail execution, valid resource allocations, duplicate-parent handling, exact returned parents, and model/guest compatibility. A compiled helper or API call name does not prove acceleration. |
| Upstream annotated offload | The recipe explicitly requires checked 64-to-32-bit CSR adaptation, actual queue/parent public APIs, 32 distinct tiles/registers total, in-ROI setup, 64-bit scout sums, serialized parent update, and source-specific CPU fallback. | Check every emitted cast/range, update of `edges_to_check`, tail transition, scout reduction, queue boundary, and returned-old-value use. Forced large-frontier top-down traversal changes algorithm selection; it must remain disclosed in any joint software/accelerator comparison. |

The pinned indirect-store contract returns successively updated old values for
repeated addresses in model processing order; it does not establish CPU-CAS
semantics or a global deterministic winner. Keep the critical section and result
completion dependency, and accept alternative structurally valid BFS parents
([operation record](../records/operations/dx100.mmio.v1.indirect-store-vector.i32.yaml)).
No actual provider output, native correctness, simulated accelerator coverage,
or candidate gain is inferred from this review. Tickets 15 and 17–20 retain
their existing empirical gates.
