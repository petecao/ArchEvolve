# Memory-call preparation bridge — 2026-10-16 ET

**Source preparation is implemented. Public call support and native acceptance remain open.**

1. `interface_memory.py` checks five immutable source hashes and extracts the
   seven memory calls' real packet operand fields from the pinned header.
   `interface_memory_prepare.h` supplies private tile/memory preparers. The width
   projection transcribes pinned `IF.cc:66-154`; it is independently checked
   against literal masks rather than inferred from familiar template type names.
2. The bridge checks first-ID region assignment/F2, builds full physical-line
   write envelopes, and uses `dxc_prepare_counted`. Condition-only roles remain
   hazards without ready counts; an eight-byte counted role includes both halves.
   Conflicting same-ID widths and physical input/output aliases refuse. Odd
   eight-byte starts remain allowed. Pure source controls passed **16/16**;
   `pure-tests.log` records those results without compiler or backend execution.
3. Each preparer leaves **one unbound command**. Its caller must immediately
   capture/bind the deferred value/history root with no intervening source action.
   Register arguments, typed values, effects, producer/size capture and immutable
   history are not implemented by these preparers. They cannot replace whole-call
   wrappers or public source validation.
4. Geometry is a private caller-selected `DXM_TILES <= 64` domain. The header uses
   `NUM_TILES = NUM_CORES * 8`; configured geometry, ABI/type identity, source-site
   instrumentation, ownership premises, address translation and actual footprint
   coverage require separate admission. Nonempty logical/physical envelopes are
   required: zero-length streams and all-inactive commands remain outside this
   bridge even though the source can issue them and count their roles. Supplied
   physical addresses are not inferred from C object validity. Line size must be
   bound to the actual configuration. Checks must remain fatal/classified domain
   checks, including with assertions disabled.
5. `prepare_artifacts.py` reads the unmodified deferred/command/region generators
   as closed AST string data and records their hashes in `source-manifest.json`.
   `native_prepare_cases.c` is an **unexecuted** prospective 53-case C11/C++17
   harness: seven mappings across six dtypes, counted waits, first-ID/F2, full-line
   conflicts, and classified width/ownership/alias/pair/empty-envelope refusals.
   It binds constant roots immediately and checks preparation only. Root must
   independently review source and freshly admit compiler/runtime, ASan/UBSan,
   guards and retained results before running it.

Only this new directory is owned by this slice. Existing production, model,
library and tests remain unchanged. No `get_tile_ready` header operation is
invented; pinned `wait_ready` performs a blocking ready-range read. Historical
86/96-case native packets supply no acceptance for this new bridge. Public
same-thread/other-thread memory/history, region/ownership/pair acceptance, formal
IEEE/source simulation and whole ticket28 closure remain open. No current0.2
version is installed or promoted.
