# 16 — Artifact reference and controls

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-26 (Eastern Time)
**Type:** slice
**Status:** claimed
**Blocked by:** 11, 13, 14
**Spec:** `../spec.md`

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

## What to build

Execute and retain the BFS-only authors' scalar/accelerated artifact comparison and additional controlled reference comparisons with matched CPU/cache/memory settings. Freeze this slice's protocols independently before its measured comparisons. Provide real reference evidence and explicit limits on attribution without waiting for candidate-workload calibration or requiring new rewrite proposals.

## Scope and spec references

Implements D10–D14 and AC10, AC13–AC16, AC18. The artifact pair preserves the authors' specified BFS input and configurations, including their different LLC settings. Controlled comparisons use the fixed scalar and author-accelerated BFS code with declared matched settings and enumerated software/accelerator differences. Candidate-specific controlled comparisons remain obligations of later candidate evaluation; these reference runs do not satisfy them automatically.

## Acceptance criteria

- [ ] Before execution, record a bounded BFS-only run plan, attempt/time/resource/storage limits, and host/lane checks. Instantiate and freeze this slice's graph/source identities, build settings, ROI, exact configurations, correctness scope, instrumentation treatment, repetitions/aggregation, and profitability/claim rules independently of ticket 15. These rules assess any reported gain; a positive gain is not required to complete the reference comparison.
- [x] Resolve the artifact's prescribed graph family/scale and actual input identity from the pinned source, retaining generated/serialized identities and realized graph properties. A convenient smaller graph or matching filename is not silently accepted as the artifact case.
- [ ] Complete real scalar and author-accelerated BFS executions under the authors' BASE/accelerated configuration pair. Retain their actual configuration difference, including the LLC difference, instead of normalizing it away and calling the result a reproduction.
- [ ] Complete the additional controlled reference comparisons with matched CPU, cache, memory, workload, traversal sources, threads, and semantic ROI as declared. Enumerate remaining software and accelerator changes; do not claim an isolated software-rewrite gain from a joint hardware/software comparison.
- [ ] Each reported comparison has explicit baseline/result identities, exact timed-binary structural correctness, accelerator-use evidence for the accelerated case, BFS ROI duration, selected-region timing, and actual dynamic memory observations with truthful scope and basis.
- [ ] Preserve raw statistics, verifier output, model/build/binary/checkpoint identities, clock/timing conversion, and host cost separately. Missing, invalid, incomplete, or failed evidence cannot produce a successful speedup claim or a neutral value of one.
- [ ] Public retrieval exposes the independently frozen protocols, the real reference/control results, all failures or regressions, and their attribution limits. Existing evidence is reused only when all relevant identities and requirements actually match.
- [ ] Results do not claim generated-candidate acceptance, completion of the two-source accelerator minimum, or a gain over the authors' accelerated BFS. A reference or control outcome may be neutral or regressing without being hidden; execution remains bounded rather than continuing until a favorable ratio appears.

## Verification

Drive protocol registration, real model executions, correctness checking, profiling, comparisons, and fresh-process result retrieval through the public workflow. Fixture checks can establish configuration-mismatch rejection and preservation of failed outcomes, but cannot establish artifact reproduction, matched-control performance, or accelerator behavior. Inspect the retained actual configurations and evidence when accepting each real pair; a declared configuration label alone is insufficient.

## Dependencies and boundaries

Ticket 11 supplies explicit protocol/comparison enforcement; tickets 13 and 14 supply exact timed-binary correctness and actual simulated profiling. Ticket 15 is deliberately not a dependency. This slice owns its separate protocol freeze and may proceed alongside the candidate-matrix pilot. It does not select candidate workloads, rewrite code to beat the author result, run DMP/DAE or parameter sweeps unless separately scoped, or reproduce benchmarks beyond the required BFS path.

## Implementation progress

2026-09-25: Root is preparing the independent reference/control batch. `../artifact-reference-plan.md` records source-backed configuration, graph/source selection, bounded execution, and distinct ROI scope before measurement. Actual execution awaits Tickets 13 and 14.

2026-09-25 23:01 ET: the prescribed uniform scale-22 graph is generated and
registered as `bfs-20260925-uniform22.f23b09bb0c0601b5`, imported in `acb361a`.
Actual pinned SourcePicker execution chose vertex 2,796,003, whose degree is 40.
The graph has 4,194,304 vertices, 134,217,158 directed adjacency entries,
undirected semantics, and zero isolated vertices. Independent streaming CSR
validation produces canonical SHA-256
`b4fb93dcda22c988de996781c6d0adf070e821796e84f469a38cb3a206f109b4`
for both SG32 and SG64. Both serialized files and all preparation stage outputs
were rehashed on mbit10; raw files remain there. See
`../observations/uniform22-preparation-a1.json` for the exact source, binary,
command, bounded execution, lane-0 generation-270, and host receipts.
This resolves only the prescribed-input criterion. Reference/control freezes,
simulated executions, exact timed-binary verification, diagnostic profiles,
and comparisons remain pending; no reproduction or gain is claimed.

2026-09-25: The identity agent prepared [the concrete freeze recipe](../../../docs/bfs-artifact-freeze-recipe-20260925.md)
with exact retained model/guest/runtime identities, the now-registered scale22
graph and actual SourcePicker result, remaining region-policy inputs, two separate
policies, and the public command sequence. Isolated
contract reproductions exposed ignored simulator identity and missing aggregate
region lookup. The additive fixes pin simulation/model and fixed author sources,
bind package-backed diagnostic regions, and enforce typed per-role accelerator
coverage. These changes and fixture tests do not complete any empirical checkbox;
the independently frozen pairs, replay results and final acceptance remain
pending. Audited scalar/MAA source candidates and diagnostic compilation records
are now available in `../observations/dx100-compile-extension-a1.json`.


## Remaining execution audit — 2026-09-26 11:42 ET

The [simulation sequence audit](../../../docs/bfs-remaining-simulation-sequence-20260926.md)
identifies four independent role/policy series: eight fresh primary and eight
fresh diagnostic executions, eight packages, four aggregates and two comparisons.
The original author binaries and compatible author-ROI diagnostic builds can be
reused only after host rehashing; the two distinct policy IDs cannot relabel one
MAA replay as both comparisons. The existing 24-hour / 60-GiB budget is shared
across the whole batch. A concrete common supervisor and absolute window are
being prepared; neither policy nor any reference comparison is yet complete.

## Reviewed prospective supervision — 2026-09-26

Reference and control collection now has reviewed owned-process cleanup, original-clock resource
accounting and failure preservation; see the [verification receipt](../observations/simulator-supervision-verification-20260926.json).
The actual Linux fixtures, runtime admission and empirical execution remain
pending. This preparation does not satisfy or change any open acceptance item.
