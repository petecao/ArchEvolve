# Ticket 05 registered counting handoff

Updated: 2026-10-06 ET. State: original mbit10 BFS/BC counts passed; corrected counts
and per-region analytic reports pending.

Run from the Git-synced checkout's `swdb-project/`. Copy authoritative `records/` into
`/data1/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/records` first. Keep raw
binaries/IR/counts/stdout on mbit10. Parent owns socket leases, source sync and dispatch;
maximum two jobs, one per socket. Each output folder must be new. Native runs retain
five independent source selections/trials, matching the registered `-g16 -k16 -n5`
workload (`-i1` for BC), with exact `gapbs.trial_lambda.v1` timing-boundary hooks.

```sh
python3 -m swdb characterize --records /data1/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/records --adapter registered-gapbs --implementation gapbs-bfs-do --input kron-g16-k16 --threads 4 --trials 5 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --run-library-path /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu --timeout-s 1800 --output /data1/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/bfs-counted --id bfs.kron-g16.t4.characterization --format json > /data1/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/bfs-characterization.json
```

```sh
python3 -m swdb characterize --records /data1/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/records --adapter registered-gapbs --implementation gapbs-bc-brandes --input kron-g16-k16 --threads 4 --trials 5 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --run-library-path /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu --timeout-s 1800 --output /data1/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/bc-counted --id bc.kron-g16.t4.characterization --format json > /data1/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a1/bc-characterization.json
```

These characterizations retain all 13 BFS / 20 BC handwritten pattern comparisons,
explicit mismatch reasons, full unmapped-loop inventory, trial source selections,
exclusive source counts, distinct executing workers plus team context, and executed
external-call events/counts/known sizes. The saved LLVM plugin and runtime hashes pin
these semantics. Current-source BFS profile IDs are reused only after byte hash and
source-extent verification; BC currently has no registered baseline profile package.

After tickets 06/07 land, freeze an estimated protocol using the measured T=4 target
snapshot, exact input/run arguments and `gapbs.trial_lambda.v1`, then run `estimate`
for both records. Its `regions` and `trials` are the per-region and whole-trial reports.
Unknown external-call costs, unsupported cache capacity/shape or aggregate-rate worker
scope remain unknown. Operation/bandwidth rates alone do not validate whole-call CPU
error. This ROI differs from the historical protected complete-call identities; those
historic timings are not yet paired application evidence.

Compact acceptance receipt should keep source/count/pipeline/binary hashes, graph and
trial identities, target/protocol hashes, validation result, all pattern comparisons,
per-region bounds/missing facts, and executed external-call inventory (known byte sizes
or explicit null). Do not copy raw traces or compiled ARM files. Keep ticket 05 claimed
until actual mbit10 reports and their acceptance evidence are captured.

Linux libomp was verified in `LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu`;
plain `lib/` does not contain it. Parent may dispatch raw output through the authorized
`/data` overflow symlink/volume instead of the illustrative `/data1` prefix above.
The shared fixture numerator rerun must explicitly pass
`--counting-pipeline source-normalized-v2`; registered runs always use v2.

Compact receipt helper (read-only, shared SWDB record-access boundary):

```sh
PYTHONPATH=. python3 .scratch/lanl-db-analytic-eval-2026-10-06/evidence/05-compact-reports.py --characterization /raw/bfs-characterization.json --estimate /raw/bfs-estimate.json --characterization /raw/bc-characterization.json --estimate /raw/bc-estimate.json --source-commit COUNTING_GIT_SHA --validate-log /raw/validate.log > /raw/05-compact-reports.json
```

Replace `/raw` with the parent's actual dispatch folder. Each estimate must match its
characterization ID. Unknown totals and byte sizes remain null; a known partial byte
subtotal is labeled separately. Zero-only region IDs and the full unmapped-loop list
remain represented, alongside every observed per-region bound and trial's executed
call inventory. This helper does not certify pairing with historical native timings.

`characterization.trials[].executed_calls` retains both external and emitted counted
call bodies, distinguished by `body_counted`. Counts/sizes are grouped per name, event
and region, with each original call site's count, size and line retained. Filter
`body_counted == false` with `cost_accounting == opaque_callee` for currently uncovered
external costs. Compiler annotation/arithmetic events retain their explicit semantic
accounting and execution counts. Distinct workers are
observed over one trial; they do not measure instantaneous or time-weighted concurrency
across changing frontier sweeps.


## Corrected intrinsic accounting receipt (a2)

The immutable a1 executions used counting source `67f1b3b` and are retained at
`origin/codex/lanl-registered-count-evidence` (`5d0fbdb`). Both g16 baseline runs
passed with five sources/trials and all handwritten comparisons. Their original
LLVM hint/checked-arithmetic accounting is not rewritten. The corrected plugin
records annotation events without runtime operation costs and counts checked
arithmetic explicitly; new runs require new IDs, binary/count/plugin hashes and
new output folders.

Parent dispatch commands from the corrected Git-synced source, after copying
current records and creating only the two parent output folders:

```sh
python3 -m swdb characterize --records /data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a2/records --adapter registered-gapbs --implementation gapbs-bfs-do --input kron-g16-k16 --threads 4 --trials 5 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --run-library-path /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu --timeout-s 1800 --output /data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a2/bfs/counted --id bfs.kron-g16.t4.characterization.a2 --format json > /data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a2/bfs/characterization.json
python3 -m swdb characterize --records /data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a2/records --adapter registered-gapbs --implementation gapbs-bc-brandes --input kron-g16-k16 --threads 4 --trials 5 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --run-library-path /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu --timeout-s 1800 --output /data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a2/bc/counted --id bc.kron-g16.t4.characterization.a2 --format json > /data/yanruj/EvolveSWDB_runs/lanl-analytic-counts-20261006-a2/bc/characterization.json
```

Freeze separate estimated protocols for BFS and BC against the merged measured T4
target description: `mode: estimated`, `estimator_version: swdb.analytic.v1`,
`roi: gapbs.trial_lambda.v1`, `threads: 4`, `inputs: [kron-g16-k16]`, and the matching
implementation in `sources`. `input_run_arguments.kron-g16-k16` is exactly
`['-g', '16', '-k', '16', '-n', '5']` for BFS, with `['-i', '1']` appended for BC.
The freeze persists the target snapshot/hash, calibration closure and implementation
bundle hash. After estimate/validate, the compact helper emits per-trial/per-region
costs and exact executed-call/worker inventories. All unsupported costs remain null.


Aggregate report interpretation (2026-10-06 ET): top-level per-region and bound
seconds are medians across trial estimates. Their input dictionaries are diagnostic
templates from the root/first observed bound, rather than one formula evaluation
that reproduces that median. `inputs_scope` labels this distinction in the compact
helper. Exact formula inputs are in `trials[].regions[].bounds[].inputs`. The overall
time is the median of complete per-trial region sums; region medians do not generally
sum to that overall median. Existing raw helper reports and estimate IDs/hashes stay
unchanged; metadata wrappers may add these interpretation labels.
