# 14 — DX100 region and memory profiling

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-26 (Eastern Time)
**Type:** slice
**Status:** claimed
**Blocked by:** 09, 12
**Spec:** `../spec.md`

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## What to build

Expose real DX100 simulated BFS ROI, selected-region timing, and dynamic memory observations through the profile-package and result-query workflow. Reuse the existing region/source and package contracts. Profile collection is independent of correctness checking: its evidence remains explicitly unverified until compatible correctness evidence is attached.

## Scope and spec references

Implements the simulated portions of D04–D06, D11, D14 and AC02–AC04, AC09, AC13. Timing attribution and memory observations must refer to actual simulated execution. Static source order is not a substitute for the executed frontier/access behavior. Full address traces and per-loop attribution of every hardware metric are not required; the available attribution granularity must be truthful.

## Acceptance criteria

- [ ] A real bounded simulation yields retrievable BFS ROI duration from an identified statistics interval, preserving raw ticks/time, units, clock configuration, binary/workload/target identity, and raw evidence. The supplied parser's hardcoded tick conversion is checked rather than assumed valid for every configuration.
- [ ] Selected-region durations are reported separately from BFS ROI duration, with exact region/source association, per-invocation or accumulated scope, and inclusive/exclusive attribution. Call counts or other attribution coverage and unavailable information remain explicit.
- [ ] The collector integrates with automatically discovered regions and refreshed source mappings, including changed or split/fused regions. A region comparison requires a stated correspondence and cannot copy baseline observations onto altered code.
- [ ] Each complete simulated profile package contains at least one actual dynamic memory-behavior observation, such as access counts or cache behavior. An all-unavailable metric set, source-derived description, or fabricated source-order traversal cannot satisfy this criterion.
- [ ] Every memory metric records its definition, units, model/collector, evidence basis, collection interval, workload/binary/configuration identity, and attribution granularity. ROI-wide counts are not presented as loop-specific measurements or native hardware observations.
- [ ] Any separate diagnostic execution identifies differences from the primary timed artifact, traversal, or modeled target. Diagnostic runtime and simulator host cost do not replace primary ROI timing; instrumentation overhead and unresolved attribution are exposed for protocol calibration.
- [ ] Measurements can be retained and queried without ticket 13's verdict, but correctness remains unknown/unverified and no successful implementation or gain claim is produced. Compatible correctness can subsequently be linked without erasing the original measurement provenance.
- [ ] Missing/malformed statistics, unsupported metrics, partial collection, timeout, and budget exhaustion return explicit stage outcomes with available evidence. A fresh process retrieves the profile and its incompleteness reasons; a complete package cannot silently omit all dynamic memory observations.

## Verification

Exercise the public workflow with deterministic simulator-output fixtures for interval selection, unit conversion, unavailable metrics, region attribution, and unverified status. Complete a bounded real simulator profiling run to establish actual ROI, region, and memory evidence; fixture values do not establish dynamic behavior. Use actual execution-derived observations for frontier-dependent accesses. Profiling jobs require explicit budgets and the repository's host/lane procedures before execution. This ticket does not require a correctness verdict to prove collection behavior, and its real profile stays unverified until one is attached.

## Dependencies and boundaries

Ticket 09 supplies actionable profile packages, source/region mappings, and public retrieval. Ticket 12 supplies the executable model and identified raw execution artifacts. Ticket 13 is deliberately not a dependency; correctness and collection remain independent evidence stages. This slice does not create a second discovery engine, implement new hardware operations, freeze final workload/noise settings, perform the full artifact campaign, or establish a candidate gain.

## Dependent preparation — 2026-09-25

Claimed while tickets 09 and 12 prepare shared packages and the executable model. The collector reuses automatically discovered source regions, consumes the actual sealed statistics interval and log, and binds all observations to the exact binary/workload/configuration. Source-inferred memory behavior and contract fixtures cannot satisfy real acceptance.

## Initial collector implementation — 2026-09-25

`swdb/dx100_profile.py` implements strict interval/clock conversion, actual ROI-wide memory counters, source-verified automatic region reuse and partial selected-loop timing; `docs/bfs-dx100-profiling.md` describes its limits. The combined DX100 fixture suite passed 23 tests in 87.32 seconds, including seven public collector cases for altered tick frequency, multiple intervals, missing memory, truncated/changed statistics, invalid clocks and stale region mappings. Complete function/exclusive-loop attribution and real simulator acceptance remain outstanding; the collector explicitly returns partial.

## Source-scope diagnostics implemented — 2026-09-25

The collector now supports shared libclang discovery with the actual simulator
preprocessor settings and compiler header search order. Separately identified
diagnostic binaries use `m5_rpns` guards for nested inclusive/exclusive simulated
elapsed intervals accumulated per executing thread. These include waits and
overlap; they are not CPU service time or primary BFS elapsed time. Model memory
counters remain attached to the primary binary and whole sealed ROI.

The unchanged author traversal diagnostic forwards its original ROI events.
Scopes entered before activation, including the enclosing BFS function, retain
explicit unavailable durations. Exact source, graph, binary, global protocol
trial, target configuration, and ROI bindings are required for packaging. The
combined relevant suite passed 42 tests in 166.32 seconds, including public
positive and negative diagnostic collection paths. A real complete simulated
profile package remains pending behind bounded model bring-up; this ticket
remains claimed.

## Preliminary handoff audit — 2026-09-25

The source-scope handoff audit reproduced and fixed two gaps before the next
real compile smoke. Candidate interface utilities could differ from the pinned
headers selected by the compiler; the public compile path now rejects changed
or shadowed inputs throughout the pinned model interface. Both actual unchanged
source manifests pass this guard, including upstream repository metadata.
Malformed diagnostic JSON objects and counter rows now retain explicit failed
collection records instead of escaping with an uncaught attribute error.

The combined public compile/collector regression passed 37 tests in 124.32
seconds. The subsequent metadata-name correction and candidate regressions
passed 22 tests in 45.18 seconds. These establish contract handling, not real
simulated profiling acceptance. The memory-gated model feasibility attempt and
real primary/diagnostic collection remain pending.

## Real source-diagnostic compilation — 2026-09-25

The public unchanged DX100 scalar diagnostic build completed on mbit10 lane 1
at 22:43 ET, using the actual GCC 13 GEM5/OpenMP flags and shared libclang
discovery. It discovered 31 source scopes and compiled the instrumented binary
with SHA-256 `40a215eac6816704b92c0847e24c1aba7abf9c5699c23b2407e55b41b212f483`.
The separate primary binary and unchanged source were also built and rehashed;
`observations/dx100-compile-smoke-a1.json` links their public records and raw
receipts. The diagnostic public call cost 64.11 host seconds within its
240-second/16-GiB bound. Discovery and compilation establish no dynamic region
durations, memory observations, or simulated correctness. Real collection
acceptance remains pending and this ticket stays claimed.

## Additional compilation evidence — 2026-09-25

At 23:11 ET all requested compile-only cells had passed: the unchanged upstream
complete-call primary/diagnostic pair and the unchanged author scalar/MAA
traversal diagnostics. Audited public records and raw-output hashes are linked
by `../observations/dx100-compile-extension-a1.json`, imported in `d9c4c10`.
Upstream discovery retained 24 source scopes; each author diagnostic retained
31. Original author scalar and MAA binaries remain unchanged. This completes
compilation preparation for both source families and ROI treatments, without
claiming simulator execution, timed correctness, or dynamic profile acceptance.

## Independent actual-observation audit — 2026-09-26

The bounded real primary and diagnostic runs at implementation checkpoint
`5802a5a` produced source-bound sealed observations. Both executions remain
`missing_observation` with **unverified correctness** under their original v1
checker. The initial orchestration omitted a required collection CLI argument;
it failed before any collector execution. An additive continuation performed
only the already planned collection, package, and fresh retrieval. Neither
simulation was repeated and the failed driver receipt remains available.

The independently audited package is
`bfs-dx100-profile-20260926-a1.package.v1.60c6fe30745432bc`, retained under
`/data/yanruj/EvolveSWDB_runs/bfs-dx100-profile-20260926-a1` on mbit10.
It contains 31 discovered regions and 39 actual ROI-wide memory observations.
Eight regions executed (three functions and five loops); 23 were unobserved.
The unsupported unused TDStepMAA SIMD scope remains explicit. Its public package
is complete under the stated package contract while the collector retains its
partial discovery limitation.

An independent worker checked 17 bounded raw/source artifacts, every region's
source byte range and diagnostic counter mapping, all 39 memory values and
intervals, and 13 access/hit/miss identities. The primary duration is
49,313,463 ticks / 10^12 ticks per second = 49.313463 microseconds. The actual
313-tick CPU period (about 3.194888 GHz) is recorded separately from the requested
3.2 GHz clock. Region durations are diagnostic accumulated per-thread elapsed
intervals; memory counters cover the primary whole ROI. They cannot be added
or substituted for primary BFS time. The audit reused the existing model-build
identity receipt rather than rehashing the large simulator and Ramulator files.

This tiny 64-vertex, 468-arc, source-0 case establishes collection behavior. It
does not establish accelerator coverage, pilot-sized feasibility, matrix
acceptance, verified correctness, or gain. Every gain flag remains false.
Fresh public retrieval matched the stored execution/profile/package records;
the separate registered workload is being added to generic chain traversal.

The independent audit found no blocking observation defect. This ticket remains
claimed until the exact metadata export is authorized and the master records
and evidence can be synchronized. This update is retained locally and excluded
from Git export while that approval is pending.

2026-09-26 local review follow-up: the public hotspot query now selects actual
simulated elapsed metrics for these profiles instead of indexing native CPU
fields. Guarded diagnostics use exclusive elapsed intervals; logging-only
profiles expose inclusive observed-loop intervals. Unobserved scopes remain
unranked and fixture evidence stays labeled. Five focused public tests and an
independent replay of the original query failure passed. This repair does not
verify the timed binary or change the actual package's evidence limits. Review
details are in `docs/bfs-interim-review-20260926.md` (repository-root path).

2026-09-26 10:04 ET health update: the original failed driver and the completed
collection/package continuations retain their prior hashes. The final package
receipt remains `a66864e…`; recent package and fresh-chain stderr logs are empty.
No profiling job remains. No new measurement, correctness result, record import,
or evidence export occurred; the exact 14-file packet approval remains pending.
