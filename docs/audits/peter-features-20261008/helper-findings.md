# Profiling helper findings

Scope: the extraction skill/scripts on main at the audit commit, plus the received v1.2 files. [helper-checks.json](helper-checks.json) records synthetic observations and exact source hashes. `check_helpers.py` mocks every subprocess call; no perf command or benchmark runs.

## Fix before using the output for quantitative offload accounting

| Finding | Evidence | Effect and requested correction |
|---|---|---|
| Symbol filter is unused | `run_perf_record_annotate`, [lines 72–91](../../../.agents/skills/extract-kernel-features/scripts/parse_perf_profile.py#L72), never uses `symbol`; the parser does not track function identity. | Synthetic unrelated-function instructions survive a `TDStep` request. Select/report actual symbols including OpenMP outlined and inlined work, and retain symbol/DSO identities. The returned `target_symbol` field alone is not proof of filtering. |
| CLI threshold is unused | [Lines 145–178](../../../.agents/skills/extract-kernel-features/scripts/parse_perf_profile.py#L145): argument is printed but not passed to `parse_annotate_output`, whose default is 1.0. | With synthetic `--threshold 30`, rows at 12, 18, 22 and 25 are still returned. Honor the setting; preserve excluded mass/raw counts for accounting. |
| Sample denominator is absent | `perf annotate --stdio` is invoked without recording percent type; rows retain only a percentage/address/instruction/free-text context. | Record local/global scope, period/hit basis, event, total samples/periods, run and ROI. Do not add local symbol percentages across functions or convert them directly to wall time. |
| Mnemonic labels overstate diagnosis | [Lines 122–131](../../../.agents/skills/extract-kernel-features/scripts/parse_perf_profile.py#L122) infer contention from `lock cmpxchg`, a miss from any memory `mov`, and divergence from any jump. | Synthetic `mov %eax,(%rdx)` is a store but is labeled `INDIRECT_LOAD_MISS`; unconditional `jmp` becomes `BRANCH_DIVERGENCE`. Emit instruction/access shapes separately from causal hypotheses, with supporting counters or other evidence when available. |
| Unavailable PMU values are not typed | [Lines 40–68](../../../.agents/skills/extract-kernel-features/scripts/parse_perf_profile.py#L40) can retain strings and then divide by them. | Synthetic `<not supported>` cycles causes `TypeError`. Carry `unsupported/not_counted/permission_error` states, null derived values and raw diagnostics; do not manufacture zero counters. Preserve count units and running/enabled/scaling data. |
| Raw evidence and run correspondence are incomplete | The helper runs `stat` and `record` separately and returns a combined JSON, but retains no raw stat text/annotate output references, run IDs, timing denominator or correspondence record. | Save raw outputs and statuses; distinguish the two invocations. A common command does not establish the same root/trial, cache state or phase. `cycles:pp` availability also needs an explicit collection outcome. |
| Old validation target | [The skill](../../../.agents/skills/extract-kernel-features/SKILL.md) says to validate with `schemas/workload.schema.json`; [that schema](../../../schemas/workload.schema.json) fixes version `0.1` and requires the old workload/pattern layout. | Received reports use schema `1.1` with `kernel`, `memory_streams`, etc. Agree on the actual adapter/validation contract; do not claim these reports pass the old schema. No new formal DSL is needed. |

The [Linux v5.15 perf-annotate documentation](https://raw.githubusercontent.com/torvalds/linux/v5.15/tools/perf/Documentation/perf-annotate.txt) explicitly distinguishes local/function versus global/data scope and sample-period versus hit-count percentages. Those are sample-attribution choices, not an automatic elapsed-time measurement. The audit does not infer an unspecified default from the reports.

The current wrapper measures the whole supplied command without an explicit kernel ROI gate. That scope may include graph construction, verification and several BFS trials. The report's average trial duration therefore needs a separate ROI/run binding before it can be combined with sample or counter shares.

## Locality interpretation

[The locality helper, lines 21–40](../../../.agents/skills/extract-kernel-features/scripts/calc_stride_locality.py#L21), computes absolute adjacent-index distance and threshold percentages. Two aligned-base examples demonstrate why its current field names are misleading:

| Indices, 4-byte elements, base 0 | Byte addresses | Helper label/value | Actual relation |
|---|---|---|---|
| `[15,16]` | 60, 64 | Same-64B-line: 100% | Different 64-byte lines. |
| `[1023,1024]` | 4092, 4096 | Same-4KB-page: 100% | Different pages. |

Keep these as **adjacent-pair proximity** metrics with exact threshold/units/scope, or compute membership from appropriately bound addresses and block IDs. Neither membership nor proximity is a cache-hit rate. Mean jump alone also cannot establish cache thrashing, TLB miss rate, DRAM row locality or the necessity of a hardware reorder buffer.

The current CLI returns no meaningful adjacent-pair statistic for fewer than two valid entries: the function returns null, but the printing path indexes it. It also silently drops non-digit lines. Record empty/one-entry/invalid-input status and rejected counts. Keep row/frontier/thread boundaries in traces so concatenation does not change a within-segment statistic into a different one.

Our existing normalizer already relabels the hash-bound historical locality reports using Peter's methodology. The concern here is preventing the new extraction skill from reintroducing the older interpretation.

## Cleanup of existing prose (not missing new measurements)

- The current methodology note's header/formula/code use 4-byte offsets, while a table and concluding discussion retain earlier 8-byte values. Binary/decimal unit labels are also inconsistent. Keep canonical byte counts and explicit units; do not request type widths as though the corrected v1.2 declarations were absent.
- The methodology's local links still name a DataLayoutAPI checkout, while the reports declare the DX100 revision. Reconcile the actual collection source/build or mark those links as historical; matching reported type widths does not bind an executed binary.
- Sparse `lqueue` is described as `thread_local_scratchpad`, but the pinned [QueueBuffer constructor](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/sliding_queue.h#L98) uses CPU-side `new[]`. It is not an accelerator scratchpad allocation.
- Dense graph formulas describe algorithmic phases. They do not establish measured elapsed cost for each phase; second-phase zero CAS does not remove first-phase CAS from the kernel.

The assembly-classification examples and exception are synthetic diagnostic results, not evidence of measured application bottlenecks. The audit proposes fixes; it does not edit Peter's helpers or reprofile the benchmark.
