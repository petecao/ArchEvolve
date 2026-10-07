# Fresh functional DX100 BFS counts and analytic report

Updated: 2026-10-06 20:34 ET. Parent owns Git source sync, copied records, socket leases and execution. Count source prerequisite: `502fea7` plus this proof/runbook commit; observer/model behavior is unchanged by these documents. Public registered canonical g8/T1 artifact count/freeze/estimate is green; this command's g16/T4 application result remains pending dispatch.

Run from `swdb-project/` in a clean immutable checkout. Create a fresh run directory and copy its authoritative `records/` into `records/` there. Replace `<newraw>` with that run directory. Preserve older record IDs and raw outputs. Wait until elapsed calibration releases its lane; count-only and elapsed calibration must not overlap.

```sh
python3 -m swdb characterize --records <newraw>/records --adapter registered-functional --source /data1/yanruj/EvolveSWDB_sources/cd21e025a0891507/bfs-functional-read-offload-20261006-a1.proposal/source/benchmarks/gapbs/src/bfs.cc --candidate bfs-functional-read-offload-20261006-a1.proposal.candidate-1 --input dx100-functional-kron-g16-k16 --threads 4 --trials 5 --object-scopes --counting-pipeline source-normalized-v2 --target-description dx100-e4fc4af-functional-analytic-v1.t4 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --run-library-path /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu --timeout-s 1800 --output <newraw>/counted --id bfs.functional.kron-g16.t4.characterization.objects.a1 --format json > <newraw>/characterization.json
```

The command verifies the immutable 25-file candidate tree `991de65287fe1fae3a20412704cccb6140a93f84cc11200032b20214f5174ff1`, source/input generator identity, full `kernel(g)` trial-lambda ROI, five source selections, actual worker/team context, loaded native runtime and declared allocator/interposer environment. Canonical wrapper/backend aliases bind their shipped source hashes and FUNC semantics. The packaging profile remains `contract_fixture`; candidate/source review labels remain unchanged. This is functional source execution for logical counting, distinct from the existing strict1.6 functional certificate and any MMIO/hardware execution.

Verify `python3 -m swdb validate --records <newraw>/records`. Keep raw LLVM IR, native binary, counts and stdout on mbit10. Export only compact source/input/trial/runtime/observer/target-policy hashes, sufficient counters and named missing facts. Instrumented driver timing text is excluded from estimator/role inputs and is never native or DX100 performance evidence. No address sequence, base or decoded row list is written by the observer.

The observed source accesses, functional target reads, private bookkeeping and derived logical transactions remain distinct. Fixed request windows close per command/worker and retain tails; placement is an explicitly inferred allocation-relative scenario, never physical DRAM placement or hardware row hits. Object views are distinct from full allocation extents. State-budget exhaustion and unsupported context keep affected quantities unknown.

After generic composition/sensitivity and all model modules stabilize, use that final source bundle to freeze a fresh estimate protocol against the unchanged literal counted target description. The count receipt retains its original observer/source/binary/policy identities. No implementation update is allowed during a measurement or between freezing and estimating. The exact registered protocol request is:

```yaml
message_version: '1.0'
id: bfs.functional.kron-g16.t4.estimate.protocol.a1
version: 1
settings:
  mode: estimated
  estimator_version: swdb.analytic.v1
  target_description: dx100-e4fc4af-functional-analytic-v1.t4
  threads: 4
  roi: gapbs.functional_trial_lambda.v1
  sources: [bfs-functional-read-offload-20261006-a1.proposal.candidate-1]
  inputs: [dx100-functional-kron-g16-k16]
  input_run_arguments:
    dx100-functional-kron-g16-k16: ['-g', '16', '-k', '16', '-n', '5']
```

Use the persisted ID returned by `freeze-protocol <request.yaml> --records <newraw>/records --format json` as `<protocol>`:

```sh
python3 -m swdb estimate --records <newraw>/records --characterization bfs.functional.kron-g16.t4.characterization.objects.a1 --target-description dx100-e4fc4af-functional-analytic-v1.t4 --protocol <protocol> --id bfs.functional.kron-g16.t4.estimate.a1 --format json > <newraw>/estimate.json
```

Inspect all five trial region reports before median aggregation. Required unknown host instruction rates, host memory model, mixed-domain overlap, setup, staging, queue service, parallelism and opaque whole-call costs keep total/ratio null; known component quantities remain visible. Rate filling cannot repair missing mechanisms or domain context. Adding a host memory mechanism, backend/surrogate correspondence or structural composition policy requires a fresh target version and observations under the strict count-reuse contract. The historical g16/k16 tuple and new input ID do not establish campaign blindness.

The companion [public proof](09-public-functional-count-proof.json) retains actual test hashes and scope. Fresh native CPU g16/g17 T1 commands are separately documented in [the object runbook](11-object-scopes-counting-runbook.md).


## Completed a2 execution and frozen report

Updated: 2026-10-06 21:15 ET. The original a1 failed before native execution on
static Linux LLVM because `opt` did not export `llvm::SHA256::hash`; its receipt
is preserved. The verified stateless native archive-member repair is `9ba9277`.
The fresh a2 run exited zero at 20:56:42 ET on node1, generation 534, with five
trials and 615 records valid. The [count receipt](09-functional-counts-mbit10-20261006-a2.json)
seals native archive/member hashes and the exact outcome-free execution arguments.

The final generic model/report source `e9d2c23`, clean merged execution tip
`bc26c9b`, froze protocol
`bfs.functional.kron-g16.t4.estimate.protocol.a2.3c10575e0635e4cc` using the same
request above with `.a2` IDs. Estimate
`bfs.functional.kron-g16.t4.estimate.a2` uses counted characterization
`bfs.functional.kron-g16.t4.characterization.objects.a2`. The persisted protocol
pins estimator bundle `3ad3ce75dc7ed90f7093c3a867ff187cf2884723adf7a98264b005c207018475`.
No source changes occurred during freeze/estimate; later integration merge
`408cc1a` changes progress prose only.

Both new canonical records and the [compact per-region report](09-functional-application-report-mbit10-20261006-a2.json)
are retained. Copied-store validation passed with 617 records; all 615 prior YAML
files are byte-identical. The [closeout proof](09-functional-estimate-closeout-20261006-a2.json)
distinguishes count self-identity/full record/file hashes and verifies every trial
region, bound, overhead, source choice and unknown result. Historical candidate/
source/fixture review labels remain unchanged. Whole-call seconds/ratio/error band
are unknown for the named numerical and structural premises; no speedup or
physical row-hit claim follows from the logical grouped-row fractions.
