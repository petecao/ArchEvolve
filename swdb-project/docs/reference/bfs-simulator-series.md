# Bounded simulator sample grids

Navigation updated: 2026-09-28 (Eastern Time).

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)

`scripts/bfs_simulator_series.py` collects one exact registered workload for an
identified candidate through the public SWDB commands. It must run on mbit10 in
an owned socket lane, with an external timeout and a new, empty raw-output child
under `/data/yanruj/EvolveSWDB_runs` or `/data1/yanruj/EvolveSWDB_runs`. Source,
generated drivers, and binaries remain under `/data1/yanruj` through the evaluators.

Without `--protocol`, the driver permits only an unchanged pinned application
snapshot of the two starting implementations or the fixed author reference. A
new snapshot of changed code is not an unchanged calibration baseline. With
`--protocol` and `--protocol-role`, primary executions bind to that existing
policy. The comparison baseline must still be the unchanged unaccelerated source.
The driver does not choose a rewrite, freeze policy, retry failures, or compare
results. A completed series is not itself a gain claim.

Each workload source gets two separate primary executions and two separate
diagnostic executions. For each source and binary, the second replay restores the
first execution's exact checkpoint through its hashed manifest. Every replay is a
new simulator process with a new ROI and correctness result; reuse avoids repeating
guest serialization without creating synthetic measurements. Checkpoints are not
shared across source vertices, primary/diagnostic binaries, or series.
Primary results carry the actual frozen source/repetition
cell when applicable. Diagnostic source scopes and binary differences are retained
separately; their durations cannot replace primary ROI timing. The driver assembles
one complete package per primary cell, then aggregates frozen primary executions
through `aggregate-evaluations`. Incomplete execution, correctness, profiling, or
aggregation stops the series with all prior evidence retained.

The normal path compiles the selected source function using the trusted complete
BFS call wrapper. `--author-binary` instead selects the unchanged built `bfs` or
`bfs_maa` artifact and preserves `bfs.dx100.traversal.v1`. Its separately compiled
diagnostic must support that exact semantic ROI; a complete-call diagnostic cannot
silently stand in for it. The original primary author executable stays unchanged.

`--diagnostic-build` selects an already completed public compilation record.
The driver requires the same candidate, entry point, source hash, model build,
target, ROI and accelerator treatment. Before any primary execution, both a
reused diagnostic and a newly compiled diagnostic must match every selected
frozen region and its collector/library/runtime hashes. Reuse preserves the
pre-freeze artifact when collector source later changes; the public execution
path still rechecks source, driver and binary files. The driver receipt retains
the selected diagnostic record and its canonical digest.

All limits appear in the driver receipt before work. Defaults follow the
[pilot plan](../../.scratch/bfs-rewrite-evaluation-2026-09-25/pilot-plan.md): 3,600 seconds
each for a primary checkpoint and traversal, 600 seconds per diagnostic execution,
32 GiB process-group RSS, 10 GiB per execution, and 40 GiB total series raw output.
The author path accepts the separately declared
[reference bounds](../../.scratch/bfs-rewrite-evaluation-2026-09-25/artifact-reference-plan.md).
Caller-selected limits cannot exceed those plans. A parent coordinator must also
enforce the pilot/reference batch's combined elapsed and storage cap across series;
per-series limits do not reset that combined budget.

Every stage retains its exact command, stdout/stderr paths and hashes, outcome,
and host wall cost. A signal or timeout first lets the public evaluator persist
its interrupted outcome, then terminates the owned process group. Thirty seconds
inside the overall elapsed limit are reserved for cleanup; repeated signals do
not interrupt that cleanup. Failed stages retain output hashes as well as their
return code and reason. Runtime monitoring
checks elapsed time, raw storage, and the 10 GiB build-volume / 30 GiB raw-volume
free-space reserves. Completed samples, source medians, repeated-sample spread,
coverage observations, package identities, and an optional aggregate ID are
written to the external driver receipt. None is fabricated for an unfinished cell.

This document describes implemented orchestration. Real simulator acceptance is
tracked independently in Tickets 12–16; local tests and a prepared command do not
establish an executed model result.
