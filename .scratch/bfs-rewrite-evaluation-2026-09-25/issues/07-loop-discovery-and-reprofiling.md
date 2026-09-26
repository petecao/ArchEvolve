# 07 — Discover BFS loops and rediscover changed hot regions

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

## What to build

Extend public hotspot discovery from functions to loops inside BFS and its helpers, and demonstrate that reprofiling a real changed BFS candidate finds expensive work absent from the baseline catalog. Associate observations with current source, including changed or split/fused regions, without copying stale baseline region properties. Region timing is diagnostic evidence with declared scope; it does not independently establish an overall BFS gain.

## Scope and spec references

This slice completes the discovery behavior in AC02–AC03 and contributes AC13 through D03–D05 and D11. The native proposal/evaluation path is already available through ticket 06's prerequisites. A manually added region annotation must not be required to make the changed-code case discoverable.

## Acceptance criteria

- [x] A public native BFS profiling query discovers and ranks attributable loops within BFS functions and helpers without mandatory manual loop annotations.
- [x] Loop output identifies the current source/binary, containing function and source context, contribution metric, units, and whether timing is per invocation or accumulated across the BFS execution.
- [x] Inclusive/exclusive attribution and unresolved work remain explicit across nested functions and loops, without double-counting their reported contributions.
- [x] A real BFS candidate introduces expensive work in a helper or loop absent from the baseline catalog; after the normal candidate/evaluation path, reprofiling discovers, locates, and ranks that work without a person first adding it to the catalog.
- [x] Reprofiled observations reference the candidate artifact rather than the baseline. Removed or changed regions do not retain unsupported baseline timing, access-pattern, or semantic assertions.
- [x] Changed, split, or fused regions have explicit correspondence when one can be established; an unresolved correspondence cannot be used to manufacture a region speedup.
- [x] Fresh-process queries recover both baseline and candidate rankings and the available correspondence, including differences between BFS-level and region-level observations.
- [x] Collection failure or incomplete source attribution remains a retained partial outcome. Diagnostic runs performed before protocol freeze do not become candidate gain claims.

## Verification

Use the public patch-to-candidate, native evaluation, profiling, and retrieval path with actual changed BFS/helper code after authorization. The new-region discovery example must execute real code; canned profiler output alone cannot satisfy it. External fixtures may cover nested accounting and failed source mapping. Check observable output and artifacts, not private collector calls or internal module layout.

## Dependencies and boundaries

Ticket 06 supplies function attribution and source context; its prerequisite chain already supplies patch candidates and native evaluation. Natural-language or annotated-source workers are not required for this discovery demonstration. Memory observations and complete package acceptance arrive separately. General program extraction, full traces, and proof of every bottleneck cause remain outside this slice.

## Answer

Resolved 2026-09-25 (Eastern Time) from real changed-source rediscovery, independent of the invalid memory observations in the same attempt.

Automatic source scopes now cover ordinary loops and eligible OpenMP iteration bodies within discovered BFS functions/helpers. Public rankings state accumulated thread CPU seconds, inclusive/exclusive accounting, invocation units, current source extents and hashes, containing functions, and exact diagnostic artifact identity. Fresh candidate instrumentation supplies all observations; only identical unambiguous fragments within a containing function receive correspondence, and changed/split/fused/removed fragments inherit neither measurements nor semantics.

The real public changed-helper demonstration in `bfs-profile-smoke-20260925-a3.changed-profile` followed proposal `bfs-profile-smoke-20260925-a3.proposal` and the independently checked primary evaluation `bfs-profile-smoke-20260925-a3.evaluation` (three sources `[0, 3, 8]`, three passes). The baseline had 31 discovered scopes; the candidate had 34. `SWDBDiscoveredHelper` at lines 313–319 and two nested loops were discovered without annotations or a name catalog. The outer loop at lines 315–317 ran three times with 0.003185478 exclusive CPU seconds; the inner loop at lines 316–317 ran 6000 times with 0.003264096 exclusive CPU seconds. Fresh-process queries ranked and retrieved both loops, the new rank-1 helper, and source/build context. Thirty unchanged fragments received correspondence; four current fragments and one previous fragment remained explicitly unresolved.

The changed source artifact is `e6e789e6942776ad88cbc3ba8377d09be8f8b8eee63e511230d7a9957a2490fd`, and the region binary is `82a31660bdda9a1a9c197753b05358df789fe05dc2f31263864147a5ed78a69c`. Metadata from commits `cd3ed062f68916dd56663e4a76623bbba72b6fae` and `3a8f8c372cba18c7cc5b8d46f4ec4fe9bd7afc02` is imported by parent checkpoint `dc12a01`; raw evidence remains on mbit10 under `/data/yanruj/EvolveSWDB_runs/bfs-profile-smoke-20260925`.

Local compiler/public integration cases cover nested scopes, single-statement loops, changed source hashes, retained discovery failures, and stale evaluation rejection. Coverage remains partial, including the unresolved continued OpenMP pragma at line 189 and excluded header/library/outlined scopes. All loop quantities are diagnostic, separate from primary complete-call wall time. The a3 memory family is explicitly invalid after its unsigned-underflow audit; Tickets 08 and 09 remain unaccepted and no region speedup or candidate gain is claimed.
