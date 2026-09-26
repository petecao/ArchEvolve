# 08 — Return actual memory-behavior observations for BFS executions

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** resolved
**Blocked by:** 06
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

**Progress (2026-09-25):** Claimed for the shared automatic source discovery and diagnostic collector. Ticket 03 has real native acceptance; dependent slices remain open until their own real evidence is collected.

**Verification progress (2026-09-25):** Six local compiler/public-workflow cases passed, including actual compiled toy nested accounting and fresh queries. The first real mbit10 profile (`bfs-profile-smoke-20260925-a1.baseline-profile`) failed closed because standalone libclang did not discover the system C++ headers. Its durable failure metadata is retained in Git commit `80d3220fdd7dc20207bbc0ef826de8d91ae0f872`; no successful regions or dynamic counts were fabricated. The collector now resolves the actual compiler's header search paths explicitly. Real acceptance remains open pending the next bounded attempt.

**Additional verification (2026-09-25):** Attempt `bfs-profile-smoke-20260925-a2.baseline-profile` failed closed on GCC-only prefix `__restrict__` syntax; metadata is retained in commit `82868c6a6d568076d63da0b690d6bbe7d51a386a`. The metadata parser now explicitly erases that qualifier for GCC inputs, without changing source bytes or executable compiler settings and without inferring alias semantics. A complete pinned DX100 translation-unit check has zero parser diagnostics locally (11 functions, 20 loops); real collection still requires another bounded mbit10 attempt. Future generated sources and binaries use a unique build directory under `/data1/yanruj`, with raw logs/results kept in `/data`.

**Counter audit (2026-09-25):** Real attempt a3 completed region collection, but its final numeric audit rejected all Callgrind memory observations: the summary contained unsigned-wrap values near 2^64, while self-cost totals were ordinary counts. The original values and raw hashes remain in master records with an explicit invalid-memory audit (imported checkpoint `dc12a01`). Official Valgrind 3.22 source identifies the cause: stopping instrumentation resets current costs before the dump subtracts its nonzero last-dump baseline. The corrected collector dumps before stopping, selects only explicit client ROI dumps, and rejects underflow, summary/self-cost inconsistency, and impossible miss hierarchies. Public queries/packages invalidate entire historical execution groups. A bounded one/four-thread control probe and fresh profiles of the retained valid primary evaluations are required before this ticket can resolve; no a3 memory number is accepted.

**Control experiment (2026-09-25):** The real one/four-thread control passed in mbit10 lane 1 generation 383 at `6f7730d27cf0cede9b35dce5c55267618bbd9e21`. Both old-order runs reproduced unsigned underflow; corrected-order runs passed all consistency checks and the expected checksum. Corrected one-thread `Dr`/`Dw` were 66425/66066; four-thread values were 1202462/67654 (OpenMP runtime activity is included, so these are not a scaling comparison). The derived [control evidence](../../../docs/evidence/bfs-callgrind-roi-20260925-a1.yaml) was imported as `4d83ef5`; all raw output remains on mbit10. This control establishes the fix's collector behavior, not real BFS memory acceptance, which still requires fresh baseline/candidate profiles.

## What to build

Extend the public BFS profiling result with actual execution- or simulation-derived memory observations, such as access counts or cache behavior. Deliver at least one supported observation family and expose unsupported metrics honestly. Tie observations to the particular source/binary and workload, including any separately instrumented diagnostic artifact, so an ensemble can distinguish observed memory behavior from static access-pattern descriptions and inferred explanations.

## Scope and spec references

This slice contributes AC04, AC09, and AC13 through D03–D05, D11, and D14. It does not require unavailable native hardware counters, full address traces, or multiple new collection systems. Counter-free execution observations or a supported memory model are acceptable when their basis and limits are explicit. DX100-specific collection follows in the simulator profiling slice.

## Acceptance criteria

- [x] A real BFS execution or supported diagnostic simulation produces at least one actual memory-behavior observation retrievable through the public profiling/query interface.
- [x] Each observation states its definition, units, collector/model identity, source/binary and workload identity, collection scope, attribution granularity, and evidence basis.
- [x] ROI-wide observations are not presented as measurements of individual loops or functions. Static formulas or source-derived access patterns are not relabeled as dynamic observations.
- [x] Unsupported, missing, or failed metrics and uncertain bottleneck explanations are explicit; a result with every dynamic memory metric unavailable cannot claim complete memory profiling.
- [x] Model-derived cache observations are labeled simulated and are not described as native hardware measurements. Actual counts are distinguished from inferred values.
- [x] If profiling uses a different instrumented artifact or execution, the result records that difference and its relationship to the timed artifact; diagnostic runtime cannot replace primary ROI timing.
- [x] Profiling a changed candidate collects fresh observations linked to that candidate. A fixed source-order graph traversal is not substituted for the actual BFS frontier order when claiming dynamic index behavior.
- [x] Successful and partial observations survive fresh-process retrieval, with raw-artifact references and failure reasons; missing evidence is not converted into a neutral performance result.

## Verification

Drive public native execution/diagnostic profiling and retrieval after authorization, retaining actual collector output for a small BFS case. Use deterministic external collector fixtures only to check parsing, evidence labels, scope, and unavailable-output behavior. Those fixtures do not satisfy the real-observation criterion. No pre-freeze gain claim or DX100 installation is required by this slice.

## Dependencies and boundaries

Ticket 06 provides execution-bound function/source context. Loop discovery is not a prerequisite because correctly scoped ROI/function observations can be useful independently. Ticket 09 assembles complete profile packages; this slice must not claim that an incomplete package meets that later gate. Choose the supported collection method during implementation design without broadening the task into full tracing or causal proof.

## Answer

Resolved 2026-09-25 (Eastern Time) from corrected real BFS diagnostics, with the earlier invalid observations preserved.

The public `bfs-profile` / `bfs-hotspots` path now returns actual Callgrind 3.22.0 data-reference events and modeled cache misses for the complete BFS call. Every observation binds the current source artifact, separate memory binary, primary evaluation/binary, canonical graph, ordered source position, repetition, thread count, and ROI. The explicit model is I1 32768/8/64, D1 49152/12/64, and LL 25165824/12/64 (bytes/associativity/line bytes), initially cold. `Dr`/`Dw` count instrumented data references; `D1mr`/`D1mw` and `DLmr`/`DLmw` are simulated misses, all scoped to the whole ROI. No hardware-counter, address-trace, per-loop-memory, source-order-traversal, or causal-bottleneck claim is made.

Actual corrected records are `bfs-profile-smoke-20260925-a4.baseline-profile` and `bfs-profile-smoke-20260925-a4.changed-profile`, collected at checkpoint `c4788fb0295bf624b36308d1fd6338f3a4899700` in lane 1 generation 385 (21:04–21:20 ET). Each profile has six independently checked diagnostic executions—three region and three memory executions—and 18 available, validated memory rows. Sources are `[0, 3, 8]`, one repetition and one thread. This is a real compiled BFS traversal on a ten-vertex diagnostic graph, not pilot performance evidence.

| Source | Baseline Dr | Baseline Dw | Changed Dr | Changed Dw |
|---|---:|---:|---:|---:|
| 0 | 8468 | 5753 | 54474 | 25757 |
| 3 | 6671 | 4594 | 52677 | 24598 |
| 8 | 4891 | 3438 | 50897 | 23442 |

The changed candidate genuinely executes `SWDBDiscoveredHelper`; fresh queries ranked it first and found both executed nested loops. The changed source artifact is `e6e789e6942776ad88cbc3ba8377d09be8f8b8eee63e511230d7a9957a2490fd`. Its primary binary is `e7db1f8531ddbd675ec5874acade25a35e675bd782e1967e8243b2322e46027a`, whereas its separately instrumented memory binary is `f2ddd8aa05c335b66907e27f5b6d88b7d2aadb611a4d4efdbe7cc90a32afd847`. The baseline memory binary is `20ebc23ffca71766cdf31c2a65e0efa9ebc8cd5622d467f721eab18ba3482e6c`. Diagnostic runtime never replaces primary complete-call wall timing.

Both profile families passed independent raw-artifact hash checks, strict parsing, summary/self-cost consistency, and cache-miss hierarchy checks after collection. The public driver completed with exit 0, retrieved eight chain records, and retained `gain_claim: false`. Metadata commit `5ea41132ac0f17b1ecb119cdaba4de3791c2dd0d` on `codex/bfs-profile-evidence-20260925-a4` contains only the two profile records; all 108 records validated before sync. Raw files remain under `/data/yanruj/EvolveSWDB_runs/bfs-profile-smoke-20260925` on mbit10, with diagnostic sources and binaries under `/data1/yanruj/EvolveSWDB_builds`.

Source attribution still reports explicit partial coverage; it does not prevent this independently complete supported memory family. Earlier a1/a2 collection failures and a3's invalid unsigned-wrap values remain retained. The [real one/four-thread control](../../../docs/evidence/bfs-callgrind-roi-20260925-a1.yaml) reproduces the old failure and validates the corrected dump-before-stop order. Historical query/package guards exclude inconsistent observations without deleting their original values. Local compiler/public workflow and parser regressions cover failure retention and invalid-count handling; actual acceptance comes from the corrected a4 executions above. Package assembly remains Ticket 09.
