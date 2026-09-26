# Native requested runtime inputs

Date: 2026-09-26 (Eastern Time).

[D13](../.scratch/bfs-rewrite-evaluation-2026-09-25/spec.md#d13-workload-identity-and-protocol-freeze)
requires the native comparison settings to be fixed before candidate
measurement. Native execution previously retained only four controlled OpenMP
variables, while four inherited inputs could differ from the admitted paired
calibration. The public pre-fix fixture is retained at
`/private/tmp/bfs-runtime-setting-audit-20260926/result.json`: a calibration-shaped
snapshot requested thread limit 4, passive waiting, and spin count 0; all twenty
fixture outputs instead received limit 1, active waiting, and spin count 300000.
The comparison remained `fixture_comparison`, with `gain_claim: false`. This is
contract evidence, not an empirical calibration or a diagnosis of pilot spread.

New native protocols require this named field in `settings`; newly collected
native evaluations and their diagnostics retain the same field in `build`:

```json
{
  "native_runtime": {
    "version": 1,
    "environment": {
      "OMP_NUM_THREADS": "4",
      "OMP_DYNAMIC": "FALSE",
      "OMP_PROC_BIND": "close",
      "OMP_PLACES": "cores",
      "OMP_THREAD_LIMIT": null,
      "OMP_WAIT_POLICY": null,
      "GOMP_SPINCOUNT": null,
      "GOMP_CPU_AFFINITY": null
    }
  }
}
```

The example shows an explicitly observed unset inherited environment, not a
default for unknown history. Exactly these eight keys are required. The first
four values must match the evaluator's controlled policy and declared thread
count. The inherited values are nonempty strings or explicit `null`; `null`
removes that variable from the child environment. Missing keys mean unknown and
are rejected. A supplied `OMP_THREAD_LIMIT` must be a positive 32-bit unsigned
integer at least the declared thread count, preventing overflow or libgomp's
upper-bound clamping in the [GCC 13.3 implementation](https://gnu.googlesource.com/gcc/+/refs/tags/releases/gcc-13.3.0/libgomp/env.c).
A supplied `OMP_WAIT_POLICY` must be ACTIVE or PASSIVE,
case insensitive with surrounding ASCII whitespace allowed. The exact input spelling
is retained. The policy does not claim to capture every possible runtime input.

These variables affect different runtime choices:
[OpenMP defines the thread limit](https://www.openmp.org/spec-html/5.1/openmpse67.html)
for a contention group, and [libgomp documents active/passive waiting](https://gcc.gnu.org/onlinedocs/libgomp/OMP_005fWAIT_005fPOLICY.html).
Their presence does not prove actual team size, worker placement, startup cost,
preemption, or the cause of observed variability. No such telemetry is synthesized.

Unfrozen native collection captures the invoking environment's four inherited
inputs alongside the four controlled inputs before collection. Frozen dispatch
constructs all eight inputs from the policy, overriding any different invoking
shell. Same-candidate paired A/A reuse requires the same runtime map as well as
the same candidate and build. Comparison reopens both evaluations and rejects a
missing, malformed, or different map. Diagnostic execution replays its primary's
map, and package assembly/regional comparison check that relationship. Native
campaign preflight requires the map and strictly matches both baseline-package
primaries to the frozen policy before submitting a proposal or executing
measurements. The paired publisher validates each explicit member version before
canonical comparison; boolean or floating-point version values cannot equal
integer version 1 through Python equality.

The publisher derives a new paired freeze from the revalidated driver's retained
inherited snapshot and all eight members' controlled inputs, checking any newer
explicit member maps too. It records that evidence basis separately. A serial
calibration requires an explicit map in every block. Unknown historical inputs
stay unknown; neither current environment values nor compiler identity fill gaps.
The original four-key `build.execution_environment` stays unchanged for historical
readers. Old records remain retrievable, and old explicit fixture-only workflows
remain executable. They cannot authorize empirical native execution or gain
under a protocol without the map. Existing old profiles remain readable; creating
a new execution profile requires a primary with recorded runtime inputs.

The field uses existing extensible protocol settings/build mappings and a strict
versioned validator, so the enclosing record format remains 0.4. No catalog
record is migrated or rehashed. Existing source, compiler, binary, graph, ROI,
lane, protocol identity, and code/runtime hash checks remain in force. Changed
collector code requires its normal new prospective runtime pin; this repair does
not update an active driver's pin or the fixed paired pilot plan. It changes no
spread, speedup, confidence, resampling, seed, source, graph, or ROI policy.
