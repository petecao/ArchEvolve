# Native pilot review and protocol publication

Date: 2026-09-25

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
Simulated durations remain separate from native durations. Collector overhead is
retained as observed diagnostic duration relative to the same source's primary
native median, explicitly across different instrumented executions; it is not a
candidate speedup or a claim of isolated instrumentation cost.

After the operator has reviewed actual size feasibility and the proposed settings,
`scripts/bfs_freeze_pilot.py publish REVIEW.json --records RECORDS --output NEW_DIR`
reconstructs the review from current records and raw artifacts. Any changed input,
plan, record identity, setting, or unmet gate rejects publication. A successful
request invokes public `freeze-protocol`, then retrieves the frozen record through
a fresh public process. Supporting pilot identities, actual samples/spreads,
rejected cases, coverage, costs, attribution, overhead, and written justifications
are retained inside immutable protocol settings and survive public retrieval.

This is a narrow native protocol publisher. It does not publish the separately
required artifact-reference or controlled-simulator policies, select a rewrite,
assess gains, or resolve Ticket15. No empirical protocol has been established by
the driver or its contract tests alone.
