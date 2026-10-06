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
are capped at11, wall time at900s and output at25MiB. The runner currently requires
`--fixture`, so its host timings cannot become native calibration.

The importer admits only an explicitly labeled fixture with
`--fixture`; its parameter basis is `reported`. Native import remains refused until
matching compiler/runtime and socket-lane evidence is implemented. Adding
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
