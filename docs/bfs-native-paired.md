# Native paired collection contract

Created: 2026-09-26 (Eastern Time).
Updated: 2026-09-26 (Eastern Time).

`swdb evaluate-pair REQUEST --runs-dir DIR [--lane LANE]` adds the
`native_paired.v1` collection method. Message version 1.0 and record format 0.4
remain unchanged. The request contains `id`, `message_version`,
`collection: {method: native_paired.v1, order_seed: INTEGER}`, an explicit
`budget: {total_seconds: POSITIVE_NUMBER}`, and `baseline` and `candidate`
objects, each a complete ordinary native evaluation request with its own ID.
Both roles must have identical workload, sources, repetitions (at least five),
threads, machine, target configuration, ROI, fixture classification, and protocol
identity. With a protocol, their explicit roles must be baseline and candidate.
The unchanged-code A/A case uses the same candidate ID in both requests; it
reuses the exact compiled executable and requires identical build settings.

An `evaluation_pair` record retains the original request, the complete prospective
schedule and its hash, two ordinary evaluation records, and the execution
receipt. The schedule visits repetitions, then the unchanged ordered sources.
For each source, a seeded shuffle balances baseline-first and candidate-first
pairs (counts differ by at most one for odd repetition counts). Each adjacent
pair consists of two fresh processes. Both artifacts are prepared before any
trial; no diagnostic profiling runs between members or during primary collection.
The receipt binds schedule/block/source/repetition/role, actual timestamps,
raw output hash, timed binary, and the structural correctness result. Failures
retain partial observations and stop the pair; they cannot produce a complete
receipt or qualify a comparison. Total pair time includes both builds, checking,
and persistence, and each ordinary evaluation retains its own total bound.

A paired frozen native protocol explicitly adds
`sampling.collection: {method: native_paired.v1, order_seed: INTEGER}` and
`sampling.analysis: paired_repetition_block_bootstrap.v1`. Its existing
`aggregation: geomean_source_median_ratio`, zero warmups, minimum five repetitions,
1.05 minimum speedup, 95% interval, 2,000 resamples, seed 20260925, and supplied
positive spread ceiling are mandatory. Each bootstrap draw samples whole
repetition blocks with replacement: the same sampled repetition indices apply
to every source and both roles. The point estimator remains the geometric mean
of per-source median baseline/candidate ratios. Comparisons require both
evaluations from the same complete, hash-bound receipt and reject incomplete,
changed, serial, or cross-pair evidence. Fixtures remain fixtures and cannot claim
gain. The spread veto remains applied to each role and source independently.
Admission reopens the registered graph representation, verifies its immutable
registration and content/canonical hashes, and independently checks every reopened
raw parent vector against that adjacency. Re-sealing timing, correctness, or
receipt metadata cannot substitute for a valid structural result. These admission
checks occur outside the measured BFS ROI.

Protocols without the new sampling fields retain serial collection and the
existing independent bootstrap. Historical serial records are not migrated or
reinterpreted. The native campaign chooses the frozen collection method and
collects each candidate (including a repair) with fresh baseline pairs, then
collects diagnostics and compares the resulting full grids.
The campaign's paired branch allows 2,400 seconds for the complete pair and
each member including its waiting time, with the existing 180-second build and
60-second process limits. Its enclosing campaign budget still applies. These
new-mode bounds do not increase any earlier pilot's allowance.

This interface does not qualify paired pilot evidence for the existing pilot
publisher, reset the expired pilot, or establish empirical readiness. A future
calibration plan must predeclare its finite count and budget; ten pairs can
provide exact role-order balance, but a passing A/A control alone does not prove
95% interval coverage or statistical power. Old failed controls remain retained.
The collector never makes a gain claim or decides calibration readiness. Any
numerical A/A gain is a failed negative control, not a candidate improvement;
the later pilot reader must retain both label directions and the fixed false-gain
veto before paired evidence can qualify protocol publication.
