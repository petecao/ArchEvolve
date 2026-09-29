# 06 — Discover expensive BFS functions through a public profiling query

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** slice
**Status:** resolved
**Blocked by:** 03
**Spec:** [BFS profiling, rewrite proposals, and hardware-aware evaluation](../spec.md)

**Execution authorization (2026-09-25):** The user explicitly authorized autonomous implementation, builds, installations, benchmark/simulator runs, remote access, Git, and Claude Code. The earlier publication-only hold is lifted; ticket dependencies and host resource rules still apply.

**Progress (2026-09-25):** Claimed for the shared automatic source discovery and diagnostic collector. Ticket 03 has real native acceptance; dependent slices remain open until their own real evidence is collected.

**Verification progress (2026-09-25):** Six local compiler/public-workflow cases passed, including actual compiled toy nested accounting and fresh queries. The first real mbit10 profile (`bfs-profile-smoke-20260925-a1.baseline-profile`) failed closed because standalone libclang did not discover the system C++ headers. Its durable failure metadata is retained in Git commit `80d3220fdd7dc20207bbc0ef826de8d91ae0f872`; no successful regions or dynamic counts were fabricated. The collector now resolves the actual compiler's header search paths explicitly. Real acceptance remains open pending the next bounded attempt.

**Additional verification (2026-09-25):** Attempt `bfs-profile-smoke-20260925-a2.baseline-profile` failed closed on GCC-only prefix `__restrict__` syntax; metadata is retained in commit `82868c6a6d568076d63da0b690d6bbe7d51a386a`. The metadata parser now explicitly erases that qualifier for GCC inputs, without changing source bytes or executable compiler settings and without inferring alias semantics. A complete pinned DX100 translation-unit check has zero parser diagnostics locally (11 functions, 20 loops); real collection still requires another bounded mbit10 attempt. Future generated sources and binaries use a unique build directory under `/data1/yanruj`, with raw logs/results kept in `/data`.

## What to build

Extend the native BFS profiling/query path to discover and rank expensive functions in BFS and its helpers from execution evidence, then return source context for those functions. A manually maintained list of kernel symbols may be a hint but cannot determine the complete set of eligible functions. Keep this slice focused on function attribution; loop discovery follows separately.

## Scope and spec references

This slice delivers the function portion of AC02 and contributes AC03 and AC13 through D03–D05 and D11. It uses the durable native evaluation behavior from ticket 03. Function-only output is an intermediate profiling result, not a claim that all loop or dynamic-memory requirements of an accepted profile package are complete.

## Acceptance criteria

- [x] A public profiling request binds exact implementation/source/binary, graph and traversal sources, native target, thread count, and ROI; the returned ranking identifies that same execution context.
- [x] Real native BFS profiling discovers functions and relevant helpers without a person first supplying their names as a required symbol catalog or adding source annotations.
- [x] The query ranks attributable function contributions using a stated metric, units, and scope, distinguishing inclusive and exclusive contributions rather than summing nested work twice.
- [x] Each resolved entry links to the correct source snapshot, location, function context, relevant callers/helpers, and access to the buildable application context.
- [x] Inlined, outlined, unresolved, or otherwise unattributed work is handled explicitly according to observed collector limits; partial coverage is not described as an exhaustive application bottleneck.
- [x] Separately instrumented or diagnostic executions identify their artifact differences and overhead treatment; their runtime does not silently replace primary native ROI timing.
- [x] A later public query retrieves the evidence and source associations, while a mismatched or stale request produces an explicit response instead of reusing another workload's ranking.
- [x] Failed or incomplete collection retains available evidence and reasons without producing a fabricated successful ranking or pre-freeze gain claim.

## Verification

Exercise public profile/query and fresh-process retrieval using a real native BFS execution after authorization. Confirm that an eligible helper not supplied in the initial catalog can appear from actual evidence. Small external collector fixtures may check output interpretation and unresolved-coverage behavior but do not prove discovery. Use the existing native path; do not require simulator availability to complete function discovery.

## Dependencies and boundaries

Ticket 03 provides native execution identity, correctness/diagnostic context, and durable results. Loop attribution is ticket 07, actual memory observations ticket 08, and accepted package assembly ticket 09. DX100-specific collection is a later backend slice. The deliverable as a whole covers both sources, but this ticket does not acquire a hidden dependency on DX100 bring-up or expand into a general application/language profiler.

## Answer

Resolved 2026-09-25 (Eastern Time) from real mbit10 diagnostic execution, independent of the invalid memory observations in the same attempt.

The public `bfs-profile` and `bfs-hotspots` path now discovers current source functions with libclang, instruments nested source scopes, and ranks accumulated exclusive function thread CPU seconds. Exact candidate/source, primary and diagnostic binaries, graph, ordered sources, thread count, lane, compiler, and complete-call ROI bindings are retained. Inclusive counters remain separate; diagnostic CPU time is not primary wall time, and instrumentation overhead is included.

Actual evidence is `bfs-profile-smoke-20260925-a3.baseline-profile` (11 functions and 20 loops) and `bfs-profile-smoke-20260925-a3.changed-profile` (12 functions and 22 loops), collected in lane 1 generation 380 at checkpoint `5790e8d5338a958a9a5db861b9bae52ed97e2f41`. The normal public patch/candidate/evaluation path introduced `SWDBDiscoveredHelper`, absent from the baseline catalog. The candidate's primary evaluation passed all three independent checks for sources `[0, 3, 8]`; the separate region executions also passed all three. The helper ranked first with three calls and 0.006454273 accumulated exclusive function thread CPU seconds. Its source and callers/helpers were returned without requiring its name as a discovery input.

The changed region binary is `82a31660bdda9a1a9c197753b05358df789fe05dc2f31263864147a5ed78a69c`; candidate artifact is `e6e789e6942776ad88cbc3ba8377d09be8f8b8eee63e511230d7a9957a2490fd`; primary binary is `e7db1f8531ddbd675ec5874acade25a35e675bd782e1967e8243b2322e46027a`. Fresh-process queries recovered the ranking and chain. Metadata was retained in remote commits `cd3ed062f68916dd56663e4a76623bbba72b6fae` and `3a8f8c372cba18c7cc5b8d46f4ec4fe9bd7afc02`, imported by parent checkpoint `dc12a01`. Raw diagnostics remain under `/data/yanruj/EvolveSWDB_runs/bfs-profile-smoke-20260925` on mbit10.

Coverage is explicitly partial: header/library/member/outlined scopes are excluded, and the unsafe continued OpenMP pragma at source line 189 remains unresolved. Earlier a1/a2 parser failures remain retained. The separately collected a3 memory counters failed a later unsigned-underflow audit; that entire observation family is invalid and does not satisfy Ticket 08 or 09. This answer accepts only independently valid function attribution. There is no gain claim.
