# Memory-call preparation bridge — 2026-10-16 ET

**Source preparation and the private 53-case C11/C++17 controls pass. Public call support remains open.**

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
   `native_prepare_cases.c` is the 53-case C11/C++17
   harness: seven mappings across six dtypes, counted waits, first-ID/F2, full-line
   conflicts, and classified width/ownership/alias/pair/empty-envelope refusals.
   It binds constant roots immediately and checks preparation only. Root must
   independently review source and freshly admit compiler/runtime, ASan/UBSan,
   guards and retained results before execution. Root's V4 execution and the
   independent cold audit below satisfy that gate for this private preparation
   slice only.

Only this new directory is owned by this slice. Existing production, model,
library and tests remain unchanged. No `get_tile_ready` header operation is
invented; pinned `wait_ready` performs a blocking ready-range read. Historical
86/96-case native packets supply no acceptance for this new bridge. Public
same-thread/other-thread memory/history, region/ownership/pair acceptance, formal
IEEE/source simulation and whole ticket28 closure remain open. No current0.2
version is installed or promoted.

The native controller's first version remains **unexecuted**. Root caught a
guard-contract mismatch before launch: exact c6 exports/scans its run token but
does not export a watchdog tag or RSS-cap environment marker. The corrected
`native_entry_v2.py`, `source_policy_v2.json`, `command_v2.json` and `plan_v2.md`
have [independent source review](independent-native-entry-review-v2-20261016.md).
V2 requires the actual token and accepts an optional real inherited tag/cap
context. Root supplies the explicit 4 GiB marker; enforcement comes from the
exact c6 `--cap-gb 4` command and actual guard evidence. Fresh root admission is
still required. The 53 preparation controls do not check memory effects or
public proof behavior, and no native result is recorded by this source review.

V2 subsequently queued out before any child admission; V3 was admitted but
refused its prospective 50 GiB disk floor before compilation. Both attempts
remain preserved. Root explicitly approved a fresh V4 namespace with a 32 GiB
free floor plus the unchanged 256 MiB raw allowance; no cleanup occurred and
the compiler/test/RSS/time criteria were unchanged. V4 passed all 53 controls
in each language under ASan/UBSan. The
[independent cold result](native-cold-audit-v4-20261016.json) matched 7628 physical
input pins, 30 raw artifacts, the exact six commands and closed environment,
99 C11 and 116 C++17 used dependency files, both frozen inputs and binaries.
Guard exit 0, 3.660139 seconds, 145.141 MiB peak under 4 GiB/180 seconds; one
inspection event ended with no final inspection/cleanup failure or unconfirmed
children. Header hashes were first captured after preprocessing, and sampled
process ownership remains the recorded boundary. This completes private
preparation controls, without replacing the remaining public call/value rules
and source-call dispatch under the permitted owned MMIO semantics premise.
