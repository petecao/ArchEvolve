# 11 — Workloads and comparison protocols

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 03
**Spec:** `../spec.md`

**Execution hold:** Publishing this ticket does not authorize implementation, builds, installations, benchmark/simulator runs, or remote execution. Wait for explicit user authorization.

## What to build

Make workload identity and comparison protocols enforceable through the public SWDB workflow. An operator can register and retrieve an identified graph/source workload, declare and freeze a comparison protocol, and request a comparison against an explicit baseline. The workflow must reject incompatible evidence instead of producing a misleading speedup. This is executable record/query/comparison behavior, not only a written run plan.

## Scope and spec references

Implements D01, D03, D11–D14 and AC13–AC16. Preserve canonical graph identity across upstream and DX100 applications while keeping serialized representations and application provenance separate. Support native comparisons, the authors' DX100 configuration pair, and controlled simulator comparisons as distinct protocols. This ticket provides their identity and enforcement; real pilot calibration and reference execution belong to tickets 15 and 16.

## Acceptance criteria

- [ ] A public request records and later retrieves graph family, generator parameters/revision, normalization, realized graph properties, canonical graph identity, actual ordered BFS source vertices, and each representation's content identity. Equivalent loaded adjacency is checked before representations are accepted as the same logical graph.
- [ ] A comparison explicitly identifies baseline and candidate evaluation evidence, independently of source ancestry. A candidate whose ancestor differs from its selected comparison baseline resolves the declared comparator.
- [ ] Protocols record target/configuration, builds, thread count, workload/source sequence, named semantic ROI, correctness coverage, instrumentation treatment, repetitions/aggregation, and profitability criteria. A frozen protocol has an immutable identity and a retrievable record of the selected values.
- [ ] Native, artifact-reference, and controlled-simulator comparisons enforce their declared requirements. Controlled comparisons match CPU/cache/memory/workload settings and enumerate remaining software/accelerator differences; artifact comparisons retain their disclosed configuration differences.
- [ ] Incompatible workloads, sources, ROI boundaries, targets, threads, or correctness evidence produce explicit non-success outcomes. Native and simulated durations cannot be divided, and diagnostic runtime or simulator host cost cannot silently replace primary ROI duration.
- [ ] Selected-region speedups require identified corresponding regions and declared per-invocation or accumulated scope, including inclusive/exclusive attribution. A local region gain is not relabeled as BFS ROI gain.
- [ ] Candidate performance assessment and successful gain claims require the applicable frozen settings. Missing, invalid, incomplete, or unverified evidence remains distinguishable and never becomes a neutral speedup of one.
- [ ] Changing a frozen workload or protocol creates a new version and identifies the comparisons that need fresh evidence. Existing results remain retrievable rather than being overwritten to hide an unfavorable case.
- [ ] A fresh process can retrieve the workload, protocol, explicit comparison baseline, compatibility decision, and evidence references through the public interface.

## Verification

Exercise the public command/message workflow against isolated records. Use small graph representations to check adjacency compatibility and deterministic evaluation fixtures to cover native/simulated separation, ROI mismatch, explicit comparator selection, missing correctness, incomplete metrics, and protocol versioning. Fixture durations establish comparison behavior only; they are not performance evidence. Reuse ticket 03's real native evaluation capability without requiring a DX100 build to complete this slice.

## Dependencies and boundaries

Ticket 03 supplies native evaluation and durable results to compare. No simulator execution dependency is added here: target/protocol rules can be checked using declared configuration records and clearly labeled fixtures. Tickets 15 and 16 populate the rules with independently frozen real-run protocols. This ticket does not select profitable workloads, choose a rewrite strategy, run the coverage matrix, or claim a gain. Any future calibration or execution requires explicit budgets and the repository's applicable host/lane procedures.
