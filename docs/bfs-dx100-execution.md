# DX100 build and smoke execution

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)

On the pinned model, `src/python/m5/simulate.py:332–336` creates an empty literal
`cpt.%d` directory before the C++ serializer expands the tick. The adapter
accepts that empty, nonsymlink placeholder alongside exactly one numeric
`cpt.<tick>` payload; any other checkpoint entry rejects restore. The first real
tiny checkpoint completed in 91.656 seconds and produced about 17 MiB of
compressed guest memory. Future smoke stages reserve 300 seconds for checkpoint
creation within their unchanged overall budgets.

The a4 checkpoint-to-restore attempt retained `budget_exhausted` after detailed
restore exceeded its 16 GiB host process-group cap. Future tiny smoke requests
reserve 32 GiB host RSS, within the pilot cap, while retaining the identical
16 GiB guest configuration. `--checkpoint-evaluation` reuses a retained real
checkpoint with its exact existing workload ID, source, representation path,
and binary binding; the public adapter revalidates all identities. Each process
stage records `sampled_peak_process_group_rss_kib` where Linux accounting is
available. This is sampled host experiment cost, never simulated BFS memory
traffic or performance.

New `swdb.dx100.checkpoint.v2` manifests bind the complete modeled cache,
mode, clock, memory, core, and target configuration in addition to the exact
binary/workload/source identities. A changed configuration rejects before
restore. Legacy v1 reuse additionally requires `checkpoint_evaluation` naming
the original retained evaluation, its identical hashed manifest, completed
checkpoint stage, matching execution binding, and identical recorded modeled
configuration. The resulting `checkpoint_compatibility_proof` records and hashes
that explicit source evidence; missing or changed proof rejects reuse. No
legacy checkpoint is silently promoted to a fully bound v2 manifest.

The public `dx100-build` and `dx100-execute` commands persist ordinary evaluation
records before starting external work. `swdb get ID` retrieves them in another
process. A completed build means identified binaries exist; completed smoke
execution means the expected ROI exit and raw statistics/configuration exist.
Builds and unchecked smoke runs leave `correctness.state: unverified`.
Optional same-process continuation attaches an explicit structural verdict;
all cases retain `gain_claim: false`. Ticket 14 adds complete profile collection.

## Build request

Save the request as YAML or JSON and run it through a current, freshly checked
socket-lane wrapper in a named tmux session. `--lane 0` and `--lane 1` are
normalized to the corresponding named socket lease and verified against the
kernel, lease holder, ancestor process, affinity, and memory binding.

```yaml
message_version: '1.0'
id: bfs-dx100-build-20260925-a1
machine: mbit10
hardware_target: dx100-e4fc4af-4c
model_root: /data1/yanruj/DX100-bfs-e4fc4af
budget:
  total_seconds: 7200
  memory_gib: 48
  storage_gib: 10
  jobs: 8
```

```sh
python3 -m swdb dx100-build BUILD_REQUEST.yaml \
  --runs-dir /data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925 \
  --lane 0 --format json
```

Real source must be a clean checkout of
`e4fc4afdf894f295442cef3604667a469fab8e62` under `/data1/yanruj/` on mbit10.
The build helper creates Ramulator2, m5ops, gem5.opt, scalar/author BFS and
converter outputs. Its external receipt records stage commands and logs,
toolchain, host/lane, dependency commits, resolved Kconfig and binary hashes.
Read [the bounded design](bfs-dx100-design.md) for the declared two-attempt cap,
capacity decisions and source-backed configuration.

The helper bounds its nested build process group, while the public adapter
bounds the helper and retained raw artifacts. Memory/storage checks are sampled,
not kernel-enforced aggregate quotas. A 30-second adapter cleanup allowance
permits the helper to terminate compiler children and retain failure evidence.
Successful real builds update the selected hardware target to `built`, with
the hashed receipt linked under `backend.build_evidence`; this never establishes
correctness. Each attempt requires a fresh ID and output directory.

## Checkpoint-to-ROI request

`dx100-execute REQUEST --runs-dir DIR --lane NODE --format json` accepts the
same version, ID, machine, target and clean model-root fields, plus:

| Field | Meaning |
|---|---|
| `build_evaluation` | Completed real build evaluation identifying both simulator and selected BFS binary |
| `simulator` | Absolute regular-file `path` and expected `sha256` for gem5.opt |
| `binary` | Absolute regular-file `path` and expected `sha256` for scalar or author BFS |
| `workload` | Nonempty logical `id`, hashed graph `representation` with `path`/`sha256`, and actual integer BFS `source` |
| `configuration` | `mode` (`BASE` or `MAA`), `l3_size_mb`, `l3_assoc`, and `tile_elements` matching the selected target |
| `checkpoint_manifest` | Optional absolute `path`/`sha256` for a previously completed compatible checkpoint manifest |
| `verification` | Optional `checker: dx100.bfs.verifier.v1` and positive integer `max_ticks` (at most 10^15) |
| `budget` | Positive integer `total_seconds`, `memory_gib`, `storage_gib`, `checkpoint_seconds`, and `run_seconds` limits |

The current adapter instantiates four X86O3CPU guest cores, 16 GB guest memory,
3.2 GHz CPU/system clocks, classic caches, two Ramulator2 channels and the
pinned Ramulator2 configuration. It preserves the authors' cache/prefetch/MMIO
settings and explicitly selects LLC size/associativity. Use BASE 10 MB/20-way
and MAA 8 MB/16-way for the artifact pair; a controlled comparison must select
and freeze matching settings separately. A configuration label does not prove
that a full comparison or artifact-matched workload executed.

The build receipt is reopened and its hash verified. Both selected executable
files must be among its hashed outputs. Each file is checked again before
restore. Guest options always select one traversal, one explicit source and
verification: `-f GRAPH -l -n 1 -v -r SOURCE`. Graph paths with whitespace are
rejected because the pinned option parser cannot represent them safely.

A new AtomicSimpleCPU checkpoint run stops at the first checkpoint using
`--max-checkpoints 1`; it does not continue into accelerator MMIO execution on
an atomic system without the modeled accelerator. The external checkpoint
manifest binds model revision, simulator/binary hashes and paths, graph/source,
guest options, core/memory layout, entry-script hash, actual checkpoint files,
and fixture/real evidence classification. An incompatible manifest is rejected
before simulation. Existing statistics never suppress a new execution.

Restore creates a fresh simulation directory and retains the actual config.ini,
statistics, exact command, simulator exit cause/tick, logs and host execution
cost. The expected `m5_exit instruction encountered` event occurs before the
author harness's verifier; an unchecked smoke run therefore remains unverified even with
exit status zero. No ROI duration or neutral speedup is invented from missing
or incomplete evidence. Checkpoint and completed-stage evidence survive later
simulator failure, missing statistics, timeout or budget exhaustion.

## Contract fixtures

Tests explicitly set `fixture: true`, select a fixture machine and fake external
simulator/compiler commands, and retain `evidence_kind: contract_fixture`.
Build fixtures supply `fixture_command` as an argument list. That field is
rejected for a real build. Fixture execution skips the real host/model checkout
requirement but keeps hash, configuration, checkpoint, failure and retention
checks. Fixture checkpoints cannot be reused as real execution evidence and
fixture builds never update executable target readiness. These tests exercise
the public workflow; they do not complete real BFS/DX100 acceptance.

## Exact guest verification

With `verification` enabled, `scripts/dx100_verify.py` executes the unmodified
pinned simulator entry script and observes its actual exit event. At the first
successful ROI exit, it copies the already guest-dumped and flushed statistics
into `roi-stats.txt`, records its hash and execution binding in `roi-seal.json`,
and resumes the same instantiated machine with one bounded `m5.simulate` call.
The timed binary returns its existing parent array to its enclosing
`BFSVerifier`. No different functional executable certifies that array.

The pinned verifier reconstructs BFS depths, checks the source parent, valid
predecessor edges and depths, and unreachable vertices. It accepts different
valid parent trees. The adapter records exact binary and simulator identities,
model/source/harness hashes, graph identity and representation, actual source,
configuration, driver hash, execution ID, seal, raw output, observed verdict
lines, final exit cause, and requested versus observed check counts.

Exactly one PASS after the seal and a successful final guest exit are required
for `correctness.state: passed`. Any printed FAIL yields failed correctness
and an `incorrect` execution outcome, including when the process exits zero.
Absent or ambiguous output, a simulation tick limit, interruption, or missing
seal cannot certify the execution. The simulation wall/memory/storage budget
also covers continuation, and its guest tick cap is explicit in `max_ticks`.
Sealed ROI evidence survives a later verifier timeout or failure. Live terminal
statistics can change during verification without altering the sealed interval.

Path evidence counts completed MAA trace units and positive instruction counters
from the sealed `finalTick - simTicks` through `finalTick` interval. Both are
required for `accelerator_executed: true`; source presence, a `td_maa` label,
and scalar fallback do not qualify. With `verification.coverage: true`, explicit
RangeFuser and indirect-store debug traces record full and tail output tiles.
Competing-parent coverage requires the returned parent's actual virtual base,
matching vector-store instruction base, and distinct values written to the same
observed physical word. Graph topology alone does not establish that case.
The address spaces are distinct: pinned `IF.cc` prints the instruction's virtual
`baseAddr`; `IndirectAccess.cc:494` adds the element offset before translating the
resulting virtual block at line 498. Only that virtual base is compared with the
guest's parent pointer. `recvData` addresses are physical cache lines and are
used only to match repeated physical words. The coverage record carries the
source hashes and line references for this contract.
Fixture PASS is always `contract_fixture` evidence. The real continuation and
accelerated acceptance criteria remain open until executed on the actual model.

## Compiling a changed candidate

`dx100-compile FILE --runs-dir DIR --lane NODE` accepts an identified `candidate`,
completed `build_evaluation`, selected BFS `function`, explicit `accelerated`
boolean, and `roi: bfs.complete_call.v1`, alongside the ordinary host/model and
budget fields. The compilation budget uses `total_seconds`, `build_seconds`,
`memory_gib`, and `storage_gib`. GCC 13 compiles the candidate against the pinned
model API and m5ops assembly without rebuilding the simulator. The result is a
`candidate_build` evaluation identifying the source artifact, compiler, flags,
generated driver, assembly, and binary. An execute request names that evaluation
as `candidate_build` and repeats the exact `candidate` and binary identity.

The trusted outer driver times initialization, traversal, and normalization in
one complete call. It suppresses source-internal reset/dump/work/exit m5 events
using protected evaluator macros and rejects candidate overrides. The unchanged
author executable retains its separately named traversal ROI. After the outer
ROI is sealed, the same returned parent array receives length/range validation
before the protected structural verifier. Output includes its source, length,
actual storage address, and a clearly labeled noncryptographic FNV-1a fingerprint;
the enclosing output itself has a SHA-256 identity. A successful compilation
does not establish accelerator execution, correctness, or performance.

Generated guest build inputs and binaries use
`/data1/yanruj/EvolveSWDB_builds/ID` on mbit10; the bounded process monitor
accounts for that folder and the raw-log folder together. The compiler version
and adapter are recorded with actual flags. A simulation request may supply
`protocol`, `protocol_role`, and `protocol_trial: {source_position: N,
repetition: N}`. Before checkpoint creation, the adapter validates actual build,
modeled configuration, instrumentation, workload, source, and ROI against the
frozen role. Each execution retains exactly one real source/repetition timing
and corresponding detailed structural check. A later public aggregation joins
separate completed executions; requested repetitions do not become evidence.

Execution budgets may explicitly reserve up to 14,400 seconds for the simulator
stage and 18,000 seconds total, accommodating the declared bounded author u22
reference. Model builds retain the 7,200-second total cap. Candidate compilation
requires its selected function to match the identified source implementation;
an unchanged author binary additionally requires the matching scalar `DOBFS`
or accelerated `DOBFSMAA` identity when a candidate is attached.
