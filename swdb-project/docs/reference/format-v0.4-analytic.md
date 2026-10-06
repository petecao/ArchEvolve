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
  --input kron-g16-k16 --function stream \
  --region-map tests/fixtures/analytic/regions.json --run-arg 8 \
  --llvm-bin /opt/homebrew/opt/llvm/bin --output /path/to/new/counting-folder \
  --fixture --id fixture.characterization --format json

python -m swdb estimate --records /path/to/copied/records \
  --characterization fixture.characterization --target-description /path/to/target.yaml \
  --protocol fixture.estimate.protocol --id fixture.estimate --format json
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

An optional `--baseline` names an explicit estimate. Its input, target-description hash,
protocol, thread count and evidence kind must match. The ratio is baseline seconds /
candidate seconds; it stays null without known positive candidate time. Until a validated
error band is supplied, the verdict is `within_error`. The first slice does not freeze
protocols, validate hardware-target correctness, establish a CPU error band or calibrate
against gem5; those operations belong to their separate tickets.

## Remaining record fields

Source and identity: `path`, `sha256`, `build_flags`, `run_arguments`, `protected_driver`, `source_location`, `column`, `identity_sha256`, `characterization_sha256`, `target_description_sha256`, `target_description_snapshot`, `binding`.

Counting receipt: `level`, `passes`, `native_runs`, `binary_sha256`, `counts_sha256`, `output_directory`, `vector_multiplicity`, `operation_definition`, `loop_definition`.

Compiler receipt: `llvm_version`, `llvm_bin`, `source_ir_sha256`, `optimized_ir_sha256`, `optimized_facts`, `mapping_note`, `loops`, `ir_lanes`, `address_expression`, `observed_address_span_bytes`.

Estimate report: `bounds`, `overheads`, `limiting_bound`, `baseline`, `ratio`, `error_band`, `llm_parameters`, `scope`, `evidence_kind`.

Envelope and portable fields: `architecture`, `atomic`, `branch`, `characterization`, `floating_point`, `format`, `id`, `integer`, `kind`, `line`, `machine`, `mapped`, `notes`, `protocol`, `schema_version`, `system`, `target_description`, `verdict`.

Binding keys are `state`, `subject_source_identity`, `input_record_sha256`, `roi`, `threads`, `run_arguments_sha256` and `note`. The first slice emits fixture or unverified state; verified state is reserved for a registered-source/protocol adapter.

Compiler distributions with a shared LLVM library link the pass against it; static LLVM distributions load the pass against `opt` host symbols, avoiding a duplicate static LLVM registry. `plugin_linkage` records this choice. Repeatable `--run-library-path` supplies native library folders (such as libomp): each enters link search, binary RPATH and runtime library search, and is retained as `run_library_paths`.
