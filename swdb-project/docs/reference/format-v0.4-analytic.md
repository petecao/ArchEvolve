# Analytic estimator: portable inputs and source counts

Updated: 2026-10-06 ET.

`swdb characterize` compiles a buildable C/C++ translation unit, analyzes its LLVM IR,
and runs a separately instrumented binary once. `swdb estimate` combines those recorded
counts with a target description to report analytic bounds in seconds. Estimates have
basis `estimated`; the counting run supplies no timing or hardware-target correctness.
The two commands use the normal validating record writer and never edit source files.

## First runnable example

Run from `swdb-project/` with Python 3.12 or later and LLVM 22 (`clang++`, `opt`, and
`llvm-config` from the same installation). A missing LLVM installation yields a clear
command failure; compiler-dependent tests skip. On an Apple Silicon Mac, for example:

```sh
python -m swdb characterize --records /path/to/copied/records \
  --source tests/fixtures/analytic/stream.cpp --implementation gapbs-bfs-do \
  --input kron-g16-k16 --function stream --roi fixture.stream.v1 \
  --region-map tests/fixtures/analytic/regions.json --run-arg 8 \
  --llvm-bin /opt/homebrew/opt/llvm/bin --output /path/to/new/counting-folder \
  --fixture --id fixture.characterization --format json

# Freeze the request below and use the full returned content-addressed ID.
python -m swdb freeze-protocol /path/to/freeze.yaml \
  --records /path/to/copied/records --format json

python -m swdb estimate --records /path/to/copied/records \
  --characterization fixture.characterization --target-description /path/to/target.yaml \
  --protocol fixture.estimate.protocol.<returned-hash> --id fixture.estimate --format json
```

The fixture label matters: its implementation/input IDs are placeholders and its numeric
parameters are test fixtures, not measurements of BFS or mbit10. Real sources omit
`--fixture`. Source and run arguments must identify the same input as the record. Supply
include, define, OpenMP and link flags with repeatable `--build-flag=-I/path` and similar
options. Supply compiler/header selection options through repeatable `--toolchain-flag`: these apply to the LLVM pass, source and runtime builds, and are retained in `compiler_flags`. For example, an installed GCC with complete headers can be selected with `--toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`. The output folder must be new, preventing reuse of stale counts. The command
retains the IR, compiled pass, binary, compact counts and native stdout/stderr there.
Do not copy target-host raw output into the source repository.

The command accepts one translation unit, including its driver. Header code can be
inlined or emitted in that unit; unresolved calls and other translation units are coverage
limits. Its recorded `subject` names either an `implementation` or a `candidate`. `binding` retains the registered subject record/source identity (and candidate snapshot/artifact/diff identity), input record hash, `--roi`, `--threads` and run-argument hash. Actual candidate artifacts must pass their existing protection checks. These identities alone leave application binding `unverified`; only a registered-source/protocol adapter can establish it. The thread count sets `OMP_NUM_THREADS` for the counted run and must match the target description.

## Workload characterization v1

A durable record has `kind: workload_characterization`, envelope `schema_version: "0.4"`,
and `format: swdb.workload-characterization.v1`. These versions have different jobs:
the envelope controls database records; the format controls portable estimator input.
The authoritative schema is `schemas/workload_characterization.schema.json` (merged with
`schemas/envelope.schema.json` by SWDB). The record is written under
`records/workload_characterizations/<id>.yaml`.

| Field | Meaning |
|---|---|
| `subject`, `input` | One candidate artifact or baseline implementation on one input/workload. |
| `source` | Source-file SHA-256, exact supplied flags and run arguments; the protected driver stays unchanged. |
| `host`, `toolchain` | Counting hostname, OS, architecture, LLVM version and installation. Counts from the Mac do not establish mbit10 timing. |
| `counting` | Counting convention, one native run, binary/count hashes and retained output folder. |
| `static_analysis` | Source-normalized loop facts and separate post-`-O3` facts, each with its IR hash. |
| `regions` | Existing region IDs matched by function and source line; multiple loops mapped to one region aggregate their counters. |
| `unmapped_loops` | Source loops that lacked an existing region mapping. They stay counted under explicit `unmapped.*` IDs. |
| `unmodeled_calls` | Call-site names/lines and actual execution counts, including bulk-memory intrinsics; downstream models can supply costs without guessing whether calls ran. |
| `coverage` | Counted scope and separate missing-count/missing-cost declarations. `whole_timed_call: null` means a paired timing's full coverage has not been established. |

Each region contains `access_patterns`, `operation_counts`, `dynamic_counts`,
`footprint_bytes`, `accelerator_calls` and `address_stream_counts`. The last two are
extension points for later mechanisms; the streaming slice leaves them empty. A footprint
union is unknown because per-access address spans do not establish overlap or aliasing.

Each access pattern identifies one IR load/store. It carries source function/line/column,
`update_kind`, `address_shape` and `stride_bytes` facts, `element_bytes`, `element_count`
and `bytes_accessed` counts, the ScalarEvolution expression and original fixed-vector
lane count. Facts have `value` and `basis`; counts also have `scope: per_run` and
`formula` (null when no symbolic formula is established). Unknown values stay null.
The measured address span is a compact live min/max summary, not a saved address stream.

The JSON region mapping is deliberately small:

```json
{"regions": [{"id": "fixture.stream", "function": "stream", "line_start": 4, "line_end": 5}]}
```

`function` is a debug function name or LLVM symbol. Lines cover loop start locations;
ambiguous mappings are refused. Without `--function`, every emitted debug function is
counted; with it, the scope is that function. This option declares counting scope, not
that a later timing necessarily covers exactly that scope.

## What “source-level” counting means

Both paths use the caller's build flags and `clang++ -O3 -g -emit-llvm`. The static path
keeps the fully optimized IR. The counting path disables LLVM optimization in the
frontend, then applies only `mem2reg` and `loop-simplify`. The same LLVM pass uses
LoopInfo, ScalarEvolution and debug locations on each path, and inserts counters into
the normalized path before vectorization, unrolling, loop deletion or call elimination.
Its separately compiled binary can then be optimized without losing calls to counters.
This preserves a source loop's executed element counts instead of guessing a multiplier
from a vectorized, unrolled loop. Explicit fixed-vector operations count their lanes;
scalable-vector accesses are refused pending a multiplicity model.

Operation classes are integer, floating point, branch and atomic. Arithmetic and
comparisons count normalized IR operations; induction increments and comparisons count;
address calculations and casts do not. An FMA counts two floating-point operations.
Branch counts are executed IR terminators, including structural branches introduced by
the frontend. These counts are source-normalized work, not final machine instruction
counts or cycles. A loop's `loop_iterations` counts body entries when its header chooses
inside versus outside; other loop shapes count header entries. Static header-trip facts
are named separately. A loop count alone must not imply every access executed that often.

The streaming fixture's eight iterations independently give eight 4-byte reads, eight
4-byte writes and sixteen floating-point operations. With 16 floating-point operations/s
and effective streaming bandwidth 32 bytes/s, the loop's compute bound is 1 second and
its streaming bound is 2 seconds. The total also includes the tiny serial-region bound.
The test uses deliberately artificial rates; they are not performance evidence.

Implementation reference: LLVM's [new pass manager](https://llvm.org/docs/NewPassManager.html)
and [pass-writing documentation](https://llvm.org/docs/WritingAnLLVMNewPMPass.html).

## Target description v1

The [native CPU calibration commands](cpu-calibration.md) measure separate per-T
constructed-work rates and import immutable descriptions with trial spread.

A target description is a record with `kind: target_description`,
`format: swdb.target-description.v1`, envelope fields, `version`, `target`, `threads`,
`estimator_variant` (`team` or `research`), `calibration_sources`,
`dram_address_layout` (null without a row-counting mechanism), and `mechanisms`.
The schema is `schemas/target_description.schema.json`. A file may be supplied directly
or stored with `swdb add` and supplied by ID.

Each mechanism has `model` and `parameters`. Each parameter has a numeric or null
`value`, `basis`, `source` and `unit`. Its source should name a measured receipt, pinned
source/configuration, paper or frozen estimation-role result. Unknown parameters use
`value: null` and `basis: unknown`; zero is not a stand-in for an unavailable rate.
Rates describe the whole frozen target/thread configuration, not a rate to multiply by
thread count a second time. The first mechanisms are:

| `model` | Parameters and units | Bound |
|---|---|---|
| `compute_throughput` | `integer_ops_per_s`, `floating_point_ops_per_s`, `branch_ops_per_s`, `atomic_ops_per_s`; each `operations/s` | Maximum of each nonzero class's count divided by its aggregate rate. |
| `streaming_bandwidth` | `bytes_per_s`; `bytes/s` | Sum of useful source element bytes divided by measured effective bandwidth using the same byte convention. |

A zero-work class needs no rate. A nonzero class with an unknown/missing/nonpositive
rate yields an unknown bound. A non-stream access stays unknown in the streaming model;
a latency/cache mechanism must cover it before the overall time can be claimed. The
first slice models useful element bytes, not cache-line bus traffic, write allocation,
reordering, cache residency or accelerator timing. Those need additional mechanism models.

## Estimates and composition

An estimate has `kind: estimate` and `format: swdb.estimate.v1` and is stored under
`records/estimates/`. A separate kind is smaller and clearer than reusing `evaluation`:
the latter requires actual timing/correctness stage receipts. An estimate never appears
in its `timing` array and native comparison/selection continues to require execution
observations. Every existing record retains its schema and validates unchanged.

The estimate names `estimator_version`, target/thread configuration, protocol ID,
characterization and target-description IDs and canonical content hashes, and embeds
the target-description snapshot. Its `regions` contain bounds with `model`, `formula`,
`inputs`, `missing`, `seconds`, `state` and basis `estimated`. Composition takes the
largest mechanism bound per region, adds declared overheads, then sums all regions,
including the serial remainder. If any required bound is unknown, that region and the
total stay null. Executed unmodeled calls add an unknown-cost bound. Known component
bounds remain visible.

When more than one resource domain has executed or unknown work, optional
`composition_contract` must declare `resource_domain_overlap: serial` or
`full_overlap`, with its basis and source. Serial sums domain maxima; full overlap
takes their maximum. Both are explicit analytic scenarios, not measured scheduling.
Absent overlap keeps each known component visible and the required total null.
Executed or unknown host source accesses also require an applicable streaming,
requests-in-flight, cache or native memory-service model; offload row/queue/staging
models cover a separate domain. Missing host memory mechanisms remain structural
unknowns that numerical parameter filling cannot repair. Proven zero work needs
neither a service rate nor an overlap policy. Additive overheads remain charged once.

An optional `--baseline` names an explicit estimate. Its input, target-description hash,
protocol, thread count and evidence kind must match. The ratio is baseline seconds /
candidate seconds; it stays null without known positive candidate time. Until a validated
error band is supplied, the verdict is `within_error`. Hardware-target correctness and
CPU error bands remain separate operations; ArchEvolve never calibrates against gem5.

## Frozen estimate protocols and the team boundary

The public `freeze-protocol` request uses the existing immutable protocol envelope:

```yaml
message_version: "1.0"
id: fixture.estimate.protocol
version: 1
settings:
  mode: estimated
  estimator_version: swdb.analytic.v1
  target_description: /path/to/target.yaml
  inputs: [kron-g16-k16]
  roi: fixture.stream.v1
  threads: 1
  input_run_arguments:
    kron-g16-k16: ["8"]  # exact counted arguments, keyed by input
  sources: [gapbs-bfs-do]  # optional explicit source record pins
```

Freeze replaces `target_description` with `{id, sha256, snapshot}`. It records
`input_identities` for input/workload records and `source_identities` for optional
implementation/candidate/source-snapshot records. `dependency_identities` pins every
stored record reachable from the target description, including calibration records
and inspected source/configuration records; mutation requires a fresh freeze. `workload_identities` is empty for
an estimate protocol; historical timed protocols retain their registered workloads.
The frozen `estimator_sha256` covers the portable SWDB Python source bundle using
relative paths and content hashes. This conservative bundle includes supporting SWDB
code as well as mechanism models: any implementation change requires a fresh protocol.
Changing the label alone cannot reuse a freeze after code changes. Counts separately
retain the compiler pass, runtime, source and count receipt identities.

Estimate execution verifies the current bundle/version, target snapshot, input hash,
`input_run_arguments`, source subject, ROI and threads. Per-input run arguments are
required for application evidence; optional for fixtures, and verified when present. An estimate records `protocol_sha256` and
`estimator_sha256` alongside the frozen protocol ID. An arbitrary source characterization
with binding `unverified` cannot become application evidence. Explicit fixtures retain
`binding.state: fixture` and `evidence_kind: contract_fixture`. Historical validation
checks frozen record integrity without requiring old source bundles to be installed.

New ArchEvolve operations default to the team policy from
[ADR 0013](../adr/0013-archevolve-mode-estimates-speed.md): they recursively refuse gem5
backend targets, gem5 execution/calibration dependencies, research estimator variants,
and Extensa estimate/protocol records. Refusals name ADR 0013 and the offending record
or dependency chain, before dispatch or persistence. Calibration dependencies must
resolve to records. A `code_reading` parameter may cite a pinned simulator source
configuration (D18); that allowance never admits an execution record as code reading.
Existing simulator records remain valid history.

An Extensa campaign keeps its inherited creation tags and existing gem5/timing path.
Explicit public use supplies `--mode extensa --campaign <valid-campaign-id>`; both tags
are attached at creation. `--mode archevolve` applies team policy even under an inherited
campaign environment. This boundary changes no simulator adapter or timing-selection rule.

## Remaining record fields

Source and identity: `path`, `sha256`, `build_flags`, `run_arguments`, `protected_driver`, `source_location`, `column`, `identity_sha256`, `characterization_sha256`, `target_description_sha256`, `target_description_snapshot`, `binding`.

Counting receipt: `level`, `passes`, `native_runs`, `binary_sha256`, `counts_sha256`, `output_directory`, `vector_multiplicity`, `operation_definition`, `loop_definition`.

Compiler receipt: `llvm_version`, `llvm_bin`, `source_ir_sha256`, `optimized_ir_sha256`, `optimized_facts`, `mapping_note`, `loops`, `ir_lanes`, `address_expression`, `observed_address_span_bytes`.

Estimate report: `bounds`, `overheads`, `limiting_bound`, `baseline`, `ratio`, `error_band`, `llm_parameters`, `scope`, `evidence_kind`.

Envelope and portable fields: `architecture`, `atomic`, `branch`, `characterization`, `floating_point`, `format`, `id`, `integer`, `kind`, `line`, `machine`, `mapped`, `notes`, `protocol`, `schema_version`, `system`, `target_description`, `verdict`.

Binding keys are `state`, `subject_source_identity`, `input_record_sha256`, `roi`, `threads`, `run_arguments_sha256` and `note`. The first slice emits fixture or unverified state; verified state is reserved for a registered-source/protocol adapter.

Compiler distributions with a shared LLVM library link the pass against it; static LLVM distributions load the pass against `opt` host symbols, avoiding a duplicate static LLVM registry. `plugin_linkage` records this choice. Static distributions also require the configured `llvm-ar`, `llvm-nm` and native `libLLVMSupport.a`. The builder extracts only `SHA256.cpp.o`, verifies SHA-256 methods plus the ABI check anchor with no extra LLVM globals or initializer functions, and links that stateless object; it never links the archive or duplicate registries. Optional `toolchain.plugin_support_objects` retains the native archive/member/object identities, sealed by `observation_contract.plugin_support_objects_sha256`. Existing records without those fields retain their original seals. Missing or unsuitable native support fails before counting. Repeatable `--run-library-path` supplies native library folders (such as libomp): each enters link search, binary RPATH and runtime library search, and is retained as `run_library_paths`.

## Registered GAPBS trials and indirect memory bounds

Updated: 2026-10-06 ET (ticket 05).

Use `--adapter registered-gapbs` for the registered `gapbs-bfs-do` or
`gapbs-bc-brandes` baseline. The adapter resolves the registered translation unit,
checks its authoritative source excerpts, derives compiler flags and graph arguments,
and inserts LLVM counter gates around the original `BenchmarkKernel` `kernel(g)` call.
The source and evaluator files stay unchanged. This ROI is `gapbs.trial_lambda.v1`:
it includes BFS's source picker and the complete kernel call. It differs from a
protected native driver that times only `DOBFS` or `Brandes`.

```sh
python -m swdb characterize --records /path/to/copied/records \
  --adapter registered-gapbs --implementation gapbs-bfs-do --input kron-g16-k16 \
  --threads 4 --trials 5 --llvm-bin /path/to/LLVM-22/bin \
  --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
  --run-library-path /path/to/LLVM-22/lib --timeout-s 1800 \
  --output /path/to/new/bfs-counting --id bfs.kron-g16.t4.characterization --format json
```

The same command with `--implementation gapbs-bc-brandes` counts BC. Its adapter
also fixes `-i 1`, matching the registered baseline's default source iteration count.
The generator arguments come from the input record; source, run, function and build
flag overrides are refused. Compiler selection flags can select installed headers and
libraries, but cannot replace source macros or the driver.

The registered counting pipeline is frozen as `source-normalized-v2`:
`function(sroa,mem2reg),cgscc(inline),function(loop-simplify)`. ROI gates and source-picker
observations are inserted before helper inlining. Counting still precedes vectorization
and unrolling. The original deterministic source picker advances between trials.
`trials` retains each invocation's position, selected source, executed exclusive regions
and calls. The top-level inventory uses trial zero's counters and retains every static
unmapped loop, including unexecuted loops. Sparse trial observations omit only proved
zero-work regions; they do not drop those loops from the inventory.

An estimate composes each trial separately, sums its exclusive region bounds and serial
remainder, then takes the median of whole-call times. Per-region median summaries are
shown for inspection; they generally do not sum to the whole-call median. Five trials'
counts are never summed and paired with the median of five timing observations. Any
unknown required cost in any trial keeps the total and ratio unknown.

Source paths and debug context map outlined workers and source helpers to existing
profile-package region IDs when their byte range, function and source-text hash still
match the current registered source. The catalog loop identity remains in the binding
map. The registered BFS/BC records currently have no site-finder statement annotations;
a loop without an existing profile region uses its qualified catalog identity.
Generated IDs include the subject and an LLVM function
qualifier, preventing collisions between functions or implementations. A shared header
helper, such as BC's several `pvector::fill` call sites, remains unmapped when its logical
instance cannot be proved. Multiple lowered loops that share one source region keep
exclusive access/operation counts and a byte union; their source-loop iteration count
stays unknown rather than summing compiler scheduling loops. `pattern_comparison`
reports every handwritten access pattern, observed shape/update kinds and an explicit
reason for each mismatch. A matching individual address site does not prove a complete
multi-step chain or the handwritten update's legality.

The pass recognizes `single_valued_indirect`, `ranged_indirect`, `pointer_chase` and
`data_dependent_merge` from SSA dependencies and ScalarEvolution. A varying loaded index,
a loaded range boundary, a load feeding its address recurrence, and a data-selected
pointer merge provide distinct evidence. Opaque calls or unresolved dependencies stay
unknown. `constant` describes a proved invariant address and is supplementary to the
formal access-pattern vocabulary.

`observed_unique_bytes` is the live union of virtual byte ranges for one address site;
`footprint_bytes` is the union for an exclusive region. Repeated addresses and overlapping
reads/writes are counted once in this footprint. Only byte totals and spans are saved;
addresses stay in process memory. These are neither physical DRAM row counts nor cache
miss measurements. Atomic RMW and compare-and-swap instructions retain their memory
operand, width, update kind and `read_write` flag. Their useful operand bytes do not
establish cache-line or bus traffic.

| Mechanism | Parameters | Convention |
|---|---|---|
| `requests_in_flight_latency` | `dependent_latency_s` (`seconds/load`), `effective_requests_per_thread` (`requests/thread`) | Non-stream requests × latency / (observed active workers × effective requests per worker). A pointer-chase recurrence caps overlap at one request per executing worker. |
| `cache_fit` | `capacity_bytes` (`bytes`), `bytes_per_s` (`bytes/s`), `cold_bytes_per_s` (`bytes/s`) | If the virtual byte footprint fits, charge distinct first-touch useful bytes at the cold rate and remaining useful bytes at the cache rate. |

Requested threads do not multiply a serial region's concurrency: `active_workers` is
the distinct executing worker count in an exclusive region within one trial.
`worker_context.team_sizes` records OpenMP team sizes separately; a sparse single-worker
branch in a four-worker team has one active worker. Compute, stream and cache rates measured with
all configured workers active apply only when that same active worker count and team
context are observed.
A serial or partially active region needs an independently measured rate; its bound
remains unknown rather than dividing an aggregate rate by the requested thread count.
Requests in flight are an effective inferred
parameter, not measured physical MSHR occupancy. The cache model assumes a cold start
per trial and ideal capacity; fit does not prove residency, conflicts or first-touch
misses. Unknown rates/counts/footprints, or a footprint outside its supported cache
capacity, keep the required bound unknown. Zero work needs no rate. Streaming bandwidth
covers stream sites; a declared latency/cache model covers other sites, avoiding a
spurious requirement that an indirect address also be a stream.

Every executed external call keeps its name, event class, count and known size in
`unmodeled_calls`. Bulk-memory intrinsics, allocation and OpenMP runtime calls are
explicit events. Calls whose selected emitted bodies are counted are marked
`body_counted`; external bodies keep missing counts and costs. An operation rate does
not cover an unknown external-call cost. These events are inputs for later mechanism
models, not zero-time assumptions.

A verified binding needs a `swdb.registered-count-receipt.v1` execution receipt. It pins
registered source/input/arguments/ROI, trial identity, LLVM and normalized pipeline,
source/binary/count hashes, and the extracted counted payload. Merely changing
`binding.state` to `verified` is refused. Fresh execution verifies available registered
source and raw artifacts. Historical validation checks the compact receipt and available
registered source, without fetching or requiring a remote raw-output directory.

`--counting-pipeline source-normalized-v1|source-normalized-v2` selects one fixed
normalization recipe for a fixture. The default fixture recipe remains v1
(`mem2reg,loop-simplify`); v2 uses the same SROA/inlining recipe as registered
application runs. Registered adapters require v2 and refuse v1. This allows shared
calibration kernels to test v2 numerator equivalence without silently counting v1.
A trial region with executed calls is retained even if it has no arithmetic, memory
access or loop-entry events, so a call-only required cost cannot disappear.

LLVM `expect` hints return their supplied value, and `experimental.noalias.scope.decl`
marks alias-scope metadata. Their executed source events use `compiler_annotation` /
`no_runtime_operation` accounting. They add no opaque callee cost. Checked signed or
unsigned add/subtract/multiply intrinsics use `compiler_arithmetic` /
`source_normalized_operations`: one arithmetic result plus one overflow predicate per
lane. These are logical normalized operations, rather than a claim of two machine
instructions. Each event retains its execution count, classification and the
[LLVM language semantics reference](https://llvm.org/docs/LangRef.html#arithmetic-with-overflow-intrinsics).
The [expect](https://llvm.org/docs/LangRef.html#llvm-expect-intrinsic) and
[alias-scope](https://llvm.org/docs/LangRef.html#llvm-experimental-noalias-scope-decl-intrinsic)
definitions govern the zero-operation annotations. Genuine allocation, OpenMP, clock
and bulk-memory calls keep their costs unknown until an applicable model covers them.
Older receipts retain their original accounting; a changed plugin requires a new
counted execution and characterization ID.

Updated 2026-10-06 ET: CPU calibration imports also create typed, hash-bound
`cpu_calibration` provenance records (`swdb.cpu-calibration-record.v1`).
Fresh target-description versions list their resolvable IDs in `calibration_sources`;
freeze pins those dependencies recursively. [CPU calibration commands and lineage](cpu-calibration.md)
describe conversion of legacy explanatory citations without changing old records.

Updated 2026-10-06 ET: optional `reported_inputs[]` stores sanitized, hash-bound
feature reports with basis `reported`. Existing count fields, native binding and
receipts remain unchanged. [Reported feature input commands, field mapping and
conflicts](feature-report-inputs.md) explain the supplied BFS reports, unresolved
source/array scope, units and timing/PMU sanitization.


## Parameter dependencies and sensitivity report

Updated: 2026-10-06 ET (ticket 09). Optional `parameter_report` uses
`swdb.parameter-sensitivity.v1` and binds the frozen target and full observation
policy hashes. Historical estimates without this addition remain valid.

`unknowns` retain each exact parameter path, null value, basis/source/unit,
dependent bounds and `required_for_total`. Required unknowns share dependency
priority 1; unused references have priority 2. A null reference has no defensible
half/double magnitude, so `impact_magnitude_seconds` and `impact_rank` stay null.
This dependency ordering does not claim a numerical ranking of unsupported guesses.

`sensitivities` vary one positive frozen value by half and double, recompose every
whole trial and then its median, and report diagnostic component medians separately.
A supported whole-call magnitude is the largest absolute change from the base
seconds; descending magnitudes receive dense numerical ranks. If another required
bound stays unknown, local component scenarios remain visible while whole-call
magnitude/rank stay null. `llm_parameters` lists the frozen parameters whose basis
is `estimated`, including their source/reason and this sensitivity. A non-finite,
nonpositive or policy-invalidating scenario supplies no numerical impact.

Observation-policy changes (including referenced capacity/window/layout/backend
facts) are `requires_fresh_observation`; old row/count facts are not relabeled or
rewritten. Numeric scenarios are analytic hypotheses, not new frozen target
versions. `structural_missing` separately lists source facts, missing mechanisms,
opaque costs and composition policies. These cannot be silently repaired by the
unknown-parameter filling role. Public validation checks every report fact against
its frozen target, its base whole-call value, and its exact policy identity.

### Registered trial-window scope

New trial count facts use `scope: per_trial`; root snapshot counts retain `per_run`.
Legacy source labels may be inferred only in a copied estimation context after
verified registered ROI/trial binding and exact call-site/bin and source-memory
partitions. The estimate retains inferred proof under
`extensions.legacy_trial_scope_reconciliations`, pinning the original characterization,
payload, runtime and trial position. Original observations are immutable. Arbitrary
scopes, unsealed fixture state and mismatched partitions retain existing unknown/refusal
behavior. Sensitivity recomposition uses the same copied scope inference; it establishes
no new cost, hardware request, residency, functional/MMIO correspondence or error band.
