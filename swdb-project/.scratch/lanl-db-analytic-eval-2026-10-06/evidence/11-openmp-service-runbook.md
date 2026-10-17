# Independent legal OpenMP count and elapsed probes

Created:2026-10-06 ET. This is the exact22-class plan in
`11-openmp-service-plan.md`. All costs remain unknown until actual native proofs,
legal event checks, library/environment identity and elapsed admission pass.
No application timing is requested. Parent owns preflight and lease dispatch.

Use a new clean immutable Git checkout plus a new external raw store copied from
canonical records. Keep full socket affinity on the collector; its timer pins one
physical core. The other socket must remain idle for elapsed work. Commands below
run from `swdb-project/` under the named socket0 lease. Set `LANL_OMP_RAW` to a new
`/data/yanruj/EvolveSWDB_runs/` folder containing its copied `records/` store.

```sh
export OMP_NUM_THREADS=1 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores
export LD_LIBRARY_PATH=/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu
python3 -m swdb.cpu_openmp_calibration --records "$LANL_OMP_RAW/records" --output "$LANL_OMP_RAW/count" --count-only --machine mbit10 --lane mbit10-evaluation-node0 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --max-wall-s 900
```

Verify four N3/5×service/driver proofs, exactly22 selected target classes, literal
ABI/immutable ident projection, matching normalized IR/map hashes and absence of
elapsed receipts. Prepare/cleanup and driver's actual event are explicit outside
callbacks. They are never presented as zero process-wide library calls.

After count proof is admitted, dispatch the following under a new lease with the
same immutable source, environment and idle-other-socket condition. The command
also retains fresh source proof within its own raw folder. Outer containment must
exceed the900s internal wall budget (recommended1200s) and preserve process-group
signal cleanup.

```sh
python3 -m swdb.cpu_openmp_calibration --records "$LANL_OMP_RAW/records" --output "$LANL_OMP_RAW/elapsed" --machine mbit10 --lane mbit10-evaluation-node0 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --repetitions 7 --min-trial-s .05 --max-wall-s 900
python3 -m swdb.cpu_openmp_calibration --validate-receipt "$LANL_OMP_RAW/elapsed/receipt.json"
python3 -m swdb import-cpu-service-calibration --records "$LANL_OMP_RAW/records" --receipt "$LANL_OMP_RAW/elapsed/receipt.json" --id mbit10.cpu.lanl20261006.service.openmp.a1 --format json
python3 -m swdb validate --records "$LANL_OMP_RAW/records" --format json
```

Every pair retains selected/driver legal-sequence counts, return sums, team size,
level and active-level checks. Both gross and empty-probe windows must reach50ms;
nonpositive paired costs remain null. Fork uses caller context; other events use
one serializedT1 team with legal state prepared/retired outside the window. Probe
clock interaction, independently constructed bounds and warmed serial transfer
are explicit premises, never physical latency or application accuracy evidence.

Export only typed calibration and compact sealed context/trial/projection metadata
through Git. Raw IR, native builds and addresses remain remote. Do not bind scalar
ABI costs until the exact application call-site/projection class guards are frozen;
application dynamic bounds remain inferred transfer and unsupported classes remain
unknown. This runbook makes no held-out application timing request.
