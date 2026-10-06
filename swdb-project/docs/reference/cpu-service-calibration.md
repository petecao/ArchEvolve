# Independent native service calibration

Created: 2026-10-06 ET. Ticket11; implementation in progress.

`import-cpu-service-calibration` retains service/driver elapsed trials and their
explicit event counts in a typed `cpu_service_calibration` record. It does not read
application timings. The cost is paired elapsed difference divided by the counted
work; raw subtraction values and spread remain visible. Any nonpositive residual
keeps the parameter unknown instead of clamping it to zero.

The portable runner times an independent clock-call loop and a matched driver. It
uses a pilot to select bounded work, alternates measurement order, retains every
trial, and consumes returned checksums outside timing. Compilation, pilot and
trials share the wall budget. Raw output stays outside the project; repetitions
are capped at11, wall time at900s and output at25MiB. Portable contract runs require `--fixture`; actual native admission is checked separately.

An explicitly labeled fixture requires `--fixture` and keeps parameter basis `reported`. Native clock import requires actual Linux/x86_64 LLVM22 timing on the registered
machine, a verified socket lane, clean committed source, a physical core, hash-bound
loaded C/C++ libraries, at least 7 repetitions and 0.05s paired pilot durations.
Counts and timed work use the identical shared header. Governor/turbo paths are
recorded as null when unavailable; no settings are changed. Adding
`--llvm-bin` runs six separate LLVM22 source-normalized-v2 count points against
the same shared service body:32/64/96 service iterations and matched drivers. The
clock numerator must be exactly one opaque ABI call per service iteration and
zero in the driver. The receipt retains the actual ABI name, pipeline, shared
header and count-driver hashes, observer hashes and all six characterization
hashes. These instrumented runs never supply elapsed calibration values.
The receipt format is `swdb.cpu-service-calibration.v1`, with `machine`, `threads`,
`context`, `settings.repetitions`, `services[]` and canonical `identity_sha256`.
Each service names its unit, event definition, execution scope and denominator,
and retains paired `events`, `gross_seconds`, `driver_seconds` and order per trial.

```sh
python3 -m swdb cpu-service-calibrate --records "$COPIED_RECORDS" \
  --output "$EXTERNAL_SERVICE_OUTPUT" --fixture --repetitions 3 \
  --min-trial-s 0.002 --max-wall-s 60 --format json
python3 -m swdb import-cpu-service-calibration --records "$COPIED_RECORDS" \
  --receipt "$FIXTURE_RECEIPT" --id fixture.service.cost --fixture --format json
python3 -m swdb validate --records "$COPIED_RECORDS"
```

The CPU band will use fresh LLVM22/libomp T1 development timings and a separate
held-out input after implementation, independent calibration and development width
freeze. Historical GCC/libgomp baselines and candidate artifacts stay in honest
estimate/exclusion reports. Missing cost, memory-state or observation scope remains
unknown. Native CPU timing continues to decide CPU evaluations.

`native_service_costs` consumes exact region-filtered call site counts through the
shared composition API. Descriptions select ABI names and seconds/call parameters
under host/serial-T1 scope; supported opaque service costs are additive. Full
site/count coverage clears that call only after a known service result. Zero
executions need no rate, counted callee bodies receive no second charge, and
unsupported length/lifecycle selectors or missing rates remain unknown.

`--count-only --llvm-bin ...` creates `count-proof.json` in the external raw folder
with `timings_collected: false`; it emits no elapsed trials or service rates. The
importer refuses this distinct `swdb.cpu-service-count-only.v1` format. Native
count-only execution retains the same verified lane, clean source and loaded ABI
identities, and is independent of application development/holdout timings.

Native count-only command inside the parent-owned node0 socket lane:

```sh
python3 -m swdb cpu-service-calibrate --records records --machine mbit10 \
  --lane mbit10-evaluation-node0 --count-only --max-wall-s 600 \
  --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin \
  --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
  --output "$NEW_EXTERNAL_COUNT_FOLDER" --format json
```

`--lane` is the exact lease-name claim, not a NUMA index. The numeric `0` claim
stopped the first remote attempt before any proof; that attempt supplies no
count/timing evidence. The corrected named lease still requires the real ancestor,
CPU affinity, memory bind policy and held lease checks; a matching string alone
does not authorize native execution. Use outer timeout900s and raw data mounts.

## Exact allocator cells (2026-10-06 ET)

`cpu-service-calibrate --service-group allocator` separately times array/scalar
allocation and deletion. The default matrix has20 cells: array sizes8192,65536,
227416,262144,524288B and scalar sizes8,16,32,64,128B, each with allocation and
free cost. These are the complete observed T1 BFS/BC allocation/lifetime bins in
`evidence/registered-counts-t1-mbit10-20261006-a1.json`. Different allocation/free
262144B totals reflect the ROI lifetime boundary. Explicit `--size` values test
all four operations at each selected bin.

One batch has at most65536 events and64MiB of live requested payload. A timed
pair has at most16777216 events, seven alternating-order repetitions,900s wall
budget and25MiB raw budget. Timed payload is untouched; the cap describes
requested live payload, not measured RSS. The gross pilot selects a batch count
with25% duration margin; native admission requires every gross repetition to
reach50ms. Each paired driver duration is retained even when shorter than50ms.
Unresolved subtraction remains null without clamping negative residuals.

The shared noinline C++11 body must retain all four ABI calls under actualO3
optimization. A separate source-normalized-v2 proof executes each operation at
3/5 events, service/driver, smallest/largest byte bins. It retains observed
allocation and free-lifetime size bins, exact ABI, count hashes and the shared
source identity. Count-only mode never runs the native timer or emits elapsed
receipts. Preparations and cleanup are outside both the counted service ROI and
timed segments.

The construction is `fresh_process_repeated_allocate_free_batches`. It measures
that construction's effective costs; transfer to the application's retained heap
state is **inferred** and requires an explicit model assumption. No physical
residency, page-fault rate or instruction-issue latency is claimed. Calibration
records preserve GLIBC_TUNABLES, actual MALLOC_* variables, preload/audit and
library-search controls. Their absence is meaningful only under the declared
scope. Legacy counted receipts lack this allocator-control declaration and cannot
prove equality. The glibc allocator [tunables](https://sourceware.org/glibc/manual/latest/html_node/Memory-Allocation-Tunables.html)
include cache and mapping thresholds, so matching requested sizes alone does not
establish allocator-state equivalence.

Parent-dispatched commands, in a clean immutable Linux checkout and a real named
node0 lease (raw folder must be new; use a different folder for each phase):

```sh
python3 -m swdb cpu-service-calibrate --records "$SWDB_RAW_RECORDS" \
  --service-group allocator --count-only --machine mbit10 \
  --lane mbit10-evaluation-node0 --llvm-bin "$SWDB_CPU_LLVM" \
  --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
  --output "$SWDB_ALLOCATOR_COUNT_RAW" --max-wall-s 600 --format json
```

After count proof and release of any other socket timing job:

```sh
python3 -m swdb cpu-service-calibrate --records "$SWDB_RAW_RECORDS" \
  --service-group allocator --machine mbit10 \
  --lane mbit10-evaluation-node0 --llvm-bin "$SWDB_CPU_LLVM" \
  --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
  --output "$SWDB_ALLOCATOR_ELAPSED_RAW" --repetitions 7 \
  --min-trial-s .05 --max-wall-s 900 --format json
python3 -m swdb import-cpu-service-calibration --records "$SWDB_RAW_RECORDS" \
  --receipt "$SWDB_ALLOCATOR_ELAPSED_RAW/receipt.json" \
  --id mbit10.cpu.lanl20261006.service.allocator.a1 --format json
python3 -m swdb validate --records "$SWDB_RAW_RECORDS"
```

Use600s inner/900s outer for count-only and900s inner/1200s outer for elapsed.
Keep node1 idle during elapsed calibration. Raw binaries, IR and logs stay remote;
only the typed service record and compact receipt metadata enter Git. Application
accuracy remains unsupported until every executed memory/runtime service and the
matched original-driver timing scope are admitted independently.
