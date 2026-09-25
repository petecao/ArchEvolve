# DX100 build and smoke execution

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)

The public `dx100-build` and `dx100-execute` commands persist ordinary evaluation
records before starting external work. `swdb get ID` retrieves them in another
process. A completed build means identified binaries exist; completed smoke
execution means the expected ROI exit and raw statistics/configuration exist.
Both leave `correctness.state: unverified` and `gain_claim: false`. Ticket 13
adds exact timed-binary checking; ticket 14 adds complete profile collection.

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
author harness's verifier; the record therefore remains unverified even with
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
