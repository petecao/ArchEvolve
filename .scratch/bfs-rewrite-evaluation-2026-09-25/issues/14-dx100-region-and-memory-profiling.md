# 14 — DX100 region and memory profiling

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** ready-for-agent
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
