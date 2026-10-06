# Independent native service calibration

Created: 2026-10-06 ET. Ticket11; implementation in progress.

`import-cpu-service-calibration` retains service/driver elapsed trials and their
explicit event counts in a typed `cpu_service_calibration` record. It does not read
application timings. The cost is paired elapsed difference divided by the counted
work; raw subtraction values and spread remain visible. Any nonpositive residual
keeps the parameter unknown instead of clamping it to zero.

The current public tracer admits only an explicitly labeled hand fixture with
`--fixture`; its parameter basis is `reported`. Native import remains refused until
matching source-count, compiler/runtime and socket-lane evidence is implemented.
The receipt format is `swdb.cpu-service-calibration.v1`, with `machine`, `threads`,
`context`, `settings.repetitions`, `services[]` and canonical `identity_sha256`.
Each service names its unit, event definition, execution scope and denominator,
and retains paired `events`, `gross_seconds`, `driver_seconds` and order per trial.

```sh
python3 -m swdb import-cpu-service-calibration --records "$COPIED_RECORDS" \
  --receipt "$FIXTURE_RECEIPT" --id fixture.service.cost --fixture --format json
python3 -m swdb validate --records "$COPIED_RECORDS"
```

The CPU band will use fresh LLVM22/libomp T1 development timings and a separate
held-out input after implementation, independent calibration and development width
freeze. Historical GCC/libgomp baselines and candidate artifacts stay in honest
estimate/exclusion reports. Missing cost, memory-state or observation scope remains
unknown. Native CPU timing continues to decide CPU evaluations.
