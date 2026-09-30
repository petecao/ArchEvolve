# Offline BFS exploration

**Rule-based prototype: no LLM calls, no benchmark execution, and no evaluated speedups.**

Each case is normalized separately. The original reports are retained unchanged. The catalog is a provisional seed from Eric's taxonomy; its hardware partitions/ports have not been reviewed as implementations.

| Case | Selected for exploration | Results |
|---|---|---|
| gapbs_bfs_top_down_step | cpu-baseline, indirect-prefetch-family, declared-gather-family | [Diagrams](case-01/diagrams/README.md), [normalized input](case-01/normalized.yaml), [request YAML](case-01/hardware-request.yaml), [selection trace](case-01/selection-trace.yaml) |
| gapbs_bfs_top_down_step_fully_connected | cpu-baseline, stride-prefetch-family, declared-bulk-read-family | [Diagrams](case-02/diagrams/README.md), [normalized input](case-02/normalized.yaml), [request YAML](case-02/hardware-request.yaml), [selection trace](case-02/selection-trace.yaml) |

## Input findings

### Case 1

- **needs_clarification:** Profiling provenance is supplied and retained as reported context. Raw artifacts, exact collection/ROI boundaries and cross-trial correspondence remain unverified; no measurements were reproduced locally.
- **interpretation_resolved:** The reported per-level scope is preserved separately from the command/counter context. No counter values are apportioned to levels, and no level means are aggregated across trials.
- **interpretation_resolved:** A frontier with fewer than two entries has no adjacent pairs. The reported mean remains in the raw section, but its analysis value is null rather than a measured zero-distance observation.
- **interpretation_resolved:** Peter's instrumentation measures adjacent-index proximity, not same cache-line/page membership or cache-hit rates. Values are relabeled descriptively and remain outside selection rules.
- **interpretation_resolved:** Peter confirmed capacity-based array footprints. Exact bytes and decimal/binary conversions are derived separately; active tile/phase working sets remain unknown and do not fix storage parameters.
- **needs_clarification:** This report includes several graph scales without binding each statistic to a run. Do not transfer values between scales.
- **needs_clarification:** Array-level features are usable for exploratory retrieval; exact statement IDs and profiled-source locations are still absent.
- **interpretation_resolved:** The snippets enumerate adjacent positions within frontiers/rows, excluding segment transitions and thread interleaving; they do not establish a global hardware-access trace. VertexOffsets: adjacent_positions_within_each_frontier; parent: adjacent_neighbors_within_each_vertex_row
- **needs_clarification:** Some reported footprints do not use the claimed binary conversion. Original numbers are preserved; exact byte-derived values are separate.

### Case 2

- **needs_clarification:** Received values are reported; raw profiling logs, build flags, dataset identity and per-run scope have not been bound/verified by this prototype.
- **needs_clarification:** Retain conditional CAS for the kernel. A reported zero-execution second phase does not remove the discovery-phase update.
- **interpretation_resolved:** Peter's instrumentation measures adjacent-index proximity, not same cache-line/page membership or cache-hit rates. Values are relabeled descriptively and remain outside selection rules.
- **interpretation_resolved:** Peter confirmed capacity-based array footprints. Exact bytes and decimal/binary conversions are derived separately; active tile/phase working sets remain unknown and do not fix storage parameters.
- **needs_clarification:** Array-level features are usable for exploratory retrieval; exact statement IDs and profiled-source locations are still absent.
- **interpretation_resolved:** The snippets enumerate adjacent positions within frontiers/rows, excluding segment transitions and thread interleaving; they do not establish a global hardware-access trace. VertexOffsets: adjacent_positions_within_each_frontier; parent: adjacent_neighbors_within_each_vertex_row

## Next handoff

Use the reported source/build context where supplied, resolve any remaining identity conflicts, and bind raw profile evidence to the relevant dataset, trial, and ROI. Have Eric review the seed capabilities and hardware I/O; Peter can then derive intrinsic specifications. Parameters remain open for tuning.
