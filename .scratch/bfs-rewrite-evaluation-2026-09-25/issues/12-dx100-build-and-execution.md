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

## Real attempt 1 and diagnosed retry — 2026-09-25

The public first build ran on mbit10 lane 0 (lease generation 265) at 17:40:46–17:41:39 ET from SWDB `4a9383316eb8b2a5dfb53a02bb6c9a4c30a31b8d`. It stopped during Ramulator CMake configuration because `du` traversed a CMake temporary file concurrently removed by CMake. This was an explicitly recorded monitor failure, not a compiler/model failure. Raw receipt and stage logs remain under `/data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925/bfs-dx100-build-20260925-a1/`; public evaluation `bfs-dx100-build-20260925-a1` is retained. Lane 0 released cleanly.

The monitor now accepts only a complete `du` directory total accompanied exclusively by explicit vanished-file warnings, retaining those warnings; permission or other errors still fail closed. `tests/test_dx100_build.py` passes three cases, including the observed race and a permission-denied failure. Request `requests/dx100-build-a2.yaml` retains the same declared budget for the diagnosed second attempt. No simulator execution is implied.

## Successful build and bounded bring-up — 2026-09-25

Real build `bfs-dx100-build-20260925-a2` completed on lane 0 with all model,
Ramulator, m5ops, scalar BFS, accelerated BFS, 1K BFS, and converter artifacts
identified. Host cost was 1804.54 seconds with peak RSS 5.60 GiB and 4.96 GiB
source/build storage, within the declared limits. Runtime dependency versions
and the known generated tracked `m5op.o` cleanup are retained separately;
linked executable hashes did not change when the tracked source object was
restored.

Real smoke a3 reached the original guest checkpoint and exited that stage
successfully in 91.656 seconds. Its adapter rejected the model's additional
empty `cpt.%d` formatting placeholder. Evaluation
`bfs-dx100-smoke-20260925-a3` retains this failed outcome and raw evidence.
The source-confirmed correction accepts exactly one numeric checkpoint plus
that explicitly empty placeholder, and rejects unexpected payloads. Six public
checkpoint tests passed in 16.56 seconds. Retry a4 was dispatched through lane 1
at 20:37 ET from `6ddaff831b85d8039729114f10a7341611b01657`, with a
300-second checkpoint bound inside the unchanged 1100-second total budget.
Checkpoint-to-ROI acceptance is still pending; this ticket remains claimed.

## Fixed host-memory diagnosis — 2026-09-25

a4 completed its checkpoint but exceeded its 16 GiB host cap during restore.
a5 reused that exact checkpoint/configuration and traversed the tiny graph, then
exceeded its 32 GiB cap during the first statistics dump (sampled 32.12 GiB).
Neither produced a sealed ROI or verifier result. Both failures are retained;
they do not establish backend acceptance. The unchanged model's approximately
4.94 million cache statistic objects have a source-derived allocation subtotal
of 26.86 GiB before allocator rounding and other state. The actual binary already
links tcmalloc. The [finite feasibility plan](../dx100-memory-feasibility-plan.md)
documents the arithmetic, uncertainties, and exactly one 48 GiB retry with host
RSS/phase observations, conditional on socket capacity and normal lane ownership.
Eight public continuation/resource tests and five observation/receipt tests pass.
At 21:22 ET, lane 1 was free but its conservative free-plus-clean-cache headroom
was only 32.60 GiB, below the plan's 52 GiB prerequisite; no retry was dispatched.
