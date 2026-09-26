# DX100 execution-derived profile collection

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)

`dx100-profile REQUEST --runs-dir DIR --format json` retains a `region_profile` and attaches exact simulated ROI timing to the selected evaluation. The request contains `message_version: '1.0'`, a new `id`, `evaluation`, `discovery_profile`, and `budget: {total_seconds: 60}`. The maximum collector budget is 600 seconds. The referenced compiler discovery must identify the same candidate; every returned source extent is checked against the current candidate bytes. Native timing observations are discarded rather than copied to the simulated profile.

The collector reopens hashed statistics, log, and actual configuration files. It reads complete intervals, selects the first guest dump, records its exact line range and number of intervals, and requires a sealed verification file to contain only that interval. Duration is `simTicks / simFreq`, with raw ticks, frequency, and resolved SrcClockDomain periods retained. The author parser's fixed divisor 313 is not a general conversion. Malformed intervals, stale files, unsupported clock values, and exhausted collection budgets retain explicit failed or incomplete outcomes.

Available cache access/hit/miss totals and MAA cache-side/memory-side packet counts become dynamic memory observations. Each names its model counter, unit, definition, collector, simulated basis, exact interval and raw hash, and entire-BFS-ROI attribution. Packet counts do not become element counts or loop-specific measurements. Missing counters remain unavailable and prevent complete packages.

The pinned cache implementation names its all-command-region totals
`overallAccesses_T::total`, `overallHits_T::total`, and
`overallMisses_T::total`. The collector recognizes these exact total suffixes
and retains generic unsuffixed totals for compatible fixtures. Numbered buckets
such as `overallAccesses_7::total` are excluded because their command-region
identity does not establish whole-ROI or source-loop attribution. BASE execution
can therefore provide actual cache observations without any MAA packet counter.

Primary `td`/`td_maa` logging can associate accumulated inclusive Start-to-Stop observations with a compiler-discovered enclosing traversal loop. These timer intervals include called work, queue advancement and any logging between their endpoints; their printed resolution is 0.00001 seconds. They do not establish exclusive time or the duration of every function/loop. `td_maa` is not evidence of acceleration because the author prints it even on scalar fallback. This logging-only route returns `partial`.

For complete source-scope attribution, `dx100-compile` accepts `diagnostic_regions: true` and optional `discovery: {library: PATH, resource_dir: PATH}`. The shared compiler discovery receives the actual GEM5/DMAA build flags and compiler-reported system header order. User-supplied preprocessor overrides are excluded. Its ordinary functions and loops receive nested scope guards using `m5_rpns`; generated source, runtime, and binary live under `/data1/yanruj/EvolveSWDB_builds/ID` on mbit10. Logs and discovery receipts remain in the chosen raw folder.

The current compile contract preserves the pinned model interface under
`include`, `util/m5/src`, and `benchmarks/API`, including utility and extensionless
headers. Candidate copies must match those inputs exactly, and basename shadows
are rejected. These include paths select the pinned model copies; accepting a
changed candidate copy would silently compile different code from the proposed
interface change. Application helpers outside this interface remain editable.
Changing the model API requires a separately supported operation contract.

Run that separate diagnostic binary through `dx100-execute`, then supply its ID as `diagnostic_evaluation` instead of `discovery_profile` in the collector request. It must match the primary candidate, graph, source, threads, modeled configuration, and semantic ROI exactly. Inclusive/exclusive simulated seconds are elapsed intervals accumulated per executing thread, including waits and overlap. Exclusive attribution subtracts only nested guarded intervals on that thread; neither quantity is CPU service time or a replacement for primary BFS duration. Invocations retain the shared discovery engine's function-call, loop-entry, or OpenMP-worker-iteration units. The report is emitted only after the ROI seal. Invalid nested accounting, changed source/binary/runtime, missing reports, and incompatible contexts fail explicitly.

The profile identifies separate region and memory executions: source scopes use the diagnostic binary, while ROI-wide memory counters use the primary binary. Every observation retains source artifact, binary, output, and raw-statistics hashes. Instrumentation overhead and unresolved scopes remain explicit. Collection completeness and structural correctness are separate fields; unverified collection cannot establish a gain.

The unchanged author baseline also supports a separate diagnostic compile with
`roi: bfs.dx100.traversal.v1`. This requires `diagnostic_regions: true`, a
`source_baseline` candidate whose code matches the pinned model, and the exact
identified `DOBFS` or `DOBFSMAA` function. The generated wrapper forwards the
author's internal m5 events; its `internal_event_hooks` activate source guards
at reset and deactivate them at dump. The receipt uses adapter
`dx100.author_roi_diagnostic.v1`, while the primary author executable stays
unchanged. A scope entered before activation, including the enclosing BFS
function, has `observation_state: unobserved`, an `unavailable_reason`, and no
inferred duration. The original returned parent array and counters are checked
after the same guest's ROI exit is sealed and continued. These diagnostics
cannot be substituted for the author's primary timing.

Correctness remains independent. Collection can retain an unverified real evaluation, and a fixture remains `contract_fixture` throughout. Nothing in collection promotes a candidate, infers a neutral speedup, or enables a gain claim. Exact candidate, source snapshot, binary, workload, source vertex, target/configuration, and actual clock remain part of the retrievable evidence.
