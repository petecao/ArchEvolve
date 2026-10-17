# Distinct floating64 monotonic atomic service

Created:2026-10-06 ET. Parent owns mbit10 preflight/leases/dispatch. The sealed
`11-float-memory-preregistration.json` freezes two independent sequential
uncontended prepared-buffer cells (32KiB/8MiB) before application outcomes. Exact
BC g16/g17 PBFS access.266 is floating64 `atomicrmw fadd monotonic`; integer
seq_cst add remains a separate cell. No application recount is needed: immutable
source_accesses already prove site, type, ordering and scoped logical counts.

Use the tested new immutable collector source, a new external raw directory and
copied records store. Full socket collector affinity is required; only its timer
pins one physical core. Keep the other lane idle for elapsed. All old sources,
integer costs, raw failures and records remain untouched. Set `LANL_FLOAT_RAW` to
a new `/data/yanruj/EvolveSWDB_runs/` root with its copied `records/` store.

```sh
export OMP_NUM_THREADS=1 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores
export LD_LIBRARY_PATH=/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu
python3 -m swdb.cpu_float_memory_calibration --records "$LANL_FLOAT_RAW/records" --output "$LANL_FLOAT_RAW/count" --count-only --machine mbit10 --lane mbit10-evaluation-node0 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --max-wall-s 900
```

Verify four N3/5 service/driver points: precisely N floating64 monotonic atomic
requests versus zero, no opaque helper, retained O3 exact primitive and matching
shared header/count source hashes. No elapsed receipt may exist in count-only
output. Native update values are checked separately outside the selected function.

After proof admission, dispatch fresh elapsed under a new named lease with the
same source and other socket idle. Use1200s outer containment for900s inner cap,
with existing process-group termination cleanup. Raw build cap64MiB and timed
metadata cap25MiB remain separate; live buffer cap8MiB, event cap134217728.

```sh
python3 -m swdb.cpu_float_memory_calibration --records "$LANL_FLOAT_RAW/records" --output "$LANL_FLOAT_RAW/elapsed" --machine mbit10 --lane mbit10-evaluation-node0 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --repetitions 7 --min-trial-s .05 --max-wall-s 900
python3 -m swdb import-cpu-service-calibration --records "$LANL_FLOAT_RAW/records" --receipt "$LANL_FLOAT_RAW/elapsed/receipt.json" --id mbit10.cpu.lanl20261006.service.float-memory.a1 --format json
python3 -m swdb.cpu_memory_resource --records "$LANL_FLOAT_RAW/records" --source-calibration mbit10.cpu.lanl20261006.service.float-memory.a1 --id mbit10.cpu.lanl20261006.resource.float-memory.a1 --format json
python3 -m swdb validate --records "$LANL_FLOAT_RAW/records" --format json
```

Gross brackets only the uninstrumented work loop; zero initialization, warm call
and per-element updated-value verification are outside. Seven alternating pairs
retain both windows/spread. Gross windows must reach50ms; driver resolution is
retained rather than silently given a matched threshold. Nonpositive source
residuals stay null. The separately typed gross resource freezes the existing
`gross_constructed_resource_v1` recipe: exact logical requests, includes driver
work, maximum composition with compute, inferred transfer. It establishes neither
physical instruction latency nor application locality/operand-state/upper bounds.

Export typed source/resource records and compact sealed proof/context/trial
summaries through Git. Add only the new resource ID to the final binder runbook;
keep integer/float parameters distinct. The model partitions exact site counts
before charging each primitive and cross-checks their sum against the unchanged
coarse add-update/8B observation. Other floating operations/orders, unresolved
source semantics or missing rates stay unknown. No application timing is requested.
