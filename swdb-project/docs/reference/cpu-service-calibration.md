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
