# Native pilot review and protocol publication

Updated: 2026-09-26 (Eastern Time).

The original serial pilot remains incomplete. A separately planned paired mode
is being implemented under [the finite paired study](bfs-native-paired-pilot-20260926.md).
It does not reinterpret or replenish the expired serial pilot. The serial
contract below remains supported for its original records.

For paired publication, retain the two source-specific diagnostic `packages`
and add `paired_calibration` containing `pairs` (all four fixed new pair IDs,
in planned order), `historical_packages` (all four original profile-package IDs,
in the original fixed cell order), and `driver_receipt: {path, sha256}` for the
complete new study. The existing `repeatability.evaluations` mapping then names
all four original first/second evaluations. Both old directions and every old
cell are reconstructed, including the failed DX100 uniform control when preparing
an upstream protocol. Missing or changed historical evidence blocks publication.

Paired admission requires every new pair, all raw parent checks, both label
directions, and the prospective 0.10 spread ceiling. The frozen sampling uses ten
repetitions, `native_paired.v1` with order seed 20260926, and
`paired_repetition_block_bootstrap.v1`; the 1.05/95%/2,000/20260925 profitability
policy is unchanged. Historical serial failures remain under
`calibration.historical_serial_control` with the original numerical-gain veto.
Historical spread diagnostics name the newly supplied ceiling explicitly; the
old pilot never froze its own spread policy. These observations are not
inputs to the new paired statistics. Old diagnostics and overhead stay tied to
their actual five-trial evaluations; matching new source/build/binary/target
treatment is required before retaining them as supporting evidence. Every
shared accelerator gate below still applies. A passing native negative control
alone cannot publish a protocol or complete Ticket 15.

`scripts/bfs_freeze_pilot.py prepare SELECTION.json --records RECORDS --output NEW_DIR`
prepares a review and exact public `freeze-protocol` request from two complete real
native packages. It does not publish a protocol. The packages must describe one
unchanged scalar implementation, one workload from each graph family, four native
threads on the same recorded lane, and five actual complete-call trials for each
ordered source `[0, 1234, 7777]`. Actual source, binary, raw output, compiler,
machine, instrumentation, structural checks, diagnostic memory, and current
function/loop source extents are revalidated. Missing remote artifacts prevent
empirical publication rather than being accepted from metadata alone.
The retained lane annotation must have the exact native verifier receipt format,
with matching socket binding, host machine, and requested lane identity. Reviewing
that historical receipt does not claim its old lease is still held.

The selection object supplies `mode: native`, a new protocol `id`, optional
`version`, two `packages`, an explicit positive `maximum_relative_spread`, and a
`spread_justification` based on the observed baseline. It also supplies
`size_selection` with `scale`, a written `justification`, optional
`rejected_evaluations`, and `accelerator_packages`. No default spread threshold is
chosen. Every actual within-source spread is reported; exceeding the supplied
threshold leaves the review unpublishable. The driver never raises the threshold.

The required `repeatability` object has two fields:

```json
{
  "evaluations": {
    "FIRST_UNIFORM_EVALUATION_ID": "EXACT_SECOND_UNIFORM_EVALUATION_ID",
    "FIRST_KRONECKER_EVALUATION_ID": "EXACT_SECOND_KRONECKER_EVALUATION_ID"
  },
  "driver_receipt": {
    "path": "/absolute/retained/second-block/driver.json",
    "sha256": "EXACT_RETAINED_FILE_HASH"
  }
}
```

These names are placeholders, not record IDs. The mapping must name exactly the
two selected first-package evaluations and their second evaluations from the
fixed `native-repeatability-20260926-a1.json` plan. Another candidate, a later
block, or selectively chosen samples cannot substitute. The driver receipt
contains all four planned cells; the review retains that complete receipt even
though its native protocol selects one implementation's two families.
This fixed repeatability plan covers **scale 18 only**. A permitted scale-16
cost fallback cannot borrow its samples: it would need its own prospectively
reviewed unchanged blocks within the original pilot budget. No such plan or
execution is added here; missing scale-16 control evidence leaves publication
blocked.

The reader reuses second-block admission to verify both fifteen-trial grids,
structural checks, unchanged source, actual binary/wrapper/compiler/settings
identity, distinct process outputs, and the recorded lane. It rehashes available
raw/source/build artifacts and binds each second evaluation to its retained
public command's exact JSON result. Missing remote files on the local Mac mean
the empirical review is unqualified; this does not label the remote records
corrupt. Missing mappings, records, or receipts also leave it unpublishable.

`calibration.repeatability_control` retains every first/second timing row and
check, both sets of stages/context/build metadata, all source-level summaries,
record identities, and both directional applications of the existing fixed
bootstrap calculation. If **either** unchanged-code direction has a lower
95% bound above **1.05**, publication is blocked independently of the supplied
spread ceiling. This is a negative control, not an empirical gain claim; a
control without a numerical gain does not establish nominal interval coverage
or power. The second block's spread must also satisfy the declared ceiling.

The receipt reports evaluator-code hashes separately and retains second-block
compiler-executable and inherited-runtime observations. Their unavailable
first-block counterparts remain explicitly unknown. Matching timed binaries
does not assert complete environmental equality. First-block profile packages
and diagnostics remain associated with their original executions; the second
block produced no new profile. This guard adds no measurement, third block,
sample exclusion, warmed-call target, or interleaving method.

Replacing a frozen protocol also supplies its exact `supersedes` ID and a greater
`version`. Preparation checks the existing name and predecessor through the core
version contract and forwards that identity unchanged. Revised settings require
fresh compatible comparisons; the preceding evidence and comparisons remain stored.

The fixed profitability policy is a 1.05 floor, a 95% bootstrap lower bound above
that floor, 2,000 resamples, and seed 20260925. Native sampling freezes five trials
and zero untimed warmups. The shared workload plan permits performance scale18,
or scale16 only with a retained unchanged scale18 resource-cost failure. Scale14
diagnostics cannot become candidate performance workloads through this driver.
Both loader representations must already establish the same loaded adjacency.

Preparing a native review may expose a missing accelerator size gate. Publication
requires exact unchanged author-reference packages on the same two registered
workloads: two distinct simulator executions per ordered source, identical
configured binary/build/instrumentation per graph, independently checked timed
results, usable region/memory evidence, measured repeatability, and observed
accelerator execution with full/tail and competing-parent coverage for each graph.
For unchanged author traversal calibration only, independently passed v2
diagnostics may supply separately retained `supporting_case_evidence` for
applicable cases. They must match the primary source/workload/cell/configuration
and model and have their own verified compiled binary, runtime, sealed raw
statistics, and trace. Primary execution and correctness remain mandatory for
each timed replay. Diagnostic case flags are never copied into primary coverage
or used to qualify a generated candidate's timed binary.
Simulated durations remain separate from native durations. Collector overhead is
retained as observed diagnostic duration relative to the same source's primary
native median, explicitly across different instrumented executions; it is not a
candidate speedup or a claim of isolated instrumentation cost.

After the operator has reviewed actual size feasibility and the proposed settings,
`scripts/bfs_freeze_pilot.py publish REVIEW.json --records RECORDS --output NEW_DIR`
reconstructs the review from current records and raw artifacts. Any changed input,
plan, repeatability receipt/result, record identity, setting, or unmet gate rejects publication. A successful
request invokes public `freeze-protocol`, then retrieves the frozen record through
a fresh public process. Supporting pilot identities, actual samples/spreads,
rejected cases, coverage, costs, attribution, overhead, and written justifications
are retained inside immutable protocol settings and survive public retrieval.

This is a narrow native protocol publisher. It does not publish the separately
required artifact-reference or controlled-simulator policies, select a rewrite,
assess gains, or resolve Ticket15. No empirical protocol has been established by
the driver or its contract tests alone.
