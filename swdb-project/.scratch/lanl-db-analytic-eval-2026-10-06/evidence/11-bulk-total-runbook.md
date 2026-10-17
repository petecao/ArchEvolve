# Independent gross bulk resource follow-up

Created:2026-10-06 ET. Parent owns preflight, socket leases and dispatch. The
original aaf9a9d paired-window attempt, its failures/partial output and all existing
records remain immutable. No application outcome has been observed. This distinct
recipe is preregistered in `11-bulk-total-preregistration.json` (identity
`1e3f1ea6c00c9c5c1c9bf11f32ef79f5b7e57676057b504d7735f5c9cae70022`).

The native helper is unchanged: gross brackets only its uninstrumented exact-copy
work loop; allocation, copy correctness and sixteen warm copies are outside it.
Gross/event includes constructed loop control. Driver/event remains a diagnostic.
A short driver never yields a known paired subtraction. The derived typed gross
resource is an inferred conditional additive overhead; it establishes neither
physical instruction latency nor a proven application upper bound. Profile maxima
remain conditional, with actual application overlap/alignment unverified.

Use a new clean immutable Git worktree/source and new raw root. Preserve full
socket affinity for the collector: **do not taskset the Python collector to CPU0**.
The validated timer pins one physical core itself. Keep the other socket idle for
elapsed commands. Copy canonical YAML records to the external raw store before
this block; this block writes only that store and new raw output folders.

Under the named socket0 lease, from the clean checkout's `swdb-project/`, set
`LANL_BULK_RAW` to a new `/data/yanruj/EvolveSWDB_runs/` folder whose `records/`
already exists. Set `LANL_BULK_PHASE=count` for the first dispatch; after its proofs
are verified, use `LANL_BULK_PHASE=elapsed` under a new named lease. Both phases
preserve every artifact. Use >=2200s outer containment per phase, with parent
process-group cleanup retained; each CLI has its own900s inner wall cap.

```sh
export OMP_NUM_THREADS=1 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores
export LD_LIBRARY_PATH=/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu
python3 - <<'PY'
import json, os, subprocess
from pathlib import Path
raw=Path(os.environ['LANL_BULK_RAW'])
phase=os.environ['LANL_BULK_PHASE']
assert phase in ('count','elapsed') and (raw/'records').is_dir()
plan=json.loads(Path('.scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-bulk-total-preregistration.json').read_text())
for batch in plan['batches']:
    argv=['python3','-m','swdb.cpu_bulk_total_calibration','--records',str(raw/'records'),
        '--output',str(raw/(batch['id']+'.'+phase)), '--machine','mbit10','--lane','mbit10-evaluation-node0',
        '--llvm-bin','/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin',
        '--toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13',
        '--repetitions','7','--min-trial-s','.05','--max-wall-s','900']
    if phase=='count':argv+=['--count-only']
    for n in batch['memmove_sizes']:argv+=['--size',str(n)]
    subprocess.run(argv,check=True,timeout=1050)
PY
```

After elapsed success, import each source calibration then derive its fresh typed
resource. Use separate IDs per batch; do not pool duplicated memcpy8 cells.

```sh
python3 -m swdb import-cpu-service-calibration --records "$LANL_BULK_RAW/records" --receipt "$LANL_BULK_RAW/bulk.a1.elapsed/receipt.json" --id mbit10.cpu.lanl20261006.service.bulk-total.a1 --format json
python3 -m swdb.cpu_bulk_resource --records "$LANL_BULK_RAW/records" --source-calibration mbit10.cpu.lanl20261006.service.bulk-total.a1 --id mbit10.cpu.lanl20261006.resource.bulk-total.a1 --format json
python3 -m swdb import-cpu-service-calibration --records "$LANL_BULK_RAW/records" --receipt "$LANL_BULK_RAW/bulk.a2.elapsed/receipt.json" --id mbit10.cpu.lanl20261006.service.bulk-total.a2 --format json
python3 -m swdb.cpu_bulk_resource --records "$LANL_BULK_RAW/records" --source-calibration mbit10.cpu.lanl20261006.service.bulk-total.a2 --id mbit10.cpu.lanl20261006.resource.bulk-total.a2 --format json
python3 -m swdb validate --records "$LANL_BULK_RAW/records" --format json
```

Export only compact source/resource records, sealed receipt/context/trial summaries
and preregistration/commit references via Git. Raw binaries, normalized IR and
addresses remain remote. Source records retain null residuals and full spread.
The binder consumes resource records only under their explicit cost recipe; its
existing exact-byte/profile/call-coverage/context guards continue to apply.
