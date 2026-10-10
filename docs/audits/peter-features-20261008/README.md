# Peter → Josh feature audit — October 8

**The forward handoff is sufficient for exploratory hardware matching. It is not yet sufficient for quantitative region-based offload accounting or ranking the proposed hybrid.** The next increment should add scoped baseline cost, profiler/IR bindings and phase counts, rather than replace the current representation.

This audits the two received v1.2 BFS reports (both still declare `schema_version: "1.1"`), Peter's current extraction skill/scripts, the existing source mapping, and the [hybrid sketch](../../designs/bfs-maple-dx100-hybrid/README.md). File hashes and the reviewed repository commit are in `manifest.json`. No Linux profiling or benchmark execution was performed. Absence below means absent from this received handoff, not proof that Peter or Yan-Ru has never collected the data elsewhere.

## Minimum next handoff

1. **Baseline cost by the actual source/IR region.** Restore runtime share, with its unit, evidence basis, ROI and denominator. Reuse the existing statement IDs; add the profiler/assembly/IR mapping. Separate row-bound loads, range/index work and neighbor loads from retained parent/CAS/store/queue effects. Line 241 contains both row-bound reads and loop control, so a line total alone cannot price that split. Account for unmatched/unattributed work instead of treating it as zero.
2. **One bound run/trial/level table.** Include the actual graph/input identity, BFS root, trial, frontier size and edges visited. Reuse already available frontier rows. Add a degree summary (at least maximum; distribution if available) so B frontier vertices are not mistaken for B neighbor requests. This helps reason about long-row continuation and DX100 utilization with MAPLE's finite queues.
3. **A reproducible evidence header.** Attach source/build/binary identity, flags, machine/thread configuration, precise workload/root/seed, ROI boundaries and raw stat/record/annotate references. Separate profiling invocations must have separate run IDs, even when they use the same command.

Unknown fields are acceptable when explicitly marked. If direct elapsed-time attribution is unavailable, send raw scoped sample/period counts with the sampling event, aggregation and denominator. An estimated runtime share may then be derived under an explicit model; a sampled cycle percentage is not automatically wall-clock runtime percentage.

## What we already have versus what is missing

| Item | Current evidence | Remaining gap / owner |
|---|---|---|
| Kernel/source identity | Both reports identify TDStep at e4fc4af. | Bind the actual profiled binary/build to that source; Peter. |
| Data types and widths | NodeID and SGOffset are reported as 32-bit / 4 bytes. | No need to re-request these as missing; clean stale prose in the methodology note. |
| Access structure | Frontier → offsets → neighbors → parent and conditional CAS are represented. | Generalized deeper chains, index arithmetic and multiple-access relationships are later coverage; Peter/Josh. |
| Seven statement IDs | Our source observations and Yan-Ru's frozen mapping cover them; row bounds have two terminal loads. | Attach measurement/IR identities and cost to these known IDs; Peter with Yan-Ru. |
| Baseline duration | Sparse report includes average trial time 0.00733 s. | No per-region runtime shares; trial/ROI linkage remains unresolved. Dense report lacks corresponding absolute timing/run provenance. |
| PMU/sample evidence | Sparse PMU metrics and dense comparative metrics are reported. | Raw outputs, denominator, error/availability/scaling status and scoped attribution are absent; Peter. |
| Phase behavior | Sparse single-traversal frontier sizes; dense topology/formula-based phases. | Bind these to the corresponding measured runs and add actual visited-edge counts. Do not merge one traversal with a five-trial average. |
| Locality | Mean absolute index distance and adjacent-pair proximity measurements. | Preserve units/order/segment scope and label proximity correctly; do not interpret as cache hits. |
| Capacity / working set | Array allocation-size formulas. | Active per-level/batch distinct bytes or accessed-element/line summaries are optional next data, not total capacity; Peter/Yan-Ru if available. |
| Legality | Stable graph arrays, mutable parent, CPU CAS and queue effects are visible in source. | Explicit ownership/alias/mutation intervals must accompany any generalized pattern; joint software/hardware mapping review. |

The reported Xeon Gold machine is valid baseline context. It should remain explicit rather than being relabeled hardware-agnostic. Cache statistics and attributed cost describe that baseline and its measurement scope.

## Tie the data to the hybrid

The proposed MAPLE stage replaces **row-bound reads**, and DX100 supplies **range expansion and neighbor reads**. The CPU retains frontier identity handling and all parent/discovery effects. A percentage for the entire inner loop would mix those responsibilities.

The hybrid also adds snapshot copying, pointer submissions, queue consumption, CPU-to-DX staging, waits and final drain. Those instructions are absent from the original baseline; they cannot be priced by copying unchanged-code measurements or silently assigned zero time. Their target costs belong to the hardware/evaluator integration, not a request for Peter to measure an accelerator he cannot run. Keep zero-device-time/zero-transfer-time placeholders labeled as prototype assumptions.

For useful first-order quantities, request each level's frontier vertex count and total visited edges. Under the sketch's semantic partition, a frontier vertex needs two row-bound values and each traversed edge yields one neighbor value. These are logical operation quantities, not guaranteed machine-load counts, transferred bytes, unique cache lines or physical DRAM transactions. Baseline compiler/IR counts and accelerator traffic must retain their own definitions.

## Profiling/helper issues to resolve with Peter

The [detailed helper findings](helper-findings.md) include controlled synthetic checks:

- The requested `--symbol` and `--threshold` are not applied to returned annotation rows.
- Instruction forms are classified as cache misses/contention/divergence without evidence establishing those causes; a store is also classified as a load miss.
- Locality threshold labels describe same-block membership while computing adjacent-distance proximity.
- Unsupported counter strings can reach numeric division and raise `TypeError`.
- The skill names the historical v0.1 workload schema, which cannot validate the received schema-1.1 report layout.

These checks concern the current helper implementation. They do not establish how the historical report numbers were obtained or invalidate all previously supplied observations. The skill still usefully describes the intended collection workflow. The helper scripts and received reports remain unchanged by this audit.

## Ownership and later refinements

| Owner | Next responsibility |
|---|---|
| Peter | Restore scoped cost attribution, fix helper labels/options/error handling, export a bound run/level table and raw evidence references. Coordinate IR coverage with Yan-Ru. |
| Josh | Agree on a small supplement, consume it without mixing units/scopes, and bind the proposed source/IR split to candidate regions. Our current normalizer ignores new region-cost fields until explicitly adapted. |
| Yan-Ru | Supply/reuse fine-grained IR/region statistics and evaluator accounting, measure or model newly introduced work, preserve correctness/evidence boundaries. |
| Eric / evaluator team | Accelerator cycles/latency, queue/tile legality, memory-route behavior, transfer/synchronization cost, parameterized area and calibrated performance models. |

Once the minimal handoff works, useful optional signals include degree distributions, zero-degree frequency, per-window unique lines/bytes, duplicate targets, reuse with defined scope, and dependencies between simultaneous access chains. Synthetic deeper-indirection/multiple-access examples can extend coverage; they are not required to finish the existing BFS sketch.

The [small supplement template](feature-supplement.template.yaml) is a discussion example with null values, not an agreed schema or profiler output. It is deliberately separate from the unchanged v1.2 inputs and is not accepted by the current pipeline as measured data. LANL's eventual exchange format may supersede it.
