# Lossless DX100 debug transport

Interface prepared: 2026-09-26 (Eastern Time). No new simulator execution is implied.

An execution may explicitly request `verification.trace_transport: gem5-gzip.v1`.
Omission preserves the historical merged plain log. The opt-in adds only gem5's
native `--debug-file=<execution>/simulation/roi-debug.trace.gz`; it preserves every
enabled debug flag and byte of the debug stream. Model, guest binary, graph, source,
ROI, correctness obligations, and budgets remain unchanged. Plain stdout retains
guest/verifier/region-counter markers and remains their authoritative source.

The pinned model `e4fc4afdf894f295442cef3604667a469fab8e62` declares `--debug-file`
and the `.gz` suffix in `src/python/m5/main.py:298–301`, invokes `trace.output` at
line 613, and selects gzip in `src/base/output.cc:231`. These are source observations,
not a new runtime proof. Switching to the post-ROI syscall trace does not close the
previous stream; normal process teardown closes it. Truncated or corrupt gzip output
cannot establish complete coverage, even if plain stdout contains PASS.

The evaluation records `context.debug_trace` and the same reference in each
coverage observation, using `swdb.dx100.debug-trace.v1`: absolute compressed path,
compressed SHA-256 and byte count, uncompressed stream SHA-256 and byte count, and
line count. Streaming collection verifies the gzip checksum and completion, retains
all bytes including unused debug messages, and writes no decompressed artifact.
Coverage locations distinguish stdout from debug-stream line numbers. Replay
reopens both identities; it cannot attach the new transport to historical output.

The explicit transport is artifact/collector provenance, outside the frozen
semantic instrumentation map. The pinned implementation changes the host output
stream, with no modeled event or tick scheduling. Debug flags, producer, verifier
runtime, model, guest, and ROI identities retain their exact existing validation;
no protocol record or prior execution is rebound or modified.
No compression ratio, runtime improvement, or feasibility is assumed. Actual
compressed storage remains inside the same existing storage limits and all reading
uses the caller's existing time allowance. Failed prior executions remain failed.

The series client exposes the same opt-in as `--trace-transport gem5-gzip.v1`.
Its driver receipt retains `trace_transport` only when selected, so the parent can
bind the explicit child treatment to its requests. It is absent by default and does
not alter fixed plans or start an attempt.

Validation recorded on 2026-09-26: the actual pinned gem5 EmptyRoot smoke
`bfs-gem5-gzip-transport-20260926-a1` produced a complete 190-byte decoded trace
(event at tick 1), switched to a separate plain trace (event at tick 2), and exited
normally. Its terminal audit is
`/data/yanruj/EvolveSWDB_runs/bfs-gem5-gzip-transport-20260926-a1.dispatch/terminal-validation.json`,
SHA-256 `fc478833e8b93b6f373d0dba49192f40e3f7f01d95c6b1538ab3d42dcc0f70b5`.
This ran no System, CPU, guest workload, or BFS. It proves native transport and
closure only; its sampled RSS did not observe the short-lived direct gem5 child.

Replay also binds the trace to the retained simulation command's exact debug-file
path and unchanged debug flags. Profiles retain trace references in execution and
raw-artifact entries; package assembly/query, correctness/comparison admission,
and freeze/coverage readers reopen the complete stream. An empty non-gzip file,
malformed DEFLATE, invalid UTF-8, truncated stream, checksum mismatch, changed
compressed/decoded identity, or a line exceeding the 1 MiB reader bound fails
closed. The reader hashes every decoded byte before interpreting supported events.

Execution, profiling, package assembly, and qualification can each rescan a large
trace. These costs still consume their existing bounded allowances. Native gzip
support and the small fixture tests do not establish that a BFS workload will fit
its time or storage bounds. No failed prior attempt is resumed by this interface.
