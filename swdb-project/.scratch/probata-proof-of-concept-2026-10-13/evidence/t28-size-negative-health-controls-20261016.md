# Strict size-negative acceptance — 2026-10-16 ET

Test-only successor`2b25ee6c7021e467176d3086f2560f5e7c5da7e8` fixes an
acceptance gap without changing production, backend failure classification,
method flags, source/model contracts or the retained actual7e642 producer.
The parent reports that original actual pytest exited0 although the negative
record was solver_error: its complete ensures results were failed/unknown/timeout,
with best timeout. That is not a healthy negative control. This producer did
not fetch/rehash the remote artifacts or diagnose that solver error; root owns
those cold audits and any later formal admission. Historical exits are unchanged.

The negative assertion now permits only ordinary unknown/timeout, requires one
SHA-pinned complete native WP inventory with unique identical goal census and
matching passed/smoke fields, and reads every prover result. Failed, computing,
invalid and unrecognized statuses refuse even if the best result is unknown or
timeout. An empty/all-untried ordinary goal cannot count as an attempted healthy
nonproof. Existing ensures-only-open, valid-smoke, nonvacuity and unrelated-RTE
checks remain. Positive proven/all-ordinary-valid/all-smoke-valid acceptance is
unchanged. None of these criteria interprets a negative as a refutation.

Pure controls retain RED13fail/5pass (0.70s/70MB), initial GREEN21pass/3actualSKIP
and final GREEN24pass/3actualSKIP (0.60s/71MB), under workerB and the8GiB/300s
guard. No actual tool, compiler, version, configuration or SSH probe ran. The
companion JSON pins both changed test modules, commands/logs/JUnit/resources,
guards and producer. All production/library/API bytes equal integrationffb967;
7e642 source and entryv2 remain immutable. The new test hash requires a separately
reviewed source/entry repin before any future actual run. Ticket28 remains open;
this patch is acceptance bookkeeping, not new actual proof evidence.
