# Independent legal OpenMP event probes

Created:2026-10-06 ET. Prospective scope; no application timing or service cost is
used to choose this recipe. The four actual static projections are the
`11-openmp-{bfs,bc}.g{16,17}-projection-mbit10-20261006-a1.json` files. They bind
exact all-trial executed site unions, normalized IR and complete characterizations.
The static facts are not runtime-state or cost measurements.

The fixed matrix has22 constructions: six fork capture arities2/3/4/5/7/8, two
barrier ident classes34/322, signed4/8-byte static initialization, static finalization,
one-variable8B reduction and matching end, single and matching end, signed4/8-byte
monotonic dynamic initialization with original schedule/step/chunk constants,
success/failure next for each width, and dispatch deinitialization. Runtime
iteration bounds are independently constructed0..31. Application dynamic bounds,
pointer identities and library internal state remain unverified transfer facts.

Each iteration establishes valid state before the measurement window and closes
it afterward. An end-reduction event requires a preceding result1 reduction and
the same lock; an end-single event requires a successful single; dispatch-next
receives a preceding initialization, and terminal paths drain it. These matching
protocols follow the LLVM [synchronization ABI](https://openmp.llvm.org/doxygen/group__SYNCHRONIZATION.html)
and [work-sharing ABI](https://openmp.llvm.org/doxygen/group__WORK__SHARING.html).
The live runtime hash, rather than the current web documentation, identifies the
actual calibrated implementation.

The selected target event alone is bracketed by two uninstrumented steady-clock
reads. The driver brackets an empty window and executes the same valid target
outside that window. Both preparations and cleanups remain outside it. Durations
are summed across independently proved event counts. All gross/driver values,
return checks and alternating-order pairs are retained. A nonpositive paired
residual remains unknown; the original result is never clamped or relabeled.
Per-event clock overhead and possible interaction with the event remain an
explicit measurement premise. These are effective constructed probe costs,
not physical instruction latency or a proven application bound.

Count-only visibility inlines the identical selected event into its ROI, keeping
legal setup/cleanup and the driver's actual event in separate noinline helpers.
Four source-normalized-v2 points cover3/5 repetitions times service/driver,
proving N versus0 for every exact source call class. Static normalized-IR projection
also verifies literal ABI operands and immutable ident flags. Instrumented
processes provide only numerators; they never provide service elapsed time.

Fork events run in caller context with an empty variadic microtask. Other events
run in one serializedT1 team. Sixteen valid warm iterations precede each pair.
The collector checks team size1, level0 for fork caller probes, level1 and active
level0 for non-fork probes. Application transfer is explicitly inferred from
T1 count context; no prewarm, task-pool, cache or page-residency identity is claimed.
Exact compiler, libomp, C/C++ libraries, OMP/KMP/GOMP environment and interposer
controls must match before a derived target can select these parameters.

Native caps are22 cells,7–11 repetitions,50–200ms minimum gross/driver duration,
16777216 events per trial,900s inner wall time,64MiB counted-build artifacts and
25MiB timed data. The helper requests less than4KiB of owned scalar/array payload;
this is not a claim about the runtime's allocation or total process RSS. Native
lane containment uses the established process-group cleanup and verified full
socket lease; each timer process pins one physical core. Parent owns dispatch,
keeps the other socket idle for elapsed work and uses a distinct raw root for
count-only and calibration. No application outcomes are available to this plan.
