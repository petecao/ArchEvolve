# Automatic BFS diagnostics

Updated: 2026-09-25 (Eastern Time).

`swdb bfs-profile REQUEST --runs-dir EXTERNAL --lane LANE` consumes one complete,
structurally checked native `evaluation`. `swdb bfs-hotspots PROFILE --kind
function|loop [--evaluation EXPECTED]` retrieves ranked attributable source scopes;
an expected evaluation mismatch is rejected. `swdb get PROFILE --chain` retains
its source, candidate, and primary execution relationship.

A request supplies `message_version: "1.0"`, a new `id`, `evaluation`, and explicit
`budget` values `discovery_seconds`, `build_seconds`, `run_seconds`, and
`total_seconds`. `repetitions` defaults to one diagnostic execution of each ordered
source. `memory` defaults true. Optional `discovery` supplies `library`,
`resource_dir`, and compiler-parser `arguments`; the exact libclang version,
library hash, arguments, diagnostics, and coverage limits survive in the record.
`correspondence` names an earlier profile of the same implementation.

Discovery uses the compiler's source extents for free functions and ordinary loops
in the current BFS translation-unit source file. Names are not an eligibility
catalog. The metadata parser disables OpenMP while retaining the actual compiler's
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
`build_directory` optionally selects a unique absolute directory outside the
repository and records. On mbit10 it must be under `/data1/yanruj` and defaults to
`/data1/yanruj/EvolveSWDB_builds/<profile-id>`. Instrumented sources, wrappers, and
binaries live there; collector logs and observation files remain in `--runs-dir`.
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
