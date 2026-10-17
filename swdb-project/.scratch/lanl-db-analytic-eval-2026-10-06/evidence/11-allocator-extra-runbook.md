# Prospective exact additional allocator bins

Created:2026-10-06 ET. The outcome-free g17 union requires array bins16384,
466112,524284 and1048568B. `11-allocator-extra-preregistration.json` freezes these
before application timing. Original allocator records/rates remain immutable.
The frozen1703c98 allocator helper/collector is unchanged. Parent owns dispatch.

Under the named socket0 lease, keep full collector affinity and the other socket
idle for elapsed. From the clean checkout's `swdb-project/`, set `LANL_ALLOC_RAW`
to a new external `/data/yanruj/EvolveSWDB_runs/` root containing its copied
`records/` store. Preserve count artifacts and a distinct elapsed output folder.
Use1200s outer containment with process-group cleanup for each900s inner CLI.

```sh
export OMP_NUM_THREADS=1 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores
export LD_LIBRARY_PATH=/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu
python3 -m swdb cpu-service-calibrate --records "$LANL_ALLOC_RAW/records" --output "$LANL_ALLOC_RAW/count" --service-group allocator --count-only --size 16384 --size 466112 --size 524284 --size 1048568 --machine mbit10 --lane mbit10-evaluation-node0 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --count-build-cap-mib 64 --max-wall-s 900 --format json
```

The existing coefficient proof testsN3/5×service/driver×four ABIs at the declared
minimum/maximum size endpoints (32points). The source forwards the dynamic size
to the exact allocator ABI; no intermediate-bin count measurement is claimed.
Four exact sizes are timed independently under all four ABIs (16cells). Rates
are never interpolated, and unused scalar bins receive no application charge.

After count admission, dispatch under a new lease with the same immutable source
and idle other socket:

```sh
python3 -m swdb cpu-service-calibrate --records "$LANL_ALLOC_RAW/records" --output "$LANL_ALLOC_RAW/elapsed" --service-group allocator --size 16384 --size 466112 --size 524284 --size 1048568 --machine mbit10 --lane mbit10-evaluation-node0 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --count-build-cap-mib 64 --repetitions 7 --min-trial-s .05 --max-wall-s 900 --format json
python3 -m swdb import-cpu-service-calibration --records "$LANL_ALLOC_RAW/records" --receipt "$LANL_ALLOC_RAW/elapsed/receipt.json" --id mbit10.cpu.lanl20261006.service.allocator-extra.a1 --format json
python3 -m swdb validate --records "$LANL_ALLOC_RAW/records" --format json
```

Keep any nonpositive paired cost null. Export only typed records and compact
sealed proof/context/trial metadata via Git; raw remains remote. Allocator-state
transfer stays inferred and separately guarded by compiler/runtime/control scope.
No application timing or error-band claim is authorized by this runbook.
