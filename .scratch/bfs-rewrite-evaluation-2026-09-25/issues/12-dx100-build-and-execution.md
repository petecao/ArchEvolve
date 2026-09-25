# 12 — DX100 build and execution

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** claimed
**Blocked by:** 03
**Spec:** `../spec.md`

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## What to build

Preparation claimed 2026-09-25 by `host_dx100`. Pinned source and bounded build
helper are prepared; real execution remains gated on ticket 03 acceptance and
root-coordinated lane assignment.

Add bounded DX100 build, checkpoint, and execution support to the public evaluation workflow. An identified pinned BFS executable and simulated target can produce a durable execution result with raw artifacts, even when correctness and complete profiling have not yet been attached. Establish a real BFS-only smoke path; do not treat that smoke run as a verified implementation or a performance acceptance result.

## Scope and spec references

Implements the backend and retention portions of D02, D03, D09, D14 and supports AC09, AC13, AC19. The inspected DX100 revision is `e4fc4afdf894f295442cef3604667a469fab8e62`; confirm the selected revision, dependencies, and supported settings during implementation. This slice builds the existing model/API and scalar/author-accelerated BFS artifacts. It does not add hardware operations, perform the full artifact campaign, or implement complete correctness/profiling acceptance.

## Acceptance criteria

- [ ] Before future build or execution, record attempt, wall-time, memory, storage, and parallelism limits; check live host capability/capacity and apply the repository's host, lane, no-sudo, storage, and synchronization procedures. Local Apple Silicon artifacts are not reused as x86 build products.
- [ ] Build provenance identifies the DX100/model revision, required dependencies, toolchain, build settings, source identities, scalar BFS and author-accelerated BFS binaries, and executing host. The host identity remains separate from the simulated hardware target.
- [ ] Public execution requests select an exact binary, workload/source arguments, simulated configuration, and checkpoint provenance. A checkpoint is not silently reused for an incompatible binary, workload, or execution context.
- [ ] A bounded real checkpoint-to-ROI smoke execution completes for the pinned BFS path and retains its actual command/configuration identities, raw simulator output, exit reason, and available ROI artifacts. Backend configuration can represent the scalar and accelerated targets without conflating them.
- [ ] The supplied checkpoint-helper argument mismatch is checked and any necessary adapter/automation correction is recorded. The backend does not infer successful execution from a preexisting statistics file or assume that a requested trial count survived the first simulation exit.
- [ ] Build failure, missing dependency/capability, invalid checkpoint, simulator failure, timeout, and budget exhaustion remain queryable with stage-specific reasons and completed evidence. A later process can retrieve the execution after the originating caller exits.
- [ ] Smoke evidence lacking explicit timed-binary correctness is labeled unverified; raw statistics and a successful process exit do not promote it to an implementation or establish a gain. Missing region or memory profiling is reported as incomplete rather than fabricated.
- [ ] Large raw artifacts and checkpoints retain external identity/location references and follow host storage rules. Host wall time is recorded as experiment cost, not simulated BFS execution time.

## Verification

Use the public workflow for deterministic external build/simulator fixtures covering failure, timeout, checkpoint mismatch, and fresh-process retrieval. Complete one bounded real DX100 BFS smoke execution for backend bring-up after authorization and resource checks. Label the fixture results and real smoke evidence separately. Neither fixture output nor a scalar-fallback smoke case satisfies later accelerator correctness or profiling acceptance.

## Dependencies and boundaries

Ticket 03 provides the public evaluation/result foundation and durable outcome handling. Ticket 13 independently adds exact timed-binary correctness; ticket 14 adds complete simulated ROI/region/memory profiling. Neither is a prerequisite for recording an explicitly unverified smoke result here. This slice does not wait for ticket 11's complete comparison machinery or ticket 15's candidate protocol freeze. Its own small execution definition and budgets must still be explicit before running. Do not reproduce unrelated benchmarks, tune for a speedup, or run without a bound until the model works.

## Implementation evidence — 2026-09-25

The public build/checkpoint/execution adapter and bounded build helper are implemented in `swdb/dx100.py` and `scripts/dx100_build.py`, with request and evidence rules in `docs/bfs-dx100-execution.md`. `python3 -m pytest tests/test_dx100.py -q` passed 7 public contract-fixture tests in 17.02 seconds. These cover build success/failure/budget, exact checkpoint bindings, missing statistics, changed binaries and simulator timeout with prior evidence retained. Real model build and smoke acceptance have not yet run; this ticket remains claimed.
