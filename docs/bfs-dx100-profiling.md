# DX100 execution-derived profile collection

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)

`dx100-profile REQUEST --runs-dir DIR --format json` retains a `region_profile` and attaches exact simulated ROI timing to the selected evaluation. The request contains `message_version: '1.0'`, a new `id`, `evaluation`, `discovery_profile`, and `budget: {total_seconds: 60}`. The maximum collector budget is 600 seconds. The referenced compiler discovery must identify the same candidate; every returned source extent is checked against the current candidate bytes. Native timing observations are discarded rather than copied to the simulated profile.

The collector reopens hashed statistics, log, and actual configuration files. It reads complete intervals, selects the first guest dump, records its exact line range and number of intervals, and requires a sealed verification file to contain only that interval. Duration is `simTicks / simFreq`, with raw ticks, frequency, and resolved SrcClockDomain periods retained. The author parser's fixed divisor 313 is not a general conversion. Malformed intervals, stale files, unsupported clock values, and exhausted collection budgets retain explicit failed or incomplete outcomes.

Available cache access/hit/miss totals and MAA cache-side/memory-side packet counts become dynamic memory observations. Each names its model counter, unit, definition, collector, simulated basis, exact interval and raw hash, and entire-BFS-ROI attribution. Packet counts do not become element counts or loop-specific measurements. Missing counters remain unavailable and prevent complete packages.

Primary `td`/`td_maa` logging can associate accumulated inclusive Start-to-Stop observations with a compiler-discovered enclosing traversal loop. These timer intervals include called work, queue advancement and any logging between their endpoints; their printed resolution is 0.00001 seconds. They do not establish exclusive time or the duration of every function/loop. `td_maa` is not evidence of acceleration because the author prints it even on scalar fallback. This initial collector therefore returns `partial`, preserving useful primary ROI and memory evidence while separate diagnostic attribution is still required.

Correctness remains independent. Collection can retain an unverified real evaluation, and a fixture remains `contract_fixture` throughout. Nothing in collection promotes a candidate, infers a neutral speedup, or enables a gain claim. Exact candidate, source snapshot, binary, workload, source vertex, target/configuration, and actual clock remain part of the retrievable evidence.
