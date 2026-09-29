# Automatic BFS diagnostics

Navigation updated: 2026-09-28 (Eastern Time).

Updated: 2026-09-26 (Eastern Time).

Future real mbit10 collections retain a bounded `swdb.host-observation.v1`
receipt with read-only load, users, disk/memory, CPU/NUMA, governor/turbo, kernel,
and SWDB revision observations. The verified lane remains in the profile context.
Unavailable host controls are recorded explicitly; collection time counts against
the diagnostic budget. Native primary evaluations retain their own separate
receipt, so a later diagnostic does not replace the timed run's host observations.

`swdb bfs-profile REQUEST --runs-dir EXTERNAL --lane LANE` consumes one complete,
structurally checked native `evaluation`. `swdb bfs-hotspots PROFILE --kind
function|loop [--evaluation EXPECTED]` retrieves ranked attributable source scopes;
an expected evaluation mismatch is rejected. `swdb get PROFILE --chain` retains
its source, candidate, and primary execution relationship.

Hotspot responses name the ranking metric, basis, quantity, and attribution,
retain the primary evaluation's `evidence_kind`, and always report
`gain_claim: false`. Native functions use the function aggregate described below;
loops use exclusive lexical thread CPU time. Older native profiles without the
function aggregate use exclusive lexical thread CPU time for the entire ranking.
Unexecuted scopes remain in the durable profile, outside the ranked rows; an
executed scope missing the selected metric is listed under `ranking.unavailable`.
Simulated profiles use the distinct elapsed-time quantities documented in
[DX100 profiling](bfs-dx100-profiling.md).

A request supplies `message_version: "1.0"`, a new `id`, `evaluation`, and explicit
`budget` values `discovery_seconds`, `build_seconds`, `run_seconds`, and
`total_seconds`. `repetitions` defaults to one diagnostic execution of each ordered
source. `memory` defaults true. Optional `discovery` supplies `library`,
`resource_dir`, and compiler-parser `arguments`; the exact libclang version,
library hash, arguments, diagnostics, and coverage limits survive in the record.
`correspondence` names an earlier profile of the same implementation.

Discovery uses the compiler's source extents for free functions and ordinary loops
in the current BFS translation-unit source file. Names are not an eligibility
catalog. Free function templates and their loops are included; their shared source
extent aggregates executed instantiations. Member templates retain the existing
member-code exclusion. The metadata parser disables OpenMP while retaining the actual compiler's
`_OPENMP` feature macro, because CIndex otherwise hides captured loop bodies.
The actual compiler's verbose system-header search paths are supplied explicitly
to standalone libclang, whose installation may otherwise omit GCC's C++ headers.
Clang's resource/intrinsic/OpenMP declarations replace the compiler-private header
slot, which may otherwise contain GCC-only builtin and attribute syntax. The C++
library's wrappers retain their preceding position in the search order. This parser
difference is recorded; the diagnostic executable still uses the original compiler
and headers.
For GCC inputs the metadata parser also erases the GNU `__restrict__` alias
qualifier, whose prefix spelling in the pinned DX100 source GCC accepts and Clang
rejects. This adaptation is recorded in `parser_adaptations`; inventory does not
infer alias semantics. Source bytes and all actual executable builds retain the
original qualifier.
Clang's predefined compiler identity and feature macros are not rewritten to
pretend it is GCC. The full source file is tokenized, including inactive branches;
uses of compiler-identity or feature-query tokens such as `__GNUC__`, `__clang__`,
and `__has_builtin` fail discovery as unresolved. This also catches aliases
defined in the source, while comments and string literals remain valid. Conditions
or aliases supplied indirectly by headers remain outside branch-equivalence
guarantees. The current pinned BFS source files do not use these tokens.
`build_directory` optionally selects a unique absolute directory outside the
repository and records. On mbit10 it must be under `/data1/yanruj` and defaults to
`/data1/yanruj/EvolveSWDB_builds/<profile-id>`. Instrumented sources, wrappers, and
binaries live there; collector logs and observation files remain in `--runs-dir`.
The diagnostic `load_average` is sampled for this profile; `primary_load_average`
retains the timed evaluation's original host-load observation. Both region and
memory collectors honor the requested repetitions and ordered traversal sources.
Parent vectors, region counters, and Callgrind summaries are parsed and hashed
from one bounded byte buffer per observation. Each execution and its metric rows
reuse that captured identity; a later file replacement cannot redefine the bytes
that were checked. Callgrind files have a 64 MiB collection/parser bound.
An additive `post_collection_audit` can invalidate a metric family while retaining
the exact original observations and raw hashes. An audit with `scope: dynamic_memory`
and `state: invalid` prevents those observations from satisfying package completeness;
it does not erase independent region or correctness evidence.
Older collectors persist the same audit under `extensions.post_collection_audit`
so their original schema remains valid.
Execution retains the primary compiler, version, and OpenMP build flags. Any parser
error fails discovery. Transformation-specific/continued OpenMP pragmas and
macro-generated loops without safe source extents remain unresolved. Header,
library, member, and compiler-outlined machine-code scopes are outside this bounded
collector; partial source coverage is never an exhaustive bottleneck ranking.

The separately built region binary inserts nested RAII guards automatically.
`CLOCK_THREAD_CPUTIME_ID` yields accumulated inclusive and exclusive thread CPU
seconds. Each thread has its own stack, so nested source scopes are subtracted once
from their enclosing scope's exclusive contribution. OpenMP loop bodies are guarded
on the worker executing each iteration; their invocation unit is an iteration.
Other loops count loop entries, and functions count calls. Function rankings use
`exclusive_function_thread_cpu_seconds`: the sum of nonoverlapping exclusive source
scopes belonging to that function, including its loops and worker iterations. This
includes its own loop work while excluding separately guarded helper functions.
Raw runtime counters must fit unsigned 64-bit integers; zero invocations require
zero duration. These checks reject malformed observations before arithmetic or
aggregation, while positive invocation counts may legitimately have zero measured
duration.
The source-scope inclusive and exclusive counters remain separately available.
Concurrent thread CPU
seconds are not complete-call wall seconds. Instrumentation overhead is included,
not guessed or subtracted. Inlined functions retain source-scope identity. Function
and loop inclusive values overlap and must not be summed as exclusive work.

A second binary uses original candidate source with Callgrind client requests around
`DOBFS`. It contains no region timing guards. Recorded `Dr` and `Dw` are executed
read/write references; `D1mr`, `D1mw`, `DLmr`, and `DLmw` are modeled cache misses.
All observations have `basis: simulated` and whole-ROI attribution. The default
explicit model is I1 32768/8/64, D1 49152/12/64, and LL 25165824/12/64
(bytes/associativity/line bytes); `memory_model` may set `I1`, `D1`, `LL`, and
`collector`. Cache state starts cold at instrumentation start. Collection is enabled for all
threads, instrumentation is globally bounded to the ROI, and the dump combines
thread events; no per-thread collection toggle can omit new OpenMP workers.
The explicit client dump occurs **before** stopping instrumentation. Only that
dump contributes observations; all raw parts, including the final process-exit
dump, remain retained. `counter_validation` requires bounded nonnegative integer
counts, summary counts at least as large as the self-cost totals, data-cache misses
no greater than their references, and last-level misses no greater than first-level
misses. Public hotspot queries also invalidate inconsistent historical execution
groups while preserving their numeric values and `recorded_available` flag.

The September 25 a3 observations exposed the reason for this ordering requirement:
Valgrind 3.22 resets current thread costs when instrumentation stops, while a prior
zero-stats operation leaves a nonzero last-dump baseline. Dumping afterward can
subtract that baseline from zero using unsigned arithmetic. The a3 `summary`
contained values near 2^64 even though `totals` contained ordinary positive values.
Both original observations and raw hashes are preserved with an invalid-memory
audit; they cannot establish Ticket 08 or package completeness. This diagnosis
follows `callgrind/main.c` (`set_instrument_state`, `zero_thread_cost`) and
`callgrind/dump.c` (`new_dumpfile`) at upstream tag `VALGRIND_3_22_0`, commit
`bd4db67b1d386c352040b1d8fab82f5f3340fc59`, in the
[official Valgrind source](https://sourceware.org/git/?p=valgrind.git;a=tree;h=bd4db67b1d386c352040b1d8fab82f5f3340fc59).
The [Callgrind format](https://valgrind.org/docs/manual/cl-format.html) specifies
the summary/self-cost relationship. `scripts/bfs_callgrind_roi_probe.py` compares
the old and corrected orders with one and four threads under a 360-second outer
budget. `scripts/bfs_profile_recollect.py` then reuses retained valid primary
evaluations for fresh baseline and changed-source diagnostics.
Valgrind schedules threads differently from native execution; the cache model
uses virtual addresses and excludes kernel/other-process cache effects. These are model
parameters, not claimed current hardware counters. No source-order proxy is
substituted for actual BFS accesses. No address trace, per-loop memory behavior, or
causal bottleneck explanation is inferred from these ROI counters.

Each diagnostic process executes the identical canonical graph and source and is
structurally checked independently. Primary binary, source, graph, and current lane
identities are verified before dispatch. The primary `evaluation` remains the
source of native complete-call ROI timing. A changed profile collects fresh data;
only identical unambiguous source fragments within a containing function receive
correspondence. Changed/split/fused/removed fragments stay unresolved and inherit
neither timings nor semantic assertions.

The durable `region_profile` record contains `request`, `evaluation`, `candidate`,
`source_snapshot`, `implementation`, `machine`, `context`, `discovery`, `build`,
`artifacts`, `outcome`, `stages`, `regions`, `dynamic_memory`, `executions`,
`correspondence`, `raw_artifacts`, `reasons`, and `gain_claim: false`. Regions include
current `path`, `lines`, `byte_range`, `source_sha256`, `text`, `function`, `usr`,
`helpers`, `callers`, compiler-derived `referenced_types`, `invocation_unit`, `metrics`, `basis`, `scope`,
`artifact_sha256`, and `source_artifact_sha256`. Executions record output/counter
hashes and structural correctness. Missing collectors and failed observations retain
available region evidence and explicit reasons. Every supported source subset is
reported as `partial`; ticket 09 can assemble a package with these stated limits
when its independent evidence gates pass.

The collector uses primary interfaces documented by
[Clang CIndex](https://clang.llvm.org/doxygen/group__CINDEX.html) and
[Callgrind's client requests and cache simulation](https://valgrind.org/docs/manual/cl-manual.html).
Local toy compiler tests check accounting and retrieval; real BFS acceptance uses
`scripts/bfs_profile_smoke.py` in an owned mbit10 lane and a public changed-helper
proposal, independent native evaluation, fresh collection, and query.
